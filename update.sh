#!/usr/bin/env bash
set -euo pipefail

# Light update for small backend/frontend code changes. Run from app-src/.
# Pulls, syncs the compose file from the repo, rebuilds and restarts containers.
# Does NOT re-ingest (no LLM cost). Use hard_update.sh when documents or KB
# logic changed and the knowledge base must be rebuilt.

here="$(cd "$(dirname "$0")" && pwd)"
appdir="$(cd "$here/.." && pwd)"

git pull

cp "$here/deploy/compose.server.yaml" "$appdir/compose.yaml"

cd "$appdir"
docker compose up -d --build

echo "Update complete (code + containers restarted, knowledge base untouched)."
