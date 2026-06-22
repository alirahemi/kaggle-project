#!/usr/bin/env bash
# Start local development stack: Postgres, Redis, API, Streamlit
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "Creating .env from .env.example"
  cp .env.example .env
fi

echo "Starting infrastructure with docker compose…"
docker compose up -d postgres redis

echo "Waiting for Postgres…"
until docker compose exec -T postgres pg_isready -U bureaucracy -d bureaucracy >/dev/null 2>&1; do
  sleep 1
done

if [[ "${1:-}" == "--docker" ]]; then
  echo "Starting API and Streamlit containers…"
  docker compose up -d api streamlit
  echo "API:       http://localhost:8000"
  echo "Streamlit: http://localhost:8501"
  exit 0
fi

echo "Starting API gateway (uvicorn)…"
export PYTHONPATH="$ROOT"
uvicorn apps.api_gateway.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

echo "Starting Streamlit…"
streamlit run apps/streamlit_app/app.py --server.port 8501 &
ST_PID=$!

trap 'kill $API_PID $ST_PID 2>/dev/null || true' EXIT

echo "API:       http://localhost:8000"
echo "Streamlit: http://localhost:8501"
echo "Press Ctrl+C to stop."

wait
