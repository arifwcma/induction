# Handover — Wimmera CMA Induction Chatbot (for the next agent)

You are taking over the induction chatbot. Read `.cursor/instructions.md` (how Arif wants you to behave), `.cursor/project.md` (context), and `.cursor/plan.md` (status) first — they are the source of truth. This file is the operational handover plus the NEXT BUILD TASK on top of them.

## Who you are working with
- Arif (also "Boss" / "Ostad"). Strong Python/GIS/ML; weaker React/TypeScript. Wants brevity, ONE best recommendation (not lists of options), readability over cleverness, NO code comments/docstrings, and every reply prefixed with a sequential label (R1, R2, ...). Honesty over guessing. Ask before long explanations or deep research.
- Hard rule: NO HACKS. If something does not work, stop and discuss to get it right.

## What this project is
A fast, concise, ChatGPT-like chatbot for NEW Wimmera CMA employees. It answers strictly from the induction documents in `documents/` (PDF + DOCX: policies, procedures, the enterprise agreement). Keeps session memory, opens with a greeting, gives a bite-sized "tour" on request, and asks one clarifying question when a query is vague instead of guessing. It is a clone of the RCS bot (`C:\Users\m.rahman\src\rcsbot`) with a different context, a different Qdrant collection, and a separate deployment. Uses the SAME OpenAI API key as the RCS bot.

## Current status — M1 RELIABILITY STACK BUILT + runtime-verified locally
- The Milestone 1 reliability stack (R1–R7) plus two post-launch reliability phases are implemented and verified locally. See `.cursor/plan.md` for scope/decisions and `.cursor/blueprint.md` §8b for the current behaviour.
- IMPORTANT: the M1 KB-handling decision is the RELIABILITY STACK (contextual chunking + structured clause model + hybrid retrieval + Cohere rerank + applicability filter + grounded/verified generation + KB map + eval harness). This OVERRIDES BOTH the old "full KB in context + prompt caching" plan AND the earlier reranker+keyword-scope build described later in this file. The "NEXT BUILD TASK" section below is HISTORICAL — do not implement it.
- Current behaviour (verified): Bug1 fixed on both halves (applicability filter stops answering from conditional clauses; query rewrite ensures the governing general clause is retrieved). Bug2 fixed (KB map authoritative for coverage/"how many"). Overviews + guided tour work. Eval 8/8; smoke (Arif's 3 verbatim cases) clean.
- Ingestion command is now `python -m app.kb.ingest_kb` (the old `app/ingest.py` and `app/regression.py` were deleted).
- Deploy uses `m1_update.sh` (one-off M1 cutover), `update.sh` (light code change), `hard_update.sh` (rebuild + re-ingest). See `deploy/README.md`.

## M1 deployment & ops (do this to ship M1)
New dependencies vs old: PostgreSQL (users/sessions/prompt/trainer-KB), Cohere Rerank API, FastAPI-Users auth.
Required env (server `.env`, gitignored): `OPENAI_API_KEY`, `COHERE_API_KEY`, `JWT_SECRET` (long random), `DATABASE_URL` (postgresql+asyncpg://...), `COOKIE_SECURE=true` (HTTPS), `ALLOWED_EMAIL_DOMAIN=wcma.vic.gov.au`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `FRONTEND_ORIGIN=https://induction.wcma.work`.
Server `compose.yaml` must gain a `postgres` service (image `postgres:16`, a named volume, the induction DB/user/password) and the `induction` backend must depend on it with `DATABASE_URL` pointing at it (see local `docker-compose.yml` for the shape). Keep `internal-apps` network + nginx SSL conventions.
Deploy steps after pushing: prefer the scripts (`m1_update.sh` first cutover, then `update.sh` / `hard_update.sh`). Manually: `git pull` + `docker compose up -d --build`, then ONE-OFF: `docker compose exec -T induction python -m app.seed_admin` (creates the admin) and `docker compose exec -T induction python -m app.kb.ingest_kb` (REQUIRED whenever ingestion/parsing/chunking logic or documents changed — existing vectors/clauses are stale). The backend container is `read_only`; the BM25 index needs a writable `kb_index` volume (see `deploy/compose.server.yaml`).
nginx: it currently only routes `/chat` to the backend. M1 adds `/auth/*`, `/users/*`, `/sessions/*`, `/kb/*`, `/admin/*` — nginx must route ALL backend API paths to the `induction` backend (not just `/chat`), or scope them under a prefix. Confirm routing before declaring done.
Cookies: auth uses an httpOnly cookie; frontend and backend are same registrable domain (induction.wcma.work) so `SameSite=Lax` works; ensure `COOKIE_SECURE=true` in prod.

## Why we are changing it (the problem Arif found)
The chunk RAG gave a WRONG answer on a real query. Asked whether a 12:00–12:30 lunch counts as work time, the bot said "counts as time worked, enter 8 hours" — but it pulled that from the conditional **Emergency-work appendix (only applies under AIIMS incident control)** and MISSED the governing general clause **23.3** ("an employee may not work more than 5 consecutive hours without a break"). Root cause: top-k chunk retrieval is structurally blind to the rest of the document — it reasons from 8 fragments, loses each clause's scope/conditions, and never sees the controlling clause. Prompt wording cannot fix a retrieval-layer blind spot.

## NEXT BUILD TASK — rearchitect to "full KB in context" + prompt caching (OpenAI)
Decision already made with Arif: the corpus is tiny (4 docs, ~80 pages, est. ~60–90k tokens), so STOP using lossy chunk retrieval and instead send the WHOLE knowledge base into every OpenAI call so the model reasons over everything. Use OpenAI prompt caching to keep cost/latency low. Do NOT use Azure AI Foundry — stay on the OpenAI API with the existing key.

Build it in this order:

1. KB builder (offline / on change). New module (e.g. `app/knowledge_base.py`) that reads `documents/` and concatenates ALL docs into ONE ordered text blob:
   - PDF via PyMuPDF page-level, prefix each page with a marker like `[Source: <filename> | page N]`.
   - DOCX via python-docx (paragraphs + tables), prefix with `[Source: <filename>]`; keep heading text so clause numbers (e.g. "23.3") survive in the text.
   - Reuse the extraction helpers already in `app/ingest.py`.
   - Expose `get_knowledge_base()` that builds the blob once and memoises it in process. Optionally precompute to a file so it is built at image-build time, not per request.
   - The markers + the clauses already printed in the text are what let the model cite accurately.

2. Chat flow (replace the LlamaIndex chat engine). Call OpenAI directly (openai SDK, streaming). Message order MUST be: `[system rules]`, `[system: KB blob]`, `[...session history...]`, `[user message]`. The big static prefix (rules + KB) goes FIRST and must be byte-identical across calls — that is what OpenAI prompt caching keys on.
   - OpenAI prompt caching is AUTOMATIC (no `cache_control` param like Anthropic): prefixes ≥1024 tokens are cached, ~5–10 min idle TTL, discounted input on hits. Just keep the prefix stable and first.
   - Keep streaming so the frontend keeps working unchanged (it reads a text stream from `POST /chat`).
   - Session history: keep `app/sessions.py` style per-session memory, or store a raw per-session message list. History grows AFTER the cached prefix so caching still works.

3. Strengthen the system prompt for grounding/reliability (keep the existing greeting/tour/clarify behaviour, add):
   - Reason over the WHOLE agreement; when clauses interact, decide which one GOVERNS and say so. A general clause overrides a conditional/appendix clause unless the condition (e.g. AIIMS emergency) actually applies.
   - CITE the clause/section + document name for every substantive claim.
   - If a clause is conditional, state the condition explicitly.
   - If the answer is not in the documents, say so and point to the manager / People & Culture — do NOT extrapolate (e.g. timesheet mechanics are not in the agreement).

4. Reliability extras (recommended, can be a second phase):
   - Verification pass: a cheap second OpenAI call that checks the drafted answer is supported by the KB and that the cited clause is the governing one; if not, regenerate or downgrade to "check with People & Culture".
   - Eval set: a small file of tricky Q&A used as a regression test. SEED IT with the meal-break / clause-23.3 case so this exact failure can never silently return.

5. Drop the now-unused retrieval layer from the runtime path: Qdrant client, embeddings, `app/rag/engine.py` vector store, `app/rag/query.py`, `app/ask.py`, and the Qdrant ingestion. You can remove the `induction-qdrant` compose service on the server too (a server change — see deployment), but do that deliberately, not as a side effect.

Constraints / checks before you code:
- MEASURE the KB token count first (tiktoken). Confirm it leaves comfortable room under 128k for history + output (aim KB ≤ ~100k). If it ever exceeds that, fall back to WHOLE-DOCUMENT selection (send the 1–2 relevant full docs) — never go back to fragments.
- Recommend switching the default model to `gpt-4o` for the governing-clause reasoning (Arif has budget and accuracy matters for HR). Keep it env-configurable (`OPENAI_CHAT_MODEL`).

## Stack
- LLM: OpenAI `gpt-4o-mini` today (recommend `gpt-4o` after rebuild). Embeddings `text-embedding-3-small` (goes away with the rebuild).
- Backend: FastAPI (streaming `POST /chat`, `GET /health`, CORS). Frontend: Next.js + assistant-ui.
- Today's RAG: LlamaIndex + Qdrant (being removed). Packaging: Docker.

## Repo layout
- `app/main.py` — FastAPI app: `/health`, streaming `POST /chat`, CORS.
- `app/config.py` — env-driven settings (pydantic-settings). `qdrant_collection` default `induction_documents`.
- `app/rag/engine.py` — LLM + embeddings + Qdrant client (to be retired).
- `app/rag/chat.py` — chat engine + `SYSTEM_PROMPT` (greeting/tour/clarify already in prompt). This is where the new full-KB chat logic lands (or a new module).
- `app/ingest.py` — PyMuPDF (PDF page-level) + python-docx (paragraphs + tables) extraction; today writes to Qdrant. Reuse its extractors for the KB builder.
- `app/sessions.py` — per-session memory. `app/ask.py` / `app/rag/query.py` — CLI (retire with Qdrant).
- `frontend/` — Next.js + assistant-ui. `app/assistant.tsx` posts to `${NEXT_PUBLIC_API_URL}/chat`, has the welcome `initialMessages` and the "Wimmera CMA Induction Assistant" header. Sidebar label "Induction Bot" in `components/threadlist-sidebar.tsx`. Metadata in `app/layout.tsx`.
- `documents/` — the induction docs (PDF + DOCX), baked into the backend image via `COPY documents`.
- `update.sh` — server update helper (pull + rebuild + conditional re-ingest). REVISIT after the rebuild: "re-ingest" becomes "rebuild KB blob"; if the KB is built at image-build time, document changes only need a rebuild, and the re-ingest step can be dropped.

## Run locally (Windows / PowerShell)
1. (Old path only) Qdrant: a container `rcsbot-qdrant` already runs on `:6333` and is reused locally; collections are isolated by name.
2. Create venv + install: `py -3.13 -m venv .venv; .\.venv\Scripts\python.exe -m pip install -r requirements.txt`.
3. Backend: `.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000`.
4. Frontend: `cd frontend; npm install; npm run dev` → http://localhost:3000.
- `.env` (gitignored) holds `OPENAI_API_KEY` (same key as rcsbot). `.env.example` lists keys. Never commit secrets.

## Server / deployment (do NOT SSH unless Arif asks; he did ask last time)
- EC2 `i-0e5194e443d3c0049`, `ap-southeast-2`, IP `13.55.191.184`, Ubuntu 24.04, t3.large.
- Access: `ssh -i 'C:\Users\m.rahman\assets\keys\Playground1.pem' ubuntu@13.55.191.184` then `sudo -u ssm-user bash` (passwordless). `ssm-user` runs `docker` WITHOUT sudo.
- App dir `/home/ssm-user/apps/induction/`: `compose.yaml` + `.env` there; source repo in `app-src/`.
- Compose services: `induction` (backend, `read_only: true`, `/tmp` tmpfs, 512M limit), `induction-frontend` (built with `NEXT_PUBLIC_API_URL=https://induction.wcma.work`), `induction-qdrant`. Network `internal-apps` (external). nginx reverse-proxies the domain and terminates SSL.
- Update the server (from `app-src/`): `bash update.sh` (light code change, no re-ingest) or `bash hard_update.sh` (rebuild + re-ingest). First M1 cutover: `bash m1_update.sh`. Manual equivalent: `cd app-src && git pull && cd .. && docker compose up -d --build`, then if ingestion logic/docs changed `docker compose exec -T induction python -m app.kb.ingest_kb`.
- Broader server docs: `C:\Users\m.rahman\src\playground_details`. The `pozi_base` path on the server is a different deployment — do not touch.

## Gotchas learned the hard way (do not repeat)
1. PROMPT CACHING IS NOT "UPLOAD ONCE". You still send the whole KB every call; OpenAI just discounts/skips re-processing an identical leading prefix (auto, ~5–10 min TTL). There is no stored handle you reference later. (If Arif ever wants true server-side storage, that is OpenAI File Search / vector stores — but that is chunk retrieval again and reintroduces the clause-23.3 blind spot, so it is NOT what we want here.)
2. Server `.env` originally had `QDRANT_COLLECTION=rcs_documents` (copied from rcsbot) — it was fixed to `induction_documents`. If you re-touch env, keep induction's own values. The server `.env` is gitignored (lives only on the box).
3. `/health` on the domain returns the FRONTEND 404 — nginx only routes `/chat` to the backend, not `/health`. The backend `/health` works internally; don't rely on the public URL for it.
4. `.doc` (old binary Word) is NOT ingestible cleanly. The one legacy `Induction Policy.doc` was converted to `.docx` via Word COM on Arif's machine. Future docs must be PDF or DOCX; convert any `.doc` to `.docx` first.
5. Windows: `Start-Process` for uvicorn inherits the WRONG working directory (workspace root = rcsbot), so it loads rcsbot's `.env`. Always pass `-WorkingDirectory` to the induction dir, or the bot silently runs against the wrong settings/collection.
6. Windows: backgrounded uvicorn keeps holding port 8000 after its launcher stops (WinError 10048). Kill the holding PID (`Get-NetTCPConnection -LocalPort 8000`), don't switch ports.
7. Backend container is `read_only: true` (only `/tmp` writable). If you precompute the KB blob to a file, write it at image-BUILD time or to `/tmp`, never into the app dir at runtime.

## Conventions
- Update `.cursor/plan.md` as you progress; at the end of each phase, commit and push.
- Git remote: `git@wcma:arifwcma/induction.git`, branch `main`. The server's `app-src` pulls from the same remote, so after you push, the server can `bash update.sh`.
- Commit messages: short, why-focused. PowerShell has no heredocs — use multiple `-m` flags.
- Histories note: local and the server's initial commit were unrelated; they were joined with a `-s ours` merge. Main is now linear-enough; just commit + push normally.
