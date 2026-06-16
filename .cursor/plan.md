# Wimmera CMA Induction Chatbot — Project Plan

## Goal
A fast, concise, ChatGPT-like chatbot for new Wimmera CMA employees. It answers from the induction documents in `documents/` (PDF and DOCX), keeps session memory, and asks clarifying questions instead of giving generic answers. Standalone site at https://induction.wcma.work/.

## Stack
1. LLM: OpenAI `gpt-4o-mini`; embeddings `text-embedding-3-small`.
2. RAG framework: LlamaIndex.
3. Vector store: Qdrant, collection `induction_documents` (kept separate from RCS vectors).
4. Backend: FastAPI (streaming chat + session memory).
5. Frontend: Next.js + assistant-ui.
6. Ingestion: PyMuPDF for PDF (page-level), python-docx for DOCX (paragraphs + tables). Clears the collection then re-ingests clean text.
7. Packaging: Docker + Docker Compose.

## Origin
Cloned from the RCS chatbot (`C:\Users\m.rahman\src\rcsbot`). Same architecture and conventions; rebranded context, new collection name, new domain. Uses the same OpenAI API tokens.

## Documents
- Supported formats: PDF and DOCX only. The legacy `Induction Policy.doc` was converted to `.docx`; future `.doc` files must be saved as `.docx` before ingestion.
- Re-ingest after adding/changing documents (ingestion clears the collection then re-ingests every page/file).

## Hosting / Deployment
- Target domain: https://induction.wcma.work/ (confirmed by Arif).
- Same AWS EC2 server and conventions as the RCS bot (see `C:\Users\m.rahman\src\playground_details`). Separate compose service names (server-side `induction`, `induction-frontend`), separate path, separate domain.
- Git remote: `git@wcma:arifwcma/induction.git`, branch `main`.

## Status
- Cloned and rebranded from rcsbot: backend (config, system prompt, collection), ingestion (PDF + DOCX), frontend (titles, sidebar, metadata, API URL), Docker/env. **[Done]**
- Local verification (ingest + /health + chat query). **[Next]**
- Deploy to https://induction.wcma.work/ via the EC2 Claude agent. **[Pending]**

## Working Convention
- Keep this `plan.md` up to date. At the end of every phase: update plan, then commit and push.
- No hacks. If something does not work, stop and discuss rather than working around it.
