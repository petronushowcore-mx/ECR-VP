#!/usr/bin/env bash
#
# Build frontend and serve everything from FastAPI on port 8000
# This is the production / single-port deployment mode.
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "  Building frontend..."
cd "$SCRIPT_DIR/frontend"
npm install
npm run build

echo "  Copying build to backend static dir..."
rm -rf "$SCRIPT_DIR/backend/static"
cp -r dist "$SCRIPT_DIR/backend/static"

echo ""
echo "  Build complete. Start with:"
echo "    cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "  Then open http://localhost:8000"
