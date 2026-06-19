# To discuss (parked decisions)

Things we deliberately deferred. Do not build these until Arif decides.

## 1. Proactive Gaps (DECISION PENDING)

We shipped the REACTIVE gap mechanism (when a user asks something the documents do not cover, the bot says so, refuses to guess, and logs a `KnowledgeGap` row that admins can review with a link to the conversation).

We have NOT built a PROACTIVE approach. The idea: let the bot (or a trainer) actively suggest how the induction documents could be arranged better and what information is likely missing that new starters would want.

Candidate approaches (pick later):
1. Isolated in-app trainer-only review module. A separate endpoint + trainer page that reads the KB map + clause table + the reactive gap log and produces suggestions. Zero shared state with the user chat, so it cannot destabilise the main bot. Strongest option because the reactive gap log becomes the proactive signal ("users asked about X N times and we have no document for it").
2. Offline with Claude chat. Paste the documents into a Claude conversation and ask for restructuring/coverage advice. Zero engineering, but not integrated, not repeatable, and not fed by real user gaps.

Recommendation when we pick this up: option 1, fed by the reactive gap log. Confirm with Arif first.

Key link to remember: the reactive `KnowledgeGap` table is the proactive feature's best input. Every real "we don't cover this" question is a ranked candidate for a new document or section.

## 2. Teaching note - why reactive Gaps are deterministic, not tool-use / MCP

Arif asked to learn what tool-use / MCP is and whether we needed it here.

What tool-use is: modern LLMs can be given a list of "tools" (functions with a name, description, and JSON argument schema). Mid-answer, the model can decide to emit a structured "call tool X with these arguments" instead of prose; our code runs the real function and feeds the result back. MCP (Model Context Protocol) is just a standard way to expose such tools/data to many models over a common protocol, instead of hand-wiring each one.

How a tool-use version of gaps would look: give the answer model a `record_knowledge_gap(topic, reason)` tool; when it judges it cannot answer from the sources, it calls the tool, and we persist the row.

Why we did NOT use it for the main chat:
1. Reliability. The answer lane (Opus) is non-deterministic and cannot be seeded. Letting it decide when to log a gap makes gap-logging flaky and adds a failure mode to the user-facing path.
2. We already have a deterministic, authoritative signal: the KB MAP says what topics exist. A cheap, seedable fast-lane classifier (`classify_gap`) checks the question against the map BEFORE we answer. If the topic is genuinely absent, we log the gap and return a fixed message. No agentic decision in the hot path.
3. Separation of concerns. Detection lives in the pipeline (`app/rag/pipeline.py`), persistence in `app/gap_store.py` - both testable without an LLM tool round-trip.

When tool-use / MCP WOULD earn its place here: the proactive module (option 1 above), where we could expose the clause table and gap log as MCP resources and let a model browse them to draft restructuring advice. Lower stakes (trainer-only, offline from the user chat), so the non-determinism is acceptable. Good place to learn it for real.
