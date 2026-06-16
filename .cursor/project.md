This is the Wimmera CMA induction chatbot.

It is used by newly joined employees at Wimmera CMA to ask questions about induction material: policies, procedures, the enterprise agreement, and related documents in the `documents/` folder (PDF and DOCX). New or updated documents arrive from time to time and the bot's knowledge is refreshed by re-running ingestion.

It is a clone of the RCS chatbot (same architecture and stack: FastAPI + LlamaIndex + Qdrant + Next.js/assistant-ui + Docker), but a separate repo, a separate Qdrant collection (`induction_documents`), and a separate deployment at https://induction.wcma.work/. It uses the same OpenAI API tokens.

Same product expectations as the RCS bot: fast, concise, ChatGPT-like, answers strictly from the documents, keeps session memory, and asks one clarifying question when a query is vague instead of giving a generic answer. No hacks; battle-tested stack only.
