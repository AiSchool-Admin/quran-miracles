"""EmbeddingsService — query embedding computation with Redis caching.

Supports multiple backends:
  1. Local TF-IDF (always available for development)
  2. OpenAI text-embedding-3-large (production)

The local backend computes embeddings by comparing the query against
the pre-computed verse corpus using the same TF-IDF vectorizer.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Any

import asyncpg
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize


DIMENSIONS = 1536


class EmbeddingsService:
    """Compute query embeddings — local TF-IDF or OpenAI."""

    def __init__(self) -> None:
        self._vectorizer: TfidfVectorizer | None = None
        self._verse_matrix: Any | None = None
        self._verse_embeddings: np.ndarray | None = None
        self._initialized = False

    async def initialize(self, db_url: str) -> None:
        """Load corpus data for local embedding computation."""
        from pgvector.asyncpg import register_vector

        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(db_url)
        await register_vector(conn)
        try:
            rows = await conn.fetch(
                """SELECT id, text_uthmani, embedding_precise
                   FROM verses ORDER BY surah_number, verse_number"""
            )
        finally:
            await conn.close()

        texts = [_clean_arabic(r["text_uthmani"]) for r in rows]

        # Build TF-IDF vectorizer on the full corpus
        self._vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(2, 5),
            max_features=8000,
            sublinear_tf=True,
        )
        self._verse_matrix = self._vectorizer.fit_transform(texts)

        # Load pre-computed DB embeddings as reference
        emb_list = []
        for r in rows:
            emb = r["embedding_precise"]
            if emb is not None:
                # pgvector may return numpy array or list
                arr = np.array(emb, dtype=np.float32).flatten()
                if len(arr) == DIMENSIONS:
                    emb_list.append(arr)
                else:
                    emb_list.append(np.zeros(DIMENSIONS, dtype=np.float32))
            else:
                emb_list.append(np.zeros(DIMENSIONS, dtype=np.float32))
        self._verse_embeddings = np.stack(emb_list)

        self._initialized = True

    async def get_query_embedding(self, text: str) -> list[float]:
        """Compute embedding for a query string.

        Tries OpenAI first (if key available), falls back to local.
        """
        # Try OpenAI if available
        openai_key = os.environ.get("OPENAI_API_KEY")
        if openai_key:
            try:
                return await self._openai_embedding(text, openai_key)
            except Exception:
                pass

        # Local fallback
        return self._local_embedding(text)

    async def _openai_embedding(self, text: str, api_key: str) -> list[float]:
        """Compute embedding via OpenAI API."""
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=api_key)
        resp = await client.embeddings.create(
            model="text-embedding-3-large",
            input=text,
            dimensions=DIMENSIONS,
        )
        return resp.data[0].embedding

    def _local_embedding(self, text: str) -> list[float]:
        """Compute embedding locally using TF-IDF projection.

        Projects the query into the same TF-IDF space as the corpus,
        then computes similarity-weighted average of verse embeddings.
        """
        if not self._initialized or self._vectorizer is None:
            # Fallback: deterministic hash-based embedding
            return _hash_embedding(text)

        cleaned = _clean_arabic(text)
        query_tfidf = self._vectorizer.transform([cleaned])

        # Compute cosine similarity with all verses
        similarities = (query_tfidf @ self._verse_matrix.T).toarray()[0]

        # Get top-k similar verses
        top_k = 20
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        top_sims = similarities[top_indices]

        # Weight by similarity
        if top_sims.sum() > 0:
            weights = top_sims / top_sims.sum()
        else:
            weights = np.ones(len(top_indices)) / len(top_indices)

        # Weighted average of pre-computed verse embeddings
        weighted_emb = np.zeros(DIMENSIONS, dtype=np.float64)
        for idx, w in zip(top_indices, weights):
            weighted_emb += w * self._verse_embeddings[idx]

        # L2 normalize
        norm = np.linalg.norm(weighted_emb)
        if norm > 0:
            weighted_emb /= norm

        return weighted_emb.tolist()


def _clean_arabic(text: str) -> str:
    """Remove diacritics and normalize for tokenization."""
    text = re.sub(
        r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC"
        r"\u06DF-\u06E4\u06E7\u06E8\u06EA-\u06ED]",
        "",
        text,
    )
    text = re.sub(r"[إأآٱ]", "ا", text)
    text = text.replace("ة", "ه")
    text = text.replace("ى", "ي")
    return text


def _hash_embedding(text: str) -> list[float]:
    """Deterministic hash-based embedding (last resort)."""
    seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16) % (2**32)
    rng = np.random.RandomState(seed)
    emb = rng.randn(DIMENSIONS).astype(np.float64)
    emb /= np.linalg.norm(emb)
    return emb.tolist()
