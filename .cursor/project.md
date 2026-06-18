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

### Issue#1 — explicit emergency-work questions abstained / answered wrongly (verifier over-reach + coarse appendix chunking + lossy condense)
Symptom: after a normal-day meal-break answer, "what would be the case during emergency work" abstained; or it answered that emergency meal breaks are NOT worked time — the OPPOSITE of the EA (Appendix C clause 1.5: "Meal intervals will not exceed 30 minutes and will be counted as time worked").

Three stacked root causes (all traced):
1. Verifier over-reach: the Bug1 scope-violation rule failed ANY answer that used conditional/emergency content, without checking whether the QUESTION was explicitly about emergencies. Fix: the applicability filter is the scope gate; the verifier now TRUSTS it (any conditional passage still present was already deemed applicable upstream) and only judges grounding + fabrication.
2. Coarse Appendix C chunking: the appendix repeats its title as a per-page running header, which matched the APPENDIX regex and split the appendix BY PAGE; its sub-clauses ("1.5.", "1.6.1.") were never split because SUB_CLAUSE rejected the trailing dot. So clause 1.5 ("counts as time worked") was buried inside a large multi-topic chunk and never retrieved. Fix (parse.py): accept trailing-dot sub-clauses, suppress repeated appendix headers, and treat numbered headings inside an appendix as sub-units of it. Re-ingest required. Appendix C went 15 coarse blobs → 66 fine sub-clause units.
3. Lossy condense on follow-ups: "what would be the case during emergency work" condensed to a topic-less standalone, dropping the meal/worked-hours subject, so retrieval missed clause 1.5. Fix (condense prompt): carry the prior topic forward ONLY when the follow-up is a bare situation/condition change ("what about during X"), never when it introduces its own topic ("lets talk about X").

### Issue#2.2 — bot could not relate "the short tours" to its own greeting offer
Root cause: the opening greeting is rendered by the frontend (initialMessages) and is never persisted, so the backend history never contains the tour offer. Fix (general): the system prompt makes the bot self-aware that it offers a guided tour, so tour/walkthrough requests are honoured even with no greeting in history.

### Issue#3 — broad open topics got only a clarifying question, no overview
Fix (prompt): for broad topics give a concise overview FIRST, then optionally one focused follow-up; never reply with only a clarifying question.

### Reliability note — map legibility + retry seeds
The KB map was rendered as one long semicolon line; the verifier intermittently failed to find real items in it (e.g. "Workplace Training Leave", §47), causing flaky Bug2 abstention. Fix: render the map one section per line. Also the generation retry now varies the LLM seed per attempt (a fixed-seed retry produced an identical draft, so retries were useless).
