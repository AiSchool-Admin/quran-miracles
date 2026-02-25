"""Compute and store embeddings for all Quranic verses.

Reads verses from PostgreSQL (must already be imported), computes
embeddings via OpenAI text-embedding-3-large, and stores them in
the ``embedding_precise`` column (vector(1536)).

Usage:
    # Compute all missing embeddings
    OPENAI_API_KEY=sk-... python data/pipelines/compute_embeddings.py

    # Re-compute all (overwrite existing)
    OPENAI_API_KEY=sk-... python data/pipelines/compute_embeddings.py --force

    # Dry run — show count without computing
    python data/pipelines/compute_embeddings.py --dry-run
"""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Any

import asyncpg

# ── Configuration ──────────────────────────────────────────────────────

MODEL = "text-embedding-3-large"
DIMENSIONS = 1536
BATCH_SIZE = 50  # verses per API call (OpenAI supports up to 2048)
DB_DEFAULT = "postgresql://quran_user:changeme@localhost:5432/quran_miracles"


async def _get_openai_embeddings(
    texts: list[str],
) -> list[list[float]]:
    """Call OpenAI embeddings API for a batch of texts."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = await client.embeddings.create(
        model=MODEL,
        input=texts,
        dimensions=DIMENSIONS,
    )
    sorted_data = sorted(response.data, key=lambda x: x.index)
    return [d.embedding for d in sorted_data]


async def compute_all_embeddings(
    db_url: str,
    *,
    force: bool = False,
    dry_run: bool = False,
) -> int:
    """Compute embeddings for verses missing them (or all if force=True).

    Returns the number of verses updated.
    """
    conn = await asyncpg.connect(db_url)
    try:
        # Fetch verses needing embeddings
        if force:
            verses: list[Any] = await conn.fetch(
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
            print("✅ All verses already have embeddings.")
            return 0

        print(f"⏳ {total} verses need embeddings...")

        if dry_run:
            print("   (dry run — not computing)")
            return 0

        updated = 0
        for i in range(0, total, BATCH_SIZE):
            batch = verses[i : i + BATCH_SIZE]
            texts = [v["text_uthmani"] for v in batch]

            embeddings = await _get_openai_embeddings(texts)

            # Store in DB
            for j, verse in enumerate(batch):
                emb_str = "[" + ",".join(str(x) for x in embeddings[j]) + "]"
                await conn.execute(
                    "UPDATE verses SET embedding_precise = $1::vector WHERE id = $2",
                    emb_str,
                    verse["id"],
                )
                updated += 1

            done = min(i + BATCH_SIZE, total)
            print(f"   ✅ {done}/{total} ({done * 100 // total}%)")

            # Rate limiting: small delay between batches
            if i + BATCH_SIZE < total:
                await asyncio.sleep(0.5)

        return updated
    finally:
        await conn.close()


async def main() -> None:
    force = "--force" in sys.argv
    dry_run = "--dry-run" in sys.argv

    db_url = os.environ.get("DATABASE_URL", DB_DEFAULT)
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

    print("=" * 60)
    print("  Verse Embeddings Pipeline")
    print(f"  Model: {MODEL} ({DIMENSIONS}D)")
    print("=" * 60)

    if not dry_run and not os.environ.get("OPENAI_API_KEY"):
        print("\n⚠️  OPENAI_API_KEY not set. Use --dry-run to check status.")
        sys.exit(1)

    updated = await compute_all_embeddings(db_url, force=force, dry_run=dry_run)
    print(f"\n✅ Done — {updated} verses updated.")


if __name__ == "__main__":
    asyncio.run(main())
