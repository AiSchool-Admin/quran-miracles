"""QuranRAGAgent — Retrieve Quranic context + 7 tafseer references.

Supports three search modes (tried in order):
  1. Vector similarity (pgvector) — when embeddings are computed
  2. Full-text search (tsvector) + LIKE — always available with DB
  3. LLM fallback — when no database is available
"""

from __future__ import annotations

import json
import os
from typing import Any

from discovery_engine.core.state import DiscoveryState
from discovery_engine.prompts.system_prompts import QURAN_SCHOLAR_SYSTEM_PROMPT

# Claude model for LLM fallback
_MODEL = "claude-sonnet-4-5-20250514"
_TEMPERATURE = 0.3

# Minimum similarity threshold for vector search
_VECTOR_SIMILARITY_THRESHOLD = 0.5

# Default database URL
_DB_DEFAULT = "postgresql://quran_user:changeme@localhost:5432/quran_miracles"


class QuranRAGAgent:
    """Retrieves relevant Quranic verses and tafseer using hybrid search.

    Search strategy:
      1. If DB available and embeddings exist → vector similarity
      2. If DB available but no embeddings → full-text + LIKE search
      3. If no DB → LLM fallback with explicit annotation
    """

    async def search(self, query: str, state: DiscoveryState) -> dict:
        """Search for relevant verses and tafseer context.

        Returns dict with ``verses``, ``tafseer_context``, and ``source`` keys.
        """
        db_url = _resolve_db_url()

        if db_url and not os.environ.get("_MOCK_DB"):
            try:
                return await self._search_db(query, state, db_url)
            except Exception as exc:
                # DB connection failed — fall through to LLM
                print(f"⚠️ DB search failed ({exc}), falling back to LLM")

        return await self._search_llm(query, state)

    # ── DB path (production) ───────────────────────────────

    async def _search_db(
        self, query: str, state: DiscoveryState, db_url: str
    ) -> dict:
        """Search PostgreSQL with vector similarity + full-text fallback."""
        import asyncpg
        from pgvector.asyncpg import register_vector

        conn = await asyncpg.connect(db_url)
        await register_vector(conn)

        try:
            verses: list[dict[str, Any]] = []

            # Check if embeddings are available
            has_embeddings = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM verses WHERE embedding_precise IS NOT NULL LIMIT 1)"
            )

            if has_embeddings:
                verses = await self._vector_search(conn, query)

            # Fallback: full-text + LIKE search if vector returned nothing
            if not verses:
                verses = await self._text_search(conn, query)

            # Fetch tafseer for each verse
            for v in verses:
                v["tafseers"] = await self._fetch_tafseers(conn, v["id"])

            return {
                "verses": verses,
                "tafseer_context": _summarise(verses),
                "source": "database",
            }
        finally:
            await conn.close()

    async def _vector_search(
        self, conn: Any, query: str
    ) -> list[dict[str, Any]]:
        """Search using pgvector cosine similarity."""
        from arabic_nlp.embeddings import compute_embeddings

        try:
            query_embedding = await compute_embeddings(query)
        except Exception:
            return []

        emb_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        rows = await conn.fetch(
            """
            SELECT id, surah_number, verse_number, text_uthmani,
                   text_simple, text_clean,
                   1 - (embedding_precise <=> $1::vector) AS similarity
            FROM verses
            WHERE embedding_precise IS NOT NULL
              AND 1 - (embedding_precise <=> $1::vector) > $2
            ORDER BY embedding_precise <=> $1::vector
            LIMIT 10
            """,
            emb_str,
            _VECTOR_SIMILARITY_THRESHOLD,
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
                "similarity": float(r["similarity"]),
            }
            for r in rows
        ]

    async def _text_search(
        self, conn: Any, query: str
    ) -> list[dict[str, Any]]:
        """Search using full-text search + LIKE fallback.

        Strategy:
          1. Try tsvector with AND (all terms must match)
          2. Try tsvector with OR (any term matches, ranked by count)
          3. Fallback: LIKE search per keyword on text_clean
        """
        # Strip common Arabic stop words that won't appear in verse text
        _STOP_WORDS = {
            "في", "من", "إلى", "على", "عن", "هل", "ما", "هو", "هي",
            "التي", "الذي", "كان", "كانت", "هذا", "هذه", "ذلك", "تلك",
            "القرآن", "الكريم", "القرآنية", "قرآنية",
        }
        keywords = [
            w for w in query.split()
            if w not in _STOP_WORDS and len(w) > 1
        ]

        # 1. Try tsvector AND search (exact match)
        rows = await conn.fetch(
            """
            SELECT id, surah_number, verse_number, text_uthmani,
                   text_simple, text_clean,
                   ts_rank(search_vector, plainto_tsquery('simple', $1)) AS rank
            FROM verses
            WHERE search_vector @@ plainto_tsquery('simple', $1)
            ORDER BY rank DESC
            LIMIT 10
            """,
            query,
        )

        if not rows and keywords:
            # 2. Try tsvector OR search (any keyword matches)
            or_query = " | ".join(keywords)
            rows = await conn.fetch(
                """
                SELECT id, surah_number, verse_number, text_uthmani,
                       text_simple, text_clean,
                       ts_rank(search_vector, to_tsquery('simple', $1)) AS rank
                FROM verses
                WHERE search_vector @@ to_tsquery('simple', $1)
                ORDER BY rank DESC
                LIMIT 10
                """,
                or_query,
            )

        if rows:
            return [
                {
                    "id": r["id"],
                    "surah_number": r["surah_number"],
                    "verse_number": r["verse_number"],
                    "verse_key": f"{r['surah_number']}:{r['verse_number']}",
                    "text_uthmani": r["text_uthmani"],
                    "text_simple": r["text_simple"],
                    "text_clean": r["text_clean"],
                    "similarity": float(r["rank"]),
                }
                for r in rows
            ]

        # 3. Fallback: LIKE search per keyword on text_clean
        search_term = keywords[0] if keywords else query
        rows = await conn.fetch(
            """
            SELECT id, surah_number, verse_number, text_uthmani,
                   text_simple, text_clean
            FROM verses
            WHERE text_clean LIKE '%' || $1 || '%'
               OR text_simple LIKE '%' || $1 || '%'
            LIMIT 10
            """,
            search_term,
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
                "similarity": 0.5,
            }
            for r in rows
        ]

    async def _fetch_tafseers(
        self, conn: Any, verse_id: int
    ) -> list[dict[str, str]]:
        """Fetch tafseer entries for a verse, ordered by priority."""
        rows = await conn.fetch(
            """
            SELECT tb.slug, tb.name_ar, tb.methodology, t.text
            FROM tafseers t
            JOIN tafseer_books tb ON tb.id = t.book_id
            WHERE t.verse_id = $1
            ORDER BY tb.priority_order
            """,
            verse_id,
        )
        return [
            {
                "slug": r["slug"],
                "name": r["name_ar"],
                "methodology": r["methodology"],
                "text": r["text"],
            }
            for r in rows
        ]

    # ── LLM fallback (no DB) ──────────────────────────────

    async def _search_llm(self, query: str, state: DiscoveryState) -> dict:
        """Use Claude to find relevant verses (mock / no-DB mode)."""
        try:
            from anthropic import AsyncAnthropic

            client = AsyncAnthropic()
            resp = await client.messages.create(
                model=_MODEL,
                max_tokens=2048,
                temperature=_TEMPERATURE,
                system=QURAN_SCHOLAR_SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"ابحث عن أهم الآيات القرآنية المتعلقة بـ: {query}\n\n"
                            "أعد JSON بالشكل:\n"
                            '{"verses": [{"surah_number": N, "verse_number": N, '
                            '"verse_key": "S:V", "text_uthmani": "...", '
                            '"text_simple": "..."}], '
                            '"tafseer_context": "ملخص التفسير"}'
                        ),
                    }
                ],
            )
            text = resp.content[0].text
            result = _parse_json(text)
            result["source"] = "llm"
            return result
        except Exception:
            result = _mock_water_verses(query)
            result["source"] = "mock"
            return result


# ── Helpers ────────────────────────────────────────────────


def _resolve_db_url() -> str | None:
    """Resolve the database URL, normalizing for asyncpg."""
    url = os.environ.get("DATABASE_URL")
    if url:
        return url.replace("postgresql+asyncpg://", "postgresql://")

    # Try default local connection
    try:
        import subprocess

        result = subprocess.run(
            ["pg_isready", "-h", "localhost", "-p", "5432"],
            capture_output=True,
            timeout=2,
        )
        if result.returncode == 0:
            return _DB_DEFAULT
    except Exception:
        pass
    return None


def _summarise(verses: list[dict]) -> str:
    parts = []
    for v in verses[:5]:
        tafseer_summary = ""
        if v.get("tafseers"):
            first = v["tafseers"][0]
            text_preview = first["text"][:200] if first.get("text") else ""
            tafseer_summary = f" [{first.get('name', '')}]: {text_preview}"
        parts.append(
            f"{v['verse_key']}: {v.get('text_simple', '')}{tafseer_summary}"
        )
    return "\n".join(parts)


def _parse_json(text: str) -> dict:
    """Extract JSON from LLM response (may be wrapped in markdown)."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    try:
        result: dict = json.loads(text)
        return result
    except json.JSONDecodeError:
        return {"verses": [], "tafseer_context": text}


def _mock_water_verses(query: str) -> dict:
    """MOCK: illustrative data when no API/DB is available."""
    return {
        "verses": [
            {
                "surah_number": 21,
                "verse_number": 30,
                "verse_key": "21:30",
                "text_uthmani": (
                    "أَوَلَمْ يَرَ الَّذِينَ كَفَرُوا "
                    "أَنَّ السَّمَاوَاتِ وَالْأَرْضَ "
                    "كَانَتَا رَتْقًا فَفَتَقْنَاهُمَا "
                    "وَجَعَلْنَا مِنَ الْمَاءِ كُلَّ "
                    "شَيْءٍ حَيٍّ"
                ),
                "text_simple": (
                    "أولم ير الذين كفروا أن السماوات "
                    "والأرض كانتا رتقا ففتقناهما "
                    "وجعلنا من الماء كل شيء حي"
                ),
            },
            {
                "surah_number": 24,
                "verse_number": 45,
                "verse_key": "24:45",
                "text_uthmani": (
                    "وَاللَّهُ خَلَقَ كُلَّ دَابَّةٍ مِن مَّاءٍ"
                ),
                "text_simple": "والله خلق كل دابة من ماء",
            },
            {
                "surah_number": 25,
                "verse_number": 54,
                "verse_key": "25:54",
                "text_uthmani": (
                    "وَهُوَ الَّذِي خَلَقَ مِنَ الْمَاءِ بَشَرًا"
                ),
                "text_simple": "وهو الذي خلق من الماء بشرا",
            },
        ],
        "tafseer_context": (
            "# MOCK: DB not connected\n"
            f"Mock tafseer context for query: {query}"
        ),
    }
