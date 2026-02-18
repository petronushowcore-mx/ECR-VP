#!/usr/bin/env bash
#
# ECR-VP Execution Shell — Start both backend and frontend
#
# Usage:
#   chmod +x start.sh
#   ./start.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "  ╔═══════════════════════════════════════════╗"
echo "  ║   ECR-VP · Verification Protocol Shell    ║"
echo "  ║   Inspired by Navigational Cybernetics 2.5║"
echo "  ╚═══════════════════════════════════════════╝"
echo ""

# ─── Check prerequisites ─────────────────────────────────────────────

check_cmd() {
  if ! command -v "$1" &>/dev/null; then
    echo "  ✗ $1 not found. $2"
    exit 1
  fi
  echo "  ✓ $1 found"
}

echo "  Checking prerequisites..."
check_cmd python3 "Install Python 3.12+: https://python.org"
check_cmd node "Install Node.js 18+: https://nodejs.org"
check_cmd npm "Comes with Node.js"
echo ""

# ─── Backend setup ────────────────────────────────────────────────────

echo "  ── Backend ──────────────────────────────────"
cd "$SCRIPT_DIR/backend"

if [ ! -d "venv" ]; then
  echo "  Creating Python virtual environment..."
  python3 -m venv venv
fi

echo "  Activating venv and installing dependencies..."
source venv/bin/activate
pip install -q -r requirements.txt

# Load .env if present
if [ -f "$SCRIPT_DIR/.env" ]; then
  echo "  Loading .env..."
  set -a
  source "$SCRIPT_DIR/.env"
  set +a
fi

echo "  Starting FastAPI backend on port 8000..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "  Backend PID: $BACKEND_PID"
echo ""

# ─── Frontend setup ──────────────────────────────────────────────────

echo "  ── Frontend ─────────────────────────────────"
cd "$SCRIPT_DIR/frontend"

if [ ! -d "node_modules" ]; then
  echo "  Installing npm dependencies..."
  npm install
fi

echo "  Starting Vite dev server on port 3000..."
npm run dev &
FRONTEND_PID=$!
echo "  Frontend PID: $FRONTEND_PID"
echo ""

# ─── Ready ────────────────────────────────────────────────────────────

sleep 2
echo ""
echo "  ╔═══════════════════════════════════════════╗"
echo "  ║           Everything is running!           ║"
echo "  ╠═══════════════════════════════════════════╣"
echo "  ║                                           ║"
echo "  ║  Frontend:  http://localhost:3000          ║"
echo "  ║  Backend:   http://localhost:8000          ║"
echo "  ║  API docs:  http://localhost:8000/docs     ║"
echo "  ║                                           ║"
echo "  ║  Press Ctrl+C to stop both servers        ║"
echo "  ╚═══════════════════════════════════════════╝"
echo ""

# Trap Ctrl+C to kill both processes
trap "echo '  Shutting down...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM

# Wait for either process to exit
wait
