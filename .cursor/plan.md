# Wimmera CMA Induction Chatbot — Project Plan

## Goal
A fast, concise, ChatGPT-like chatbot for new Wimmera CMA employees. It answers strictly from the induction documents in `documents/` (PDF and DOCX: policies, procedures, the enterprise agreement), keeps session memory, cites its sources, and asks a clarifying question instead of guessing. The overriding requirement is reliability: it must never confidently answer when unsure. Live at https://induction.wcma.work/.

## Milestones (redesigned)
1. Milestone 1 — MVP: commercially usable on a static, limited KB. (current focus)
2. Milestone 2 — Scale + self-service ingestion: auto-refresh ingestion on document upload, and robust retrieval for a large KB.

## Origin
Cloned from the RCS chatbot (`C:\Users\m.rahman\src\rcsbot`). Same architecture and conventions; rebranded context, collection `induction_documents`, domain https://induction.wcma.work/. Uses the same OpenAI API key.

---

## Milestone 1 — MVP (commercially usable on a static, limited KB)

### Top requirement
Reliability over cost. The bot must never guess or hallucinate; when unsure it says so or asks a clarifying question. No hacks.

### M1 scope (agreed expectations)
1. Reliability is the uncompromisable requirement.
2. No guessing / no hallucination — enforced by prompt + a retrieval confidence gate, not tone alone.
3. Simple registration / sign-in on the home page, restricted to `@wcma.vic.gov.au` emails.
4. Users can see their past sessions (ChatGPT-style thread list).
5. The bot remembers past sessions in summarised form (lightweight: per-session summary + a small rolling user-profile summary injected into new sessions).
6. Admin panel: view users and their conversations, reset user passwords, promote users to trainer.
7. Two user roles: basic and trainer (plus admin).
8. All users are basic by default; admin can promote to trainer.
9. Trainer knowledge enters the KB two ways: an "Add to KB" button on a message (saves that message's text), and trainer document upload (PDF/DOCX/TXT). Both stored with provenance (trainer + date), live immediately; admin can audit/remove.
10. Admin can view the system prompt in a textbox and edit it; saving reconfigures the bot at runtime.
11. The bot cites the source of each answer: document + section/page where feasible. Trainer-sourced answers say so.
12. The bot must never answer on lexical match alone (Bug1: the leave-vs-emergency-appendix / clause-23.3 bug).

### Locked decisions
1. KB handling (req 12): RELIABILITY STACK (revised 2026-06-17). This SUPERSEDES both the earlier "full KB in context" idea and the first reranker+keyword-scope build. The keyword `detect_scope` (AIIMS/incident-control) and emergency-specific prompt lines were a Bug1-specific hack and are being removed. The reliability stack treats scope as a representation problem solved at ingestion (Anthropic Contextual Retrieval), not a ranking trick, and adds grounded/verified generation, calibrated abstention, and an eval harness. See blueprint.md for the full spec.
2. Reranker vendor: Cohere Rerank (env-configurable `COHERE_API_KEY`). Offloads compute (backend container capped at 512M).
3. Auth: self-hosted. Postgres + FastAPI-Users (JWT, roles, admin password reset, domain-restricted signup). [Built]
4. Database: PostgreSQL — users, roles, sessions, messages, summaries, trainer-KB entries, editable system prompt. [Built]
5. Cross-session memory: lightweight (per-session summary + rolling user-profile summary). [Built]
6. System prompt: in DB config, loaded at runtime, admin-editable. [Built]
7. Citations: span-grounded (verbatim span + clause number), validated against the structured clause model.

### Reliability stack (req 1, 2, 12) — the real fix, replacing the keyword hack
Why the first build was wrong: it ranked + tagged for the known emergency case. Scope (a clause applying only under a condition, e.g. emergency / casual / probation) is set by a chunk's place in the document heading hierarchy, which naive chunking severs. The fix makes every chunk carry its own structural context, generically.

A. Knowledge representation
1. Structure-aware parsing: split by real structure (EA clause numbers like 23, 23.1, Appendix C; DOCX heading styles); strip page noise (OFFICIAL, running headers); record clause number, title, parent path, page.
2. Contextual chunking (keystone, Anthropic Contextual Retrieval): prepend each chunk with a deterministic breadcrumb + a 50-100 token LLM situating-context stating its scope, before embedding and BM25.
3. Structured clause model for the EA: clauses extracted to a table (number, title, scope, parent, cross-references) so applicability is queryable data, not inferred.

B. Retrieval
4. Hybrid dense + BM25 (BM25 catches exact refs like "23.3").
5. Cohere cross-encoder rerank to top-k.
6. Expansion: include the full governing clause + cross-referenced clauses so interactions are visible.

C. Grounded generation
7. Generic scope/precedence prompt (NO hardcoded keywords): obey conditions stated in a passage; conditional clauses govern only if their condition is met; apply precedence (NES-overrides per EA clause 4.3; specific-over-general).
8. Span-grounded citations: every claim anchored to a verbatim span + clause number.
9. Verifier pass: cheap second call checks each claim is supported, the cited clause exists/in-scope, no interacting clause ignored; fail -> regenerate once, else abstain.
10. Calibrated abstention: rerank confidence + verifier verdict -> answer / clarify / route to People & Culture. Never guess. Verifier runs in parallel with streaming so latency stays low.

D. Measurement and feedback
11. Eval harness (first-class): adversarial cases across scope, clause-interaction, scenario/computation (the 0-vs-30 case), out-of-scope (must abstain), citation-correctness; pass-rate per category; runs as a regression gate.
12. Observability + loop: log retrieved clauses, scores, verifier verdicts; flagged answers feed the eval set.
13. Trainer-content guard: trainer KB is scoped and still subject to grounding/verification; it cannot silently override authoritative clauses.

Honest residual: target is calibration (right when confident, abstain when not), not perfection; gold eval answers need human (People & Culture) validation; embedding model is a tunable the eval will surface.

### Reliability-stack build order (supersedes the steps below; commit/push at natural points)
R1. Structure-aware parsing (EA clause numbers + DOCX headings, strip page noise).
R2. Contextual chunking (breadcrumb + LLM situating-context) before embedding/BM25.
R3. Structured clause model for the EA.
R4. Hybrid retrieval (dense + BM25) + Cohere rerank + governing/cross-ref expansion.
R5. Grounded generation: generic scope/precedence prompt, span citations, verifier pass, calibrated abstention (verifier parallel to streaming).
R6. Remove the AIIMS keyword detect_scope + emergency-specific prompt lines.
R7. Eval harness (per-category pass rates, regression gate) + observability.

### Original M1 build order (superseded for retrieval; auth/sessions/admin parts still stand)
1. Retrieval rebuild (section-aware ingestion + scope tags + dense top-k + Cohere rerank + confidence gate + citations). **[Superseded by the reliability stack — was the keyword-hack build]**
2. Regression eval seeded with the clause-23.3 case. **[Folded into the eval harness R7]**
3. Postgres + FastAPI-Users auth, roles, domain-restricted signup, admin reset (cookie JWT, env-seeded admin). **[Done, 7954a80]**
4. Persisted sessions/messages + lightweight cross-session memory. **[Done, 06f2730]**
5. System prompt in DB config, runtime-loaded. **[Done, b6414c2]**
6. Trainer KB: "Add to KB" + document upload, with provenance. **[Done, a86b237]**
7. Admin panel APIs. **[Done, bfe3240]**
8. Frontend: auth UI, persisted thread list, citations (cited inline in answers), Add-to-KB button, admin panel. **[Done, b008679 — typecheck + next build + oxlint pass; not browser-tested against a live backend]**
9. docker-compose: local Postgres added (7954a80). Server `compose.yaml` Postgres service + new env + nginx routing + prod-hardening documented in handover.md. **[Local done; server steps documented for the EC2 deploy agent]**

### M1 status: RELIABILITY STACK BUILT + runtime-verified locally (Postgres + Qdrant + Cohere live).
The reliability stack (R1–R7) is implemented and verified locally against real Postgres/Qdrant/Cohere/OpenAI. Two post-launch reliability phases followed:

Phase 1 (generation/retrieval reliability, no re-ingest needed):
- Bug2 fix: the KB MAP is authoritative for EXISTENCE/COVERAGE/ENUMERATION ("how many", lists, overviews) in both generation and verification; substantive facts still require retrieved source; scope violations stay a hard fail. Removed the old hard rerank confidence gate and the separate clarify/deflect path.
- Bug1 second half: query rewriting (`build_search_query`) — retrieve on both the user's wording and a concept-focused rewrite, fuse, then rerank — so the governing general clause is actually retrieved even when a conditional look-alike is the lexical match.
- Fixed `seed` on all chat/verifier LLM calls to cut non-determinism.

Phase 2 (structure-agnostic ingestion, requires re-ingest):
- LLM-generated section TITLE per unit (used when the document has no heading); flows into breadcrumb, chunk header, clause record, and the map.
- Per-page fallback segmentation so unstructured PDFs never yield zero units.
- KB MAP built from the clause table (not a live regex re-parse), so it reflects generated titles.

Phase 3 (emergency-work questions + conversational polish; requires re-ingest):
- Verifier trusts the applicability filter as the scope gate (no longer fails answers for using emergency/conditional content) — fixes Issue#1/#2 false abstention; Bug1 still holds via the filter + generator prompt.
- Finer appendix segmentation (`parse.py`): accept trailing-dot sub-clauses, suppress repeated per-page appendix headers, treat numbered headings inside an appendix as its sub-units. Appendix C: 15 → 66 fine units; buried rules (e.g. clause 1.5 "meal interval counts as time worked") now retrievable.
- Topic-carrying condense for bare situation/condition follow-ups ("what would be the case during emergency work" → "During emergency work, does a meal break count as worked hours?"), but never for topic switches.
- Tour self-awareness + overview-first in the system prompt (Issue#2.2, Issue#3).
- Map rendered one section per line (verifier could not reliably find items in the old wall-of-text) and varied retry seeds.

Acceptance: `app.eval_harness` 9/9 (incl. Bug1 ordinary-day AND Issue#1 emergency-work meal break); `app.smoke` Cases 1–6 in `.cursor/smokecases.md` clean (Issue#1 measured 6/6 correct). Re-ingest ~385 chunks / ~368 clauses. Bugs/Issues documented in `.cursor/project.md`. Deploy per `deploy/README.md` — Phase 3 changed ingestion, so a re-ingest is MANDATORY (`hard_update.sh`).

Phase 4 (model upgrade + hybrid split + agentic retrieval + streaming; NO re-ingest):
- Answer model upgraded to **Claude Opus 4.8** via a provider-agnostic factory (`app/llm_factory.py`, `LLM_PROVIDER=anthropic`). Opus 4.8 quirks handled at runtime (unknown to the pinned package; rejects `temperature`).
- Hybrid split: Opus 4.8 answers; `gpt-4o-mini` runs condense/query-rewrite/applicability/verifier/situating/summary. Keeps retrieval seeded/deterministic and cuts a clean turn to ~8–11s to first token.
- Applicability filter reworked to keep-by-default + breadcrumb context + concurrent checks — fixed false drops (clause 1.5, clause 36.1) the stricter fast model exposed.
- Agentic re-retrieval: refine query + re-retrieve + retry once before abstaining.
- Real streaming: `/chat` now emits newline-delimited JSON frames (`status`/`delta`/`reset`/`final`); the verifier still gates (unverified draft is reset/replaced). New deps: `llama-index-llms-anthropic==0.11.4`. New env: `LLM_PROVIDER`, `ANTHROPIC_API_KEY`, `ANTHROPIC_CHAT_MODEL`, `FAST_LLM_PROVIDER`, `FAST_CHAT_MODEL`. Deploy = `update.sh` (no ingestion change). Eval 9/9 on Opus 4.8.

Phase 6 (category-aware ingestion + generic prompts + Gaps + admin user-deletion; POST-`m1-stable`; requires re-ingest + migration):
- Category-aware, multi-format ingestion: `documents/` reorganised into category folders driven by `objectives.json`; six file types (`.pdf`, `.docx`, `.doc` via LibreOffice, `.json` flatten, `link_*.txt` URL fetch via trafilatura, `.txt`); `clause.category` column; KB MAP grouped by category with objectives. New deps: `trafilatura`; backend image adds `libreoffice-writer`.
- Generic prompts: ALL document-specific instructions removed from `DEFAULT_SYSTEM_PROMPT` and the condense/split/situating examples (no emergency/AIIMS/NES/clause-numbers). Scope/precedence stated generically only. Explicit no-general-knowledge rule. The emergency scope cases now pass on the generic mechanisms alone (verified). Per Arif's instruction, future misses are fixed generically, not by re-coupling the prompt to a document.
- Reactive Gaps: a fast-lane `classify_gap` gate checks each question against the KB MAP; genuinely out-of-scope questions log a `KnowledgeGap` (with a link to the conversation) and return a fixed "noted for management" message instead of guessing. Admin Gaps view + status. (Proactive Gaps deferred — see `.cursor/to_discuss.md`.)
- Attribution: trainer-contributed facts are surfaced as "learned from management".
- Admin: `DELETE /admin/users/{id}` cascades the user's sessions/messages/gaps, nulls `trainer_id` on their KB entries (knowledge survives), and refuses self/last-admin deletion. Admin-is-trainer already held.
- Robustness: idempotent startup column migration (`app/db_migrate.py`); answer-lane retry on transient provider overload (Anthropic 529 mid-stream). Deploy = `hard_update.sh` + `reset_prompt`. Re-ingest ~446 chunks / ~418 clauses.

Phase 7 (trainer "Add to KB" + deferred document upload + apply-pending; NO re-ingest, additive table):
- Both trainer contributions are now DEFERRED, not instant. "Add to KB" (on the trainer's own message) calls `POST /kb/summarise` (fast lane, `summarise_trainer_knowledge`) to distil any taught knowledge from the session into an editable statement; Save writes it to the writable `documents/trainer/` volume and records a `PendingIngest` row. "Upload document to KB" now also just stages the file under `documents/trainer/` + a pending row (no instant embed). If the conversation has no taught knowledge the popup says so and nothing is saved.
- Ingestion is AUTOMATIC + silent: saving a note or uploading a document fires a FastAPI background task (`apply_pending_in_background`) that ingests every pending file IN-PROCESS via the refactored `embed_and_index_file` (the `ingest_one` core: Qdrant + BM25 + clause table), marks each applied (idempotent — never re-ingests an applied file), then resets the BM25 + KB-outline caches so the knowledge is retrievable a few seconds later without a container restart (the container can't restart itself). No manual "apply" button.
- Deleting a chat (user-initiated or admin per-conversation delete) now also deletes that conversation's logged `KnowledgeGap` rows so they aren't orphaned.
- Attribution: trainer files carry `origin="trainer"` (derived from the new `trainer` category), so `passage_label` keeps surfacing them as "learned from management". Adding `trainer` to `objectives.json` means a full re-ingest re-walks `documents/trainer`, so applied trainer knowledge survives a destructive rebuild (on the server it lives in the new `induction_trainer_docs` volume mounted at `/app/documents/trainer`).
- New table `PendingIngest` (auto-creates on startup). New endpoints: `POST /kb/summarise`, `POST /kb/trainer-file`, `GET /kb/pending`, `POST /kb/apply-pending`; `POST /kb/document` repurposed to staging. Deploy = `update.sh` (no re-ingest), but the server compose must add the `induction_trainer_docs` volume first. Eval 11/11, smoke Cases 1–12 clean after the change.

### New backend endpoints (for the frontend to consume)
- Auth: `POST /auth/register`, `POST /auth/jwt/login`, `POST /auth/jwt/logout`, `POST /auth/forgot-password`, `POST /auth/reset-password`; `GET /users/me`.
- Chat (login required): `POST /chat` (stream); `GET /sessions`; `GET /sessions/{id}/messages`.
- Trainer: `POST /kb/text`, `POST /kb/document`.
- Admin: `GET /admin/prompt`, `PUT /admin/prompt`, `GET /admin/users`, `POST /admin/users/{id}/role`, `POST /admin/users/{id}/reset-password`, `DELETE /admin/users/{id}` (cascade), `GET /admin/users/{id}/sessions`, `GET /admin/users/{id}/sessions/{sid}/messages`, `GET /admin/kb`, `DELETE /admin/kb/{id}`, `GET /admin/gaps`, `POST /admin/gaps/{id}/status`.
- All browser calls must send `credentials: "include"` (httpOnly cookie auth).

### Decisions made when Arif skipped the auth questions (defaults applied)
1. Login required to chat.
2. JWT carried in an httpOnly cookie.
3. First admin seeded from `ADMIN_EMAIL`/`ADMIN_PASSWORD` via `python -m app.seed_admin`.

---

## Stack (M1 target)
1. LLMs (provider-agnostic, two lanes — `app/llm_factory.py`): answer lane = Claude Opus 4.8 (`LLM_PROVIDER=anthropic`); fast lane = `gpt-4o-mini` for all mechanical steps. Embeddings `text-embedding-3-small`.
2. RAG: LlamaIndex. Vector store: Qdrant (`induction_documents`).
3. Reranker: Cohere Rerank.
4. Relational DB: PostgreSQL (new).
5. Auth: FastAPI-Users (new).
6. Backend: FastAPI (streaming chat + persisted sessions + auth/admin APIs).
7. Frontend: Next.js + assistant-ui (chat, thread list, auth, admin panel).
8. Packaging: Docker + Docker Compose (app + frontend + Qdrant + Postgres).

## Documents
- `documents/` is organised into progressive CATEGORY folders; `documents/objectives.json` defines the categories + their objectives and is the SOURCE OF TRUTH for what gets ingested (folders not listed there, and root files, are skipped).
- Six ingestible file types per category: `.pdf`, `.docx`, `.doc` (auto-converted via headless LibreOffice), `.json` (flattened to text), `link_*.txt` (single-URL fetch via trafilatura, no recursion), plain `.txt`. Trainer uploads still accept PDF/DOCX/TXT.
- Every clause carries its `category`; the KB MAP is grouped by category with each category's objective. Re-ingest after adding/changing documents.
- `app/ingest_one.py` appends a SINGLE document to the live stores (Qdrant + BM25 + clause table) without the destructive full rebuild — `python -m app.ingest_one "<path>" [category]`, then restart the backend so the cached BM25 index + KB map reload. Used to add the two `category3` policies without a full re-ingest. Next planned feature (see `.cursor/handover.md` §10): trainer "Add to KB" — summarise a chat into a knowledge `.txt` under `documents/trainer/` and an "apply pending" button that `ingest_one`s them + refreshes caches in-process.

## Hosting / Deployment
- Domain https://induction.wcma.work/. Same AWS EC2 server and conventions as the RCS bot (see `C:\Users\m.rahman\src\playground_details`). Separate compose service names (`induction`, `induction-frontend`), separate path, separate domain. Adding Postgres increases the server footprint — size during prod-hardening.
- Git remote: `git@wcma:arifwcma/induction.git`, branch `main`. Deployment by the EC2 Claude agent after push.

## Working Convention
- Keep this `plan.md` up to date. At the end of every checkpoint: update plan, commit, push.
- No hacks. If something does not work, stop and discuss rather than working around it.
- Git tag `pre_m1` (in the rcsbot repo) marks the shared pre-M1 baseline.

## Pre-M1 status (live, old architecture)
- Cloned from rcsbot, rebranded, deployed and verified at https://induction.wcma.work/.
- Old architecture = chunk RAG: PyMuPDF/python-docx ingestion -> Qdrant -> top-k=8 chunk retrieval -> `gpt-4o-mini` via LlamaIndex `condense_plus_context`. M1 replaces the retrieval/chat layer with the reranker pipeline above.
