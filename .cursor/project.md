This is the Wimmera CMA induction chatbot.

It is used by newly joined employees at Wimmera CMA to ask questions about induction material: policies, procedures, the enterprise agreement, and related documents in the `documents/` folder (PDF and DOCX). New or updated documents arrive from time to time and the bot's knowledge is refreshed by re-running ingestion.

It is a clone of the RCS chatbot (same architecture and stack: FastAPI + LlamaIndex + Qdrant + Next.js/assistant-ui + Docker), but a separate repo, a separate Qdrant collection (`induction_documents`), and a separate deployment at https://induction.wcma.work/. It uses the same OpenAI API tokens.

Same product expectations as the RCS bot: fast, concise, ChatGPT-like, answers strictly from the documents, keeps session memory, and asks one clarifying question when a query is vague instead of giving a generic answer. No hacks; battle-tested stack only.

## Known bugs to prevent

### Bug1 — wrong-context retrieval (lexical-match-over-relevance)
The bot answered a normal leave question from an emergency-only appendix because that appendix text matched the question's keywords better, even though the appendix did not apply to the asked situation. Root cause: retrieval ranked by raw text/embedding similarity, not by true contextual relevance or document applicability. The bot must never answer on lexical match alone; it must pick the contextually correct section and, when unsure which context applies, ask a clarifying question instead of guessing.
