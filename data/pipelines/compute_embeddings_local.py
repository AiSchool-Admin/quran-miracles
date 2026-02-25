"""Compute local development embeddings for Quranic verses.

Uses TF-IDF + Truncated SVD to produce 1536-dimensional vectors locally,
without requiring the OpenAI API. These embeddings capture word co-occurrence
patterns and are suitable for development and testing.

For production, use compute_embeddings.py with the OpenAI API.

Usage:
    DATABASE_URL=postgresql://... python data/pipelines/compute_embeddings_local.py

    # Overwrite existing embeddings
    DATABASE_URL=postgresql://... python data/pipelines/compute_embeddings_local.py --force
"""

from __future__ import annotations

import asyncio
import os
import re
import sys

import asyncpg
import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

# ── Configuration ──────────────────────────────────────────────────────
DIMENSIONS = 1536
DB_DEFAULT = "postgresql://quran_user:changeme@localhost:5432/quran_miracles"


def _clean_arabic(text: str) -> str:
    """Remove diacritics and normalize Arabic text for tokenization."""
    # Remove Arabic diacritics (tashkeel)
    text = re.sub(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E4\u06E7\u06E8\u06EA-\u06ED]", "", text)
    # Normalize alef variants
    text = re.sub(r"[إأآٱ]", "ا", text)
    # Normalize taa marbuta
    text = text.replace("ة", "ه")
    # Normalize yaa
    text = text.replace("ى", "ي")
    return text


def _compute_local_embeddings(texts: list[str]) -> np.ndarray:
    """Compute TF-IDF + SVD embeddings for Arabic text.

    Uses character n-grams (2-5) + word unigrams/bigrams to capture
    morphological patterns in Arabic text.
    """
    cleaned = [_clean_arabic(t) for t in texts]

    n_samples = len(cleaned)
    # SVD components must be < min(n_samples, n_features)
    n_components = min(DIMENSIONS, n_samples - 1)

    # Character n-grams capture Arabic morphological patterns well
    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(2, 5),
        max_features=8000,
        sublinear_tf=True,
    )
    tfidf_matrix = vectorizer.fit_transform(cleaned)

    # Also add word-level features
    word_vectorizer = TfidfVectorizer(
        analyzer="word",
        ngram_range=(1, 2),
        max_features=4000,
        sublinear_tf=True,
    )
    word_matrix = word_vectorizer.fit_transform(cleaned)

    # Combine character and word features
    from scipy.sparse import hstack
    combined = hstack([tfidf_matrix, word_matrix])

    # Reduce to target dimensions via SVD
    svd = TruncatedSVD(n_components=n_components, random_state=42)
    reduced = svd.fit_transform(combined)

    # If n_components < DIMENSIONS, pad with zeros
    if n_components < DIMENSIONS:
        padding = np.zeros((n_samples, DIMENSIONS - n_components))
        reduced = np.hstack([reduced, padding])

    # L2 normalize for cosine similarity
    embeddings = normalize(reduced, norm="l2")
    return embeddings


async def compute_all_local_embeddings(
    db_url: str,
    *,
    force: bool = False,
) -> int:
    """Compute local embeddings for all verses and store in DB."""
    conn = await asyncpg.connect(db_url)
    try:
        if force:
            verses = await conn.fetch(
                "SELECT id, text_uthmani FROM verses ORDER BY surah_number, verse_number"
            )
        else:
            verses = await conn.fetch(
                """
                SELECT id, text_uthmani FROM verses
                WHERE embedding_precise IS NULL
                ORDER BY surah_number, verse_number
                """
            )

        total = len(verses)
        if total == 0:
            print("All verses already have embeddings.")
            return 0

        print(f"Computing local embeddings for {total} verses...")

        texts = [v["text_uthmani"] for v in verses]
        ids = [v["id"] for v in verses]

        # Compute all embeddings at once (TF-IDF needs full corpus)
        embeddings = _compute_local_embeddings(texts)

        print(f"Embedding matrix shape: {embeddings.shape}")
        print("Storing in database...")

        # Store in batches
        batch_size = 100
        updated = 0
        for i in range(0, total, batch_size):
            batch_ids = ids[i : i + batch_size]
            batch_embs = embeddings[i : i + batch_size]

            for j, verse_id in enumerate(batch_ids):
                emb_str = "[" + ",".join(f"{x:.8f}" for x in batch_embs[j]) + "]"
                await conn.execute(
                    "UPDATE verses SET embedding_precise = $1::vector WHERE id = $2",
                    emb_str,
                    verse_id,
                )
                updated += 1

            done = min(i + batch_size, total)
            print(f"  {done}/{total} ({done * 100 // total}%)")

        return updated
    finally:
        await conn.close()


async def main() -> None:
    force = "--force" in sys.argv

    db_url = os.environ.get("DATABASE_URL", DB_DEFAULT)
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

    print("=" * 60)
    print("  Local Verse Embeddings Pipeline")
    print(f"  Method: TF-IDF + SVD ({DIMENSIONS}D)")
    print("  Note: For production, use compute_embeddings.py with OpenAI")
    print("=" * 60)

    updated = await compute_all_local_embeddings(db_url, force=force)
    print(f"\nDone — {updated} verses updated.")


if __name__ == "__main__":
    asyncio.run(main())
