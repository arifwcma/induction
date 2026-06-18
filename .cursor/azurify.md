# Azurify — Rebuilding the Induction Chatbot on Azure AI Foundry (reliability-first)

Audience: the next agent. Task: rebuild the SAME product (see `.cursor/blueprint.md`) on Azure AI Foundry, with **reliability as the single highest priority**. Arif has effectively unlimited Azure credit, so always choose the stronger/more-managed option over the cheaper one. This is a detailed, step-by-step plan with ONE recommended choice per decision and the reason. Verify exact model/deployment names and API versions in the Foundry portal as you go (the catalog moves fast).

Context verified June 2026: Azure AI Foundry (a.k.a. Microsoft Foundry) hosts **GPT-5.4** ("Direct from Azure", GA, Microsoft-managed, "higher factual accuracy and reduced hallucinations") AND **Claude Opus 4.8** (`claude-opus-4-8`, partner model, Global Standard, 200k context). Azure AI Search does **hybrid (vector+BM25) + RRF + semantic ranker (L2 cross-encoder, score 0–4) + query rewriting + agentic retrieval** as one managed service. These two facts shape the whole design.

---

## 1. Guiding principle (read first)
1. **Keep our custom grounded-generation pipeline.** The reliability that took this project weeks is the discipline: query rewrite → sub-question split → applicability filter → grounded generation → grounding verifier → agentic re-retrieval → calibrated abstention, plus map/source/conversation authority. Azure's turnkey "chat with your data" gives great retrieval but NOT this discipline. Do NOT replace the pipeline with a black-box agent. Port it.
2. **Replace the commodity infrastructure with managed Azure services.** Self-hosted Qdrant + rank-bm25 + Cohere + EC2 + FastAPI-Users + `.env` files are exactly the parts that caused operational pain (daily-cap drift, stale prompt, stale container, nginx timeouts). Azure has stronger managed equivalents. Use them.
3. **Add the reliability layers Azure gives for free on top of ours:** Content Safety **Groundedness detection** (a managed second grounding check), Foundry **Evaluations** (groundedness/relevance as a CI gate + online), and **tracing** (per-turn observability we never built). These are pure wins.
4. **One model decision, settled by the eval harness, not by opinion.** Deploy two answer models and let the ported eval pick. Default recommendation below, but measure.

## 2. Architecture decision table (current → Azure best choice)
| Concern | Current (AWS/self-host) | Azure choice (recommended) | Why |
|---|---|---|---|
| Answer LLM | Claude Opus 4.8 (Anthropic API) | **GPT-5.4** (Azure OpenAI, Direct-from-Azure); A/B vs **Claude Opus 4.8** (`claude-opus-4-8` on Foundry) | First-party, Microsoft-managed, tightest Foundry/eval/safety integration, lower hallucination claims, no partner export-control exposure (Fable 5/Mythos 5 got suspended June 2026). Opus 4.8 is the proven incumbent and is ON Foundry, so keep it as the measured alternative. |
| Fast/mechanical LLM | `gpt-5.4-mini` (OpenAI) | **`gpt-5.4-mini`** / GPT-5-mini class (Azure OpenAI), `temperature=0` + seed | Cheap, fast, deterministic for condense/split/rewrite/applicability/verify. Same family we already tuned. |
| Embeddings | `text-embedding-3-small` (OpenAI) | **`text-embedding-3-large`** (Azure OpenAI) | Unlimited credit → take the stronger embedding for better recall. |
| Vector store + lexical + rerank | Qdrant + rank-bm25 + Cohere rerank (3 systems) | **Azure AI Search** (one service): hybrid (vector+BM25) + RRF + **semantic ranker** | Collapses three moving parts into one managed, battle-tested service whose semantic ranker is a proper L2 cross-encoder. Removes the BM25-on-disk/`kb_index` volume hack. |
| Query rewrite | our `build_search_query` (fast LLM) | keep ours; OPTIONALLY enable AI Search **query rewriting** too | Belt-and-suspenders recall; our concept rewrite + AI Search's up-to-10 rewrites compound. |
| Compound/multi-intent | our split + per-sub-question union | keep ours; OPTIONALLY AI Search **agentic retrieval** (query planning + parallel) | Our split is deterministic and tested. Agentic retrieval is a strong managed alternative — evaluate, don't assume. |
| Relational DB | PostgreSQL 16 on EC2 | **Azure Database for PostgreSQL Flexible Server** | We already use Postgres → near-zero porting; managed backups/HA. |
| Auth | FastAPI-Users (cookie JWT) | **Microsoft Entra ID** (tenant-restricted) | `@wcma.vic.gov.au` is an Entra tenant → real SSO, MFA, no password storage, no domain-restriction code. Far more reliable than rolling our own. |
| Secrets | `.env` on disk | **Azure Key Vault** + **managed identity** | Kills the `.env` drift + stale-model footguns; no secrets on disk; rotation. |
| Backend host | Docker on EC2 behind nginx | **Azure Container Apps** | Serverless containers, revisions, built-in ingress with long/streaming timeouts (no nginx idle-timeout abort), scale rules, managed identity. |
| Frontend host | Docker on EC2 | **Azure Static Web Apps** (Next.js) or Container Apps | Managed CDN + auth integration; simpler than self-hosting. |
| Orchestration | custom FastAPI pipeline | **keep custom** on Container Apps (calls Foundry models + AI Search) | Maximum control over the verifier/applicability discipline. (Foundry Agent Service is the alternative; not recommended for the reliability bar.) |
| Hallucination guard | our LLM verifier | our verifier **+ Content Safety Groundedness detection** | A managed grounding check layered on our verifier = defence in depth. |
| Eval | `app/eval_harness.py` | **Azure AI Foundry Evaluations** (offline CI gate + online) | Groundedness/relevance/coherence + custom evaluators; port our 11 cases as custom evaluators; run continuously. |
| Observability | logs only | **Foundry tracing (OpenTelemetry) + Application Insights** | Per-turn trace of retrieval ranks, applicability, verifier verdicts — the observability we listed as future work. |
| Content ingestion | custom contextual chunking | **keep custom** (Anthropic Contextual Retrieval) → push to AI Search | Our situating-context + breadcrumb + scope tags are the heart of Bug1's fix. AI Search "integrated vectorization" can't reproduce the situating LLM step; keep it and push enriched docs. |

## 3. How each reliability mechanism maps onto Azure
1. **Bug1 (scope) two-halves** — (a) don't answer out-of-scope: keep the applicability filter on the fast lane; (b) retrieve the governing general clause: keep query rewrite + now AI Search hybrid + semantic ranker (stronger recall than our Cohere step). The contextual chunk (breadcrumb + situating scope) is still what gets indexed — store it in a searchable AI Search field.
2. **Bug2 (coverage/"how many")** — keep the KB MAP from the clause table; keep MAP-authoritative verification. Unchanged (it's a prompt/verifier concern, not infra).
3. **Compound questions** — keep split + per-sub-question retrieval (run N parallel AI Search queries, union). Optionally compare against AI Search agentic retrieval via the eval.
4. **Conversational recap** — keep history-aware verifier. Unchanged.
5. **Determinism** — fast lane `temperature=0` + seed (Azure OpenAI supports seed). Answer lane stays non-deterministic; that's why mechanical steps are on the fast lane. Unchanged.
6. **Calibrated abstention** — keep verifier-decides; ADD an AI Search `@search.rerankerScore` floor (drop chunks below ~1.5–2.0 before grounding) and Content Safety Groundedness as a second gate. More reliable abstention than before.
7. **Liveness/streaming** — Container Apps ingress supports long-lived streaming responses; set generous request/idle timeouts. Keep the heartbeat anyway (cheap insurance). LLM client timeouts still apply.

## 4. Step-by-step build

### Phase 0 — Provision the foundation
1. Create a **Resource Group** (e.g. `rg-induction-prod`, region `australiaeast` for data residency — Victorian gov data should stay in-country; confirm Claude/GPT-5.4 availability in that region, else `australiasoutheast` or the nearest region that has both).
2. Create an **Azure AI Foundry** resource + a **project** (the project is the unit that holds model deployments, evaluations, tracing, and connections).
3. Create **Azure Key Vault**; create a **user-assigned managed identity** for the backend; grant it Key Vault Secrets User.
4. Create **Application Insights** (wire to the Foundry project for tracing).
5. Enable **Azure AI Content Safety** (or use the Foundry-integrated Content Safety).

### Phase 1 — Deploy the models (Foundry → Models + endpoints)
1. **Answer lane:** deploy **`gpt-5.4`** (Global/Standard). Also deploy **`claude-opus-4-8`** (Global Standard) so the eval can A/B them. Pick the winner by groundedness score in Phase 8.
2. **Fast lane:** deploy a **`gpt-5.4-mini`** / GPT-5-mini class deployment. This runs condense, split, query-rewrite, applicability, verifier, situating, summary.
3. **Embeddings:** deploy **`text-embedding-3-large`**.
4. Give each a generous TPM/RPM quota (unlimited credit → request quota increases up front so you never hit a per-minute cap mid-demo). Note: Azure uses RPM/TPM quotas, not the per-day RPD cap that bit us on `gpt-4o-mini` — but still size generously.
5. Put all endpoint URLs + keys (or better, use **Entra/managed-identity auth to the models**, no keys) in Key Vault.

### Phase 2 — Ingestion + the AI Search index
1. Keep the parsing + **contextual chunking** code essentially as-is (`app/kb/parse.py`, `app/kb/contextual.py`, `app/kb/clause_model.py`). The situating LLM call now uses the Azure fast-lane deployment. Output per chunk: `text_for_index` (breadcrumb + situating + body), `raw_text`, `breadcrumb`, `title`, `scope`, `condition`, `clause_number`, `source`, `page`.
2. Create an **Azure AI Search** service (tier **Standard S1 or higher** — semantic ranker requires a tier that supports it; unlimited credit → S2/S3 for headroom). Enable **semantic ranker**.
3. Define the index schema (fields): `id` (key), `content` (searchable, = `text_for_index`), `raw_text` (retrievable), `contentVector` (Collection(Edm.Single), HNSW, dim = 3072 for `text-embedding-3-large`), plus filterable/retrievable `breadcrumb`, `title`, `scope`, `condition`, `clause_number`, `source`, `page`, `origin` (document|trainer).
4. Add a **vector profile** (HNSW) and a **semantic configuration** naming the title field (`title`) and content fields (`content`, `breadcrumb`) so the semantic ranker has good descriptive inputs.
5. Ingestion writes: embed `text_for_index` with `text-embedding-3-large`, push documents to the index (replace the Qdrant push + the BM25 `kb_index` save — AI Search does lexical BM25 internally; the on-disk BM25 hack is gone). Keep persisting the **clause table to Postgres** (the KB MAP + expansion still read it).
6. Re-ingest = rebuild the index (or use a new index name + swap an alias). This removes the destructive Qdrant-wipe-erases-trainer-KB issue if you keep trainer docs in a separate index or re-push them.

### Phase 3 — Retrieval (replaces `retrieval.py`)
1. For each sub-question, issue ONE AI Search **hybrid** query: text = the sub-question, vector = its embedding, with **`k=50`** (and `maxTextRecallSize` so they sum to ≥50 — the semantic ranker needs up to 50 inputs), `queryType=semantic`, the semantic configuration from Phase 2, and `top` ~8.
2. Optionally enable AI Search **query rewriting** on the query (it adds up to 10 rewrites pre-L1) in addition to our concept rewrite.
3. Read `@search.rerankerScore` (0–4) and **drop results below a threshold** (~1.5–2.0, tune on the eval) — this is a stronger, calibrated recall floor than our old Cohere score.
4. Union passages across sub-questions (keep our per-sub-question union; do NOT blend into one query — same eviction lesson applies).
5. Keep **clause expansion** from Postgres (sibling + cross-ref). Keep the **applicability filter** exactly as-is (fast lane, keep-by-default, breadcrumb-aware, concurrent).

### Phase 4 — Grounded generation (port `chat.py` + `pipeline.py` almost verbatim)
1. Port `condense_to_standalone_question`, `split_into_questions`, `build_search_query`, `build_refined_search_query`, `generate_answer_stream`, `verify_answer`, the system prompt, and `stream_grounded_answer` unchanged in logic — only swap the LLM client construction to the Azure deployments (an `AzureOpenAI` LLM for OpenAI models; the Foundry Anthropic endpoint for Claude). Keep the hybrid lanes, the heartbeat, the per-request timeouts, and the verifier-gates-streaming rule.
2. After the verifier passes, ADD a **Content Safety Groundedness** check on the final answer against the retrieved passages (managed second grounding gate). If it flags ungrounded, treat like a verifier fail (reset → agentic re-retrieval → abstain). Also run **Prompt Shields** on user input (jailbreak/prompt-injection guard).
3. Keep the KB MAP (from Postgres clause table) and the map/source/conversation authority in the verifier.

### Phase 5 — Auth (replaces FastAPI-Users)
1. Register an **Entra ID app**; configure sign-in restricted to the `wcma.vic.gov.au` tenant (single-tenant). Use **Easy Auth** on Container Apps / Static Web Apps so the platform handles tokens — the backend just reads the validated principal.
2. Map Entra groups/app-roles to our `basic` / `trainer` / `admin` roles (drop the email-domain-restriction code; the tenant restriction replaces it).
3. Keep the Postgres `user`/role rows for app-specific data (or store role in Entra app roles and mirror minimal profile in Postgres).

### Phase 6 — Data + secrets
1. **Azure Database for PostgreSQL Flexible Server** (zone-redundant HA, unlimited credit). Point `DATABASE_URL` at it (still `postgresql+asyncpg://...`). Tables auto-create as today.
2. All secrets/config in **Key Vault**; the backend reads them via **managed identity** at startup (no `.env` on disk → the stale-`.env`/daily-cap drift footgun disappears). Model/deployment names live in app config + Key Vault, single source of truth.

### Phase 7 — Hosting
1. **Backend → Azure Container Apps.** Same Dockerfile. Assign the managed identity. Set ingress to allow long streaming responses (generous response timeout; no 60s idle abort like nginx). Min replicas ≥1 (avoid cold start for the demo), scale rule on concurrency. Health probe on `/health`.
2. **Frontend → Azure Static Web Apps** (Next.js) with the API linked to the Container App; or a second Container App. Wire Entra Easy Auth.
3. Custom domain `induction.wcma.work` → Static Web App / Container App ingress + managed TLS.

### Phase 8 — Evaluation + observability (the reliability proof)
1. Port the 11 eval cases (`app/eval_harness.py`) + the 12 smoke cases as **Azure AI Foundry Evaluations**: use built-in **Groundedness**, **Relevance**, **Coherence** evaluators PLUS custom evaluators encoding our assertions (`expect_contains_any`, `expect_absent_all`, `expect_abstain`, the compound `expect_contains_all_groups`).
2. Run the eval as a **CI gate** (GitHub Action / Azure DevOps) on every deploy — block deploy if groundedness or pass-rate regresses. This is the regression gate we always wanted, now managed.
3. Turn on **online/continuous evaluation** + **tracing** so every production turn logs retrieval ranks, applicability decisions, verifier verdict, groundedness score to Application Insights. Flagged low-groundedness turns feed back into the eval set.

### Phase 9 — Cutover
1. Stand up the Azure stack in parallel with the live AWS site. Ingest. Run the eval (must match or beat 11/11 + clean smoke). A/B the two answer models; pick by groundedness.
2. Point `induction.wcma.work` DNS at Azure once green. Keep AWS as rollback for a week.

## 5. What to port vs replace (so you know what to touch)
1. **Port almost unchanged:** `parse.py`, `contextual.py`, `clause_model.py`, `kb_outline.py`, `expansion.py`, `applicability.py`, `chat.py` (prompts + condense/split/rewrite/verify), `pipeline.py` (orchestration + heartbeat), the eval/smoke cases, the Postgres models.
2. **Replace:** `retrieval.py` (→ AI Search SDK), `bm25_index.py` (→ deleted; AI Search has BM25), `engine.py`/`llm_factory.py` (→ Azure model clients + Key Vault), `auth.py`/`seed_admin.py` (→ Entra), `.env` (→ Key Vault), the deploy scripts + compose (→ Container Apps + Bicep/Terraform).
3. **Add:** Content Safety (Groundedness + Prompt Shields) calls, Foundry Evaluations harness, tracing wiring.

## 6. Azure-specific pitfalls (avoid relearning the hard way)
1. **Semantic ranker needs ~50 inputs.** If you pre-filter too hard before ranking, you starve it. Filter AFTER, or keep `k`+`maxTextRecallSize` ≥ 50. Use the `@search.rerankerScore` (0–4) as the quality floor, not the raw vector score.
2. **Region must have BOTH the chosen models AND semantic ranker.** Pick the region in Phase 0 only after confirming GPT-5.4 + (optionally) `claude-opus-4-8` + AI Search semantic tier are all available there, ideally in-country for gov data residency.
3. **Partner models can be pulled.** Claude Fable 5/Mythos 5 were suspended (export controls, June 2026). Don't build a hard dependency on a single partner model; GPT-5.4 (first-party) as primary + Opus 4.8 as alternative keeps you resilient. This is a real reliability argument, not theory.
4. **Quotas are per-minute (TPM/RPM), not per-day.** Better than the `gpt-4o-mini` RPD cap that bit us, but still request increases up front; the pipeline makes several fast-lane calls per turn.
5. **Don't let "chat with your data" tempt you.** It will look like it does everything in one click. It will NOT enforce our applicability filter or our map/source/conversation-authority verifier, so it will reintroduce Bug1/Bug2. Keep the custom pipeline.
6. **Streaming timeouts:** confirm the Container Apps ingress doesn't cap streaming responses; keep the 15s heartbeat regardless.
7. **Groundedness ≠ correctness:** Content Safety Groundedness checks the answer is supported by the passages; it does NOT judge scope. Our applicability filter is still required for the emergency-vs-ordinary logic. Layer them; don't substitute.

## 7. Cost / tier guidance (unlimited credit → buy reliability)
1. AI Search **Standard S2/S3** with semantic ranker (more replicas/partitions = HA + throughput).
2. Postgres Flexible Server **zone-redundant HA**.
3. Model deployments: generous TPM; consider **Provisioned Throughput Units (PTU)** for the answer model if latency consistency matters for the demo.
4. Container Apps min replicas ≥1 (no cold starts).
5. Turn on everything that improves reliability/observability: tracing, online evaluation, Content Safety. Cost is not the constraint; a wrong HR answer is.

## 8. Definition of done
1. Eval ≥ 11/11 (ported) with built-in Groundedness ≥ the current baseline; smoke Cases 1–12 clean.
2. Auth = Entra tenant-restricted SSO; roles enforced.
3. Secrets only in Key Vault; no `.env` on disk.
4. Per-turn tracing visible in App Insights (retrieval, applicability, verifier, groundedness).
5. CI blocks deploys on eval regression.
6. `induction.wcma.work` served from Azure; AWS kept as rollback.
