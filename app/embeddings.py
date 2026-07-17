"""Local embedding model plugged into LlamaIndex's BaseEmbedding interface.

A hashed bag-of-features embedder (words + character trigrams hashed into a
fixed 512-dim vector). Deterministic, dependency-free, no fitting step —
which means queries and documents embed identically with no training data.

Fidelity is deliberately modest: in this hybrid pipeline BM25 carries exact
form-code/terminology matching, the vector side adds paraphrase tolerance,
and reciprocal-rank fusion merges them. Swapping in a hosted embedder
(Voyage/Cohere/OpenAI) is a one-line change where the index is built,
because everything speaks LlamaIndex's BaseEmbedding interface.
"""

import hashlib
import math
import re

from llama_index.core.base.embeddings.base import BaseEmbedding

DIM = 512


def _features(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    feats = list(words)
    for w in words:
        if len(w) > 3:
            feats.extend(w[i:i + 3] for i in range(len(w) - 2))
    return feats


def _embed(text: str) -> list[float]:
    vec = [0.0] * DIM
    for feat in _features(text):
        h = int(hashlib.md5(feat.encode()).hexdigest()[:8], 16)
        vec[h % DIM] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


class HashedEmbedding(BaseEmbedding):
    """LlamaIndex-compatible local embedder."""

    def _get_query_embedding(self, query: str) -> list[float]:
        return _embed(query)

    def _get_text_embedding(self, text: str) -> list[float]:
        return _embed(text)

    async def _aget_query_embedding(self, query: str) -> list[float]:
        return _embed(query)

    async def _aget_text_embedding(self, text: str) -> list[float]:
        return _embed(text)
