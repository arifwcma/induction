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
1. KB handling (req 12): RERANKER PIPELINE. This OVERRIDES the earlier "full KB in context + prompt caching" decision recorded in `handover.md`. Pipeline = section-aware chunks with metadata + generous dense retrieval + Cohere cross-encoder rerank + confidence gate + citations. The full-KB-in-context approach is noted as a fallback and the reranker/hierarchical path is also the M2 direction for a big KB.
2. Reranker vendor: Cohere Rerank (env-configurable `COHERE_API_KEY`). Chosen over a local cross-encoder because the backend container is capped at 512M; rerank compute is offloaded like embeddings.
3. Auth: self-hosted. Postgres + FastAPI-Users (JWT, roles, admin password reset, domain-restricted signup).
4. Database: PostgreSQL — users, roles, sessions, messages, summaries, trainer-KB entries, editable system prompt.
5. Cross-session memory: lightweight (per-session summary + rolling user-profile summary).
6. System prompt: moves out of `app/rag/chat.py` into DB config, loaded at runtime, admin-editable.
7. Citations: ingestion becomes section-aware (document, section/clause heading, page).

### Bug1 residual risk + mitigation
A reranker only re-orders what was retrieved; Bug1 returns if the governing clause (e.g. 23.3) is never retrieved. Mitigations: generous top-k before rerank, section-aware chunking so a hit pulls its whole clause, scope tags so emergency-only chunks are filtered out of general questions, a confidence gate that clarifies instead of guessing, and a seeded regression eval (the meal-break / clause-23.3 case) so this exact failure cannot silently return.

### Build order (commit/push at each checkpoint)
1. Retrieval rebuild (section-aware ingestion + scope tags + dense top-k + Cohere rerank + confidence gate + citations). Fixes Bug1. **[Done, commit d513066 — needs COHERE_API_KEY + re-ingest to verify]**
2. Regression eval seeded with the clause-23.3 case. **[Done — `python -m app.regression`]**
3. Postgres + FastAPI-Users auth, roles, domain-restricted signup, admin reset (cookie JWT, env-seeded admin). **[Done, commit 7954a80 — needs JWT_SECRET + running Postgres to verify]**
4. Persisted sessions/messages + lightweight cross-session memory. **[Next]**
5. System prompt in DB config, runtime-loaded.
6. Trainer KB: "Add to KB" + document upload, with provenance.
7. Admin panel APIs.
8. Frontend: auth UI, persisted thread list, citations display, Add-to-KB button, admin panel.
9. docker-compose: add Postgres, env.example, prod-hardening. (Postgres service added with step 3.)

### Decisions made when Arif skipped the auth questions (defaults applied)
1. Login required to chat.
2. JWT carried in an httpOnly cookie.
3. First admin seeded from `ADMIN_EMAIL`/`ADMIN_PASSWORD` via `python -m app.seed_admin`.

---

## Stack (M1 target)
1. LLM: OpenAI `gpt-4o-mini` default, `gpt-4o` fallback for hard governing-clause reasoning. Embeddings `text-embedding-3-small`.
2. RAG: LlamaIndex. Vector store: Qdrant (`induction_documents`).
3. Reranker: Cohere Rerank.
4. Relational DB: PostgreSQL (new).
5. Auth: FastAPI-Users (new).
6. Backend: FastAPI (streaming chat + persisted sessions + auth/admin APIs).
7. Frontend: Next.js + assistant-ui (chat, thread list, auth, admin panel).
8. Packaging: Docker + Docker Compose (app + frontend + Qdrant + Postgres).

## Documents
- Supported formats: PDF and DOCX (plus TXT for trainer uploads). Legacy `.doc` must be converted to `.docx` first.
- Re-ingest after adding/changing documents.

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
