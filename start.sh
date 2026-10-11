#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$HERE/backend"
FRONTEND="$HERE/frontend"

echo "Starting ProductHunter AI local environment..."
echo "Repo root: $HERE"

echo "Opening backend terminal..."
if command -v gnome-terminal >/dev/null 2>&1; then
  gnome-terminal -- bash -c "cd '$BACKEND' && bash launch_backend.sh"
elif command -v x-terminal-emulator >/dev/null 2>&1; then
  x-terminal-emulator -e "bash -c 'cd \"$BACKEND\" && bash launch_backend.sh; exec bash'"
else
  echo "Open a terminal in $BACKEND and run: bash launch_backend.sh"
fi

sleep 2

echo "Opening frontend terminal..."
if command -v gnome-terminal >/dev/null 2>&1; then
  gnome-terminal -- bash -c "cd '$FRONTEND' && npm install && npm run dev"
elif command -v x-terminal-emulator >/dev/null 2>&1; then
  x-terminal-emulator -e "bash -c 'cd \"$FRONTEND\" && npm install && npm run dev; exec bash'"
else
  echo "Open a terminal in $FRONTEND and run: npm install && npm run dev"
fi

echo "Backend API: http://localhost:8000"
echo "Frontend: http://localhost:3000"
