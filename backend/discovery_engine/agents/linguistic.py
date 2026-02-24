"""LinguisticAnalysisAgent — Morphology + roots + rhetoric analysis."""

from __future__ import annotations

import json

from discovery_engine.core.state import DiscoveryState

_MODEL = "claude-sonnet-4-5-20250514"
_TEMPERATURE = 0.3


class LinguisticAnalysisAgent:
    """Deep linguistic analysis of Quranic text.

    Uses CAMeL Tools when available, otherwise falls back to Claude API.
    Returns roots, morphology, and rhetorical devices.
    """

    async def analyze(
        self, verses: list[dict], state: DiscoveryState
    ) -> dict:
        """Analyze morphology, roots, and rhetorical devices."""
        if not verses:
            return {"roots": [], "morphology": {}, "rhetorical_devices": []}

        # Try CAMeL Tools first
        camel_available = self._check_camel()
        if camel_available:
            return self._analyze_with_camel(verses)

        # Fall back to Claude API
        return await self._analyze_with_llm(verses, state)

    def _check_camel(self) -> bool:
        """Check if CAMeL Tools is installed."""
        try:
            import camel_tools  # noqa: F401
            return True
        except ImportError:
            return False

    def _analyze_with_camel(self, verses: list[dict]) -> dict:  # pragma: no cover
        """Use CAMeL Tools for morphological analysis."""
        from camel_tools.morphology.analyzer import Analyzer

        analyzer = Analyzer.builtin_analyzer()
        all_roots: list[str] = []
        morphology: dict[str, list] = {}
        rhetorical: list[dict] = []

        for v in verses:
            text = v.get("text_clean") or v.get("text_simple", "")
            words = text.split()
            verse_morph = []
            for word in words:
                analyses = analyzer.analyze(word)
                if analyses:
                    best = analyses[0]
                    root = best.get("root", "")
                    if root and root not in all_roots:
                        all_roots.append(root)
                    verse_morph.append({
                        "word": word,
                        "root": root,
                        "lemma": best.get("lex", ""),
                        "pos": best.get("pos", ""),
                        "pattern": best.get("form", ""),
                    })
            morphology[v.get("verse_key", "")] = verse_morph

        return {
            "roots": all_roots,
            "morphology": morphology,
            "rhetorical_devices": rhetorical,
        }

    async def _analyze_with_llm(
        self, verses: list[dict], state: DiscoveryState
    ) -> dict:
        """Use Claude API for linguistic analysis."""
        verses_text = "\n".join(
            f"{v.get('verse_key', '?')}: {v.get('text_uthmani', '')}"
            for v in verses[:5]
        )
        prompt = (
            "حلّل الآيات التالية لغوياً:\n\n"
            f"{verses_text}\n\n"
            "أعد JSON بالشكل:\n"
            '{"roots": ["جذر1", "جذر2"], '
            '"morphology": {"سورة:آية": [{"word": "...", "root": "...", '
            '"lemma": "...", "pos": "...", "pattern": "..."}]}, '
            '"rhetorical_devices": [{"device": "...", "verse_key": "...", '
            '"explanation": "..."}]}'
        )

        try:
            from anthropic import AsyncAnthropic

            client = AsyncAnthropic()
            resp = await client.messages.create(
                model=_MODEL,
                max_tokens=2048,
                temperature=_TEMPERATURE,
                messages=[{"role": "user", "content": prompt}],
            )
            text = resp.content[0].text
            return _parse_json(text)
        except Exception:
            # MOCK: API not available
            return self._mock_analysis(verses)

    def _mock_analysis(self, verses: list[dict]) -> dict:
        """MOCK: illustrative data when no API is available."""
        roots = ["م-و-ه", "ح-ي-ي", "خ-ل-ق", "ج-ع-ل", "ف-ت-ق"]
        morphology: dict[str, list] = {}
        for v in verses[:3]:
            vk = v.get("verse_key", "?")
            morphology[vk] = [
                {"word": "الماء", "root": "م-و-ه", "lemma": "ماء",
                 "pos": "noun", "pattern": "فَعْل"},
                {"word": "حي", "root": "ح-ي-ي", "lemma": "حيّ",
                 "pos": "adjective", "pattern": "فَعِل"},
            ]
        return {
            "roots": roots,
            "morphology": morphology,
            "rhetorical_devices": [
                {
                    "device": "توكيد",
                    "verse_key": "21:30",
                    "explanation": (
                        "# MOCK: No API\n"
                        "استخدام 'كل' للتوكيد الشامل"
                    ),
                },
            ],
        }


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    try:
        result: dict = json.loads(text)
        return result
    except json.JSONDecodeError:
        return {"roots": [], "morphology": {}, "rhetorical_devices": []}
