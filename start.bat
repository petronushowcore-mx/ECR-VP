@echo off
echo ═══════════════════════════════════════════════
echo  ECR-VP Execution Shell — Starting...
echo ═══════════════════════════════════════════════
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install from https://python.org
    pause
    exit /b 1
)

:: Check Node
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found. Install from https://nodejs.org
    pause
    exit /b 1
)

:: Setup backend venv if needed
if not exist "backend\venv" (
    echo [SETUP] Creating Python virtual environment...
    cd backend
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
    cd ..
) 

:: Setup frontend if needed
if not exist "frontend\node_modules" (
    echo [SETUP] Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
)

:: Check .env
if not exist "backend\.env" (
    echo [WARNING] No backend\.env found. Copying from .env.example...
    copy .env.example backend\.env
    echo [INFO] Edit backend\.env and add your API keys, then run this script again.
    pause
    exit /b 0
)

echo.
echo [1/2] Starting backend on port 8000...
start "ECR-VP Backend" cmd /k "cd backend && venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload --port 8000"

timeout /t 3 /nobreak >nul

echo [2/2] Starting frontend on port 3000...
start "ECR-VP Frontend" cmd /k "cd frontend && npm run dev"

timeout /t 3 /nobreak >nul

echo.
echo ═══════════════════════════════════════════════
echo  ECR-VP is running at http://localhost:3000
echo  Backend API at http://localhost:8000/api
echo ═══════════════════════════════════════════════
echo.
echo Press any key to open in browser...
pause >nul
start http://localhost:3000
