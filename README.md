# Insurance RAG Chatbot — LangChain + LangGraph + LlamaIndex

A working implementation of the [production RAG system design](https://github.com/Krish-sants/insurance-rag-system-design)
for an insurance agent knowledge assistant: grounded, citation-validated
answers over a governed corpus of policy forms, endorsements, claims
procedures, underwriting guidelines and FAQs — with ACL security trimming,
jurisdiction filtering, version awareness, and a full audit trace per query.

Each framework plays its natural role:

| Framework | Role here |
|---|---|
| **LlamaIndex** | Indexing + hybrid retrieval: `VectorStoreIndex` + `BM25Retriever` merged by `QueryFusionRetriever` (reciprocal-rank fusion), custom `BaseEmbedding` implementation, metadata-driven graph expansion of amending endorsements |
| **LangGraph** | Query orchestration as a `StateGraph`: screen → understand → retrieve → generate → validate → finalize, with conditional edges to blocked / clarify / refuse outcomes |
| **LangChain** | LLM provider layer: `ChatAnthropic` + `ChatPromptTemplate` when `ANTHROPIC_API_KEY` is set, deterministic extractive fallback otherwise — same interface, graceful degradation |

## Run

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements-dev.txt
.venv\Scripts\python -m uvicorn api.index:app --port 8020
# open http://127.0.0.1:8020  (chat UI with role switcher + sample queries)
.venv\Scripts\python -m pytest tests -q          # 12 tests
```

Optional: `set ANTHROPIC_API_KEY=...` to switch generation from the
extractive fallback to Claude via LangChain — no other change.

## What the design's requirements look like in code

- **Security trimming before retrieval** (`app/indexing.py: trim_nodes`) —
  the candidate set is filtered by role ACL, active status, and
  jurisdiction *before* any retriever runs. A personal-lines agent asking
  about commercial HNOA coverage never has those chunks ranked, retrieved,
  or cited. Tested.
- **Version awareness** — the superseded 2019 HO-3 edition is excluded from
  default scope; asking "what did the 2019 edition say" flips historical
  mode and labels the answer. Tested.
- **Hybrid retrieval** — BM25 catches form codes ("CA 20 54", "HNOA");
  the vector side catches paraphrase; RRF merges. Soft facet boosts
  (policy type) instead of hard filters preserve recall.
- **Graph expansion** — the TX amendatory endorsement (`amends` metadata
  link) is co-retrieved whenever its base form is, so cancellation answers
  cite both the base condition and the 30-day Texas amendment. Tested.
- **Citation validation** (`app/guards.py`) — every `[n]` must resolve and
  every citing line must be lexically supported by its cited source;
  failures fall back to sources-only mode instead of shipping an
  unvalidated synthesis. Confidence banding (high/medium/low) from
  retrieval strength + validation coverage.
- **Guardrails** — prompt-injection screen, claim-outcome-prediction
  refusal (explains provisions, never predicts payment), off-corpus
  refusal that explicitly says absence-of-answer ≠ "no", one-question
  clarification for ambiguous queries, disclaimer on every answer,
  source-text-is-data framing in the system prompt. All tested.
- **Audit trace** — every LangGraph node appends to `state["trace"]`;
  the UI shows the full node-by-node trace per query.

## Corpus

14 synthetic chunks for the fictional "Acme Mutual": HO-3 Texas (2024
active + 2019 superseded), TX & FL amendatory endorsements, DP-3 Texas,
commercial-auto HNOA endorsement, water-damage claims procedure,
high-value-homes underwriting guideline (underwriter-only ACL), and a
flood FAQ — chosen so every design behavior (jurisdiction, version, ACL,
endorsement expansion, comparison) is demonstrable.

## Live demo

**https://insurance-rag-chatbot-mauve.vercel.app** — deployed on Vercel
serverless (`api/index.py` ASGI entry, `vercel.json` rewrites). Use the
role switcher to see ACL security trimming change the answers, and the
sample chips to exercise jurisdiction filtering, endorsement co-retrieval,
and the injection guardrail.

## Scaling path

This repo is the design's architecture at demo scale. Production deltas,
per the design doc: per-request retriever construction becomes index-level
metadata filtering; the hashed embedder becomes a hosted embedding model
(one class swap — everything speaks `BaseEmbedding`); the lexical
entailment check becomes an NLI/LLM-judge; add the ingestion pipeline,
SSO, observability and evaluation stack from the design.
