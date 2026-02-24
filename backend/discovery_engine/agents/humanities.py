"""HumanitiesAgent — Psychology, sociology, economics, leadership connections."""

from __future__ import annotations

import json

from discovery_engine.prompts.system_prompts import HUMANITIES_SCHOLAR_SYSTEM_PROMPT

_MODEL = "claude-sonnet-4-5-20250514"
_TEMPERATURE = 0.3


class HumanitiesAgent:
    """Analyzes humanities connections with Quranic text.

    Disciplines covered:
      - Psychology
      - Sociology
      - Economics
      - Management & Leadership
      - Ethics & Moral Philosophy
      - Linguistics & Discourse Analysis

    Correlation types:
      intersecting:   concept and theory describe the same phenomenon
      parallel:       clear methodological similarity, not full overlap
      inspirational:  Quranic concept inspires the research direction

    Always includes ``intellectual_honesty_note``.
    """

    async def analyze(
        self,
        verses: list[dict],
        context: dict,
        disciplines: list[str],
    ) -> list[dict]:
        """Find humanities connections for the given verses.

        Args:
            verses: list of verse dicts with ``verse_key`` and ``text_uthmani``.
            context: dict with ``tafseer_context`` and other findings.
            disciplines: e.g. ``["psychology", "sociology", "economics"]``.

        Returns:
            List of finding dicts, each with ``correlation_type`` and
            ``intellectual_honesty_note``.
        """
        if not verses:
            return []

        verses_text = "\n".join(
            f"{v.get('verse_key', '?')}: {v.get('text_uthmani', '')}"
            for v in verses[:5]
        )

        disciplines_str = "، ".join(disciplines) if disciplines else "علم النفس، علم الاجتماع"

        prompt = (
            f"الآيات:\n{verses_text}\n\n"
            f"التخصصات المطلوبة: {disciplines_str}\n\n"
            f"سياق التفسير:\n{context.get('tafseer_context', '')}\n\n"
            "حلّل الروابط بين المفاهيم القرآنية والنظريات الحديثة.\n"
            "لكل رابط أعد JSON:\n"
            '{"verse_key": "...", "quranic_concept": "...", '
            '"modern_theory": {"name": "...", "author": "...", "year": N}, '
            '"discipline": "...", '
            '"correlation_type": "intersecting|parallel|inspirational", '
            '"analysis": "...", '
            '"differences": "...", '
            '"intellectual_honesty_note": "...", '
            '"pre_islamic_precedent": "..."}'
        )

        try:
            from anthropic import AsyncAnthropic

            client = AsyncAnthropic()
            resp = await client.messages.create(
                model=_MODEL,
                max_tokens=2048,
                temperature=_TEMPERATURE,
                system=HUMANITIES_SCHOLAR_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            return _parse_findings(resp.content[0].text)
        except Exception:
            # MOCK: API not available
            return self._mock_findings(disciplines)

    def _mock_findings(self, disciplines: list[str]) -> list[dict]:
        """MOCK: illustrative data when API is unavailable."""
        return [
            {
                "verse_key": "21:30",
                "quranic_concept": (
                    "وحدة أصل الحياة — «وجعلنا من الماء كل شيء حي»"
                ),
                "modern_theory": {
                    "name": "Biophilia Hypothesis",
                    "author": "Edward O. Wilson",
                    "year": 1984,
                },
                "discipline": "psychology",
                "correlation_type": "parallel",
                "analysis": (
                    "# MOCK: No API\n"
                    "مفهوم الارتباط الفطري بالطبيعة عند ويلسون "
                    "يتقاطع مع الإشارة القرآنية لوحدة أصل الحياة من الماء"
                ),
                "differences": (
                    "الآية تتحدث عن الخلق (أنطولوجيا) بينما "
                    "نظرية ويلسون تتحدث عن الميل النفسي (إبستمولوجيا)"
                ),
                "intellectual_honesty_note": (
                    "الارتباط على مستوى المفهوم العام وليس التطابق الحرفي. "
                    "الآية وصفية كونية، والنظرية تجريبية نفسية."
                ),
                "pre_islamic_precedent": (
                    "فلسفة طاليس (624 ق.م) اعتبرت الماء أصل الوجود"
                ),
            },
            {
                "verse_key": "49:13",
                "quranic_concept": (
                    "التنوع البشري والتعارف — "
                    "«وجعلناكم شعوبا وقبائل لتعارفوا»"
                ),
                "modern_theory": {
                    "name": "Contact Hypothesis",
                    "author": "Gordon Allport",
                    "year": 1954,
                },
                "discipline": "sociology",
                "correlation_type": "intersecting",
                "analysis": (
                    "# MOCK: No API\n"
                    "نظرية الاتصال لألبورت تؤكد أن التفاعل بين المجموعات "
                    "المتنوعة يقلل التحيز، وهو ما يتوافق مع مفهوم "
                    "«لتعارفوا» كغاية من التنوع البشري"
                ),
                "differences": (
                    "الآية تجعل التعارف غاية إلهية حكيمة، بينما "
                    "ألبورت يصفه كآلية اجتماعية تجريبية"
                ),
                "intellectual_honesty_note": (
                    "التقاطع في المفهوم العام واضح، لكن السياق مختلف: "
                    "ديني-تشريعي مقابل اجتماعي-تجريبي. "
                    "لا يمكن القول إن القرآن «أثبت» نظرية ألبورت."
                ),
                "pre_islamic_precedent": (
                    "مفهوم التعايش بين الشعوب معروف في الحضارات القديمة"
                ),
            },
        ]


def _parse_findings(text: str) -> list[dict]:
    """Extract JSON list from LLM response."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    try:
        data: list | dict = json.loads(text)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "findings" in data:
            findings: list[dict] = data["findings"]
            return findings
        return [data]
    except json.JSONDecodeError:
        return []
