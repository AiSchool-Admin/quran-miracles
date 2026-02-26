"""QuranRAGAgent — Retrieve Quranic context + 7 tafseer references.

Supports three search modes (tried in order):
  1. DatabaseService + EmbeddingsService (when injected)
  2. DatabaseService text-only (no embeddings service)
  3. LLM fallback — when no database is available
"""

from __future__ import annotations

import json
from typing import Any

from discovery_engine.core.state import DiscoveryState
from discovery_engine.prompts.system_prompts import QURAN_SCHOLAR_SYSTEM_PROMPT

_MODEL = "claude-sonnet-4-5-20250514"
_TEMPERATURE = 0.3


class QuranRAGAgent:
    """Retrieves relevant Quranic verses and tafseer using hybrid search.

    When db/embeddings services are injected, uses the shared pool.
    Otherwise falls back to LLM.
    """

    def __init__(
        self,
        db: Any | None = None,
        embeddings: Any | None = None,
    ):
        self.db = db
        self.embeddings = embeddings

    async def search(self, query: str, state: DiscoveryState) -> dict:
        """Search for relevant verses and tafseer context."""
        # Path 1: services injected → vector + text search
        if self.db is not None and self.embeddings is not None:
            try:
                return await self._search_with_services(query, state)
            except Exception as exc:
                print(f"⚠️ Service search failed ({exc}), trying text-only")

        # Path 2: DB only → text search
        if self.db is not None:
            try:
                return await self._search_db_text_only(query, state)
            except Exception as exc:
                print(f"⚠️ DB text search failed ({exc}), falling back to LLM")

        # Path 3: LLM fallback
        return await self._search_llm(query, state)

    async def _search_with_services(
        self, query: str, state: DiscoveryState
    ) -> dict:
        """Search using DatabaseService + EmbeddingsService."""
        query_embedding = await self.embeddings.get_query_embedding(query)
        verses = await self.db.search_verses_by_vector(
            query_embedding, limit=10, threshold=0.3
        )
        if not verses:
            verses = await self.db.search_verses_by_text(query, limit=10)

        await self._attach_tafseers(verses)

        return {
            "verses": verses,
            "tafseer_context": _summarise(verses),
            "source": "database",
        }

    async def _search_db_text_only(
        self, query: str, state: DiscoveryState
    ) -> dict:
        """Text search only (no embeddings)."""
        verses = await self.db.search_verses_by_text(query, limit=10)
        await self._attach_tafseers(verses)
        return {
            "verses": verses,
            "tafseer_context": _summarise(verses),
            "source": "database",
        }

    async def _attach_tafseers(self, verses: list[dict]) -> None:
        """Attach tafseers to each verse dict (in-place)."""
        if not verses or self.db is None:
            return
        verse_ids = [v["id"] for v in verses]
        all_tafseers = await self.db.get_tafseers_for_verses(verse_ids)
        by_verse: dict[int, list[dict]] = {}
        for t in all_tafseers:
            by_verse.setdefault(t["verse_id"], []).append(t)
        for v in verses:
            v["tafseers"] = by_verse.get(v["id"], [])

    async def _search_llm(self, query: str, state: DiscoveryState) -> dict:
        """Use Claude to find relevant verses (no-DB mode)."""
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
            result = _parse_json(resp.content[0].text)
            result["source"] = "llm"
            return result
        except Exception:
            result = _mock_water_verses(query)
            result["source"] = "mock"
            return result


def _summarise(verses: list[dict]) -> str:
    parts = []
    for v in verses[:5]:
        tafseer_summary = ""
        if v.get("tafseers"):
            first = v["tafseers"][0]
            text_preview = first["text"][:200] if first.get("text") else ""
            tafseer_summary = f" [{first.get('name', '')}]: {text_preview}"
        parts.append(
            f"{v.get('verse_key', '?')}: {v.get('text_simple', '')}{tafseer_summary}"
        )
    return "\n".join(parts)


def _parse_json(text: str) -> dict:
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
    return {
        "verses": [
            {
                "surah_number": 21, "verse_number": 30, "verse_key": "21:30",
                "text_uthmani": (  # noqa: E501
                    "أَوَلَمْ يَرَ الَّذِينَ كَفَرُوا أَنَّ السَّمَاوَاتِ وَالْأَرْضَ "
                    "كَانَتَا رَتْقًا فَفَتَقْنَاهُمَا وَجَعَلْنَا مِنَ الْمَاءِ كُلَّ شَيْءٍ حَيٍّ"
                ),
                "text_simple": (
                    "أولم ير الذين كفروا أن السماوات والأرض كانتا رتقا "
                    "ففتقناهما وجعلنا من الماء كل شيء حي"
                ),
            },
        ],
        "tafseer_context": f"# MOCK: DB not connected\nMock tafseer for: {query}",
    }
