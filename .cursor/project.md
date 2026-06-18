This is the Wimmera CMA induction chatbot.

It is used by newly joined employees at Wimmera CMA to ask questions about induction material: policies, procedures, the enterprise agreement, and related documents in the `documents/` folder (PDF and DOCX). New or updated documents arrive from time to time and the bot's knowledge is refreshed by re-running ingestion.

It is a clone of the RCS chatbot (same architecture and stack: FastAPI + LlamaIndex + Qdrant + Next.js/assistant-ui + Docker), but a separate repo, a separate Qdrant collection (`induction_documents`), and a separate deployment at https://induction.wcma.work/. It uses the same OpenAI API tokens.

Same product expectations as the RCS bot: fast, concise, ChatGPT-like, answers strictly from the documents, keeps session memory, and asks one clarifying question when a query is vague instead of giving a generic answer. No hacks; battle-tested stack only.

## Known bugs to prevent

### Bug1 — wrong-context retrieval (lexical-match-over-relevance)
The bot answered a normal break/hours question from the emergency-only Appendix C because that text matched the question's keywords, even though the appendix did not apply. Root cause is fundamental: a clause's applicability is set by its place in the document's heading hierarchy, which naive chunking severs from the chunk text — so no reranker or keyword can reliably know a chunk is conditional. This is NOT emergency-specific (same for casual-only, probation-only, etc.).

First attempted fix was a hack (keyword `detect_scope` on "AIIMS/incident control" + emergency-specific prompt lines) — REJECTED. Proper fix (the reliability stack, see blueprint.md): contextual chunking so every chunk carries its own structural scope, hybrid retrieval + rerank, a structured clause model, grounded/verified generation with span citations, calibrated abstention, and an eval harness measuring per-category reliability. The bot must never answer on lexical match alone, must respect clause scope/precedence, and must abstain/clarify when not confident.

### Bug2 — false abstention on coverage/enumeration questions (verifier vs map)
Symptom: a coverage/counting question that the KB can clearly answer — e.g. follow-up "how many of them we got" after "tell me about leaves and breaks" (canonical smoke Case#1 Q2) — returns the canned "could not find this clearly…" abstention most of the time. Measured non-deterministically across runs: ~83–88% abstain (5/6 and 7/8 in two trace runs); occasionally it answers. Flaky abstention is worse than a clean result.

Root cause (traced, not inferred): the model correctly enumerates all leave types from the KB MAP (the structural map of documents + section titles injected each turn), e.g. all 13 EA leave sections incl. Emergency Services Leave (§33), Defence Reserve Leave (§34). But the verifier validates each enumerated item against the RETRIEVED SOURCE MATERIAL only. Retrieval surfaces just a few leave clauses, so the verifier flags the rest as "type of leave not supported by source material" and fails both generation attempts → pipeline returns UNSURE. The map (deterministically derived from the real documents) is authoritative for what EXISTS, but the verifier was not treating it as such.

Re-ingestion does NOT fix Bug2: the map already contains every section; the defect is in verification scope, not ingestion.

Proper fix (general, no case-specific keywords): treat the KB map as an authoritative source for EXISTENCE / COVERAGE / ENUMERATION claims (what documents and topics/sections exist, how many) in both generation and verification, while still REQUIRING retrieved source material for any SUBSTANTIVE policy fact (rules, numbers, durations, eligibility, conditions) and keeping the scope-violation (Bug1) check a hard fail. This removes false abstention on KB-answerable coverage questions without opening a hallucination hole, because the map carries only section titles — never rule content. Guiding principle (Arif): answer only accurately, but never abstain on a question that is clearly answerable from the KB.
