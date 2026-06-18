# Handover — Wimmera CMA Induction Chatbot (for the next agent)

You are taking over the induction chatbot. This file is the single onboarding doc: who you work with, the goal, how it works, the recurring challenges, **what we tried that did NOT work**, server access, deployment, testing, and the roadmap. Read it fully, then skim `.cursor/blueprint.md` (reproduction spec — now the FINAL config), `.cursor/project.md` (bug context), `.cursor/plan.md` (status), `.cursor/manual.md` (local run), and `.cursor/instructions.md` (how Arif wants you to behave). For an Azure rebuild, see `.cursor/azurify.md`.

---

## 1. Who you work with — Arif (also "Boss" / "Ostad")
- Strong Python / GIS / ML (recent ML PhD). Weaker React/TypeScript. ~16+ yrs software.
- Wants: brevity; ONE best recommendation (never a menu unless he asks); readability over cleverness; honesty over guessing. He prefers a one-word/one-line answer when possible and gets frustrated by walls of text and by lectures.
- Every reply starts with a sequential label `R1, R2, ...`.
- NO code comments / docstrings, ever. Minimal function parameters (hard-code constants inside the function). Descriptive names. Unroll clever one-liners.
- Ask before long explanations or deep research. Wrong/guessed answers frustrate him more than slow ones.
- HARD RULES (`.cursor/instructions.md`):
  - NO CASE-SPECIFIC FIXES — fix the general mechanism for the whole class of inputs, never special-case the one example he reported.
  - SMOKE TEST after any major LLM change — run `app.smoke` (his verbatim cases) AND `app.eval_harness`. NEVER reword his smoke cases; real users phrase casually.
  - NO HACKS. If something doesn't work, stop and discuss.
  - When in Ask mode and he asks for a change, do NOT write code — remind him to switch to Agent mode.

## 2. Overall goal
A fast, concise, ChatGPT-like assistant for NEW Wimmera CMA employees. It answers strictly from the induction documents in `documents/` (the EA + three DOCX policies) plus trainer-added knowledge. Per-session + lightweight cross-session memory, source citations, a greeting, a short guided tour, helpful overviews. Overriding requirement: **reliability** — answer only when grounded, but NEVER abstain on something the KB can clearly answer. Live at https://induction.wcma.work/. Clone of the RCS bot (`C:\Users\m.rahman\src\rcsbot`); same OpenAI key, separate repo / Qdrant collection (`induction_documents`) / deployment.

Milestones: **M1 = MVP on a static KB (current, essentially done).** M2 = scale + self-service ingestion (Roadmap §10).

## 3. Current status (verified locally against real Postgres/Qdrant/Cohere/OpenAI/Anthropic)
The M1 reliability stack is built and runtime-verified. Both target bugs and every live-testing issue are fixed and genuinely grounded.
- Bug1 fixed on BOTH halves; Bug2 fixed; Issue#1/#2/#2.2/#3 fixed (see §5).
- Compound single-turn questions answered (ordinary + emergency in one message).
- Conversational recaps ("what were we talking about?") answered, not abstained.
- `app.eval_harness` = **11/11**. `app.smoke` (Arif's verbatim Cases 1–12 in `.cursor/smokecases.md`) = clean. Re-ingest produces ~385 chunks / ~368 clauses.
- **Answer model = Claude Opus 4.8** (answer lane); **fast lane = `gpt-5.4-mini`** (was `gpt-4o-mini` — changed after the daily-cap incident, §9). Hybrid split, agentic re-retrieval, real streaming, LLM timeouts + streaming heartbeat all live.
- Ingestion command: `python -m app.kb.ingest_kb`.

## 4. How it works — the answer pipeline
Everything funnels through `stream_grounded_answer` in `app/rag/pipeline.py` (an async generator yielding UI frames). `produce_grounded_answer` drives it and returns only the final string for non-streaming callers (`app.ask`, `app.smoke`, eval). `/chat` streams the frames. Two LLM lanes (`app/llm_factory.py`): the **answer lane** is Claude Opus 4.8 (`build_llm`); the **fast lane** is `gpt-5.4-mini` (`build_fast_llm`) for every mechanical step. Per turn:
1. KB MAP (`app/rag/kb_outline.py`) — documents + the topics/sections each covers, from the clause table, cached. Injected as a system message. Authoritative for EXISTENCE/COVERAGE/overview/tour/"how many"; NOT a source of rule content.
2. Condense (`condense_to_standalone_question`, fast) → standalone question. Carries the prior topic forward for bare situation/condition follow-ups only.
3. Split (`split_into_questions`, fast) → up to 4 self-contained sub-questions (handles compound messages).
4. Per sub-question: query rewrite (`build_search_query`, fast) → retrieve dense (Qdrant) + BM25 for the sub-question AND its rewrite, fuse/dedup, Cohere-rerank against the sub-question (`app/rag/retrieval.py`). Union passages across sub-questions. (Retrieving per sub-question avoids the dominant intent evicting the others' passages.)
5. Expand clauses (`app/rag/expansion.py`): add sibling + cross-referenced clauses from the clause table.
6. Applicability filter (`app/rag/applicability.py`, fast, async/concurrent): SCOPE GATE, KEEP-BY-DEFAULT. Sees each conditional provision's breadcrumb; drops it ONLY when it clearly belongs to a special/different scenario than the question. Runs per sub-question; survivors unioned. Primary Bug1 guard.
7. Generate (`generate_answer_stream`, Opus 4.8) — streamed live, with system prompt + MAP + SOURCE MATERIAL + history.
8. Verify (`verify_answer`, fast): MAP-authoritative for coverage; SOURCE-required for substantive facts; CONVERSATION-authoritative for recap/meta claims. Does NOT re-judge scope (trusts the applicability filter). Pass → commit (`final`). Fail → reset + regenerate (varied seed); still fail → agentic re-retrieval (`build_refined_search_query` → re-retrieve → merge) + retry; still fail → abstain (`UNSURE_RESPONSE`).

`/chat` streams ndjson frames: `{"t":"status"}` (milestone), `{"t":"delta"}` (live answer token), `{"t":"reset"}` (clear an unverified failed draft), `{"t":"final"}` (committed verified answer). A heartbeat re-emits the current status every 15s during the silent mechanical/agentic steps so the stream never goes idle. Every LLM client has a hard timeout (45s fast / 120s answer) + `max_retries=2`. Frontend parser + muted "thinking" rendering: `frontend/app/assistant.tsx`.

Ingestion (`app/kb/ingest_kb.py`): parse (`app/kb/parse.py`) → situate+chunk with generated titles (`app/kb/contextual.py`, fast) → embed to Qdrant + save BM25 corpus (`kb_index/`) + persist clause table (`app/kb/clause_model.py`). Full rebuild each run; wipes the Qdrant collection (so trainer-added KB vectors are erased).

## 5. Recurring challenges (the heart of this project — read carefully)
1. **Bug1 — lexical-match-over-relevance (THE original bug).** A normal lunch-break question answered from emergency-only Appendix C because it matched keywords, missing governing clause 23. Root cause is structural: applicability comes from heading hierarchy, which naive chunking severs. TWO halves, BOTH must hold: (a) don't ANSWER from a conditional clause out of scope → applicability filter; (b) still RETRIEVE the governing general clause → query rewrite + fused retrieval. We re-broke (b) once (filter stripped Appendix C but 23.2 was never retrieved → abstain); query rewrite fixed it. Never special-case emergencies.
2. **Bug2 — false abstention on coverage/"how many".** Model listed every leave type from the MAP, but the verifier graded each against retrieved passages and failed them → ~83% abstain. Fix: MAP authoritative for existence/coverage in both generation and verification. Principle: answer only accurately, but NEVER abstain on a clearly KB-answerable question.
3. **Fast models are NOT deterministic even at temperature 0.** Identical input gave different verdicts run-to-run. A fixed `seed` materially stabilises it but is best-effort. The verifier is both the main reliability lever AND the main false-abstention risk — tune its prompt carefully and re-measure stability over SEVERAL runs, not once.
4. **Don't trust document structure.** Future docs may have no headings — we generate a TITLE per unit and fall back to per-page units for unstructured PDFs. The KB MAP is built from the clause table so generated titles flow through. Dense numbered appendices hid two traps: a per-page running header matching the APPENDIX regex (split the appendix by page) and trailing-dot sub-clause numbers (`1.5.`) the regex rejected. `parse.py` now suppresses repeated appendix headers, accepts trailing-dot sub-clauses, and treats numbered headings inside an appendix as its sub-units. Watch for the same in new docs.
5. **The verifier must NOT re-judge scope.** Originally it failed any answer using emergency/conditional content → false abstention on EXPLICIT emergency questions. Scope is decided ONCE upstream by the applicability filter; the verifier trusts it and only checks grounding + fabrication. Don't reintroduce a scope check there.
6. **Condense can silently lose the topic.** "what would be the case during emergency work" condensed to a topic-less standalone → retrieval missed the meal-break clause. Condense now carries the prior topic forward for bare situation/condition follow-ups — but NOT for topic switches ("lets talk about X"). Re-measure several runs after touching it.
7. **Applicability conditions are often DESCRIPTIVE, not exclusionary.** Clauses carry a terse `condition` ("non-casual employees", "after probation", cryptic tags like "AIMS control system"). Judging that string in isolation dropped the PRIMARY clause for plain questions (clause 36.1 annual leave; clause 1.5 emergency meal). Fix that holds: feed the judge the section BREADCRUMB and KEEP-BY-DEFAULT — exclude only when the provision clearly belongs to a special/different scenario. Don't revert to "does the employee meet this condition?" hard gating.
8. **Compound questions need per-sub-question retrieval.** A single message can bundle an ordinary-day AND an emergency intent. A blended query lets the dominant intent flood the reranked top-K and EVICT the other's clause (emergency Appendix C crowding out clause 23.2). Fix: split into sub-questions and retrieve + filter PER sub-question, then union. A single-intent question is just one retrieval, so unchanged.
9. **The verifier needs conversation history for meta questions.** It only saw policy SOURCE MATERIAL, so a correct recap ("what were we talking about?") was graded ungrounded and abstained. Fix: pass history into `verify_answer`; the verifier treats the CONVERSATION as authoritative for recap/meta claims (still requires source for substantive facts).
10. **Hybrid lanes are deliberate — keep them separate.** Opus 4.8 cannot be seeded and rejects `temperature` (adaptive thinking), so anything it touches varies run-to-run; that's why the retrieval-SHAPING steps run on the seedable fast lane. Swapping the model on a step can change behaviour (the upgrade exposed that the fast model is a STRICTER applicability judge than Opus and over-dropped clauses). If you change which model runs a step, re-measure.
11. **Verification gates streaming, never the reverse.** The Opus answer streams live, but a draft that fails verification is `reset` (cleared) and replaced. Never stream a final the verifier hasn't passed.
12. **Diagnose, don't guess.** Every real fix here came from tracing the actual pipeline (retrieval ranks, applicability output, verifier verdict/reason), not from assuming. When something abstains or errors, find out WHICH stage produced it before changing anything.

## 6. What we tried that did NOT work (dead-ends — don't repeat)
1. **Keyword `detect_scope` (AIIMS/incident-control) + emergency-specific prompt lines.** The very first Bug1 "fix". REJECTED on principle (case-specific hack) and because it only patched the one example. The general fix is contextual chunking + applicability filter.
2. **"Full KB in context + prompt caching" instead of RAG.** Considered, never built, now abandoned. The reliability stack supersedes it.
3. **Running EVERYTHING on Opus 4.8.** ~60–110s/turn AND non-deterministic (no seed, no temperature 0), which broke reproducible retrieval. Replaced by the hybrid split (Opus answers; fast lane does mechanical steps).
4. **Applicability as a strict "does the employee meet this condition?" hard gate, judging the bare condition string.** Dropped relevant primary clauses (36.1, 1.5) once the stricter fast model replaced Opus. Replaced by keep-by-default + breadcrumb context.
5. **Fixed-seed verifier RETRY.** A retry with the same seed produced an IDENTICAL draft, so retries were useless. Now the seed varies per attempt.
6. **KB MAP rendered as one long semicolon line.** The verifier intermittently failed to find real items in the wall of text (e.g. "Workplace Training Leave", §47) → flaky Bug2 abstention. Now one section per line.
7. **A single blended query for compound questions.** The dominant intent evicted the other intent's clauses. Replaced by per-sub-question retrieval + union (challenge §5.8).
8. **Verifier without conversation history.** Caused false abstention on recap/meta questions (challenge §5.9).
9. **`gpt-4o-mini` for the fast lane.** Hit OpenAI's hard 10k-requests/day Tier-1 cap in production; every turn 429'd, retried, stalled, and the stream died ("network error"). Replaced by `gpt-5.4-mini` (no RPD cap; GPT-5 reasoning-effort handled). See §9.
10. **Relying on the reverse proxy's default idle timeout during silent steps.** The mechanical block sends no bytes; a slow run exceeded nginx's 60s read timeout and the in-flight stream was aborted mid-response. Fixed by a 15s heartbeat + explicit LLM client timeouts. (You can ALSO raise `proxy_read_timeout`/`proxy_send_timeout` on the nginx induction block as belt-and-suspenders.)
11. **A separate clarify/deflect path + a hard rerank-confidence gate.** Removed; the verifier verdict alone now decides answer vs abstention (calibrated abstention).

## 7. Key files
- `app/llm_factory.py` — provider-agnostic builder; answer lane (Opus 4.8) vs fast lane (`gpt-5.4-mini`); Opus runtime quirks; GPT-5 reasoning effort; per-request timeouts + retries.
- `app/rag/pipeline.py` — the one answer path: `stream_grounded_answer` (frames + heartbeat + sub-question retrieval + agentic re-retrieval) and `produce_grounded_answer`.
- `app/rag/chat.py` — system prompt, condense, `split_into_questions`, `build_search_query`, `build_refined_search_query`, `generate_answer(_stream)`, `verify_answer` (map/source/conversation authority), `build_llm`/`build_fast_llm`, `UNSURE_RESPONSE`.
- `app/rag/retrieval.py` — dense+BM25 gathering over multiple queries, fuse/dedup, Cohere rerank, `dedup_key`.
- `app/rag/applicability.py` — async keep-by-default conditional filter with breadcrumb context (primary Bug1 guard).
- `app/rag/expansion.py`, `app/rag/kb_outline.py` — clause expansion; KB MAP.
- `app/kb/parse.py`, `app/kb/contextual.py`, `app/kb/clause_model.py`, `app/kb/bm25_index.py`, `app/kb/ingest_kb.py`, `app/kb/store_clauses_from_corpus.py` — ingestion.
- `app/main.py` — FastAPI wiring + all endpoints (incl. `DELETE /sessions/{id}`); `/chat` streams the pipeline.
- `app/reset_prompt.py` — re-seed the DB system prompt after a prompt change.
- `app/eval_harness.py` (11 cases), `app/smoke.py` (Arif's 12 verbatim cases).
- Auth/stores: `app/auth.py`, `app/models.py`, `app/schemas.py`, `app/seed_admin.py`, `app/chat_store.py`, `app/config_store.py`, `app/kb_store.py`, `app/admin_store.py`, `app/trainer_kb.py`.
- `frontend/` — Next.js + assistant-ui (auth gate, sidebar sessions + hover-delete, muted streaming "thinking", trainer upload, admin panel).

## 8. Server & deployment
- EC2 `i-0e5194e443d3c0049`, region `ap-southeast-2`, IP `13.55.191.184`, Ubuntu, t3.large. Live https://induction.wcma.work/.
- **SSH:** `ssh -t -i 'C:\Users\m.rahman\assets\keys\Playground1.pem' ubuntu@13.55.191.184`, then `sudo -u ssm-user bash` (passwordless). `ssm-user` runs `docker` WITHOUT sudo. Do NOT change the server unless Arif asks.
- **Alternative (no SSH key needed) — AWS SSM**, which I used to diagnose/fix the box from Windows (AWS CLI authenticated, region `ap-southeast-2`). Run a shell command on the instance and read the result:
  ```powershell
  # put commands in a JSON file to avoid PowerShell quoting hell:
  # _ssm.json -> { "commands": ["docker ps", "docker logs --tail 50 induction 2>&1"] }
  $cid = aws ssm send-command --instance-ids i-0e5194e443d3c0049 --document-name "AWS-RunShellScript" --parameters file://_ssm.json --query "Command.CommandId" --output text
  aws ssm get-command-invocation --command-id $cid --instance-id i-0e5194e443d3c0049 --query "StandardOutputContent" --output text
  ```
  This runs as root and is the easiest way to inspect `docker logs`, check the container `.env` (`docker exec induction printenv | grep FAST_CHAT_MODEL`), or test a fast-lane call. Clean up the temp JSON afterwards.
- App dir `/home/ssm-user/apps/induction/`: holds `compose.yaml` + `.env`; the repo is in `app-src/`. Compose services: `induction` (backend, `read_only: true`, 512M, `/tmp` tmpfs, writable `induction_kb_index` volume at `/app/kb_index`), `induction-frontend`, `induction-postgres`, `induction-qdrant`. Network `internal-apps` (external). Shared `nginx-reverse-proxy` terminates SSL.
- Deploy scripts (run from `app-src/`; they copy `deploy/compose.server.yaml` → `../compose.yaml`):
  - `bash m1_update.sh` — ONCE, first M1 cutover; builds, seeds admin, first ingest.
  - `bash update.sh` — small code change; rebuild + restart; NO re-ingest.
  - `bash hard_update.sh` — documents or KB/parsing/chunking/clause-schema changed; rebuild + (prompted) full re-ingest INSIDE the container (`docker compose exec -T induction python -m app.kb.ingest_kb`).
  - Rule of thumb: changed `app/kb/**`, `documents/`, or the map/clause schema → `hard_update.sh`. Changed only `app/rag/**` or frontend → `update.sh`. Changed `DEFAULT_SYSTEM_PROMPT` → also `docker compose exec -T induction python -m app.reset_prompt`.
- **Server `.env` is gitignored** (lives only on the box) and must be kept in sync with code defaults. Required keys: `LLM_PROVIDER=anthropic`, `ANTHROPIC_API_KEY`, `ANTHROPIC_CHAT_MODEL=claude-opus-4-8`, `FAST_LLM_PROVIDER=openai`, `FAST_CHAT_MODEL=gpt-5.4-mini`, `OPENAI_API_KEY`, `OPENAI_EMBEDDING_MODEL`, `COHERE_API_KEY`, `COHERE_RERANK_MODEL`, `QDRANT_COLLECTION`, `DOCUMENTS_DIR`, `FRONTEND_ORIGIN=https://induction.wcma.work`, `JWT_SECRET`, `POSTGRES_PASSWORD`, `COOKIE_SECURE=true`, `ALLOWED_EMAIL_DOMAIN=wcma.vic.gov.au`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`. `DATABASE_URL` + `QDRANT_URL` come from compose — don't hardcode localhost on the server. After editing `.env`, recreate the container so it re-reads `env_file`: `docker compose up -d --force-recreate --no-deps induction` (a bare restart may not pick it up).
- nginx (one-time, manual): the `induction.wcma.work` 443 block must route ALL backend paths, not just `/chat`. Matcher: `location ~ ^/(chat|auth|users|sessions|kb|admin/|health)`. NOTE the trailing slash on `admin/`: `/admin` is also a frontend page, so a bare `admin` token routes the PAGE to the backend → `{"detail":"Not Found"}`; `admin/` sends only the `/admin/...` APIs to the backend and lets the `/admin` page reach the frontend (incident §9.4). It also sets `proxy_buffering off` for streaming; consider `proxy_read_timeout 300s; proxy_send_timeout 300s;` there too. Full block + reload in `deploy/README.md`. Without the matcher, login/admin/sessions 404.
- Verify after deploy: `docker compose exec -T induction python -m app.eval_harness` (11/11) and `... app.smoke` (no abstentions on Cases 1–12).

## 9. Incident log (recent, so you have the full story)
1. **"Stuck at Searching the policy library… then network error" (the big one).** Browser console showed `POST /chat net::ERR_HTTP2_PROTOCOL_ERROR 200 (OK)` then `TypeError: network error`. The `200` proved the stream OPENED then was torn down mid-flight. Root cause (found via SSM `docker logs induction`): the server `.env` still had `FAST_CHAT_MODEL=gpt-4o-mini`, which had hit its 10k-requests/day cap — `openai.RateLimitError: 429 ... requests per day (RPD): Limit 10000, Used 10000`. Every fast-lane call 429'd → retried → the silent stream exceeded the proxy idle timeout → reset. Fix applied on the box via SSM: set `FAST_CHAT_MODEL=gpt-5.4-mini`, `docker compose up -d --force-recreate --no-deps induction`, verified a live fast-lane call returned OK. Code fixes shipped the same day: LLM per-request timeouts + a 15s streaming heartbeat (so a future stall fails fast and the stream stays alive). Lesson: keep the server `.env` in sync; the heartbeat/timeout code masks slowness but the real cause was the stale model + daily cap.
2. **Stale system prompt in production.** A server with current code + KB still gave the old wrong emergency-work answer because its stored prompt was the old short one (2142 vs 4198 chars). The prompt is seeded once and not refreshed by deploys → run `python -m app.reset_prompt`. (Footgun §10.7.)
3. **Delete-session "didn't work".** The backend was a stale uvicorn instance missing the `DELETE /sessions/{id}` route, and the frontend swallowed the error. Fixed by restarting the backend + better frontend error handling.
4. **`/admin` returned `{"detail":"Not Found"}`.** The nginx matcher `^/(chat|auth|users|sessions|kb|admin|health)` routed the `/admin` FRONTEND page to the backend (which has no `GET /admin`, only `/admin/users|prompt|kb`). The JSON 404 (vs an HTML 404) was the tell that the page hit FastAPI. Fixed on the box via SSM: matcher → `...|kb|admin/|health` (trailing slash), so only `/admin/...` APIs go to the backend and the `/admin` page reaches the frontend. Verified: `GET /admin` → 200 text/html, `GET /admin/users` → 401 JSON. Backed up the config first; `nginx -t` + reload.

## 10. Roadmap / next tasks
M2 (planned): auto-refresh ingestion on document upload (change-detection), and robust retrieval for a larger KB (hierarchical/structured retrieval beyond rerank).

Concrete follow-ups (rough priority):
1. **Trainer KB survives re-ingest.** A full ingest wipes the Qdrant collection, erasing trainer-added vectors. Trainer content lives in Postgres (`trainer_kb_entry`); re-embed it after each ingest (or ingest from the DB) so re-ingest is non-destructive.
2. **Verifier robustness if false abstention recurs.** It's an LLM and can flip on edge cases. Consider confirm-on-fail (a true scope/hallucination fails consistently; noise won't reproduce) — but keep scope violations a hard fail. Measure over many runs.
3. **PDF text encoding artifact.** Some apostrophes extract as the replacement char (`�`). Cosmetic; normalise at parse time if Arif wants clean output.
4. **Stronger structure-agnostic segmentation.** Current fallback is one-unit-per-page. A layout-aware segmenter (font size/weight via PyMuPDF) + DOCX-without-headings handling would be more robust.
5. **Observability.** Log retrieved clauses, scores, and verifier verdicts per turn; feed flagged answers into the eval set.
6. **Span-grounded citations.** Citations are clause-number level today; verbatim-span anchoring would be stronger.
7. **Azure rebuild.** If Arif greenlights it, follow `.cursor/azurify.md`.

## 11. Gotchas learned the hard way (do not repeat)
1. `.doc` (old binary Word) is NOT cleanly ingestible — convert to `.docx` first. Future docs must be PDF or DOCX.
2. Windows: backgrounded uvicorn can inherit the WRONG cwd (workspace root = rcsbot) and load rcsbot's `.env`, silently running against the wrong collection. Pass the induction dir explicitly. If port 8000 stays held after exit (WinError 10048), kill the holding PID — don't switch ports. `--reload` file-watching is flaky on Windows; restart the backend if a change doesn't take.
3. Backend container is `read_only` (only `/tmp` + the `kb_index` volume writable). The BM25 index needs that writable volume; ingest must run inside the container so the index persists.
4. Keep DB work under a single `asyncio.run` (a second `asyncio.run` in one process crashed ingest with "Event loop is closed"). `store_clauses_from_corpus.py` rebuilds the clause table cheaply from the saved BM25 corpus if an ingest dies after the expensive situating step.
5. Re-ingest is DESTRUCTIVE (wipes Qdrant incl. trainer KB) and SLOW (~8–12 min). Only run when ingestion logic or documents changed.
6. PowerShell has no heredocs and mangles inline quoting. For git commit messages, write the message to a temp file and `git commit -F file`. For SSM, put the command list in a JSON file and use `--parameters file://...`.
7. **System-prompt staleness footgun** (§9.2): the prompt is DB-stored and seeded ONCE; code edits do NOT reach a running bot until `python -m app.reset_prompt`.
8. **Fast-lane daily cap footgun** (§9.1): don't use `gpt-4o-mini` for the fast lane; keep `FAST_CHAT_MODEL=gpt-5.4-mini` in both code default and server `.env`.

## 12. Conventions
- Keep `.cursor/plan.md` current; commit + push at the end of each phase. Update `.cursor/blueprint.md` when the architecture/config changes.
- Git remote `git@wcma:arifwcma/induction.git`, branch `main`. The server's `app-src` pulls the same remote.
- Commit messages: short, why-focused, via a temp file + `git commit -F`.
- `.sh` and `deploy/*.yaml` are pinned to LF endings (`.gitattributes`) for Linux.
- Broader server docs: `C:\Users\m.rahman\src\playground_details`. The `pozi_base` path on the server is a different deployment — do not touch.
- NEVER commit `.env` or any secrets. NEVER paste real API keys / passwords into docs.
