#!/usr/bin/env bash
set -euo pipefail

echo "Building PRISM for production..."

# Install Python dependencies
echo "Installing Python dependencies..."
cd "$(dirname "$0")/../backend"
pip install -r requirements.txt

# Build Tauri app (includes Vite build)
cd "$(dirname "$0")/.."
echo "Building Tauri application..."
npm run tauri build

echo "Build complete."
