"""Embedding generation using OpenAI text-embedding-3-large.

Provides async functions for computing 1536-dimensional embeddings
for Quranic text. Embeddings are stored in pgvector columns.

Usage:
    from arabic_nlp.embeddings import compute_embeddings, compute_embeddings_batch

    vector = await compute_embeddings("بسم الله الرحمن الرحيم")
    vectors = await compute_embeddings_batch(["text1", "text2"])
"""

from __future__ import annotations

import os

from openai import AsyncOpenAI

# ── Configuration ──────────────────────────────────────────────────────

MODEL = "text-embedding-3-large"
DIMENSIONS = 1536
MAX_BATCH_SIZE = 2048  # OpenAI batch limit per request

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    """Get or create the OpenAI async client."""
    global _client  # noqa: PLW0603
    if _client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            msg = "OPENAI_API_KEY environment variable is not set"
            raise RuntimeError(msg)
        _client = AsyncOpenAI(api_key=api_key)
    return _client


# ── Public API ─────────────────────────────────────────────────────────


async def compute_embeddings(text: str) -> list[float]:
    """Generate embedding for a single text string.

    Uses OpenAI text-embedding-3-large (1536 dimensions).

    Args:
        text: Arabic or multilingual text to embed.

    Returns:
        List of 1536 floats representing the embedding vector.
    """
    client = _get_client()
    response = await client.embeddings.create(
        model=MODEL,
        input=text,
        dimensions=DIMENSIONS,
    )
    result: list[float] = response.data[0].embedding
    return result


async def compute_embeddings_batch(
    texts: list[str],
) -> list[list[float]]:
    """Generate embeddings for a batch of texts.

    Automatically chunks requests that exceed the API batch limit.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors, one per input text, in the same order.
    """
    if not texts:
        return []

    client = _get_client()
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), MAX_BATCH_SIZE):
        batch = texts[i : i + MAX_BATCH_SIZE]
        response = await client.embeddings.create(
            model=MODEL,
            input=batch,
            dimensions=DIMENSIONS,
        )
        sorted_data = sorted(response.data, key=lambda x: x.index)
        all_embeddings.extend([d.embedding for d in sorted_data])

    return all_embeddings
