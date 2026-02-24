"""SynthesisAgent — Multi-disciplinary academic synthesis."""

from __future__ import annotations

from discovery_engine.core.state import DiscoveryState
from discovery_engine.prompts.system_prompts import SYNTHESIS_SYSTEM_PROMPT

_MODEL = "claude-sonnet-4-5-20250514"
_TEMPERATURE = 0.6  # Higher temperature for creative synthesis


class SynthesisAgent:
    """Synthesizes findings from all other agents into a coherent analysis.

    Produces the six required elements:
      1. Executive summary (3 sentences for general audience)
      2. Detailed analysis (for specialists)
      3. Confidence scores table
      4. New research hypotheses
      5. Objections and controversial points
      6. Future research suggestions

    Uses higher temperature (0.6) for richer synthesis.
    """

    async def synthesize(
        self, all_findings: dict, state: DiscoveryState
    ) -> str:
        """Synthesize findings from all agents.

        Args:
            all_findings: dict with keys ``verses``, ``linguistic_analysis``,
                ``science_findings``, ``tafseer_findings``,
                ``humanities_findings``.
            state: current discovery state.

        Returns:
            Synthesis text (Markdown) with embedded confidence_tier.
        """
        prompt = self._build_prompt(all_findings, state)

        try:
            from anthropic import AsyncAnthropic

            client = AsyncAnthropic()
            resp = await client.messages.create(
                model=_MODEL,
                max_tokens=4096,
                temperature=_TEMPERATURE,
                system=SYNTHESIS_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            result: str = resp.content[0].text
            return result
        except Exception:
            # MOCK: API not available
            return self._mock_synthesis(all_findings, state)

    async def synthesize_stream(
        self, all_findings: dict, state: DiscoveryState
    ):
        """Stream synthesis token by token via async generator.

        Yields:
            str chunks as they arrive from the API.
        """
        prompt = self._build_prompt(all_findings, state)

        try:
            from anthropic import AsyncAnthropic

            client = AsyncAnthropic()
            async with client.messages.stream(
                model=_MODEL,
                max_tokens=4096,
                temperature=_TEMPERATURE,
                system=SYNTHESIS_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception:
            # MOCK: yield mock synthesis in chunks
            mock = self._mock_synthesis(all_findings, state)
            for i in range(0, len(mock), 50):
                yield mock[i : i + 50]

    def _build_prompt(self, all_findings: dict, state: DiscoveryState) -> str:
        """Build the synthesis prompt from all agent findings."""
        query = state.get("query", "")
        verses = all_findings.get("verses", [])
        linguistic = all_findings.get("linguistic_analysis", {})
        science = all_findings.get("science_findings", [])
        tafseer = all_findings.get("tafseer_findings", {})
        humanities = all_findings.get("humanities_findings", [])

        verses_summary = "\n".join(
            f"  - {v.get('verse_key', '?')}: {v.get('text_simple', '')}"
            for v in verses[:5]
        )

        science_summary = "\n".join(
            f"  - [{f.get('confidence_tier', '?')}] {f.get('scientific_claim', '')}"
            for f in science[:5]
        )

        humanities_summary = "\n".join(
            f"  - [{f.get('correlation_type', '?')}] {f.get('quranic_concept', '')}"
            for f in humanities[:5]
        )

        roots = ", ".join(linguistic.get("roots", [])[:10])
        devices = ", ".join(
            d.get("device", "") for d in linguistic.get("rhetorical_devices", [])[:5]
        )

        consensus = tafseer.get("consensus_view", "")[:500]
        shaarawy = tafseer.get("shaarawy_linguistic_note", "")[:500]

        return (
            f"الاستعلام الأصلي: {query}\n\n"
            f"═══ الآيات ═══\n{verses_summary}\n\n"
            f"═══ التحليل اللغوي ═══\n"
            f"الجذور: {roots}\n"
            f"الأساليب البلاغية: {devices}\n\n"
            f"═══ الارتباطات العلمية ═══\n{science_summary}\n\n"
            f"═══ التفسير ═══\n"
            f"الإجماع: {consensus}\n"
            f"ملاحظة الشعراوي: {shaarawy}\n\n"
            f"═══ العلوم الإنسانية ═══\n{humanities_summary}\n\n"
            "المطلوب: أنتج تقريراً بحثياً يتضمن العناصر الستة:\n"
            "1. ملخص تنفيذي (3 جمل)\n"
            "2. التحليل التفصيلي\n"
            "3. جدول درجات الثقة\n"
            "4. الفرضيات الجديدة المقترحة\n"
            "5. الاعتراضات والنقاط المثيرة للجدل\n"
            "6. اقتراحات البحث المستقبلي\n\n"
            "أنهِ التقرير بتحديد confidence_tier الإجمالي: tier_1 / tier_2 / tier_3"
        )

    def _mock_synthesis(self, all_findings: dict, state: DiscoveryState) -> str:
        """MOCK: illustrative synthesis when API is unavailable."""
        query = state.get("query", "البحث")
        return (
            f"# MOCK: No API\n\n"
            f"# تقرير التوليف البحثي: {query}\n\n"
            "## 1. الملخص التنفيذي\n"
            "وجدت الدراسة ارتباطات متعددة بين الآيات القرآنية المتعلقة بالماء "
            "والاكتشافات العلمية الحديثة في البيولوجيا والفيزياء. "
            "معظم الارتباطات تقع في المستوى الثاني (tier_2) مع وجود "
            "اعتراضات مشروعة تتعلق بالمعرفة المتوفرة قبل الإسلام. "
            "يُوصى بمزيد من البحث في الجوانب اللغوية الدقيقة.\n\n"
            "## 2. التحليل التفصيلي\n"
            "### الآية 21:30\n"
            "- **الإجماع التفسيري**: الماء أصل كل حي\n"
            "- **الملاحظة اللغوية (الشعراوي)**: «جعلنا» تفيد التحويل لا الخلق\n"
            "- **الارتباط العلمي**: الماء يشكل 60-70% من الكائنات الحية\n"
            "- **الاعتراض**: طاليس (624 ق.م) سبق بفكرة مشابهة\n\n"
            "## 3. جدول درجات الثقة\n"
            "| الآية | الارتباط | المستوى |\n"
            "|-------|----------|--------|\n"
            "| 21:30 | الماء أصل الحياة | tier_2 |\n"
            "| 24:45 | خلق الدواب من الماء | tier_2 |\n"
            "| 25:54 | خلق البشر من الماء | tier_3 |\n\n"
            "## 4. فرضيات مقترحة\n"
            "- دراسة الفرق الدلالي بين «جعل» و«خلق» في السياق العلمي\n"
            "- مقارنة مفهوم «الماء» في القرآن مع الفلسفات القديمة\n\n"
            "## 5. الاعتراضات\n"
            "- المعرفة بأهمية الماء كانت متوفرة في الحضارات القديمة\n"
            "- الآيات قد تُفسَّر بالمني لا الماء المعروف\n\n"
            "## 6. اقتراحات البحث المستقبلي\n"
            "- تحليل إحصائي لتكرار لفظ «ماء» ومشتقاته في القرآن\n"
            "- مقارنة بين التفاسير الكلاسيكية والحديثة لآيات الماء\n\n"
            "---\n"
            "**confidence_tier: tier_2**\n"
        )
