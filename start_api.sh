#!/bin/bash
# Wait for postgres to be ready before starting the API.
# pg_isready polls the socket — no application-level retry needed.
echo "[start_api] Waiting for postgres..."
until pg_isready -h 127.0.0.1 -d slope64 -U postgres -q; do
    sleep 1
done
echo "[start_api] Postgres ready — starting uvicorn."
exec uvicorn server:app --host 0.0.0.0 --port 8110
