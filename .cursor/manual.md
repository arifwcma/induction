# Operations Manual — Induction Chatbot

A concise guide to run the project from a fresh start, plus what to re-do after changes.

## Prerequisites (one-off per machine)

1. Docker Desktop installed and running.
2. Python venv created and deps installed:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```
3. Frontend deps installed:
   ```powershell
   cd frontend
   npm install
   ```
4. `.env` filled in (OpenAI key, Cohere key, JWT secret, admin email/password). Already done.

## Ports & gotchas

- Backend (FastAPI): **http://localhost:8000** (docs at `/docs`)
- Frontend (Next.js): **http://localhost:3000**
- Postgres: host port **5433** (container is 5432; native Windows Postgres squats 5432 — do not change this)
- Qdrant: **6333**
- Run the backend on the **host** (uvicorn), NOT the docker `app` service — the BM25 index lives on disk in `kb_index/`.

## Fresh start — run order (3 terminals)

Run each in its own terminal, from `c:\Users\m.rahman\src\induction`.

**Terminal 1 — Docker services** (Postgres + Qdrant):
```powershell
docker compose up -d postgres qdrant
```

**Terminal 2 — Backend:**
```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 3 — Frontend:**
```powershell
cd frontend
npm run dev
```

Then open http://localhost:3000.

## One-off / occasional commands

Run these from the project root (`induction`), not as always-on terminals.

| Task | Command | Notes |
|---|---|---|
| Seed/ensure admin user | `.\.venv\Scripts\python.exe -m app.seed_admin` | Idempotent. Run once after a fresh DB. |
| Full knowledge-base ingest | `.\.venv\Scripts\python.exe -m app.kb.ingest_kb` | SLOW + costs API. See warning below. |
| Rebuild clause table only (cheap recovery) | `.\.venv\Scripts\python.exe -m app.kb.store_clauses_from_corpus` | ~2s, no API cost. Uses existing `kb_index/`. |
| Run reliability eval | `.\.venv\Scripts\python.exe -m app.eval_harness` | ~30s. Should be 6/6. |

### Ingest warning (read before running `app.kb.ingest_kb`)

- **Time: ~8–12 minutes** (one sequential LLM call per clause, ~298 of them).
- **Cost: ~$0.05–$0.10** per run (gpt-4o-mini situating + embeddings).
- It is a **full rebuild, no duplication**: it wipes the Qdrant collection, overwrites the BM25 corpus, and replaces the clause table.
- It **finishes and exits** (not a server) — prints `Ingested N chunks, N clauses...` when done.
- **It erases trainer-added KB** (anything trainers added live via the app), because it deletes the whole Qdrant collection. Only the files in `documents/` are re-ingested.

## What to re-do after a change

| You changed... | Re-do this |
|---|---|
| Backend Python code (`app/**`) | Nothing — uvicorn `--reload` picks it up. If it didn't, restart Terminal 2. |
| Frontend code (`frontend/**`) | Nothing — `npm run dev` hot-reloads. |
| `.env` values | Restart the backend (Terminal 2). Restart frontend only if you changed `NEXT_PUBLIC_*`. |
| Documents in `documents/` (added/edited/removed) | Re-run **full ingest** (`app.kb.ingest_kb`). ~8–12 min. |
| Parsing / chunking / situating logic (`app/kb/**`) | Re-run **full ingest**. |
| Retrieval / generation / verifier logic (`app/rag/**`) | Nothing to re-ingest — just restart backend (or rely on `--reload`). Re-run `app.eval_harness` to confirm reliability. |
| DB models (`app/models.py`) | Tables auto-create on startup for NEW tables only. For changed columns, drop/recreate: `docker compose down -v` then bring Postgres back up + re-seed + re-ingest (destroys data). |
| `requirements.txt` | `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`, then restart backend. |
| `frontend/package.json` | `cd frontend; npm install`, then restart frontend. |

## Stopping / resetting

- Stop a server: `Ctrl+C` in its terminal.
- Stop Docker services (keeps data): `docker compose stop`
- **Full data wipe** (Postgres + Qdrant volumes): `docker compose down -v` — then you must re-seed admin and re-ingest.

## Quick health checks

- Backend alive: open http://localhost:8000/docs
- Vectors present: should be ~500 in Qdrant after ingest.
- Clauses present: ~298 rows in the `clause` table after ingest.
- Reliability OK: `app.eval_harness` returns OVERALL 6/6.

## Typical daily start (everything already set up)

1. `docker compose up -d postgres qdrant` (if not already running)
2. Start backend (Terminal 2)
3. Start frontend (Terminal 3)
4. Open http://localhost:3000

No need to re-seed or re-ingest unless documents or ingest logic changed.
