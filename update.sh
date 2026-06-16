#!/usr/bin/env bash
set -euo pipefail

git pull
cd ..
docker compose up -d --build

echo "Update complete."
echo "If documents or ingestion logic changed, re-ingest with:"
echo "  docker compose exec -T induction python -m app.ingest"
