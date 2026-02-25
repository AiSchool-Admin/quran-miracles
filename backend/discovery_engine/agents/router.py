"""RouteQueryAgent — Classify queries and decide which agents to activate."""

from __future__ import annotations

import json

from discovery_engine.core.state import DiscoveryState

_MODEL = "claude-sonnet-4-5-20250514"
_TEMPERATURE = 0.1  # Low temperature for deterministic routing

# Keywords for fast heuristic routing (before LLM fallback)
_SCIENCE_KEYWORDS = {
    "فيزياء", "كيمياء", "بيولوجيا", "طب", "فلك", "جيولوجيا",
    "علم", "ذرة", "كون", "نجوم", "أرض", "جبال", "بحر",
    "ماء", "نبات", "حيوان", "خلق", "جنين", "رحم",
    "physics", "chemistry", "biology", "medicine", "astronomy",
}

_HUMANITIES_KEYWORDS = {
    "نفس", "اجتماع", "اقتصاد", "إدارة", "قيادة", "أخلاق",
    "فلسفة", "سلوك", "مجتمع", "ثروة", "فقر", "عدل", "شورى",
    "صبر", "طمأنينة", "خوف", "رجاء", "توبة", "زكاة",
    "psychology", "sociology", "economics", "management", "ethics",
}

_TAFSEER_KEYWORDS = {
    "تفسير", "معنى", "سبب", "نزول", "مكي", "مدني",
    "ناسخ", "منسوخ", "إعراب", "بلاغة", "لغة", "شعراوي",
    "ابن كثير", "طبري", "رازي", "قرطبي", "سعدي",
}


class RouteQueryAgent:
    """Classifies the query type and determines which agents to activate.

    Routes:
      - science:    natural science topics → ScientificExplorerAgent
      - humanities: social science topics → HumanitiesAgent
      - tafseer:    interpretation queries → TafseerAgent
      - parallel:   broad queries → all three agents in parallel
    """

    def route(self, state: DiscoveryState) -> str:
        """Determine which agent path to take.

        Returns:
            One of ``"science"``, ``"humanities"``, ``"tafseer"``,
            or ``"parallel"`` (all three).
        """
        query = state.get("query", "").lower()
        mode = state.get("mode", "guided")
        disciplines = state.get("disciplines", [])

        # Autonomous mode always runs all agents
        if mode == "autonomous" or mode == "cross_domain":
            return "parallel"

        # Check if disciplines hint at routing
        if disciplines:
            has_science = any(
                d in ("physics", "chemistry", "biology", "medicine",
                      "astronomy", "geology")
                for d in disciplines
            )
            has_humanities = any(
                d in ("psychology", "sociology", "economics",
                      "management", "ethics", "linguistics")
                for d in disciplines
            )
            if has_science and not has_humanities:
                return "science"
            if has_humanities and not has_science:
                return "humanities"

        # Heuristic keyword matching
        score_science = sum(1 for kw in _SCIENCE_KEYWORDS if kw in query)
        score_humanities = sum(1 for kw in _HUMANITIES_KEYWORDS if kw in query)
        score_tafseer = sum(1 for kw in _TAFSEER_KEYWORDS if kw in query)

        max_score = max(score_science, score_humanities, score_tafseer)

        if max_score == 0:
            # No clear signal — run everything
            return "parallel"

        # If one category clearly dominates
        if score_tafseer > score_science and score_tafseer > score_humanities:
            return "tafseer"
        if score_science > score_humanities and score_science > score_tafseer:
            return "science"
        if score_humanities > score_science and score_humanities > score_tafseer:
            return "humanities"

        # Tie or mixed — run all
        return "parallel"

    async def route_with_llm(self, state: DiscoveryState) -> str:
        """Use Claude to classify ambiguous queries (expensive fallback)."""
        query = state.get("query", "")

        prompt = (
            f"صنّف هذا الاستعلام: «{query}»\n\n"
            "الخيارات:\n"
            "- science: إذا كان عن علوم طبيعية (فيزياء، بيولوجيا، طب...)\n"
            "- humanities: إذا كان عن علوم إنسانية (نفس، اجتماع، اقتصاد...)\n"
            "- tafseer: إذا كان عن تفسير أو لغة أو بلاغة\n"
            "- parallel: إذا كان عاماً أو يشمل أكثر من تخصص\n\n"
            'أعد JSON: {"route": "science|humanities|tafseer|parallel"}'
        )

        try:
            from anthropic import AsyncAnthropic

            client = AsyncAnthropic()
            resp = await client.messages.create(
                model=_MODEL,
                max_tokens=64,
                temperature=_TEMPERATURE,
                messages=[{"role": "user", "content": prompt}],
            )
            text = resp.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0]
            data = json.loads(text)
            route = data.get("route", "parallel")
            if route in ("science", "humanities", "tafseer", "parallel"):
                return route
        except Exception:
            pass

        return self.route(state)
