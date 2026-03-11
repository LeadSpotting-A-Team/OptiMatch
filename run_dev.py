#!/usr/bin/env python3
"""
Run backend (FastAPI) and frontend (Vite) together.
Usage: python run_dev.py
Press Ctrl+C to stop both.
"""
import subprocess
import sys
import signal
import os
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

processes = []


def ensure_backend_deps():
    """Install backend API deps (fastapi, uvicorn) if not found."""
    missing = []
    for mod in ("fastapi", "uvicorn"):
        try:
            subprocess.run(
                [sys.executable, "-c", f"import {mod}"],
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError:
            missing.append("fastapi" if mod == "fastapi" else "uvicorn[standard]")
    if missing:
        pkgs = ["fastapi", "uvicorn[standard]", "python-multipart"]
        print("Installing backend API dependencies...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install"] + pkgs,
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


def main():
    if not (BACKEND_DIR / "api_server.py").exists():
        print("Error: backend/api_server.py not found")
        sys.exit(1)
    if not (FRONTEND_DIR / "package.json").exists():
        print("Error: frontend/package.json not found")
        sys.exit(1)

    ensure_backend_deps()

    npm_path, use_npx, node_dir = find_npm()
    if not npm_path:
        print("Error: npm not found. Install Node.js from https://nodejs.org")
        sys.exit(1)
    node_env = env_with_node(node_dir) if node_dir else None

    # Frontend: ensure deps installed (need npm for install)
    if not (FRONTEND_DIR / "node_modules").exists():
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

    # Backend: uvicorn (from backend dir so imports work)
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api_server:app", "--reload", "--host", "0.0.0.0"],
        cwd=str(BACKEND_DIR),
        stdout=sys.stdout,
        stderr=sys.stderr,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
    )
    processes.append(backend)

    # Frontend: npm run dev or npx vite
    frontend_cmd = [npm_path, "vite"] if use_npx else [npm_path, "run", "dev"]
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

    print("\n--- Visual Investigator ---")
    print("Backend:  http://localhost:8000")
    print("Frontend: http://localhost:5173")
    print("Press Ctrl+C to stop\n")

    try:
        backend.wait()
    except KeyboardInterrupt:
        pass
    finally:
        kill_all()


if __name__ == "__main__":
    main()
