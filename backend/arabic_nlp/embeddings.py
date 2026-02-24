"""Embedding generation using text-embedding-3-large (OpenAI)."""


class EmbeddingService:
    """Generates and manages embeddings for Quranic text.

    Uses OpenAI text-embedding-3-large (1536 dimensions).
    Embeddings are pre-computed and stored in pgvector.
    """

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a text string."""
        return []

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        return []
