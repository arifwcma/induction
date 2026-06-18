# Handover — Wimmera CMA Induction Chatbot (for the next agent)

You are taking over the induction chatbot. This file is the single onboarding doc: overall goal, how it works, the recurring challenges we keep fighting, server access, deployment, testing, and the roadmap. Read it fully, then skim `.cursor/blueprint.md` (reproduction spec), `.cursor/project.md` (context + known bugs), `.cursor/plan.md` (status), and `.cursor/instructions.md` (how Arif wants you to behave).

---

## 1. Who you work with — Arif (also "Boss" / "Ostad")
- Strong Python / GIS / ML (recent ML PhD). Weaker React/TypeScript. ~16+ yrs software.
- Wants: brevity; ONE best recommendation (never a menu of options unless he asks); readability over cleverness; honesty over guessing.
- Every reply starts with a sequential label `R1, R2, ...`.
- NO code comments / docstrings, ever. Minimal function parameters (hard-code constants inside the function). Descriptive names. Unroll clever one-liners.
- Ask before long explanations or deep research. Wrong/guessed answers frustrate him more than slow ones.
- HARD RULES (see `.cursor/instructions.md`):
  - NO CASE-SPECIFIC FIXES — fix the general mechanism for the whole class of inputs, never special-case the one example he reported.
  - SMOKE TEST after any major LLM change — run `app.smoke` (his 3 verbatim cases) AND `app.eval_harness`. NEVER reword his smoke cases; real users phrase casually.
  - NO HACKS. If something doesn't work, stop and discuss.

## 2. Overall goal
A fast, concise, ChatGPT-like assistant for NEW Wimmera CMA employees. It answers strictly from the induction documents in `documents/` (PDF + DOCX: policies, procedures, the enterprise agreement) plus trainer-added knowledge. It keeps per-session + lightweight cross-session memory, cites sources, opens with a greeting, can give a short guided tour, and gives helpful overviews. Overriding requirement: **reliability** — answer only when grounded, but NEVER abstain on something the KB can clearly answer. Live at https://induction.wcma.work/. Clone of the RCS bot (`C:\Users\m.rahman\src\rcsbot`); same OpenAI key, separate repo / Qdrant collection (`induction_documents`) / deployment.

Milestones: **M1 = MVP on a static KB (current, essentially done).** M2 = scale + self-service ingestion (see Roadmap §9).

## 3. Current status (verified locally against real Postgres/Qdrant/Cohere/OpenAI)
The M1 reliability stack is built and runtime-verified. Both target bugs plus the second round of live-testing issues are fixed and genuinely grounded:
- Bug1 fixed on BOTH halves (see §5).
- Bug2 fixed (see §5).
- Issue#1 (explicit emergency-work questions): fixed — answers correctly that during emergency work a meal break COUNTS as time worked (clause 1.5), the opposite of the normal day. Required finer appendix chunking (re-ingest), a topic-carrying condense, and making the verifier trust the applicability filter for scope (see §5).
- Issue#2 (emergency overview), Issue#2.2 ("short tours" relates to the bot's own tour offer even with no greeting in history), Issue#3 (broad topics get an overview first): fixed.
- Overviews, "how many", and the guided tour all work.
- `app.eval_harness` = 9/9. `app.smoke` (Arif's verbatim Cases 1–6 in `.cursor/smokecases.md`) = clean. Re-ingest produces ~385 chunks / ~368 clauses.
- Ingestion command is `python -m app.kb.ingest_kb` (old `app/ingest.py` and `app/regression.py` were deleted). Phase 3 changed `app/kb/parse.py`, so the server needs a re-ingest (`hard_update.sh`).
- **Phase 4 (current): the answer model is Claude Opus 4.8.** A provider-agnostic factory (`app/llm_factory.py`) runs Opus 4.8 for the user-facing answer and keeps the mechanical steps on fast, deterministic `gpt-4o-mini` (hybrid split). Added agentic re-retrieval and real streaming (`/chat` emits newline-delimited JSON frames). Phase 4 did NOT change ingestion, so it deploys with `update.sh` (no re-ingest); it adds the `llama-index-llms-anthropic` dep and the `LLM_PROVIDER`/`ANTHROPIC_*`/`FAST_*` env vars.

## 4. How it works — the answer pipeline
Everything funnels through `stream_grounded_answer` in `app/rag/pipeline.py` (an async generator yielding UI frames). `produce_grounded_answer` drives it and returns only the final string for non-streaming callers (`app.ask`, `app.smoke`, eval). `/chat` streams the frames. Two LLM lanes (`app/llm_factory.py`): the **answer lane** is Claude Opus 4.8 (`build_llm`); the **fast lane** is `gpt-4o-mini` (`build_fast_llm`) for every mechanical step. Per turn:
1. Build the KB MAP (`app/rag/kb_outline.py`) — documents + the topics/sections each covers, from the clause table, cached. Injected as a system message. Authoritative for EXISTENCE/COVERAGE/overview/tour/"how many"; NOT a source of rule content.
2. Condense history + message → standalone question (`condense_to_standalone_question`, fast lane).
3. Query rewrite (`build_search_query`, fast lane) → a concept-focused search query (drops scenario noise, expands "lunch"→"meal break").
4. Retrieve: dense (Qdrant) + BM25 candidates gathered for BOTH the standalone question and the rewritten query, fused/deduped, then Cohere-reranked against the true question (`app/rag/retrieval.py`).
5. Expand clauses: add sibling + cross-referenced clauses from the clause table (`app/rag/expansion.py`).
6. Applicability filter (`app/rag/applicability.py`, fast lane, async/concurrent): the SCOPE GATE, now KEEP-BY-DEFAULT. It sees each conditional provision's section breadcrumb and drops it ONLY when it clearly belongs to a special/different scenario than the question (e.g. emergency-only for an ordinary day); it keeps it for explicit-scenario questions ("emergency work") and for merely-descriptive conditions ("non-casual employees"). Primary Bug1 guard.
7. Generate (`generate_answer_stream`, Opus 4.8) — streamed live token-by-token, with the system prompt + MAP + SOURCE MATERIAL.
8. Verify (`verify_answer`, fast lane): map-authoritative for coverage; source-required for substantive facts. It does NOT re-judge scope — it trusts the applicability filter. Pass → commit (`final`). Fail → reset the unverified draft + regenerate (another attempt); still fail → AGENTIC re-retrieval (`build_refined_search_query` → re-retrieve → merge) + retry; still fail → abstain (`UNSURE_RESPONSE`).
Fast-lane calls use `temperature=0` + a fixed `seed` (per-attempt varied), so retrieval-shaping is reproducible. Opus 4.8 can't be seeded and rejects `temperature` (adaptive thinking) — that's the whole reason the deterministic steps live on the fast lane.

`/chat` streams newline-delimited JSON frames: `{"t":"status",...}` (progress milestone), `{"t":"delta",...}` (live answer token), `{"t":"reset"}` (clear an unverified draft that failed verification), `{"t":"final",...}` (the committed verified answer). Users never keep unverified content. Frontend parser: `frontend/app/assistant.tsx`.

Ingestion (`app/kb/ingest_kb.py`): parse (`app/kb/parse.py`) → situate+chunk with generated titles (`app/kb/contextual.py`, fast lane) → embed to Qdrant + save BM25 corpus (`kb_index/`) + persist clause table (`app/kb/clause_model.py`). Full rebuild each run; wipes the Qdrant collection (so trainer-added KB is erased).

## 5. Recurring challenges (the heart of this project — read carefully)
1. **Bug1 — lexical-match-over-relevance (THE original bug).** A normal lunch-break question was answered from the emergency-only Appendix C because it matched the keywords, missing the governing general clause 23. Root cause is structural: a clause's applicability (emergency-only / casual-only / probation-only) comes from its place in the heading hierarchy, which naive chunking severs. It has TWO halves and BOTH must hold:
   - Don't ANSWER from a conditional clause when its condition doesn't apply → applicability filter (step 6).
   - Still RETRIEVE the governing general clause → query rewrite + fused retrieval (steps 3–4). We re-broke this once: applicability correctly stripped Appendix C, but clause 23.2 was never retrieved for Arif's casual wording, so the bot abstained. Query rewrite fixed it.
   A keyword `detect_scope` hack was tried early and REJECTED. Never special-case emergencies.
2. **Bug2 — false abstention on coverage/"how many".** The model listed every leave type from the MAP correctly, but the verifier graded each item against retrieved passages and failed them → canned abstention ~83% of runs. Fix: MAP is authoritative for existence/coverage/enumeration in both generation and verification. Principle: answer only accurately, but NEVER abstain on a clearly KB-answerable question.
3. **gpt-4o-mini is NOT deterministic even at temperature 0.** Identical input gave different verdicts run-to-run (e.g. 5/6 abstain then 3/3 pass). A fixed `seed` materially stabilised it but it is best-effort (OpenAI does not guarantee determinism). The verifier is both the main reliability lever AND the main false-abstention risk — tune its prompt carefully and always re-measure stability over several runs, not once.
4. **Don't trust document structure.** Future docs may have no headings. We generate a section TITLE per unit at ingest and fall back to per-page units for unstructured PDFs. The KB MAP is built from the clause table so generated titles flow through. Phase 3 lesson: dense numbered appendices (Appendix C) hid two structural traps — a per-page running header that matched the APPENDIX regex (split the appendix by page) and trailing-dot sub-clause numbers (`1.5.`) the regex rejected (so sub-rules never split and were unretrievable). `parse.py` now suppresses repeated appendix headers, accepts trailing-dot sub-clauses, and treats numbered headings inside an appendix as its sub-units. Watch for the same patterns in new documents.
5. **The verifier must NOT re-judge scope.** Originally the verifier failed any answer that used emergency/conditional content, which caused false abstention on EXPLICIT emergency questions (Issue#1/#2) — it kept calling an emergency question "ordinary". The fix: scope/applicability is decided ONCE, upstream, by the applicability filter; the verifier trusts that and only checks grounding + fabrication. Don't reintroduce a scope check in the verifier.
6. **Condense can silently lose the topic.** "what would be the case during emergency work" condensed to a topic-less standalone, so retrieval missed the meal-break clause. The condense now carries the prior topic forward for bare situation/condition follow-ups — but NOT for topic switches ("lets talk about X"), which it must leave alone (carrying the wrong topic broke the tour case). Re-measure several runs after touching the condense prompt.
7. **Map legibility matters for the verifier.** The map rendered as one long semicolon line caused the verifier to intermittently miss real items (e.g. "Workplace Training Leave", §47) → flaky Bug2 abstention. It's now one section per line. And a fixed-seed retry is useless (identical draft) — the retry varies the seed.
8. **The answer model (Opus 4.8) is non-deterministic and the fast model is stricter — keep the lanes separate.** Opus 4.8 cannot be seeded and rejects `temperature` (adaptive thinking), so anything it touches varies run-to-run; that's why the retrieval-SHAPING steps (condense, query rewrite, applicability, verifier) run on the seedable `gpt-4o-mini` fast lane. Beware: swapping the model on a step can change behaviour — the upgrade exposed that `gpt-4o-mini` is a STRICTER applicability judge than Opus, which over-dropped clauses (see next). If you change which model runs a step, re-measure.
9. **Applicability conditions are often DESCRIPTIVE, not exclusionary — don't hard-gate on them.** Clauses are ingested with a terse `condition` string that is frequently just "who/when this normally applies" (`'non-casual employees'`, `'after probation'`) or a cryptic tag (`'AIMS control system'`). Judging that string in isolation made the filter drop the PRIMARY clause for a plain question (clause 36.1 annual leave; clause 1.5 emergency meal). Fix that holds: feed the judge the section BREADCRUMB (so cryptic tags resolve from their heading) and KEEP-BY-DEFAULT — exclude only when the provision clearly belongs to a special/different scenario than the question. Don't revert to "does the employee meet this condition?" hard gating.
10. **Verification gates streaming, never the reverse.** The Opus answer streams live, but the verifier still decides what stands: a draft that fails verification is `reset` (cleared on screen) and replaced. Never stream a final answer the verifier hasn't passed.
5. **Diagnose, don't guess.** Every real fix here came from tracing the actual pipeline (retrieval ranks, applicability output, verifier verdict/reason), not from assuming. When something abstains, find out WHICH stage produced the abstention before changing anything.

## 6. Key files
- `app/llm_factory.py` — provider-agnostic LLM builder; answer lane (Opus 4.8) vs fast lane (`gpt-4o-mini`); registers Opus 4.8 runtime quirks.
- `app/rag/pipeline.py` — the one answer path: `stream_grounded_answer` (frames + agentic re-retrieval) and `produce_grounded_answer` (returns the final).
- `app/rag/chat.py` — system prompt, condense, `build_search_query`, `build_refined_search_query`, `generate_answer` + `generate_answer_stream`, verifier, `build_llm` (answer lane) / `build_fast_llm` (fast lane), `UNSURE_RESPONSE`.
- `app/rag/retrieval.py` — dense+BM25 candidate gathering over multiple queries, fuse/dedup, Cohere rerank.
- `app/rag/applicability.py` — async keep-by-default conditional-passage filter with breadcrumb context (primary Bug1 guard).
- `app/rag/expansion.py` — sibling + cross-ref clause expansion.
- `app/rag/kb_outline.py` — the KB MAP (from clause table, cached).
- `app/kb/parse.py` — PDF/DOCX parsing (merges split headings; per-page fallback).
- `app/kb/contextual.py` — situating LLM (prose + scope + generated TITLE), effective title/breadcrumb, chunking.
- `app/kb/clause_model.py`, `app/kb/bm25_index.py`, `app/kb/ingest_kb.py`, `app/kb/store_clauses_from_corpus.py` — clause records, BM25 index, full ingest, cheap clause-table recovery.
- `app/main.py` — FastAPI wiring + all endpoints; `/chat` calls the pipeline.
- `app/eval_harness.py` — regression gate (scope/out-of-scope/meta/overview/coverage(Bug2)/tour). `app/smoke.py` — Arif's 3 verbatim cases.
- Auth/stores: `app/auth.py`, `app/models.py`, `app/schemas.py`, `app/seed_admin.py`, `app/chat_store.py`, `app/config_store.py`, `app/kb_store.py`, `app/admin_store.py`, `app/trainer_kb.py`.
- `frontend/` — Next.js + assistant-ui (auth gate, sidebar sessions, trainer upload, admin panel).

## 7. Run locally (Windows / PowerShell) — full detail in `.cursor/manual.md`
- Ports: backend :8000, frontend :3000, Postgres host :5433 (container 5432; native Windows Postgres squats 5432 — don't change), Qdrant :6333.
- Run the backend on the HOST (uvicorn), not the docker `app` service, because the BM25 index lives on disk in `kb_index/`.
- Start: `docker compose up -d postgres qdrant` → `.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000 --reload` → `cd frontend; npm run dev`.
- One-offs: `python -m app.seed_admin`; `python -m app.kb.ingest_kb` (~8–12 min, full rebuild, erases trainer KB).
- `.env` (gitignored) holds the keys; same OpenAI key as rcsbot.

## 8. Server & deployment
- EC2 `i-0e5194e443d3c0049`, region `ap-southeast-2`, IP `13.55.191.184`, Ubuntu 24.04, t3.large.
- Access: `ssh -i 'C:\Users\m.rahman\assets\keys\Playground1.pem' ubuntu@13.55.191.184`, then `sudo -u ssm-user bash` (passwordless). `ssm-user` runs `docker` WITHOUT sudo. Do NOT SSH/change the server unless Arif asks.
- App dir `/home/ssm-user/apps/induction/`: holds `compose.yaml` + `.env`; the repo is in `app-src/`. Compose services: `induction` (backend, `read_only: true`, 512M, `/tmp` tmpfs, writable `induction_kb_index` volume at `/app/kb_index`), `induction-frontend`, `induction-postgres`, `induction-qdrant`. Network `internal-apps` (external). Shared `nginx-reverse-proxy` terminates SSL.
- Deploy scripts (run from `app-src/`, they copy `deploy/compose.server.yaml` → `../compose.yaml`):
  - `bash m1_update.sh` — ONCE, first M1 cutover; builds, seeds admin, first ingest.
  - `bash update.sh` — small code change; rebuild + restart; NO re-ingest.
  - `bash hard_update.sh` — documents or KB/parsing/chunking logic changed; rebuild + (prompted) full re-ingest. The ingest runs INSIDE the container (`docker compose exec -T induction python -m app.kb.ingest_kb`).
  - Rule of thumb: changed anything under `app/kb/**`, `documents/`, or the map/clause schema → `hard_update.sh`. Changed only `app/rag/**` or frontend → `update.sh`.
- Required server `.env` keys: `LLM_PROVIDER=anthropic`, `ANTHROPIC_API_KEY`, `ANTHROPIC_CHAT_MODEL=claude-opus-4-8`, `FAST_LLM_PROVIDER=openai`, `FAST_CHAT_MODEL=gpt-4o-mini`, `OPENAI_API_KEY`, `OPENAI_CHAT_MODEL`, `OPENAI_EMBEDDING_MODEL`, `COHERE_API_KEY`, `COHERE_RERANK_MODEL`, `QDRANT_COLLECTION`, `DOCUMENTS_DIR`, `FRONTEND_ORIGIN=https://induction.wcma.work`, `JWT_SECRET`, `POSTGRES_PASSWORD`, `COOKIE_SECURE=true`, `ALLOWED_EMAIL_DOMAIN=wcma.vic.gov.au`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`. `DATABASE_URL` + `QDRANT_URL` come from compose — don't hardcode localhost on the server. Server `.env` is gitignored (lives only on the box). NOTE: before the first Phase 4 deploy, add the `ANTHROPIC_API_KEY` + the `LLM_PROVIDER`/`FAST_*` keys to the server `.env`, then `bash update.sh` (Phase 4 changed no ingestion, so no re-ingest).
- nginx (one-time, manual): the `induction.wcma.work` 443 block must route ALL backend paths, not just `/chat`. Matcher: `location ~ ^/(chat|auth|users|sessions|kb|admin|health)`. Full block + reload command in `deploy/README.md`. Without it, login/admin/sessions 404.
- Verify after deploy: `docker compose exec -T induction python -m app.eval_harness` (9/9) and `... python -m app.smoke` (no abstentions on Cases 1–6).

## 9. Roadmap / next tasks
M2 (planned): auto-refresh ingestion on document upload (change-detection so a new/edited doc re-ingests automatically), and robust retrieval for a larger KB (hierarchical/structured retrieval beyond the current rerank step).

Concrete follow-ups worth doing (in rough priority):
1. **Trainer KB survives re-ingest.** Today a full ingest wipes the Qdrant collection, erasing trainer-added entries. Trainer content lives in Postgres (`trainer_kb_entry`); re-add it after each ingest (or ingest from the DB), so re-ingest is non-destructive to trainer knowledge.
2. **Verifier robustness if false abstention recurs.** The verifier is an LLM and can still flip on edge cases. If it does, consider confirm-on-fail (a true scope/hallucination fails consistently; noise won't reproduce) — but keep scope violations a hard fail. Measure over many runs before/after.
3. **PDF text encoding artifact.** Some apostrophes extract as the replacement char (shows as `�`). Cosmetic. Normalise at parse time (`app/kb/parse.py`) if Arif wants clean output.
4. **Stronger structure-agnostic segmentation.** The current fallback is one-unit-per-page. A layout-aware segmenter (font size/weight via PyMuPDF) and DOCX-without-headings handling would be more robust for genuinely messy future docs.
5. **Observability** (blueprint §6D item 12): log retrieved clauses, scores, and verifier verdicts per turn; feed flagged answers back into the eval set.
6. **Span-grounded citations** (blueprint §6C item 8): citations are clause-number level today; verbatim-span anchoring would be stronger.

## 10. Gotchas learned the hard way (do not repeat)
1. `.doc` (old binary Word) is NOT cleanly ingestible — convert to `.docx` first. Future docs must be PDF or DOCX.
2. Windows: `Start-Process`/backgrounded uvicorn inherits the WRONG cwd (workspace root = rcsbot) and loads rcsbot's `.env`, silently running against the wrong collection. Pass the induction dir explicitly. If port 8000 stays held after exit (WinError 10048), kill the holding PID — don't switch ports.
3. Backend container is `read_only` (only `/tmp` + the `kb_index` volume writable). The BM25 index needs that writable volume; ingest must run inside the container so the index persists.
4. Postgres event-loop bug (fixed): the ingest once made two `asyncio.run()` calls and crashed on the second ("Event loop is closed"). Keep DB work under a single `asyncio.run`. `app/kb/store_clauses_from_corpus.py` rebuilds the clause table cheaply from the saved BM25 corpus if a re-ingest dies after the expensive situating step.
5. Re-ingest is DESTRUCTIVE (wipes Qdrant collection incl. trainer KB) and SLOW (~8–12 min). Only run it when ingestion logic or documents changed.
6. The previously-live site ran an OLD chunk-RAG architecture; the reliability stack supersedes BOTH that and the (never-built, now-deleted) "full KB in context + prompt caching" idea. Ignore any mention of those as current.
7. **System-prompt staleness footgun (bit us in production).** The system prompt lives in the DB (`system_prompt_config`) and is seeded ONLY when the row is absent (`ensure_prompt_seeded`). So editing `DEFAULT_SYSTEM_PROMPT` in code and deploying does NOT change a running bot — it keeps serving the old/admin-edited stored prompt. Symptom we saw: a server with current code + current KB still gave a wrong, un-cited emergency-work answer because its stored prompt was the old short one (2142 vs 4198 chars). Fix: run `python -m app.reset_prompt` (added) after any prompt change on deploy. The KB/clause table refreshes via ingest, but the prompt does NOT — they are separate.

## 11. Conventions
- Keep `.cursor/plan.md` current; commit + push at the end of each phase.
- Git remote `git@wcma:arifwcma/induction.git`, branch `main`. The server's `app-src` pulls the same remote.
- Commit messages: short, why-focused. PowerShell has no heredocs — use multiple `-m` flags.
- `.sh` and `deploy/*.yaml` are pinned to LF endings (`.gitattributes`) for Linux.
- Broader server docs: `C:\Users\m.rahman\src\playground_details`. The `pozi_base` path on the server is a different deployment — do not touch.
