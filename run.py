#!/usr/bin/env python3
"""
Run backend (FastAPI) and frontend (Vite) together.
Usage: python run.py   or   run.exe
Press Ctrl+C to stop both.

Ports and backend constants can be configured via config.json placed next to
this file (or next to run.exe when frozen).
"""
import json
import subprocess
import sys
import signal
import os
import shutil
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

# When frozen by PyInstaller, __file__ lives inside a temp _MEIPASS directory.
# Use sys.executable's parent instead so PROJECT_ROOT always points to the
# folder containing .venv/, backend/, frontend/, and config.json.
PROJECT_ROOT = (
    Path(sys.executable).resolve().parent
    if getattr(sys, "frozen", False)
    else Path(__file__).resolve().parent
)
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

processes = []

# ── Config ────────────────────────────────────────────────────────────────────

DEFAULT_CONFIG: dict = {
    "backend":        {"host": "0.0.0.0", "port": 8000, "reload": True},
    "frontend":       {"port": 5173},
    "face_detection": {"confidence_threshold": 0.5, "min_face_size": 64},
    "embedding":      {"model": "ArcFace"},
    "faiss":          {"ivf_nlist": 100},
    "paths":          {"data_dir": "backend/data"},
}


def load_config() -> dict:
    config_path = PROJECT_ROOT / "config.json"
    if not config_path.exists():
        print("[warn] config.json not found, using defaults")
        return DEFAULT_CONFIG
    with open(config_path) as f:
        user = json.load(f)
    # Deep merge: user values override defaults, missing keys fall back silently
    return {
        section: {**DEFAULT_CONFIG[section], **user.get(section, {})}
        for section in DEFAULT_CONFIG
    }


def resolve_path(raw: str) -> Path:
    """Resolve a path from config: absolute paths are used as-is,
    relative paths are resolved relative to PROJECT_ROOT."""
    p = Path(raw)
    return p if p.is_absolute() else (PROJECT_ROOT / p).resolve()

# ── Helpers ───────────────────────────────────────────────────────────────────

def find_venv_python():
    """Return the venv Python executable if it exists, otherwise sys.executable."""
    if sys.platform == "win32":
        venv_python = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
    else:
        venv_python = PROJECT_ROOT / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def ensure_backend_deps(python_exe):
    """Install backend API deps (fastapi, uvicorn) if not found."""
    missing = []
    for mod in ("fastapi", "uvicorn"):
        try:
            subprocess.run(
                [python_exe, "-c", f"import {mod}"],
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError:
            missing.append("fastapi" if mod == "fastapi" else "uvicorn[standard]")
    if missing:
        pkgs = ["fastapi", "uvicorn[standard]", "python-multipart"]
        print("Installing backend API dependencies...")
        subprocess.run(
            [python_exe, "-m", "pip", "install"] + pkgs,
            check=True,
        )


def find_npm():
    """Find npm/npx - check PATH and common Windows paths. Returns (path, use_npx, node_dir)."""
    for name in ("npm", "npm.cmd"):
        path = shutil.which(name)
        if path:
            node_dir = str(Path(path).parent)
            return path, False, node_dir
    for name in ("npx", "npx.cmd"):
        path = shutil.which(name)
        if path:
            node_dir = str(Path(path).parent)
            return path, True, node_dir
    # Windows: try Node.js default install
    for base in [
        os.environ.get("ProgramFiles", "C:\\Program Files"),
        os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
    ]:
        node_dir = Path(base) / "nodejs"
        if not node_dir.exists():
            continue
        node_dir_str = str(node_dir)
        for cmd, use_npx in (("npm.cmd", False), ("npx.cmd", True), ("npm", False), ("npx", True)):
            p = node_dir / cmd
            if p.exists():
                return str(p), use_npx, node_dir_str
    return None, False, None


def env_with_node(node_dir):
    """Return env dict with node_dir prepended to PATH so 'node' is found."""
    env = os.environ.copy()
    sep = ";" if sys.platform == "win32" else ":"
    env["PATH"] = node_dir + sep + env.get("PATH", "")
    return env


def kill_all():
    for p in processes:
        try:
            p.terminate()
            p.wait(timeout=3)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass


def sig_handler(signum, frame):
    kill_all()
    sys.exit(0)


def _open_url(url: str) -> None:
    """Open a URL in the default browser.
    Uses os.startfile on Windows (reliable in frozen PyInstaller EXEs)
    and webbrowser.open on other platforms."""
    if sys.platform == "win32":
        os.startfile(url)
    else:
        webbrowser.open(url)


def open_browser_when_ready(frontend_url: str, backend_url: str, timeout: int = 60) -> None:
    """Poll the backend /health endpoint until it responds with any HTTP status,
    then open the frontend in the default browser.
    Runs in a daemon thread so it never blocks the main process."""
    import urllib.error
    health_url = backend_url.rstrip("/") + "/health"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(health_url, timeout=2)
            print(f"[browser] Backend is ready — opening {frontend_url}")
            _open_url(frontend_url)
            return
        except urllib.error.HTTPError:
            print(f"[browser] Backend is ready — opening {frontend_url}")
            _open_url(frontend_url)
            return
        except Exception:
            # Connection refused or timeout — backend not ready yet
            time.sleep(1)
    print(f"[warn] Backend did not respond within {timeout}s — browser not opened automatically.")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not (BACKEND_DIR / "src" / "app" / "web" / "server.py").exists():
        print("Error: backend/src/app/web/server.py not found")
        sys.exit(1)
    if not (FRONTEND_DIR / "package.json").exists():
        print("Error: frontend/package.json not found")
        sys.exit(1)

    cfg = load_config()

    python_exe = find_venv_python()
    ensure_backend_deps(python_exe)

    npm_path, use_npx, node_dir = find_npm()
    if not npm_path:
        print("Error: npm not found. Install Node.js from https://nodejs.org")
        sys.exit(1)
    node_env = env_with_node(node_dir) if node_dir else None

    # Frontend: always run npm install to pick up any dependency changes
    if use_npx:
        print("Note: Run 'npm install' in frontend/ first. Trying npx vite...")
    else:
        print("Installing frontend dependencies...")
        subprocess.run(
            [npm_path, "install"],
            cwd=str(FRONTEND_DIR),
            check=True,
            env=node_env,
        )

    # Resolve paths from config (relative → absolute based on PROJECT_ROOT)
    data_dir = resolve_path(cfg["paths"]["data_dir"])

    # Backend env — pass config values so backend/src/app/config.py picks them up
    backend_env = os.environ.copy()
    backend_env.update({
        "FACE_CONFIDENCE_THRESHOLD": str(cfg["face_detection"]["confidence_threshold"]),
        "MIN_FACE_SIZE":             str(cfg["face_detection"]["min_face_size"]),
        "EMBEDDING_MODEL":           cfg["embedding"]["model"],
        "IVF_NLIST":                 str(cfg["faiss"]["ivf_nlist"]),
        "DATA_DIR":                  str(data_dir),
    })

    # Backend: uvicorn started from backend/ so src.app.* imports resolve correctly
    backend_cmd = [
        python_exe, "-m", "uvicorn", "src.app.web.server:app",
        "--host", cfg["backend"]["host"],
        "--port", str(cfg["backend"]["port"]),
    ]
    if cfg["backend"]["reload"]:
        backend_cmd.append("--reload")

    backend = subprocess.Popen(
        backend_cmd,
        cwd=str(BACKEND_DIR),
        stdout=sys.stdout,
        stderr=sys.stderr,
        env=backend_env,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
    )
    processes.append(backend)

    # Frontend: npm run dev -- --port <N>  (or npx vite --port <N>)
    if use_npx:
        frontend_cmd = [npm_path, "vite", "--port", str(cfg["frontend"]["port"])]
    else:
        frontend_cmd = [npm_path, "run", "dev", "--", "--port", str(cfg["frontend"]["port"])]

    frontend_kw = dict(
        cwd=str(FRONTEND_DIR),
        stdout=sys.stdout,
        stderr=sys.stderr,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
    )
    if node_env:
        frontend_kw["env"] = node_env
    frontend = subprocess.Popen(frontend_cmd, **frontend_kw)
    processes.append(frontend)

    signal.signal(signal.SIGINT, sig_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, sig_handler)

    backend_url  = f"http://localhost:{cfg['backend']['port']}"
    frontend_url = f"http://localhost:{cfg['frontend']['port']}"

    browser_thread = threading.Thread(
        target=open_browser_when_ready,
        args=(frontend_url, backend_url),
        daemon=True,
    )
    browser_thread.start()

    print("\n--- Visual Investigator ---")
    print(f"Backend:  {backend_url}")
    print(f"Frontend: {frontend_url}")
    print("Press Ctrl+C to stop\n")

    try:
        backend.wait()
    except KeyboardInterrupt:
        pass
    finally:
        kill_all()


if __name__ == "__main__":
    main()
