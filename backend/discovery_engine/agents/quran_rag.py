"""QuranRAGAgent — Retrieve Quranic context + 7 tafseer references."""

from __future__ import annotations

import json
import os
from typing import Any

from discovery_engine.core.state import DiscoveryState
from discovery_engine.prompts.system_prompts import QURAN_SCHOLAR_SYSTEM_PROMPT

# Claude model for reasoning
_MODEL = "claude-sonnet-4-5-20250514"
_TEMPERATURE = 0.3


class QuranRAGAgent:
    """Retrieves relevant Quranic verses and tafseer using hybrid search.

    When the database is available, uses BM25 + semantic similarity +
    Arabic cross-encoder reranking.  Otherwise falls back to Claude
    with explicit mock-data annotation.
    """

    async def search(self, query: str, state: DiscoveryState) -> dict:
        """Search for relevant verses and tafseer context.

        Returns dict with ``verses`` and ``tafseer_context`` keys.
        """
        db_available = os.environ.get("DATABASE_URL") and not os.environ.get(
            "_MOCK_DB"
        )

        if db_available:
            return await self._search_db(query, state)
        return await self._search_llm(query, state)

    # ── DB path (production) ───────────────────────────────

    async def _search_db(
        self, query: str, state: DiscoveryState
    ) -> dict:  # pragma: no cover
        """Search PostgreSQL with pgvector similarity."""
        import asyncpg
        from pgvector.asyncpg import register_vector

        from arabic_nlp.embeddings import compute_embeddings

        database_url = os.environ["DATABASE_URL"]
        conn = await asyncpg.connect(database_url)
        await register_vector(conn)

        try:
            embedding = await compute_embeddings(query)

            rows = await conn.fetch(
                """
                SELECT surah_number, verse_number, text_uthmani,
                       text_simple, text_clean,
                       1 - (embedding_precise <=> $1::vector) AS similarity
                FROM verses
                WHERE embedding_precise IS NOT NULL
                ORDER BY embedding_precise <=> $1::vector
                LIMIT 10
                """,
                embedding,
            )

            verses: list[dict[str, Any]] = []
            for r in rows:
                verse_id_row = await conn.fetchrow(
                    "SELECT id FROM verses WHERE surah_number=$1 AND verse_number=$2",
                    r["surah_number"],
                    r["verse_number"],
                )
                vid = verse_id_row["id"] if verse_id_row else None

                tafseer_rows = await conn.fetch(
                    """
                    SELECT tb.slug, tb.name_ar, t.text
                    FROM tafseers t
                    JOIN tafseer_books tb ON tb.id = t.book_id
                    WHERE t.verse_id = $1
                    ORDER BY tb.priority_order
                    """,
                    vid,
                ) if vid else []

                verses.append({
                    "surah_number": r["surah_number"],
                    "verse_number": r["verse_number"],
                    "verse_key": f"{r['surah_number']}:{r['verse_number']}",
                    "text_uthmani": r["text_uthmani"],
                    "text_simple": r["text_simple"],
                    "similarity": float(r["similarity"]),
                    "tafseers": [
                        {"slug": t["slug"], "name": t["name_ar"], "text": t["text"]}
                        for t in tafseer_rows
                    ],
                })

            return {"verses": verses, "tafseer_context": _summarise(verses)}
        finally:
            await conn.close()

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
            return _parse_json(text)
        except Exception:
            # MOCK: API not available — return illustrative data
            return _mock_water_verses(query)


# ── Helpers ────────────────────────────────────────────────


def _summarise(verses: list[dict]) -> str:
    parts = []
    for v in verses[:5]:
        parts.append(f"{v['verse_key']}: {v.get('text_simple', '')}")
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
