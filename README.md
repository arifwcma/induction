# Wimmera CMA Induction Chatbot

A fast, concise, ChatGPT-like chatbot for new Wimmera CMA employees. It answers from the induction documents in `documents/` (PDF and DOCX), keeps session memory, and asks a clarifying question instead of guessing.

Same architecture as the RCS bot (FastAPI + LlamaIndex + Qdrant + Next.js/assistant-ui), a separate Qdrant collection (`induction_documents`), and a separate deployment at https://induction.wcma.work/.

## Documents

Supported formats: PDF and DOCX. Save any legacy `.doc` as `.docx` before adding it. Re-ingest after adding or changing documents.

## RAG core

```bash
docker run -d --name induction-qdrant -p 6333:6333 -v induction_qdrant_storage:/qdrant/storage qdrant/qdrant:v1.12.5
.venv\Scripts\python.exe -m app.ingest
.venv\Scripts\python.exe -m app.ask "What is the uniform policy?"
```

## Chat API

```bash
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```bash
curl -N -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "{\"session_id\":\"s1\",\"message\":\"What is the uniform policy?\"}"
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. The backend URL defaults to `http://localhost:8000`; override with `NEXT_PUBLIC_API_URL` in `frontend/.env.local` if needed.

## Local run (without Docker)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m app.main
```

Then open http://localhost:8000/health

## Local run (with Docker)

```bash
copy .env.example .env
docker compose up --build
```

App: http://localhost:8000/health
Qdrant: http://localhost:6333/dashboard

## Stack

1. LLM: OpenAI `gpt-4o-mini`; embeddings `text-embedding-3-small`.
2. RAG: LlamaIndex.
3. Vector store: Qdrant (collection `induction_documents`).
4. Backend: FastAPI.
5. Frontend: Next.js + assistant-ui.
6. Ingestion: PyMuPDF (PDF, page-level) + python-docx (DOCX). Clears the collection then re-ingests clean text.

## Deployment

Built and pushed to git by the Cursor agent. A Claude agent on the AWS EC2 server deploys the Docker app at https://induction.wcma.work/, keeping consistency with the other deployed apps on that server.
