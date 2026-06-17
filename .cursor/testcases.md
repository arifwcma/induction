# Induction Chatbot — Test Cases (M1)

Human-readable test cases, grouped basic -> critical -> tricky. Each case has a purpose, steps, and expected result. Use these to test on your own or to drive a test session with the agent. "API" means the FastAPI backend; "UI" means the Next.js frontend.

Prerequisites for a full run:
- `.env` has `OPENAI_API_KEY`, `COHERE_API_KEY`, `JWT_SECRET`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`.
- `docker compose up -d postgres qdrant`, then `python -m app.ingest`, then `python -m app.seed_admin`.
- Backend running on :8000, frontend on :3000.

---

## A. Basic

### A1. Health check
Purpose: backend is up.
Steps: GET `/health`.
Expected: `{"status":"ok", ...}`.

### A2. Ingestion runs
Purpose: documents load into Qdrant with the new section-aware schema.
Steps: `python -m app.ingest`.
Expected: prints "Ingested N PDF pages and M DOCX sections into collection 'induction_documents'." No errors.

### A3. Domain-restricted registration (happy path)
Purpose: a wcma user can register.
Steps: register with `someone@wcma.vic.gov.au` + password.
Expected: 201 / success; user created with role `basic`.

### A4. Login + session cookie
Purpose: login issues the auth cookie.
Steps: login with the A3 credentials.
Expected: 200; an httpOnly cookie is set; `GET /users/me` returns the user.

### A5. Basic chat answer
Purpose: the bot answers a covered question.
Steps (logged in): ask "What should I wear to work?" (uniform policy).
Expected: a concise answer grounded in the uniform policy, with a citation (document + section/page).

---

## B. Critical

### B1. Registration blocked for non-wcma email
Purpose: enforce req 3 (domain restriction).
Steps: register with `someone@gmail.com`.
Expected: 400, message "Registration is restricted to @wcma.vic.gov.au email addresses." No user created.

### B2. Auth required for chat
Purpose: login is mandatory to chat.
Steps: POST `/chat` with no cookie.
Expected: 401 Unauthorized.

### B3. Past sessions appear and reload
Purpose: req 4 (ChatGPT-style history).
Steps: have a conversation, refresh the UI, click the session in the sidebar.
Expected: the session is listed by title; clicking it reloads its full message history.

### B4. Memory within a session
Purpose: the bot remembers earlier turns in the same session.
Steps: "I work part-time." then "How much annual leave do I get?"
Expected: the follow-up is interpreted in light of part-time; the bot does not re-ask what you already said.

### B5. Roles: basic cannot train
Purpose: req 7/8 enforcement.
Steps: as a basic user, call `POST /kb/text`.
Expected: 403 Not permitted. The "Add to KB" button is not shown in the UI.

### B6. Admin promotes a user to trainer
Purpose: req 8.
Steps: admin panel -> Users -> change a user's role to `trainer`.
Expected: role updates; that user now sees Add-to-KB and document upload.

### B7. Trainer "Add to KB"
Purpose: req 9 (message -> KB).
Steps: as trainer, click "Add to KB" on a user message stating a fact (e.g. "The office kitchen is cleaned every Friday.").
Expected: success; later a relevant question returns that fact, cited as trainer-provided.

### B8. Trainer document upload
Purpose: req 9 (document -> KB).
Steps: as trainer, upload a small PDF/DOCX/TXT.
Expected: success; its content becomes answerable and cited by filename.

### B9. Admin edits the system prompt and it takes effect
Purpose: req 10.
Steps: admin panel -> change the prompt (e.g. add "Always greet the user by saying 'Gday'.") -> save -> start a new chat.
Expected: the new behaviour appears without a redeploy.

### B10. Admin password reset
Purpose: req 6.
Steps: admin resets a user's password; user logs in with the new password.
Expected: old password fails, new password works.

### B11. Admin views a user's conversations
Purpose: req 6.
Steps: admin panel -> Users -> View chats -> pick a session.
Expected: the user's messages are shown.

---

## C. Tricky / reliability

### C1. Bug1 — meal break vs emergency appendix (THE headline case)
Purpose: req 12; prove the lexical-match bug is gone.
Steps: ask "I work 8 hours and take a 30 minute lunch from 12:00 to 12:30. Does that lunch count as time worked?"
Expected: the answer is governed by clause 23 (Rest Breaks / Meal Breaks) and cited as such, NOT Appendix C / Emergency Response. Part of the eval harness (category: scope), not a one-off.

### C1b. Scope generalisation (beyond emergency)
Purpose: prove the fix is general, not Bug1-specific.
Steps: ask a question whose answer differs for a conditional category (e.g. a casual-only or probation-only clause) while phrasing it as an ordinary employee.
Expected: the bot applies the general clause, not the conditional one, and states the condition if it ever relies on a conditional clause. Covered by the eval harness "clause-interaction"/"scope" categories.

### C1c. Verifier catches an unsupported claim / bad citation
Purpose: grounded-generation + verifier pass.
Steps: in the eval harness, include a case where the tempting answer cites a non-existent or out-of-scope clause.
Expected: the verifier fails it; the system regenerates or abstains; no fabricated clause number is shown.

### C1d. Citation validity
Purpose: span-grounded citations are real.
Steps: for answered cases, check the cited clause number exists in the structured clause model and the quoted span is verbatim.
Expected: 100% of shown citations resolve to a real clause/span.

### C2. Confidence gate — out-of-scope question
Purpose: req 2 (no guessing).
Steps: ask something not in the documents, e.g. "What's the wifi password for the Melbourne office?"
Expected: the bot says it could not find it and points to manager / People & Culture; it does NOT invent an answer.

### C3. Vague topic -> clarifying question
Purpose: req 2 (qualify, don't dump).
Steps: type just "leave".
Expected: one focused clarifying question (which kind of leave / what aspect), not a wall of every leave rule.

### C4. Conditional clause not misapplied
Purpose: scope-tagging works.
Steps: ask a normal question whose keywords also appear in the emergency appendix.
Expected: the emergency/AIIMS content is not used unless you explicitly describe an emergency/incident-control situation.

### C5. Cross-session memory (summarised)
Purpose: req 5.
Steps: in session 1 say "I'm a new field officer starting next Monday." End it. Start session 2 and ask "What should I prepare for my first day?"
Expected: the answer reflects awareness of the field-officer/new-start context from session 1, without you repeating it.

### C6. Trainer KB removal by admin
Purpose: audit/removal of trainer knowledge.
Steps: admin panel -> KB entries -> delete the entry added in B7.
Expected: the entry disappears; a later question no longer returns that fact (its vectors are removed from Qdrant).

### C7. Citation correctness
Purpose: req 11.
Steps: ask a question answered by a specific clause.
Expected: the cited document + section/page actually contains the answer (spot-check it).

### C8. Trainer-provenance labelling
Purpose: req 11 (say when info came from a trainer).
Steps: ask a question answered by trainer-added knowledge.
Expected: the bot states the information was trainer-provided.

### C9. Session isolation between users
Purpose: privacy.
Steps: user A creates sessions; user B logs in.
Expected: user B sees only their own sessions; cannot fetch A's messages.

### C10. Unsupported upload type
Purpose: input validation.
Steps: trainer uploads a `.png`.
Expected: 400, "Unsupported file type. Upload a PDF, DOCX, or TXT file."
