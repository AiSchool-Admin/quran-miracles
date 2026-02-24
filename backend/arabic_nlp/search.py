"""Hybrid search — BM25 + semantic similarity + Arabic cross-encoder reranking."""


class HybridSearch:
    """Implements hybrid search for Quranic text retrieval.

    Combines:
    1. BM25 for lexical matching
    2. Semantic similarity via pgvector
    3. Arabic cross-encoder reranking for final ordering
    """

    async def search(self, query: str, top_k: int = 10) -> list[dict]:
        """Execute hybrid search and return ranked results."""
        return []
