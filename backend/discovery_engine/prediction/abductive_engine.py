"""محرك الاستنتاج الابتكاري — Abductive Reasoning Engine.

يعمل كـ "مفتش بوارو" للقرآن الكريم:
- يلاحظ تفصيلاً غير عادي في الآية
- يبحث عن أفضل تفسير ممكن
- يولّد الفرضية الأكثر احتمالاً
- يقترح كيف يمكن اختبارها
"""

import json
import re

from pydantic import BaseModel

from .statistical_safeguards import StatisticalSafeguards
from .tier_system import PredictiveTier, assign_tier


class PredictedMiracle(BaseModel):
    """نموذج المعجزة المتنبأ بها."""

    hypothesis_ar: str
    discipline: str
    novelty_score: float
    testability_score: float
    linguistic_support: float
    initial_tier: str
    p_value: float
    bayes_factor: float
    main_objection: str
    alternative_explanation: str
    research_steps: list[str]
    estimated_verification_time: str
    honesty_notes: list[str]
    pre_islamic_precedent: str


class AbductiveReasoningEngine:
    """محرك الاستنتاج الابتكاري.

    المبدأ: "من بين كل التفسيرات الممكنة للظاهرة القرآنية،
    ما الفرضية الأكثر احتمالاً التي تستحق البحث؟"
    """

    SYSTEM_PROMPT = """
أنت نظام استنتاج ابتكاري متخصص في توليد
فرضيات بحثية قابلة للاختبار من الآيات القرآنية.

مبدأك: "من بين كل التفسيرات الممكنة للظاهرة
القرآنية، ما الفرضية الأكثر احتمالاً؟"

لكل فرضية يجب أن تذكر:
1. الفرضية بدقة (لا تعميم)
2. التخصص العلمي الدقيق
3. قابلية الاختبار (كيف؟ ببيانات ماذا؟)
4. أقوى اعتراض بصدق تام
5. التفسير الأبسط البديل
6. هل المفهوم موجود قبل الإسلام؟
7. خطوات التحقق (3-4 خطوات)
8. الوقت المقدر للتحقق

أجب بـ JSON فقط — لا مقدمات.
"""

    def __init__(self, llm_client, validator: StatisticalSafeguards):
        self.llm = llm_client
        self.validator = validator

    async def generate_predictions(
        self,
        verses: list[dict],
        discipline: str,
        max_hypotheses: int = 5,
    ) -> list[PredictedMiracle]:
        """توليد تنبؤات بالمعجزات المحتملة لمجموعة آيات."""
        # بناء السياق من الآيات
        verses_text = "\n".join(
            [
                f"({v.get('surah_number', '?')}:{v.get('verse_number', '?')}) "
                f"{v.get('text_uthmani', v.get('text', ''))}"
                for v in verses[:5]
            ]
        )

        response = await self.llm.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=3000,
            system=self.SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"الآيات:\n{verses_text}\n\n"
                        f"التخصص: {discipline}\n\n"
                        f"ولّد {max_hypotheses} فرضيات بحثية.\n"
                        "JSON المطلوب:\n"
                        '[{{"hypothesis_ar": "...", '
                        '"discipline": "...", '
                        '"novelty_score": 0.0-1.0, '
                        '"testability_score": 0.0-1.0, '
                        '"linguistic_support": 0.0-1.0, '
                        '"main_objection": "...", '
                        '"alternative_explanation": "...", '
                        '"pre_islamic_precedent": "...", '
                        '"research_steps": ["...", "...", "..."], '
                        '"estimated_verification_time": "..."'
                        "}}]"
                    ),
                }
            ],
            temperature=0.5,
        )

        text = response.content[0].text
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if not match:
            return []

        raw_list = json.loads(match.group())
        results = []

        for raw in raw_list:
            # التحقق الإحصائي
            stats = await self.validator.validate(raw, verses)
            tier = assign_tier(stats["p_value"], stats["effect_size"])

            # tier_0 لا يُعرض
            if tier == PredictiveTier.TIER_0:
                continue

            results.append(
                PredictedMiracle(
                    hypothesis_ar=raw.get("hypothesis_ar", ""),
                    discipline=raw.get("discipline", discipline),
                    novelty_score=float(raw.get("novelty_score", 0.5)),
                    testability_score=float(
                        raw.get("testability_score", 0.5)
                    ),
                    linguistic_support=float(
                        raw.get("linguistic_support", 0.5)
                    ),
                    initial_tier=tier.value,
                    p_value=stats["p_value"],
                    bayes_factor=stats["bayes_factor"],
                    main_objection=raw.get("main_objection", ""),
                    alternative_explanation=raw.get(
                        "alternative_explanation", ""
                    ),
                    research_steps=raw.get("research_steps", []),
                    estimated_verification_time=raw.get(
                        "estimated_verification_time", "غير محدد"
                    ),
                    honesty_notes=stats["honesty_notes"],
                    pre_islamic_precedent=raw.get(
                        "pre_islamic_precedent", "غير محدد"
                    ),
                )
            )

        # ترتيب: الأعلى قيمةً أولاً
        return sorted(
            results,
            key=lambda h: (
                h.novelty_score * 0.40
                + h.testability_score * 0.35
                + h.linguistic_support * 0.25
            ),
            reverse=True,
        )
