#!/usr/bin/env bash
set -euo pipefail

if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python -m venv .venv
fi

source .venv/bin/activate
pip install -r requirements.txt --quiet

export POSTGRES_DSN="${POSTGRES_DSN:-postgresql+psycopg://producthunter:producthunter_local_dev_password@localhost:5432/producthunter}"
export REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"

alembic upgrade head

exec uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
