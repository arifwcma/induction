# Lecture Project Plan — Sydney Met Guest Lecture (ICT108)

Working plan for Arif's 1-hour guest lecture explaining the induction chatbot as a
real-world AI case study. This file tracks the LEARNING journey (Arif building a solid
end-to-end mental model) plus the deliverables. Companion to `.cursor/handover_lecture.md`
(the engagement facts, constraints, and 5-step narrative arc).

## Logistics (fixed)
- Unit ICT108, Sydney Met. Tuesday 14 July 2026, 2:00–3:00 pm. In person + live stream.
- Speaker: Dr Mohammad Arifur Rahman, Analyst Programmer, Wimmera CMA, Victoria.
- Goal: explain a real AI project at a CONCEPTUAL level (ideas + real problems, not code).

## Why this plan
Arif knows the project through the BUGS he found and fixed with Claude, not as a strict
end-to-end build. Before slides, he wants a solid mental model of how it works overall,
which component sits where, and the jargon at each step. Sequence agreed:
1. Understand the system end-to-end (this file — the explanations below).
2. Build the slide deck (pptx) from that understanding.
3. Write the spoken transcripts.

## Time budget (as of ~28h before the lecture)
- 8h sleep/other, 10h office → ~5h for slides + practice.
- Plan: ~1.5h build deck (Claude drafts, Arif reviews), ~3h rehearse out loud (2–3 full
  passes — the real nerve-killer), ~0.5h buffer (timing, opening/closing lines).

## The system in two lifecycles (the mental-model skeleton)

### A. Ingestion — how the bot "learns" the documents (offline)
1. Discover documents — walk the category folders (`ingest_kb.py`). Jargon: corpus.
2. Parse structure — split by real headings/clause numbers (`parse.py`). Jargon: chunking,
   structure-aware parsing.
3. Contextualise each chunk — prepend breadcrumb + a scope line (`contextual.py`, fast LLM).
   Jargon: contextual retrieval, chunk, breadcrumb.
4. Embed — text → vector; store in Qdrant (OpenAI `text-embedding-3-small`). Jargon:
   embedding, vector, vector database.
5. Keyword index — index the same chunks for exact word match (`bm25_index.py`). Jargon:
   BM25, lexical/keyword search.
6. Clause table + KB MAP — structured records in Postgres; the MAP is the table-of-contents
   of everything that exists. Jargon: metadata, knowledge base.

### B. Query time — how it answers one question (online, per turn)
1. Load history — session's past messages (FastAPI + Postgres).
2. Condense — history + new question → one standalone question (fast lane). Jargon: query
   condensing.
3. Gap gate — is this in the documents at all? (fast lane vs the MAP). Jargon: scope,
   abstention.
4. Split — break a compound message into sub-questions. Jargon: decomposition.
5. Rewrite — turn each into a clean search query. Jargon: query rewriting/expansion.
6. Retrieve — candidates by meaning (Qdrant) + by keyword (BM25), fused. Jargon: RAG,
   hybrid retrieval, dense vs sparse.
7. Rerank — smarter model re-scores top passages (Cohere). Jargon: reranking, cross-encoder.
8. Applicability filter — drop out-of-scope conditional passages (the Bug1 fix, fast lane).
   Jargon: scope gate.
9. Generate — strong model writes the answer only from MAP + passages, streamed (Opus 4.8).
   Jargon: LLM, grounded generation, context window, streaming.
10. Verify — checker grades every claim against the source before the user keeps it (Bug2
    area, fast lane). Jargon: hallucination, grounding, verification.
11. Retry / abstain — re-search and retry; if still weak, admit it doesn't know. Jargon:
    agentic re-retrieval, calibrated abstention.

Key structural fact: TWO AI lanes. Opus 4.8 writes the final answer; a fast cheap model
(`gpt-5.4-mini`) does every mechanical step. Smart AND fast.

## TODO — explain each of these to Arif in detail (tracking)
Claude will walk Arif through each, one at a time, plain language, lecture-pitched:
- [ ] A. Ingestion (all 6 steps) — IN PROGRESS
- [ ] B2–B3. Condense + gap gate
- [ ] B4–B5. Split + query rewrite
- [ ] B6–B8. Hybrid retrieval + rerank + applicability filter (RAG core)
- [ ] B9. Grounded generation + the two-lane split
- [ ] B10–B11. Verifier + grounding + calibrated abstention
- [ ] Jargon glossary (one accessible line each) for the deck
- [ ] Map the above onto the 5-step lecture arc (handover_lecture.md §4)

## Deliverables status
- flyer.pptx + build_flyer.py — DONE.
- writeup.txt (neutral session description) — DONE.
- design_brief.txt (poster brief for external designer) — DONE.
- Slide deck (main ask) — NOT STARTED (build after the mental model is solid).
- Spoken transcripts — NOT STARTED.

## Open items
- Flyer Bug1 framing (handover_lecture.md §4 note): the "grabbed the wrong rule" hint sits
  on the RAG card but the error is really the naive-vector-match step. Decide before the deck.
