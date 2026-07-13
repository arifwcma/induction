# Lesson Notes — Understanding the Induction Chatbot (for Arif)

These are the detailed explanations, saved verbatim so Arif can re-read them without an
agent. Companion to `.cursor/lecture_project.md` (the plan + TODO). New detailed
explanations get APPENDED here as we work through the system.

---

## Lesson 0 — The whole system in two lifecycles (the skeleton)

An AI can't "search" a pile of PDFs directly. The system has two lives: an OFFLINE prep
(ingestion) that turns documents into something searchable by meaning, and an ONLINE flow
(query time) that answers one question per turn.

### A. Ingestion — how the bot "learns" the documents (offline, run when docs change)
1. **Discover** — walk the category folders. Component: `ingest_kb.py`. Jargon: corpus.
2. **Parse structure** — split each document by its real headings/clause numbers, not
   blindly. Component: `parse.py`. Jargon: chunking, structure-aware parsing.
3. **Contextualise each chunk** — prepend a breadcrumb + a one-line "what this is / when it
   applies". Component: `contextual.py` (fast LLM). Jargon: contextual retrieval, chunk,
   breadcrumb.
4. **Embed** — turn each chunk's text into a vector (list of numbers). Component: OpenAI
   `text-embedding-3-small` → stored in Qdrant. Jargon: embedding, vector, vector database.
5. **Keyword index** — also index the same chunks for exact word matching. Component:
   `bm25_index.py`. Jargon: BM25, lexical/keyword search.
6. **Clause table + KB MAP** — structured records (title, scope, page) in Postgres; the MAP
   is the table-of-contents of everything that exists. Jargon: metadata, knowledge base.

### B. Query time — how it answers one question (online, per turn)
1. **Load history** — pull the session's past messages. Component: FastAPI + Postgres.
2. **Condense** — fold history + new question into one standalone question. Fast lane.
   Jargon: query condensing.
3. **Gap gate** — is this even in the documents? Fast lane vs the MAP. Jargon: scope,
   abstention.
4. **Split** — break a compound message into sub-questions. Jargon: decomposition.
5. **Rewrite** — turn each into a clean search query ("lunch" → "meal break"). Jargon:
   query rewriting/expansion.
6. **Retrieve** — candidates two ways: by meaning (Qdrant vectors) + by keyword (BM25),
   fused. Jargon: RAG, hybrid retrieval, dense vs sparse.
7. **Rerank** — a smarter model re-scores the top passages. Component: Cohere. Jargon:
   reranking, cross-encoder.
8. **Applicability filter** — drop passages whose conditions don't fit the question (the
   Bug1 fix). Fast lane. Jargon: scope gate.
9. **Generate** — the strong model writes the answer only from the MAP + retrieved
   passages, streamed live. Component: Claude Opus 4.8. Jargon: LLM, grounded generation,
   context window, streaming.
10. **Verify** — a checker grades every claim against the source before the user keeps it
    (the Bug2 area). Fast lane. Jargon: hallucination, grounding, verification.
11. **Retry / abstain** — if it fails, re-search and retry; if still weak, admit it doesn't
    know. Jargon: agentic re-retrieval, calibrated abstention.

**The one structural fact to hold onto:** two AI "lanes" — Opus 4.8 writes the final
answer; a fast cheap model (`gpt-5.4-mini`) does every mechanical step (condense, split,
filter, verify). That split is why it's both smart and fast.

---

## Lesson A — Ingestion in detail

### The one idea behind ingestion
An AI can't "search" a pile of PDFs directly. Before anyone asks anything, you must
pre-process the documents into a form the machine can find things in by meaning. Ingestion
is that offline prep step. It runs once (and again whenever documents change), not per
question. Think of it as building a library's catalogue before opening to the public.

### The 6 steps, and why each exists

**1. Discover — find which documents to load.**
The documents sit in folders by category (induction, policies, enterprise agreement…). A
config file (`objectives.json`) says which folders count. The code walks those folders and
collects every PDF/DOCX/etc.
- Jargon: **corpus** = the whole collection of documents the bot knows.
- Why it matters for the talk: the bot's knowledge is exactly these files and nothing else.
  That boundary is the whole point of "answers strictly from the documents."

**2. Parse structure — cut each document into meaningful pieces.**
You can't feed a 79-page agreement to the AI at once, so you cut it up. The naive way is to
cut every N words. The smart way — what this does — is cut along the document's real
structure: clause 23, clause 23.1, Appendix C. Each piece stays a coherent unit.
- Jargon: **chunking** = splitting a document into pieces ("chunks"); **structure-aware
  parsing** = splitting along real headings, not blindly.
- This is where the Bug1 story is born: naive chunking throws away the fact that "Appendix
  C" only applies in emergencies. Step 3 is the fix.

**3. Contextualise each chunk — give every piece a memory of where it came from.**
A lone chunk like "meals count as time worked" has lost its context — is that always, or
only in emergencies? So before storing it, we glue a short header onto each chunk: a
breadcrumb (`Enterprise Agreement > 23. Meal Breaks > 23.3`) and a one-line "what this is /
when it applies." Now the piece carries its own scope.
- Jargon: **breadcrumb** = the heading trail showing where a piece sits; **contextual
  retrieval** = storing each chunk with that context attached (an Anthropic-recommended
  technique).
- Lecture value: this is the elegant fix to the problem step 2 created. A great "and then
  we solved it" beat.

**4. Embed — turn text into numbers that capture meaning.**
This is the heart of modern AI search. Each chunk's text is fed to an embedding model that
outputs a vector — a long list of numbers (a point in "meaning space"). Chunks about
similar things land near each other, even with different words. "lunch break" and "meal
interval" end up close. These vectors go into a vector database (Qdrant) built to find
nearest points fast.
- Jargon: **embedding / vector** = text turned into coordinates of meaning; **vector
  database** = storage that searches by nearness in that space.
- This is the `queen − female + male ≈ king` slide. The single most important concept in
  the whole lecture.

**5. Keyword index — also keep an old-fashioned word index.**
Meaning-search is great but sometimes you need an exact match — someone types "clause 23.3"
and you want that literal string. So the same chunks are also indexed the classic
search-engine way.
- Jargon: **BM25** = a standard keyword-ranking method; **lexical/keyword search** =
  matching actual words, not meaning.
- Why both: meaning-search + keyword-search together (combined at query time as "hybrid").

**6. Clause table + KB MAP — build the table of contents.**
Alongside all that, we save a structured list: every document, its sections, titles, page
numbers — as plain database rows. From it we build the KB MAP: a definitive "here is
everything that exists" index.
- Jargon: **metadata** = data about the data (titles, pages, scope); **knowledge base** =
  the organised store the bot answers from.
- Why it matters: later, when the bot must say "we have 13 kinds of leave," it trusts this
  MAP for what exists — the seed of the Bug2 story.

**Takeaway line for the room:** ingestion is where the documents are turned into something
searchable by meaning — cut into pieces, each piece told where it belongs, each converted
into numbers, and catalogued. Everything at question-time depends on this prep being good.
