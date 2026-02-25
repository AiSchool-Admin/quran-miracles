"""الموجّه البحثي — يحوّل الفرضية إلى خطة بحث قابلة للتنفيذ.

مُلهَم من:
- Google AI Co-Scientist (2025): تقليل وقت توليد الفرضيات
- Value of Information (VOI) Framework: تحديد أعلى قيمة بحثية
- Active Learning: توجيه الباحث نحو الفجوات المعرفية الكبرى
"""

from .abductive_engine import PredictedMiracle


class ResearchNavigator:
    """يحوّل الفرضية إلى خطة بحث قابلة للتنفيذ."""

    async def generate_research_map(
        self, hypothesis: PredictedMiracle
    ) -> dict:
        """توليد خارطة بحث مخصصة للفرضية."""
        priority_score = (
            hypothesis.novelty_score * 0.35
            + hypothesis.testability_score * 0.30
            + hypothesis.linguistic_support * 0.20
            + (1 - hypothesis.p_value) * 0.15
        )

        if priority_score > 0.75:
            priority_label = "🔴 أولوية عالية جداً"
        elif priority_score > 0.50:
            priority_label = "🟡 أولوية متوسطة"
        else:
            priority_label = "🟢 أولوية منخفضة"

        return {
            "hypothesis": hypothesis.hypothesis_ar,
            "tier": hypothesis.initial_tier,
            "priority_score": round(priority_score, 3),
            "priority_label": priority_label,
            "research_steps": hypothesis.research_steps,
            "estimated_time": hypothesis.estimated_verification_time,
            "stop_signals": [
                "وجود تفسير أبسط يُفسّر النمط بالكامل",
                "عدم القدرة على دحض التفسير البديل",
                "p_value لا يتحسن رغم زيادة البيانات",
                "نفس النمط موجود في نصوص مشابهة",
            ],
            "honesty_notes": hypothesis.honesty_notes,
            "main_objection": hypothesis.main_objection,
            "alternative": hypothesis.alternative_explanation,
            "pre_islamic": hypothesis.pre_islamic_precedent,
        }
