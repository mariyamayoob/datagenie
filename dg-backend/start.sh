#!/bin/bash

echo "⏳ Waiting for MySQL (dg-db:3306) and Chroma (dg-vector:8001)..."

function wait_for_service() {
  local host=$1
  local port=$2
  local retries=20

  for i in $(seq 1 $retries); do
    echo "🔄 Checking $host:$port... (try $i/$retries)"
    if nc -z "$host" "$port"; then
      echo "✅ $host:$port is available"
      return 0
    fi
    sleep 2
  done

  echo "❌ Timed out waiting for $host:$port"
  exit 1
}

wait_for_service "dg-db" 3306
wait_for_service "dg-vector" 8000

echo "🚀 Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8003
