# =============================================================================
# OptiMatch - Setup Script
# Prepares a fresh machine and builds run.exe
# Usage: Right-click setup.bat -> "Run as administrator"  (or: .\setup.ps1)
# =============================================================================

$ErrorActionPreference = "Stop"

$PROJECT_ROOT  = Split-Path -Parent $MyInvocation.MyCommand.Path
$VENV_DIR      = Join-Path $PROJECT_ROOT ".venv"
$BACKEND_DIR   = Join-Path $PROJECT_ROOT "backend"
$FRONTEND_DIR  = Join-Path $PROJECT_ROOT "frontend"
$MODELS_DIR    = Join-Path $BACKEND_DIR "src\app\ml\models"
$MODEL_PATH    = Join-Path $MODELS_DIR "arcface_w600k_r50.onnx"
$MODEL_URL     = "https://huggingface.co/facefusion/models-3.0.0/resolve/main/arcface_w600k_r50.onnx"
$REQUIREMENTS  = Join-Path $PROJECT_ROOT "requirements.txt"

# ── Helpers ──────────────────────────────────────────────────────────────────

function Write-Step { param([string]$msg)  Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Write-Ok   { param([string]$msg)  Write-Host "    [OK] $msg" -ForegroundColor Green }
function Write-Warn { param([string]$msg)  Write-Host "    [WARN] $msg" -ForegroundColor Yellow }
function Write-Fail { param([string]$msg)  Write-Host "`n[ERROR] $msg" -ForegroundColor Red; exit 1 }

# ── Step 1: Check Python ──────────────────────────────────────────────────────

Write-Step "Checking Python..."
try {
    $pyVersion = & python --version 2>&1
    if ($pyVersion -match "Python (\d+)\.(\d+)") {
        $major = [int]$Matches[1]; $minor = [int]$Matches[2]
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 9)) {
            Write-Fail "Python 3.9+ required, found: $pyVersion. Download from https://python.org"
        }
        Write-Ok "$pyVersion"
    } else {
        Write-Fail "Could not determine Python version. Download from https://python.org"
    }
} catch {
    Write-Fail "Python not found. Download from https://python.org"
}

# ── Step 2: Check Node.js / npm ───────────────────────────────────────────────

Write-Step "Checking Node.js / npm..."
try {
    $nodeVersion = & node --version 2>&1
    $npmVersion  = & npm  --version 2>&1
    Write-Ok "Node $nodeVersion  /  npm $npmVersion"
} catch {
    Write-Fail "Node.js not found. Download from https://nodejs.org"
}

# ── Step 3: Create virtual environment ───────────────────────────────────────

Write-Step "Setting up Python virtual environment..."
if (-not (Test-Path $VENV_DIR)) {
    & python -m venv $VENV_DIR
    Write-Ok "Created .venv"
} else {
    Write-Ok ".venv already exists — skipping creation"
}

$PIP    = Join-Path $VENV_DIR "Scripts\pip.exe"
$PYTHON = Join-Path $VENV_DIR "Scripts\python.exe"

# ── Step 4: Install Python dependencies ──────────────────────────────────────

Write-Step "Installing Python dependencies from requirements.txt..."
& $PIP install --upgrade pip --quiet
& $PIP install -r $REQUIREMENTS
Write-Ok "Python packages installed"

# ── Step 5: Install PyInstaller ───────────────────────────────────────────────

Write-Step "Installing PyInstaller..."
& $PIP install pyinstaller --quiet
Write-Ok "PyInstaller ready"

# ── Step 6: Download ArcFace model ───────────────────────────────────────────

Write-Step "Checking ArcFace model..."
if (Test-Path $MODEL_PATH) {
    Write-Ok "Model already present — skipping download"
} else {
    Write-Host "    Downloading arcface_w600k_r50.onnx from HuggingFace (~170 MB)..." -ForegroundColor Yellow
    try {
        $ProgressPreference = "SilentlyContinue"
        Invoke-WebRequest -Uri $MODEL_URL -OutFile $MODEL_PATH -UseBasicParsing
        $ProgressPreference = "Continue"
        Write-Ok "Model downloaded to $MODEL_PATH"
    } catch {
        Write-Fail "Failed to download ArcFace model: $_`nManual download: $MODEL_URL"
    }
}

# ── Step 7: Install frontend dependencies ────────────────────────────────────

Write-Step "Installing frontend npm dependencies..."
Push-Location $FRONTEND_DIR
& npm install
Pop-Location
Write-Ok "Frontend packages installed"

# ── Step 8: Build run.exe ─────────────────────────────────────────────────────

Write-Step "Building run.exe with PyInstaller..."
$PYINSTALLER = Join-Path $VENV_DIR "Scripts\pyinstaller.exe"
Push-Location $PROJECT_ROOT
& $PYINSTALLER --onefile --console --name "run" run.py
Pop-Location
Write-Ok "Build complete"

# ── Step 9: Copy EXE to project root ─────────────────────────────────────────

Write-Step "Deploying run.exe to project root..."
$SRC = Join-Path $PROJECT_ROOT "dist\run.exe"
$DST = Join-Path $PROJECT_ROOT "run.exe"

if (Test-Path $DST) {
    try {
        Remove-Item $DST -Force
    } catch {
        Write-Fail "Cannot overwrite run.exe — make sure it is not running, then re-run setup."
    }
}
Copy-Item $SRC $DST -Force
Write-Ok "run.exe deployed to project root"

# ── Done ──────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Setup complete!  Run:  .\run.exe          " -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
