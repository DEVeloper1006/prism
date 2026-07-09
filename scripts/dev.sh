#!/usr/bin/env bash
set -euo pipefail

echo "Starting PRISM development environment..."

# Start Python backend
echo "Starting Python backend on port 8420..."
cd "$(dirname "$0")/../backend"
python3 main.py &
BACKEND_PID=$!

# Start Tauri dev mode (includes Vite)
cd "$(dirname "$0")/.."
echo "Starting Tauri + Vite..."
npm run tauri dev

# Cleanup
kill $BACKEND_PID 2>/dev/null || true
