"""QualityReviewAgent — Academic quality gate for discovery results."""

from __future__ import annotations

import json

from discovery_engine.core.state import DiscoveryState

_MODEL = "claude-sonnet-4-5-20250514"
_TEMPERATURE = 0.3


class QualityReviewAgent:
    """Reviews discovery results for academic rigor.

    Checks:
      - Are objections mentioned for every claim?
      - Is the confidence tier correctly assigned?
      - Are sources properly cited?
      - Is pre-Islamic knowledge addressed?
      - Is intellectual honesty maintained?

    Returns quality_score (0-1), quality_issues, should_deepen.
    """

    async def review(self, state: DiscoveryState) -> dict:
        """Review the current state for quality.

        Returns:
            Dict with ``quality_score`` (float 0-1),
            ``quality_issues`` (list[str]),
            ``should_deepen`` (bool).
        """
        # Rule-based checks first
        issues = self._rule_based_checks(state)
        rule_score = max(0.0, 1.0 - len(issues) * 0.15)

        # Try LLM review for deeper analysis
        llm_result = await self._llm_review(state)
        if llm_result:
            issues.extend(llm_result.get("quality_issues", []))
            llm_score = llm_result.get("quality_score", rule_score)
            final_score = (rule_score + llm_score) / 2
        else:
            final_score = rule_score

        final_score = round(max(0.0, min(1.0, final_score)), 2)
        should_deepen = final_score < 0.6

        return {
            "quality_score": final_score,
            "quality_issues": issues,
            "should_deepen": should_deepen,
        }

    def _rule_based_checks(self, state: DiscoveryState) -> list[str]:
        """Apply deterministic quality rules."""
        issues: list[str] = []

        # Check: science findings have objections
        for finding in state.get("science_findings", []):
            if not finding.get("main_objection"):
                vk = finding.get("verse_key", "?")
                issues.append(
                    f"ارتباط علمي بدون اعتراض رئيسي: {vk}"
                )
            tier = finding.get("confidence_tier", "")
            if tier not in ("tier_1", "tier_2", "tier_3"):
                issues.append(
                    f"مستوى ثقة غير صالح: {tier}"
                )

        # Check: humanities findings have honesty note
        for finding in state.get("humanities_findings", []):
            if not finding.get("intellectual_honesty_note"):
                vk = finding.get("verse_key", "?")
                issues.append(
                    f"ارتباط إنساني بدون ملاحظة أمانة علمية: {vk}"
                )
            ctype = finding.get("correlation_type", "")
            if ctype not in ("intersecting", "parallel", "inspirational"):
                issues.append(
                    f"نوع ارتباط غير صالح: {ctype}"
                )

        # Check: tafseer has consensus and Shaarawy note
        tafseer = state.get("tafseer_findings", {})
        if isinstance(tafseer, dict):
            if not tafseer.get("consensus_view"):
                issues.append("لا يوجد رأي إجماعي في التفسير")
            if not tafseer.get("shaarawy_linguistic_note"):
                issues.append("لا توجد ملاحظة لغوية من الشعراوي")

        # Check: synthesis exists and mentions tier
        synthesis = state.get("synthesis", "")
        if not synthesis:
            issues.append("لا يوجد توليف بحثي")
        elif "tier_" not in synthesis:
            issues.append("التوليف لا يتضمن مستوى الثقة الإجمالي")

        # Check: linguistic analysis
        linguistic = state.get("linguistic_analysis", {})
        if not linguistic.get("roots"):
            issues.append("لا توجد جذور لغوية في التحليل")

        # Check: at least some verses found
        if not state.get("verses"):
            issues.append("لم يتم العثور على آيات")

        return issues

    async def _llm_review(self, state: DiscoveryState) -> dict | None:
        """Use Claude for deeper quality analysis."""
        synthesis = state.get("synthesis", "")
        if not synthesis:
            return None

        science_count = len(state.get("science_findings", []))
        humanities_count = len(state.get("humanities_findings", []))

        prompt = (
            "راجع جودة هذا التقرير البحثي:\n\n"
            f"التوليف:\n{synthesis[:2000]}\n\n"
            f"عدد الارتباطات العلمية: {science_count}\n"
            f"عدد الارتباطات الإنسانية: {humanities_count}\n\n"
            "قيّم:\n"
            "1. هل الاعتراضات مذكورة بشكل كافٍ؟\n"
            "2. هل مستويات الثقة مُسندة بأدلة؟\n"
            "3. هل المعرفة السابقة للإسلام مُعالجة؟\n"
            "4. هل الأمانة العلمية متحققة؟\n\n"
            "أعد JSON:\n"
            '{"quality_score": 0.0-1.0, '
            '"quality_issues": ["..."], '
            '"should_deepen": true/false}'
        )

        try:
            from anthropic import AsyncAnthropic

            client = AsyncAnthropic()
            resp = await client.messages.create(
                model=_MODEL,
                max_tokens=1024,
                temperature=_TEMPERATURE,
                messages=[{"role": "user", "content": prompt}],
            )
            return _parse_json(resp.content[0].text)
        except Exception:
            return None


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
        return {}
