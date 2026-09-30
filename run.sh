#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

python3 -m venv .venv 2>/dev/null || true
source .venv/bin/activate
pip install -q -r requirements.txt

[ -f .env ] || cp .env.example .env

echo "Draait op http://localhost:8000"
PYTHONPATH=backend uvicorn app.main:app --reload --port 8000 --app-dir backend
