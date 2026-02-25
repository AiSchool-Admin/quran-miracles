"""نظام المستويات الخمسة — من النمط الخام إلى الاكتشاف المؤكد.

tier_0: نمط خام — داخلي فقط
tier_1: فرضية أولية — تستحق النظر
tier_2: ارتباط محتمل — يستحق الدراسة
tier_3: نتيجة أولية مُتحقق منها
tier_4: اكتشاف مؤكد — إجماع أكاديمي
"""

from enum import Enum


class PredictiveTier(str, Enum):
    TIER_0 = "tier_0"  # نمط خام — داخلي فقط
    TIER_1 = "tier_1"  # فرضية أولية
    TIER_2 = "tier_2"  # ارتباط محتمل
    TIER_3 = "tier_3"  # نتيجة أولية مُتحقق منها
    TIER_4 = "tier_4"  # اكتشاف مؤكد


TIER_CONFIG = {
    PredictiveTier.TIER_0: {
        "label_ar": "🔴 نمط خام",
        "visible": False,  # لا يُعرض للمستخدم
        "min_pvalue": 1.0,
        "min_effect": 0.0,
    },
    PredictiveTier.TIER_1: {
        "label_ar": "🟠 فرضية أولية",
        "visible": True,
        "warning": "فرضية آلية — لم تُراجَع بعد",
        "min_pvalue": 0.05,
        "min_effect": 0.3,
    },
    PredictiveTier.TIER_2: {
        "label_ar": "🟡 ارتباط محتمل",
        "visible": True,
        "warning": "تحت المراجعة",
        "min_pvalue": 0.01,
        "min_effect": 0.5,
    },
    PredictiveTier.TIER_3: {
        "label_ar": "🟢 نتيجة أولية",
        "visible": True,
        "min_pvalue": 0.001,
        "min_effect": 0.8,
        "requires": "مراجعة متخصص",
    },
    PredictiveTier.TIER_4: {
        "label_ar": "✅ اكتشاف مؤكد",
        "visible": True,
        "requires": "نشر أكاديمي محكّم",
    },
}


def assign_tier(p_value: float, effect_size: float) -> PredictiveTier:
    """تصنيف الفرضية في النظام الخماسي."""
    d = abs(effect_size)

    if p_value < 0.001 and d > 0.8:
        return PredictiveTier.TIER_3
    elif p_value < 0.01 and d > 0.5:
        return PredictiveTier.TIER_2
    elif p_value < 0.05 and d > 0.3:
        return PredictiveTier.TIER_1
    else:
        return PredictiveTier.TIER_0
