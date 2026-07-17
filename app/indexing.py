"""Retrieval layer built on LlamaIndex.

Implements the design's retrieval contract:
  1. SECURITY TRIMMING FIRST — the candidate node set is filtered by ACL,
     status and jurisdiction BEFORE any retriever runs, so unauthorized or
     superseded text can never reach ranking, let alone the LLM.
  2. HYBRID SEARCH — BM25 (exact form codes, defined terms) in parallel
     with vector search (paraphrase), merged with reciprocal-rank fusion
     via LlamaIndex's QueryFusionRetriever.
  3. Graph expansion — endorsements that amend a retrieved document are
     co-retrieved via the `amends` metadata link.

At this corpus scale, building the per-request retrievers over the trimmed
node set costs milliseconds and makes pre-filtering literal. At production
scale the same trimming happens as index-level metadata filters (see the
system design, §8); the interface below would not change.
"""

from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.llms import MockLLM
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.core.schema import NodeWithScore, TextNode
from llama_index.retrievers.bm25 import BM25Retriever

from .documents import CHUNKS
from .embeddings import HashedEmbedding

EMBED = HashedEmbedding()
# Generation happens in the LangChain layer; LlamaIndex is retrieval-only
# here, so pin its global settings to local components (no OpenAI default).
Settings.llm = MockLLM()
Settings.embed_model = EMBED


def build_nodes() -> list[TextNode]:
    nodes = []
    for i, chunk in enumerate(CHUNKS):
        meta = {k: v for k, v in chunk.items() if k != "text"}
        nodes.append(TextNode(
            id_=f"n{i:03d}",
            # Prepending title/section improves both lexical and vector match
            # for context-dependent clauses (design §5, step 8).
            text=f"{chunk['title']} — {chunk['section_path']}\n{chunk['text']}",
            metadata=meta,
        ))
    return nodes


ALL_NODES = build_nodes()


def trim_nodes(user: dict, historical: bool, state_filter: str | None) -> list[TextNode]:
    """Security + scope trimming (the non-negotiable pre-filter)."""
    allowed = []
    for node in ALL_NODES:
        m = node.metadata
        if user["role"] not in m["acl_roles"]:
            continue
        if m["status"] != "active" and not historical:
            continue
        if m["jurisdiction"] not in ("US",) and user.get("licensed_states") \
                and m["jurisdiction"] not in user["licensed_states"]:
            continue
        if state_filter and m["jurisdiction"] not in (state_filter, "US"):
            continue
        allowed.append(node)
    return allowed


def hybrid_retrieve(query: str, nodes: list[TextNode], top_k: int = 8) -> list[NodeWithScore]:
    if not nodes:
        return []
    k = min(top_k, len(nodes))
    vector_index = VectorStoreIndex(nodes=nodes, embed_model=EMBED)
    fusion = QueryFusionRetriever(
        retrievers=[
            vector_index.as_retriever(similarity_top_k=k),
            BM25Retriever.from_defaults(nodes=nodes, similarity_top_k=k),
        ],
        mode="reciprocal_rerank",
        similarity_top_k=k,
        num_queries=1,          # query expansion handled by the LangGraph rewrite node
        use_async=False,
    )
    results = fusion.retrieve(query)

    # Soft facet boost (design §8: doc-type/policy-type as boosts, not hard
    # filters): nudge chunks whose policy_type is named in the query.
    q_lower = query.lower()
    for r in results:
        facet_words = r.node.metadata.get("policy_type", "").split("_")
        if any(w and w in q_lower for w in facet_words):
            r.score = (r.score or 0) + 0.02
    results.sort(key=lambda r: r.score or 0, reverse=True)

    # Graph expansion: co-retrieve endorsements amending any retrieved doc.
    retrieved_docs = {r.node.metadata["doc_id"] for r in results}
    have = {r.node.id_ for r in results}
    for node in nodes:
        if node.metadata.get("amends") in retrieved_docs and node.id_ not in have:
            results.append(NodeWithScore(node=node, score=0.01))
    return results
