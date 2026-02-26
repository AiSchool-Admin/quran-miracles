"""Centralized database service — connection pool + query methods.

Provides a single DatabaseService that all agents share,
avoiding per-request connection overhead.
"""

from __future__ import annotations

import os
from typing import Any

import asyncpg
from pgvector.asyncpg import register_vector


_DB_DEFAULT = "postgresql://quran_user:changeme@localhost:5432/quran_miracles"


class DatabaseService:
    """Shared database service with asyncpg connection pool."""

    def __init__(self, db_url: str | None = None):
        self.db_url = db_url or os.environ.get("DATABASE_URL", _DB_DEFAULT)
        # Normalize asyncpg URL
        self.db_url = self.db_url.replace("postgresql+asyncpg://", "postgresql://")
        self.pool: asyncpg.Pool | None = None

    async def connect(self, timeout: float = 10) -> None:
        """Initialize the connection pool with pgvector support."""
        import asyncio

        if self.pool is not None:
            return
        self.pool = await asyncio.wait_for(
            asyncpg.create_pool(
                self.db_url,
                min_size=1,
                max_size=20,
                command_timeout=30,
                init=_init_connection,
            ),
            timeout=timeout,
        )

    async def close(self) -> None:
        """Close the connection pool."""
        if self.pool is not None:
            await self.pool.close()
            self.pool = None

    def _ensure_pool(self) -> asyncpg.Pool:
        if self.pool is None:
            msg = "DatabaseService not connected — call connect() first"
            raise RuntimeError(msg)
        return self.pool

    # ── Surah / Verse lookups ─────────────────────────────────

    async def list_surahs(self) -> list[dict[str, Any]]:
        """Return all 114 surahs ordered by number."""
        pool = self._ensure_pool()
        rows = await pool.fetch(
            """
            SELECT number, name_arabic, name_english, name_transliteration,
                   revelation_type, revelation_order, verse_count,
                   word_count, letter_count, muqattaat,
                   juz_start, page_start
            FROM surahs
            ORDER BY number
            """
        )
        return [dict(r) for r in rows]

    async def get_surah(self, surah_number: int) -> dict[str, Any] | None:
        """Return a single surah by its number (1-114)."""
        pool = self._ensure_pool()
        row = await pool.fetchrow(
            """
            SELECT number, name_arabic, name_english, name_transliteration,
                   revelation_type, revelation_order, verse_count,
                   word_count, letter_count, muqattaat,
                   juz_start, page_start, themes_ar, summary_ar
            FROM surahs
            WHERE number = $1
            """,
            surah_number,
        )
        return dict(row) if row else None

    async def get_verses_by_surah(
        self, surah_number: int
    ) -> list[dict[str, Any]]:
        """Return all verses for a given surah, ordered by verse_number."""
        pool = self._ensure_pool()
        rows = await pool.fetch(
            """
            SELECT id, surah_number, verse_number,
                   text_uthmani, text_simple, text_clean,
                   juz, page_number, word_count, letter_count
            FROM verses
            WHERE surah_number = $1
            ORDER BY verse_number
            """,
            surah_number,
        )
        return [dict(r) for r in rows]

    async def get_verse_detail(
        self, surah_number: int, verse_number: int
    ) -> dict[str, Any] | None:
        """Return a single verse with extended metadata."""
        pool = self._ensure_pool()
        row = await pool.fetchrow(
            """
            SELECT id, surah_number, verse_number,
                   text_uthmani, text_simple, text_clean,
                   juz, page_number, word_count, letter_count,
                   sajda, sajda_type, themes_ar
            FROM verses
            WHERE surah_number = $1 AND verse_number = $2
            """,
            surah_number,
            verse_number,
        )
        return dict(row) if row else None

    # ── Verse search ───────────────────────────────────────────

    async def search_verses_by_vector(
        self,
        query_embedding: list[float],
        limit: int = 10,
        threshold: float = 0.3,
    ) -> list[dict[str, Any]]:
        """Semantic search using pgvector cosine similarity."""
        import numpy as np

        pool = self._ensure_pool()

        # pgvector-registered connections accept numpy arrays directly
        emb_array = np.array(query_embedding, dtype=np.float32)

        rows = await pool.fetch(
            """
            SELECT
                id, surah_number, verse_number,
                text_uthmani, text_simple, text_clean,
                juz AS juz_number, page_number,
                1 - (embedding_precise <=> $1) AS similarity
            FROM verses
            WHERE embedding_precise IS NOT NULL
              AND 1 - (embedding_precise <=> $1) > $2
            ORDER BY embedding_precise <=> $1
            LIMIT $3
            """,
            emb_array,
            threshold,
            limit,
        )
        return [
            {
                "id": r["id"],
                "surah_number": r["surah_number"],
                "verse_number": r["verse_number"],
                "verse_key": f"{r['surah_number']}:{r['verse_number']}",
                "text_uthmani": r["text_uthmani"],
                "text_simple": r["text_simple"],
                "text_clean": r["text_clean"],
                "juz_number": r["juz_number"],
                "page_number": r["page_number"],
                "similarity": float(r["similarity"]),
            }
            for r in rows
        ]

    async def search_verses_by_text(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Text search fallback — tsvector OR then LIKE."""
        pool = self._ensure_pool()

        # Strip common stop words
        _STOP_WORDS = {
            "في", "من", "إلى", "على", "عن", "هل", "ما", "هو", "هي",
            "التي", "الذي", "كان", "كانت", "هذا", "هذه", "ذلك", "تلك",
            "القرآن", "الكريم", "القرآنية", "قرآنية",
        }
        keywords = [w for w in query.split() if w not in _STOP_WORDS and len(w) > 1]

        # 1. tsvector AND
        rows = await pool.fetch(
            """
            SELECT id, surah_number, verse_number, text_uthmani,
                   text_simple, text_clean,
                   ts_rank(search_vector, plainto_tsquery('simple', $1)) AS rank
            FROM verses
            WHERE search_vector @@ plainto_tsquery('simple', $1)
            ORDER BY rank DESC LIMIT $2
            """,
            query,
            limit,
        )

        # 2. tsvector OR
        if not rows and keywords:
            or_query = " | ".join(keywords)
            rows = await pool.fetch(
                """
                SELECT id, surah_number, verse_number, text_uthmani,
                       text_simple, text_clean,
                       ts_rank(search_vector, to_tsquery('simple', $1)) AS rank
                FROM verses
                WHERE search_vector @@ to_tsquery('simple', $1)
                ORDER BY rank DESC LIMIT $2
                """,
                or_query,
                limit,
            )

        # 3. LIKE
        if not rows and keywords:
            search_term = keywords[0]
            rows = await pool.fetch(
                """
                SELECT id, surah_number, verse_number, text_uthmani,
                       text_simple, text_clean
                FROM verses
                WHERE text_clean LIKE '%' || $1 || '%'
                   OR text_simple LIKE '%' || $1 || '%'
                LIMIT $2
                """,
                search_term,
                limit,
            )

        return [
            {
                "id": r["id"],
                "surah_number": r["surah_number"],
                "verse_number": r["verse_number"],
                "verse_key": f"{r['surah_number']}:{r['verse_number']}",
                "text_uthmani": r["text_uthmani"],
                "text_simple": r["text_simple"],
                "text_clean": r["text_clean"] or "",
                "similarity": float(r.get("rank", 0.5)),
            }
            for r in rows
        ]

    # ── Tafseer queries ───────────────────────────────────────

    async def get_tafseers_for_verse(self, verse_id: int) -> list[dict[str, Any]]:
        """Fetch tafseers for a single verse, ordered by priority."""
        pool = self._ensure_pool()
        rows = await pool.fetch(
            """
            SELECT
                t.verse_id, t.text,
                tb.name_ar, tb.slug,
                tb.methodology, tb.priority_order
            FROM tafseers t
            JOIN tafseer_books tb ON t.book_id = tb.id
            WHERE t.verse_id = $1
            ORDER BY tb.priority_order
            """,
            verse_id,
        )
        return [
            {
                "verse_id": r["verse_id"],
                "slug": r["slug"],
                "name": r["name_ar"],
                "methodology": r["methodology"],
                "text": r["text"],
                "priority_order": r["priority_order"],
            }
            for r in rows
        ]

    async def get_tafseers_for_verses(
        self, verse_ids: list[int]
    ) -> list[dict[str, Any]]:
        """Fetch tafseers for multiple verses, ordered by priority."""
        pool = self._ensure_pool()
        rows = await pool.fetch(
            """
            SELECT
                t.verse_id, t.text,
                tb.name_ar, tb.slug,
                tb.methodology, tb.priority_order
            FROM tafseers t
            JOIN tafseer_books tb ON t.book_id = tb.id
            WHERE t.verse_id = ANY($1)
            ORDER BY t.verse_id, tb.priority_order
            """,
            verse_ids,
        )
        return [
            {
                "verse_id": r["verse_id"],
                "slug": r["slug"],
                "name": r["name_ar"],
                "methodology": r["methodology"],
                "text": r["text"],
                "priority_order": r["priority_order"],
            }
            for r in rows
        ]

    # ── Discovery persistence ─────────────────────────────────

    async def save_discovery(self, discovery: dict[str, Any]) -> str:
        """Save a discovery to the database. Returns the discovery UUID."""
        pool = self._ensure_pool()
        row_id = await pool.fetchval(
            """
            INSERT INTO discoveries
                (title_ar, description_ar, category, discipline,
                 verse_ids, confidence_tier, confidence_score,
                 verification_status, evidence, counter_arguments,
                 discovery_source)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING id
            """,
            discovery.get("title_ar", discovery.get("query", "اكتشاف جديد")),
            discovery.get("description_ar", discovery.get("synthesis", "")),
            discovery.get("category", "scientific"),
            discovery.get("discipline"),
            discovery.get("verse_ids"),
            discovery.get("confidence_tier", "tier_2"),
            discovery.get("confidence_score"),
            discovery.get("verification_status", "pending"),
            discovery.get("evidence"),
            discovery.get("counter_arguments"),
            "ai_autonomous",
        )
        return str(row_id)

    # ── Utility ───────────────────────────────────────────────

    async def get_discovery_by_id(self, discovery_id: str) -> dict[str, Any] | None:
        """Retrieve a discovery by its UUID."""
        pool = self._ensure_pool()
        row = await pool.fetchrow(
            "SELECT * FROM discoveries WHERE id = $1::uuid",
            discovery_id,
        )
        return dict(row) if row else None

    async def list_discoveries(
        self, tier: str | None = None, limit: int = 20
    ) -> list[dict[str, Any]]:
        """List discoveries, optionally filtered by tier."""
        pool = self._ensure_pool()
        if tier:
            rows = await pool.fetch(
                """SELECT * FROM discoveries
                   WHERE confidence_tier = $1
                   ORDER BY created_at DESC LIMIT $2""",
                tier,
                limit,
            )
        else:
            rows = await pool.fetch(
                "SELECT * FROM discoveries ORDER BY created_at DESC LIMIT $1",
                limit,
            )
        return [dict(r) for r in rows]


async def _init_connection(conn: asyncpg.Connection) -> None:
    """Per-connection initialization: register pgvector type."""
    await register_vector(conn)
