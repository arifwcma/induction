#!/usr/bin/env bash
set -euo pipefail

# One-time Milestone 1 setup on the server. Run ONCE from app-src/ after `git pull`.
# It installs the M1 compose (adds Postgres + a writable kb_index volume), validates
# the server .env, builds everything, seeds the admin, and runs the first ingest.

here="$(cd "$(dirname "$0")" && pwd)"
appdir="$(cd "$here/.." && pwd)"
envfile="$appdir/.env"

required_keys=(
  OPENAI_API_KEY
  COHERE_API_KEY
  COHERE_RERANK_MODEL
  JWT_SECRET
  POSTGRES_PASSWORD
  COOKIE_SECURE
  ALLOWED_EMAIL_DOMAIN
  ADMIN_EMAIL
  ADMIN_PASSWORD
  FRONTEND_ORIGIN
)

echo "Checking $envfile for required M1 keys..."
missing=()
for key in "${required_keys[@]}"; do
  if ! grep -q "^${key}=" "$envfile" 2>/dev/null; then
    missing+=("$key")
  fi
done
if [ "${#missing[@]}" -ne 0 ]; then
  echo "ERROR: the server .env is missing required keys:"
  for key in "${missing[@]}"; do echo "  - $key"; done
  echo "Add them to $envfile and re-run."
  exit 1
fi

echo "Backing up current compose.yaml and installing the M1 compose..."
if [ -f "$appdir/compose.yaml" ]; then
  cp "$appdir/compose.yaml" "$appdir/compose.yaml.bak.$(date +%Y%m%d-%H%M%S)"
fi
cp "$here/deploy/compose.server.yaml" "$appdir/compose.yaml"

cd "$appdir"
echo "Building and starting all services..."
docker compose up -d --build

echo "Waiting for Postgres to accept connections..."
for _ in $(seq 1 30); do
  if docker compose exec -T induction-postgres pg_isready -U induction >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

echo "Seeding admin user..."
docker compose exec -T induction python -m app.seed_admin

echo "Running first knowledge-base ingest."
echo "WARNING: this is SLOW (~8-12 min) and makes paid OpenAI calls (~\$0.05-0.10)."
docker compose exec -T induction python -m app.kb.ingest_kb

echo "Restarting backend so it loads the fresh BM25 index..."
docker compose restart induction

echo
echo "M1 setup complete."
echo "REMINDER: nginx must route /auth /users /sessions /kb /admin to the backend."
echo "If you have not applied the nginx change yet, login/admin will 404."
