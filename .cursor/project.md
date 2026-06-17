This is the Wimmera CMA induction chatbot.

It is used by newly joined employees at Wimmera CMA to ask questions about induction material: policies, procedures, the enterprise agreement, and related documents in the `documents/` folder (PDF and DOCX). New or updated documents arrive from time to time and the bot's knowledge is refreshed by re-running ingestion.

It is a clone of the RCS chatbot (same architecture and stack: FastAPI + LlamaIndex + Qdrant + Next.js/assistant-ui + Docker), but a separate repo, a separate Qdrant collection (`induction_documents`), and a separate deployment at https://induction.wcma.work/. It uses the same OpenAI API tokens.

Same product expectations as the RCS bot: fast, concise, ChatGPT-like, answers strictly from the documents, keeps session memory, and asks one clarifying question when a query is vague instead of giving a generic answer. No hacks; battle-tested stack only.

## Known bugs to prevent

### Bug1 — wrong-context retrieval (lexical-match-over-relevance)
The bot answered a normal break/hours question from the emergency-only Appendix C because that text matched the question's keywords, even though the appendix did not apply. Root cause is fundamental: a clause's applicability is set by its place in the document's heading hierarchy, which naive chunking severs from the chunk text — so no reranker or keyword can reliably know a chunk is conditional. This is NOT emergency-specific (same for casual-only, probation-only, etc.).

First attempted fix was a hack (keyword `detect_scope` on "AIIMS/incident control" + emergency-specific prompt lines) — REJECTED. Proper fix (the reliability stack, see blueprint.md): contextual chunking so every chunk carries its own structural scope, hybrid retrieval + rerank, a structured clause model, grounded/verified generation with span citations, calibrated abstention, and an eval harness measuring per-category reliability. The bot must never answer on lexical match alone, must respect clause scope/precedence, and must abstain/clarify when not confident.
