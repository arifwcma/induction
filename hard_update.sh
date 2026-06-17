#!/usr/bin/env bash
set -euo pipefail

# Hard update: full rebuild AND rebuild the knowledge base (LLM-level work).
# Use when documents/ changed, or parsing/chunking/situating logic changed.
# Run from app-src/.

here="$(cd "$(dirname "$0")" && pwd)"
appdir="$(cd "$here/.." && pwd)"

git pull

cp "$here/deploy/compose.server.yaml" "$appdir/compose.yaml"

cd "$appdir"
docker compose up -d --build --force-recreate

echo "Ensuring admin user..."
docker compose exec -T induction python -m app.seed_admin

echo
echo "About to REBUILD the knowledge base (full ingest)."
echo "WARNING: SLOW (~8-12 min) and makes paid OpenAI calls (~\$0.05-0.10)."
echo "This wipes and rebuilds vectors, BM25, and the clause table."
echo "NOTE: trainer-added KB entries are erased; only documents/ is re-ingested."
read -r -p "Proceed with re-ingest? [y/N] " answer
if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
  docker compose exec -T induction python -m app.kb.ingest_kb
  docker compose restart induction
  echo "Hard update complete (code + knowledge base rebuilt)."
else
  echo "Skipped re-ingest. Code and containers were still rebuilt/restarted."
fi
