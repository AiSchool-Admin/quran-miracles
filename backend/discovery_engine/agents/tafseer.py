"""TafseerAgent — Compare 7 tafseer references with Shaarawy emphasis."""

from __future__ import annotations

import json
from typing import Any

from discovery_engine.core.state import DiscoveryState
from discovery_engine.prompts.system_prompts import QURAN_SCHOLAR_SYSTEM_PROMPT

_MODEL = "claude-sonnet-4-5-20250514"
_TEMPERATURE = 0.3


class TafseerAgent:
    """Compares interpretations from 7 authoritative tafseer sources.

    The seven references (by priority):
      1. Ibn Kathir    — Athari (primary)
      2. Al-Tabari     — Athari (comprehensive)
      3. Al-Shaarawy ★ — Linguistic (deep word analysis)
      4. Al-Razi       — Rationalist (logical)
      5. Al-Saadi      — Simplified (practical)
      6. Ibn Ashour    — Reformist (modern linguistic)
      7. Al-Qurtubi    — Fiqh-oriented

    ★ Al-Shaarawy is highlighted for precise linguistic analysis.
    """

    def __init__(self, db: Any = None):
        self.db = db

    async def analyze(
        self, verses: list[dict], state: DiscoveryState
    ) -> dict:
        """Compare tafseer for the given verses.

        Returns:
            Dict with ``consensus_view``, ``differences``,
            ``shaarawy_linguistic_note``, and per-verse ``tafseer_details``.
        """
        if not verses:
            return {
                "consensus_view": "",
                "differences": [],
                "shaarawy_linguistic_note": "",
                "tafseer_details": [],
            }

        # If verses already have tafseers from QuranRAG, use them
        has_tafseers = any(v.get("tafseers") for v in verses)

        # If not, try fetching from DB via service
        if not has_tafseers and self.db is not None:
            try:
                verse_ids = [v["id"] for v in verses if v.get("id")]
                if verse_ids:
                    all_tafseers = await self.db.get_tafseers_for_verses(verse_ids)
                    by_verse: dict[int, list[dict]] = {}
                    for t in all_tafseers:
                        by_verse.setdefault(t["verse_id"], []).append(t)
                    for v in verses:
                        v["tafseers"] = by_verse.get(v.get("id", 0), [])
                    has_tafseers = any(v.get("tafseers") for v in verses)
            except Exception as exc:
                print(f"⚠️ TafseerAgent DB fetch failed: {exc}")

        if has_tafseers:
            return self._analyze_from_db(verses)

        # Fall back to Claude API
        return await self._analyze_with_llm(verses, state)

    def _analyze_from_db(self, verses: list[dict]) -> dict:
        """Analyze tafseers already fetched from the database."""
        all_details: list[dict] = []
        consensus_parts: list[str] = []
        differences: list[dict] = []
        shaarawy_notes: list[str] = []

        for v in verses[:5]:
            vk = v.get("verse_key", "?")
            tafseers = v.get("tafseers", [])
            detail: dict = {"verse_key": vk, "tafseers": {}}

            for t in tafseers:
                slug = t.get("slug", "")
                detail["tafseers"][slug] = {
                    "name": t.get("name", slug),
                    "text": t.get("text", ""),
                }
                if "shaarawy" in slug.lower():
                    shaarawy_notes.append(
                        f"{vk}: {t.get('text', '')[:500]}"
                    )

            all_details.append(detail)
            if tafseers:
                consensus_parts.append(
                    f"{vk}: {tafseers[0].get('text', '')[:200]}"
                )

        return {
            "consensus_view": "\n".join(consensus_parts),
            "differences": differences,
            "shaarawy_linguistic_note": "\n".join(shaarawy_notes)
            if shaarawy_notes
            else "لا يتوفر تفسير الشعراوي لهذه الآيات",
            "tafseer_details": all_details,
        }

    async def _analyze_with_llm(
        self, verses: list[dict], state: DiscoveryState
    ) -> dict:
        """Use Claude API to provide tafseer analysis."""
        verses_text = "\n".join(
            f"{v.get('verse_key', '?')}: {v.get('text_uthmani', '')}"
            for v in verses[:5]
        )
        prompt = (
            "قارن بين تفاسير العلماء السبعة المعتمدين للآيات التالية:\n\n"
            f"{verses_text}\n\n"
            "المطلوب:\n"
            "1. consensus_view: الرأي المشترك بين المفسرين\n"
            "2. differences: الاختلافات مع ذكر اسم المفسر\n"
            "3. shaarawy_linguistic_note: ملاحظة الشعراوي اللغوية الدقيقة\n"
            "4. tafseer_details: تفصيل كل مفسر لكل آية\n\n"
            "أعد JSON بالشكل:\n"
            '{"consensus_view": "...", '
            '"differences": [{"verse_key": "...", "scholar": "...", '
            '"opinion": "...", "evidence": "..."}], '
            '"shaarawy_linguistic_note": "...", '
            '"tafseer_details": [{"verse_key": "...", "tafseers": {...}}]}'
        )

        try:
            from anthropic import AsyncAnthropic

            client = AsyncAnthropic()
            resp = await client.messages.create(
                model=_MODEL,
                max_tokens=3000,
                temperature=_TEMPERATURE,
                system=QURAN_SCHOLAR_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            return _parse_json(resp.content[0].text)
        except Exception:
            # MOCK: API not available
            return self._mock_tafseer(verses)

    def _mock_tafseer(self, verses: list[dict]) -> dict:
        """MOCK: illustrative tafseer data when API is unavailable."""
        return {
            "consensus_view": (
                "# MOCK: No API\n"
                "اتفق المفسرون على أن الماء أصل الحياة كما جاء في "
                "قوله تعالى «وجعلنا من الماء كل شيء حي»، "
                "والمراد بالماء هنا الماء المعروف عند جمهور المفسرين"
            ),
            "differences": [
                {
                    "verse_key": "21:30",
                    "scholar": "الرازي",
                    "opinion": (
                        "الماء هنا يشمل المني والماء المعروف، "
                        "وهو أعم من تفسير ابن كثير"
                    ),
                    "evidence": "التفسير الكبير، الجزء 22",
                },
                {
                    "verse_key": "21:30",
                    "scholar": "القرطبي",
                    "opinion": (
                        "المراد: كل حيوان خُلق من الماء، "
                        "وهذا يشمل الملائكة عند بعضهم"
                    ),
                    "evidence": "الجامع لأحكام القرآن",
                },
            ],
            "shaarawy_linguistic_note": (
                "# MOCK: No API\n"
                "الشعراوي يلفت النظر إلى دقة استخدام «جعلنا» بدل «خلقنا»: "
                "فالجَعل يتضمن التحويل والتصيير، أي أن الله حوّل الماء "
                "إلى كائنات حية، بينما الخَلق هو الإيجاد من العدم. "
                "هذا الفرق اللغوي الدقيق يُظهر أن الماء مادة خام "
                "تحوّلت إلى حياة وليس أن الحياة خُلقت من لا شيء."
            ),
            "tafseer_details": [
                {
                    "verse_key": "21:30",
                    "tafseers": {
                        "ibn_kathir": "جعلنا من الماء كل شيء حي: أي أصل كل الأحياء من الماء",
                        "tabari": "كل ما فيه روح فأصله من الماء",
                        "shaarawy": "الجَعل هنا تصيير وتحويل لا خَلق من عدم",
                        "razi": "يشمل الماء والمني وكل سائل حيوي",
                        "saadi": "دليل على قدرة الله في جعل الحياة من مادة واحدة",
                        "ibn_ashour": "الماء هو العنصر الأساسي المشترك في كل الكائنات",
                        "qurtubi": "فيه دلالة على وجوب شكر نعمة الماء",
                    },
                },
            ],
        }


def _parse_json(text: str) -> dict:
    """Extract JSON from LLM response."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    try:
        result: dict = json.loads(text)
        return result
    except json.JSONDecodeError:
        return {
            "consensus_view": text,
            "differences": [],
            "shaarawy_linguistic_note": "",
            "tafseer_details": [],
        }
