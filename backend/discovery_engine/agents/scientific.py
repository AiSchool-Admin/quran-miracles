"""ScientificExplorerAgent — Find scientific correlations (3-tier system)."""

from __future__ import annotations

import json

from discovery_engine.prompts.system_prompts import SCIENCE_EXPLORER_SYSTEM_PROMPT

_MODEL = "claude-sonnet-4-5-20250514"
_TEMPERATURE = 0.3


class ScientificExplorerAgent:
    """Explores scientific correlations with Quranic verses.

    Every correlation is classified:
      tier_1: clear translation + classical scholars understood it
      tier_2: acceptable translation + documented correlation
      tier_3: possible correlation needing more evidence

    Always includes ``main_objection`` for academic honesty.
    """

    async def explore(
        self,
        query: str,
        discipline: str,
        context: dict,
    ) -> list[dict]:
        """Find and evaluate scientific correlations.

        Args:
            query: the user's search query.
            discipline: e.g. "physics", "biology", "psychology".
            context: dict with ``verses`` and ``tafseer_context``.

        Returns:
            List of finding dicts with ``confidence_tier`` and
            ``main_objection``.
        """
        verses_text = "\n".join(
            f"{v.get('verse_key', '?')}: {v.get('text_uthmani', '')}"
            for v in context.get("verses", [])[:5]
        )

        prompt = (
            f"الاستعلام: {query}\n"
            f"التخصص: {discipline}\n\n"
            f"الآيات:\n{verses_text}\n\n"
            f"سياق التفسير:\n{context.get('tafseer_context', '')}\n\n"
            "أعد JSON array من الارتباطات العلمية. لكل ارتباط:\n"
            '{"verse_key": "...", "scientific_claim": "...", '
            '"discipline": "...", "confidence_tier": "tier_1|tier_2|tier_3", '
            '"evidence": "...", "main_objection": "...", '
            '"pre_islamic_knowledge": "..."}'
        )

        try:
            from anthropic import AsyncAnthropic

            client = AsyncAnthropic()
            resp = await client.messages.create(
                model=_MODEL,
                max_tokens=2048,
                temperature=_TEMPERATURE,
                system=SCIENCE_EXPLORER_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            return _parse_findings(resp.content[0].text)
        except Exception:
            # MOCK: API not available
            return self._mock_findings(query, discipline)

    def _mock_findings(self, query: str, discipline: str) -> list[dict]:
        """MOCK: illustrative data when API is unavailable."""
        return [
            {
                "verse_key": "21:30",
                "scientific_claim": (
                    "الآية تصف أن كل شيء حي مخلوق من الماء، "
                    "وهو ما يتوافق مع البيولوجيا الحديثة"
                ),
                "discipline": discipline,
                "confidence_tier": "tier_2",
                "evidence": (
                    "# MOCK: No API\n"
                    "الماء يشكل 60-70% من الكائنات الحية"
                ),
                "main_objection": (
                    "المعرفة بأهمية الماء للحياة كانت متوفرة "
                    "في الحضارات القديمة (طاليس، الفلسفة اليونانية)"
                ),
                "pre_islamic_knowledge": (
                    "نعم — طاليس (624 ق.م) اعتبر الماء أصل كل شيء"
                ),
            },
            {
                "verse_key": "24:45",
                "scientific_claim": (
                    "الآية تذكر خلق كل دابة من ماء، "
                    "وهو مبدأ بيولوجي أساسي"
                ),
                "discipline": discipline,
                "confidence_tier": "tier_2",
                "evidence": (
                    "# MOCK: No API\n"
                    "البروتوبلازم يتكون بشكل رئيسي من الماء"
                ),
                "main_objection": (
                    "الآية قد تشير إلى المني وليس الماء بمعناه العام"
                ),
                "pre_islamic_knowledge": (
                    "جزئياً — الربط بين الماء والحياة معروف قديماً"
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
