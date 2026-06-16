#!/usr/bin/env bash
set -euo pipefail

before_pull=$(git rev-parse HEAD)
git pull
after_pull=$(git rev-parse HEAD)

documents_changed=false
if ! git diff --quiet "$before_pull" "$after_pull" -- documents; then
  documents_changed=true
fi

cd ..
docker compose up -d --build

if [ "$documents_changed" = true ]; then
  echo "Documents changed — re-ingesting."
  docker compose exec -T induction python -m app.ingest
else
  echo "No document changes — skipping re-ingest."
fi

echo "Update complete."
