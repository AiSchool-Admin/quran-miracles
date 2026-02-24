# 🔮 القسم الحادي عشر: محرك التنبؤ بالمعجزات المحتملة
> المرجع: CLAUDE.md → docs/11_predictive_engine.md
> ⭐ هذا القسم هو الميزة الأكثر تميزاً في التطبيق
> يشمل: نظام المستويات الخمسة + AbductiveReasoningEngine + StatisticalSafeguards + ResearchNavigator + UI Dashboard

---
# ═══════════════════════════════════════════
# القسم الثاني عشر [جديد]: محرك التنبؤ بالمعجزات المحتملة
## 🔮 Predictive Miracles Engine
# ═══════════════════════════════════════════

## 12.1 الفلسفة — لماذا التنبؤ وليس الاكتشاف فقط؟

```
الاستكشاف يجيب: "ما الذي اكتُشف حتى الآن؟"
التنبؤ والاستنتاج يجيب: "ما الذي لم يُكتشف بعد وكيف نتوجه إليه؟"

التطبيق الذي يستكشف فقط هو مكتبة.
التطبيق الذي يتنبأ ويوجه هو عالِم.

الهدف: الذكاء الاصطناعي يقرأ القرآن الكريم ويقول للباحث:
  "هذه الآية تحمل إشارةً لم يدرسها أحد بعد في مجال الكيمياء الحيوية —
   إليك الخطوات التي تحتاجها لإثباتها أو نفيها."
```

---

## 12.2 مبدأ التشغيل — من النمط إلى الفرضية إلى التوجيه

```
[المرحلة 1: الكشف]        الذكاء الاصطناعي يكتشف نمطاً أو إشارةً في الآيات
        ↓
[المرحلة 2: الاستنتاج]    يستنتج: ما المعجزة المحتملة خلف هذا النمط؟
        ↓
[المرحلة 3: التحقق الآلي] يختبر إحصائياً: هل هذا أكثر من صدفة؟
        ↓
[المرحلة 4: التصنيف]      يُصنِّف الفرضية في الخمسة مستويات الجديدة
        ↓
[المرحلة 5: التوجيه]      يُصدر "خارطة بحث" للباحث: ماذا تفعل؟ من تسأل؟ ماذا تقرأ؟
```

---

## 12.3 الخمسة مستويات الجديدة — من النمط إلى الاكتشاف المؤكد

```python
# discovery_engine/prediction/tier_system.py

PREDICTIVE_TIER_SYSTEM = {

    "tier_0": {
        "اسم_عربي":    "🔴 نمط خام — للمعالجة الداخلية فقط",
        "وصف":         "اكتشفه الذكاء الاصطناعي لكن لم يُختبر إحصائياً بعد",
        "حالة_العرض":  "لا يُعرض للمستخدم — داخلي فقط",
        "الشرط":       "p_value غير محسوب بعد",
        "ما_يحدث_بعده": "يدخل خط أنابيب التحقق الإحصائي تلقائياً"
    },

    "tier_1": {
        "اسم_عربي":    "🟠 فرضية أولية — تستحق النظر",
        "وصف":         "نجح في التحقق الإحصائي الأولي لكن لم يُراجَع بشرياً",
        "حالة_العرض":  "يُعرض مع تحذير صريح: (فرضية آلية — لم تُراجَع بعد)",
        "الشرط":       "p_value < 0.05 بعد تصحيح FDR + Effect Size > 0.3",
        "ما_يحدث_بعده": "تُرسَل للمراجعة المجتمعية والخبراء"
    },

    "tier_2": {
        "اسم_عربي":    "🟡 ارتباط محتمل — يستحق الدراسة",
        "وصف":         "نجح في مراجعة أولية من خبير متخصص واحد على الأقل",
        "حالة_العرض":  "يُعرض مع badge: (محتمل — تحت المراجعة)",
        "الشرط":       "p_value < 0.01 + مراجعة خبير واحد + لا نسخة مماثلة في النصوص الأخرى",
        "ما_يحدث_بعده": "يدخل قائمة توجيه الباحثين للدراسة المعمّقة"
    },

    "tier_3": {
        "اسم_عربي":    "🟢 نتيجة أولية مُتحقق منها",
        "وصف":         "مراجعة متعددة التخصصات + تكرار النتيجة في تحليل مستقل",
        "حالة_العرض":  "يُعرض كـ (نتيجة أولية) مع جميع المصادر والاعتراضات",
        "الشرط":       "p_value < 0.001 + Bayes Factor > 10 + مراجعة فريق متعدد التخصصات",
        "ما_يحدث_بعده": "يُقترح للنشر الأكاديمي + إشعار الباحثين المتخصصين"
    },

    "tier_4": {
        "اسم_عربي":    "✅ اكتشاف مؤكد — إجماع أكاديمي",
        "وصف":         "منشور في مجلة محكّمة + إجماع علمي + تحقق مستقل",
        "حالة_العرض":  "يُعرض كـ (اكتشاف مؤكد) بالمرجع الكامل",
        "الشرط":       "نشر أكاديمي محكّم + تكرار مستقل + توافق علماء القرآن",
        "ما_يحدث_بعده": "يدخل قاعدة الحقائق الثابتة للتطبيق"
    }
}
```

---

## 12.4 محرك الاستنتاج الابتكاري — Abductive Reasoning Engine

```python
# discovery_engine/prediction/abductive_engine.py

from anthropic import AsyncAnthropic
from pydantic import BaseModel
from typing import Optional
import json

class PredictedMiracle(BaseModel):
    """نموذج المعجزة المتنبأ بها"""
    
    verse_ids: list[str]              # الآيات المعنية
    hypothesis_ar: str                # الفرضية بالعربية
    hypothesis_en: str                # الفرضية بالإنجليزية
    discipline: str                   # التخصص العلمي
    subfield: str                     # الفرع الدقيق
    
    # درجات التقييم
    novelty_score: float              # الجدة (0-1): هل اكتُشف من قبل؟
    testability_score: float          # القابلية للاختبار (0-1)
    linguistic_support: float         # الدعم اللغوي (0-1)
    
    # خارطة البحث المقترحة
    research_steps: list[str]         # خطوات البحث المقترحة
    key_papers_to_read: list[str]     # أبحاث يجب قراءتها
    experts_to_contact: list[str]     # تخصصات الخبراء المطلوبين
    estimated_verification_time: str  # الوقت المقدر للتحقق
    
    # التحذيرات
    main_objection: str               # أقوى اعتراض محتمل
    alternative_explanation: str      # التفسير البديل الأبسط
    
    # التصنيف
    initial_tier: str                 # المستوى الأولي (tier_0 → tier_1)
    confidence_interval: tuple        # [أدنى, أعلى] لدرجة الثقة


class AbductiveReasoningEngine:
    """
    محرك الاستنتاج الابتكاري
    
    يعمل كـ "مفتش بوارو" للقرآن الكريم:
    - يلاحظ تفصيلاً غير عادي في الآية
    - يبحث عن أفضل تفسير ممكن
    - يولّد الفرضية الأكثر احتمالاً
    - يقترح كيف يمكن اختبارها
    """
    
    ABDUCTIVE_SYSTEM_PROMPT = """
    أنت نظام استنتاج ابتكاري (Abductive Reasoning System) متخصص
    في توليد فرضيات بحثية قابلة للاختبار من الآيات القرآنية.

    مبدأ الاستنتاج الابتكاري:
    "من بين كل التفسيرات الممكنة للظاهرة القرآنية،
     ما الفرضية الأكثر احتمالاً التي تستحق البحث؟"

    منهجيتك:
    1. ابدأ بالملاحظة: ما الظاهرة غير العادية في هذه الآية؟
       - كلمة نادرة الاستخدام؟
       - وصف دقيق غير معهود في القرن السابع؟
       - نمط تكراري غير متوقع؟
       - تفاصيل علمية لم تُعرف إلا حديثاً؟

    2. اقترح الفرضية: ما المعجزة المحتملة؟
       - كن محدداً: ليس "القرآن يذكر الفيزياء" بل
         "الآية (36:38) قد تصف مدار الشمس حول مركز المجرة"
       - اقترح فرضيتين أو ثلاث — ليس واحدة فقط

    3. حدد قابلية الاختبار:
       - هل يمكن قياس الفرضية تجريبياً؟
       - ما البيانات المطلوبة؟
       - ما الأدوات العلمية اللازمة؟

    4. اذكر أقوى اعتراض على الفرضية بصدق تام

    الإخراج: JSON مُنظَّم بالعربية والإنجليزية
    """

    def __init__(self, llm_client: AsyncAnthropic, knowledge_graph, validator):
        self.llm = llm_client
        self.kg = knowledge_graph
        self.validator = validator
    
    async def generate_predictions(
        self,
        verse_ids: list[str],
        context: dict,
        max_hypotheses: int = 5
    ) -> list[PredictedMiracle]:
        """
        توليد تنبؤات بالمعجزات المحتملة لمجموعة آيات
        """
        
        # 1. تجميع السياق الكامل
        full_context = await self._build_full_context(verse_ids, context)
        
        # 2. الاستنتاج الابتكاري بـ Claude
        response = await self.llm.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4000,
            system=self.ABDUCTIVE_SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": f"""
                السياق القرآني:
                {json.dumps(full_context, ensure_ascii=False, indent=2)}
                
                المطلوب:
                ولِّد {max_hypotheses} فرضيات بحثية قابلة للاختبار.
                رتّبها حسب: الجدة × قابلية الاختبار × الدعم اللغوي.
                
                لكل فرضية أعطِ:
                - الفرضية بالعربية والإنجليزية
                - التخصص العلمي الدقيق
                - خارطة البحث (3-5 خطوات)
                - أبرز 3 أبحاث يجب قراءتها
                - تخصصات الخبراء المطلوبين
                - أقوى اعتراض على الفرضية
                - التفسير البديل الأبسط
                
                أجب بـ JSON فقط.
                """
            }],
            temperature=0.4
        )
        
        raw_hypotheses = self._parse_response(response.content[0].text)
        
        # 3. التحقق الإحصائي الفوري لكل فرضية
        validated = []
        for hyp in raw_hypotheses:
            stats = await self.validator.quick_validate(hyp, full_context)
            hyp["p_value"]     = stats["p_value"]
            hyp["effect_size"] = stats["effect_size"]
            hyp["initial_tier"] = self._assign_initial_tier(stats)
            validated.append(PredictedMiracle(**hyp))
        
        # 4. الترتيب: الأعلى قيمةً أولاً
        return sorted(
            validated,
            key=lambda h: (h.novelty_score * 0.4 + 
                          h.testability_score * 0.35 + 
                          h.linguistic_support * 0.25),
            reverse=True
        )
    
    def _assign_initial_tier(self, stats: dict) -> str:
        """تصنيف الفرضية في النظام الخماسي"""
        p = stats.get("p_value", 1.0)
        d = abs(stats.get("effect_size", 0.0))
        
        if p < 0.001 and d > 0.8:   return "tier_2"  # مباشرة للمرحلة الثانية
        elif p < 0.05 and d > 0.3:  return "tier_1"  # فرضية أولية
        else:                        return "tier_0"  # نمط خام
```

---

## 12.5 الموجّه البحثي — Research Navigator

```python
# discovery_engine/prediction/research_navigator.py

class ResearchNavigator:
    """
    الموجّه البحثي — يحوّل الفرضيات إلى خطط بحث قابلة للتنفيذ
    
    مُلهَم من:
    - Google AI Co-Scientist (2025): تقليل وقت توليد الفرضيات من أسابيع لأيام
    - Value of Information (VOI) Framework: تحديد أعلى قيمة بحثية
    - Active Learning: توجيه الباحث نحو الفجوات المعرفية الكبرى
    """
    
    async def generate_research_map(
        self,
        hypothesis: PredictedMiracle,
        researcher_profile: dict
    ) -> dict:
        """
        توليد خارطة بحث مخصصة للباحث
        
        تراعي:
        - تخصص الباحث وخبرته
        - الوقت المتاح للبحث
        - الموارد المتاحة (مختبر / بيانات / خبراء)
        - الأولويات البحثية الحالية في التخصص
        """
        
        research_map = {
            "الفرضية": hypothesis.hypothesis_ar,
            "المستوى_الحالي": hypothesis.initial_tier,
            "لماذا_تستحق_البحث": await self._generate_value_statement(hypothesis),
            
            "خطوات_التحقق": {
                "الخطوة_الأولى": {
                    "المهمة": "مراجعة التفسير اللغوي",
                    "الأدوات": ["قاعدة بيانات الجذور", "CAMeL Tools", "مراجعة تفسير ابن منظور"],
                    "الوقت_المقدر": "3-5 أيام",
                    "معيار_النجاح": "التحقق من أن المعنى العربي الأصيل يدعم الفرضية"
                },
                "الخطوة_الثانية": {
                    "المهمة": "مسح الأدبيات العلمية",
                    "الأدوات": ["Semantic Scholar API", "PubMed", "arXiv"],
                    "الوقت_المقدر": "1-2 أسابيع",
                    "معيار_النجاح": "إيجاد 5+ أبحاث محكّمة ذات صلة"
                },
                "الخطوة_الثالثة": {
                    "المهمة": "التحليل الإحصائي التفصيلي",
                    "الأدوات": ["Monte Carlo Validator", "SciPy", "PyMC"],
                    "الوقت_المقدر": "2-3 أسابيع",
                    "معيار_النجاح": "p_value < 0.001 بعد تصحيح FDR"
                },
                "الخطوة_الرابعة": {
                    "المهمة": "مراجعة متخصصين",
                    "الأدوات": ["نموذج مراجعة الخبراء في التطبيق"],
                    "الوقت_المقدر": "3-4 أسابيع",
                    "معيار_النجاح": "موافقة خبيرين على الأقل من تخصصين مختلفين"
                }
            },
            
            "الخبراء_المقترحون": hypothesis.experts_to_contact,
            "الأبحاث_الأساسية": hypothesis.key_papers_to_read,
            "الاعتراض_الرئيسي": hypothesis.main_objection,
            "التفسير_البديل": hypothesis.alternative_explanation,
            
            "مقاييس_التقدم": {
                "كيف_تعرف_أنك_تتقدم": [
                    "زيادة درجة الثقة الإحصائية",
                    "تراكم الأدلة الداعمة من مصادر مستقلة",
                    "انخفاض عدد التفسيرات البديلة المعقولة",
                    "توافق متزايد بين الخبراء"
                ],
                "إشارات_التوقف": [
                    "وجود تفسير أبسط يُفسّر النمط بالكامل",
                    "عدم القدرة على دحض التفسير البديل",
                    "p_value لا يتحسن رغم زيادة البيانات",
                    "اكتشاف نفس النمط في نصوص مشابهة أخرى"
                ]
            }
        }
        
        return research_map
    
    async def rank_research_priorities(
        self,
        hypotheses: list[PredictedMiracle],
        field: str = "all"
    ) -> list[dict]:
        """
        ترتيب الفرضيات حسب أولوية البحث بنظام VOI
        
        معادلة الأولوية:
        Priority = (Novelty × 0.35) + (Testability × 0.30) +
                   (Impact × 0.20) + (Feasibility × 0.15)
        """
        
        ranked = []
        for hyp in hypotheses:
            impact = await self._estimate_impact(hyp)          # الأهمية لو ثبتت
            feasibility = await self._estimate_feasibility(hyp) # سهولة التحقق
            
            priority_score = (
                hyp.novelty_score     * 0.35 +
                hyp.testability_score * 0.30 +
                impact                * 0.20 +
                feasibility           * 0.15
            )
            
            ranked.append({
                "hypothesis": hyp,
                "priority_score": priority_score,
                "priority_label": self._get_priority_label(priority_score),
                "voi_breakdown": {
                    "novelty":      hyp.novelty_score,
                    "testability":  hyp.testability_score,
                    "impact":       impact,
                    "feasibility":  feasibility
                }
            })
        
        return sorted(ranked, key=lambda x: x["priority_score"], reverse=True)
```

---

## 12.6 الضمانات الإحصائية — منع التضخيم الكاذب

```python
# discovery_engine/prediction/statistical_safeguards.py

class StatisticalSafeguards:
    """
    درع الأمانة العلمية
    
    الدرس المستفاد من "Bible Codes":
    فحص 6,236 آية × 100+ علم = 623,600 اختبار ضمني.
    بدون تصحيح: 31,180 نتيجة إيجابية كاذبة متوقعة!
    
    الحل: 4 ضمانات إلزامية لا تُتجاوز.
    """
    
    def __init__(self):
        self.control_corpora = [
            "pre_islamic_arabic_poetry",  # شعر عربي قبل الإسلام
            "bible_arabic_translation",   # الكتاب المقدس بالعربية
            "shuffled_quran",             # القرآن مُرتَّب عشوائياً
            "quran_same_length_texts",    # نصوص عربية بنفس الطول
        ]
    
    async def validate_hypothesis(self, hyp: dict, corpus: dict) -> dict:
        """
        التحقق الإحصائي الإلزامي الرباعي
        """
        
        results = {}
        
        # ═══════════════════════════════════
        # الضمان 1: تصحيح الاختبارات المتعددة (FDR)
        # ═══════════════════════════════════
        raw_pvalue = await self._compute_raw_pvalue(hyp, corpus)
        n_tests = await self._count_total_tests(corpus)
        
        fdr_corrected = self._benjamini_hochberg(raw_pvalue, n_tests)
        
        results["fdr_correction"] = {
            "raw_p_value":       raw_pvalue,
            "corrected_p_value": fdr_corrected,
            "n_tests_total":     n_tests,
            "passes":            fdr_corrected < 0.05
        }
        
        # ═══════════════════════════════════
        # الضمان 2: نصوص التحكم — هل النمط فريد للقرآن؟
        # ═══════════════════════════════════
        control_results = {}
        for corpus_name in self.control_corpora:
            control_pvalue = await self._compute_raw_pvalue(hyp, corpus_name)
            control_results[corpus_name] = control_pvalue
        
        quran_is_unique = fdr_corrected < min(control_results.values()) * 0.1
        
        results["control_corpus_comparison"] = {
            "control_p_values":  control_results,
            "quran_p_value":     fdr_corrected,
            "quran_is_unique":   quran_is_unique,
            "warning": None if quran_is_unique else
                "⚠️ نفس النمط موجود في نصوص أخرى — ليس فريداً للقرآن"
        }
        
        # ═══════════════════════════════════
        # الضمان 3: عامل بايز — ضد الصدفة
        # ═══════════════════════════════════
        bayes_factor = self._compute_bayes_factor(
            h1_likelihood=raw_pvalue,
            h0_likelihood=1 / n_tests,
            prior_h1=0.001  # افتراض متشكك: احتمال 0.1٪ أن أي ادعاء صحيح
        )
        
        results["bayesian_analysis"] = {
            "bayes_factor":     bayes_factor,
            "interpretation":   self._interpret_bayes_factor(bayes_factor),
            "skeptical_prior":  0.001,
            "posterior_probability": self._compute_posterior(bayes_factor, 0.001)
        }
        
        # ═══════════════════════════════════
        # الضمان 4: تحليل الحساسية
        # ═══════════════════════════════════
        sensitivity_results = {}
        for prior in [0.000001, 0.001, 0.01, 0.10, 0.50]:
            posterior = self._compute_posterior(bayes_factor, prior)
            sensitivity_results[f"prior_{prior}"] = posterior
        
        significant_across_priors = all(
            p > 0.5 for p in sensitivity_results.values()
        )
        
        results["sensitivity_analysis"] = {
            "posteriors_by_prior":        sensitivity_results,
            "significant_across_priors":  significant_across_priors,
            "warning": None if significant_across_priors else
                "⚠️ النتيجة حساسة لافتراضات الأولوية — تحتاج أدلة إضافية"
        }
        
        # ═══════════════════════════════════
        # التقييم النهائي
        # ═══════════════════════════════════
        overall_valid = (
            results["fdr_correction"]["passes"] and
            results["control_corpus_comparison"]["quran_is_unique"] and
            bayes_factor > 10 and
            significant_across_priors
        )
        
        return {
            "overall_valid":    overall_valid,
            "details":          results,
            "recommendation":   self._generate_recommendation(results, overall_valid),
            "what_not_to_say":  self._generate_honesty_note(results)
        }
    
    def _interpret_bayes_factor(self, bf: float) -> str:
        """تفسير عامل بايز بالعربية"""
        if bf > 100:  return "دليل استثنائي على الفرضية"
        if bf > 30:   return "دليل قوي جداً"
        if bf > 10:   return "دليل قوي"
        if bf > 3:    return "دليل معتدل"
        if bf > 1:    return "دليل ضعيف"
        return "لا دليل — أو دليل ضد الفرضية"
    
    def _generate_honesty_note(self, results: dict) -> str:
        """ماذا لا يجب قوله عن هذه النتيجة"""
        notes = []
        
        if not results["control_corpus_comparison"]["quran_is_unique"]:
            notes.append("لا يجوز القول: 'هذا النمط فريد للقرآن' — فهو موجود في نصوص أخرى")
        
        if not results["sensitivity_analysis"]["significant_across_priors"]:
            notes.append("لا يجوز القول: 'هذا دليل قاطع' — النتيجة حساسة للافتراضات")
        
        if results["fdr_correction"]["corrected_p_value"] > 0.01:
            notes.append("لا يجوز القول: 'ثبت إحصائياً' — الدلالة الإحصائية لم تصل للحد المطلوب")
        
        return notes if notes else ["النتائج الإحصائية سليمة — يمكن الاستشهاد بها بحذر"]
```

---

## 12.7 واجهة التنبؤ — Research Frontier Dashboard

```typescript
// components/prediction/ResearchFrontierDashboard.tsx

'use client';
import { useState, useEffect } from 'react';

export default function ResearchFrontierDashboard() {
  const [predictions, setPredictions] = useState<PredictedMiracle[]>([]);
  const [selectedTier, setSelectedTier] = useState<string>('all');
  const [selectedField, setSelectedField] = useState<string>('all');
  
  return (
    <div dir="rtl" className="research-frontier">
      
      {/* رأس اللوحة */}
      <header className="frontier-header">
        <h1>🔮 حدود المعرفة — ما لم يُكتشف بعد</h1>
        <p className="subtitle">
          فرضيات اكتشفها الذكاء الاصطناعي تستحق البحث الأكاديمي المعمّق
        </p>
        <div className="disclaimer-banner">
          ⚠️ هذه فرضيات آلية — لم تُراجَع بشرياً بعد.
          كل فرضية تحمل مستوى ثقتها الإحصائية وخارطة التحقق منها.
        </div>
      </header>
      
      {/* فلاتر التصفية */}
      <FilterPanel
        tiers={PREDICTIVE_TIER_SYSTEM}
        fields={SCIENCE_FIELDS}
        onTierChange={setSelectedTier}
        onFieldChange={setSelectedField}
      />
      
      {/* بطاقات الفرضيات */}
      <div className="predictions-grid">
        {predictions
          .filter(p => selectedTier === 'all' || p.initial_tier === selectedTier)
          .filter(p => selectedField === 'all' || p.discipline === selectedField)
          .map(prediction => (
            <PredictionCard
              key={prediction.id}
              prediction={prediction}
              onExploreFurther={() => launchDiscoverySession(prediction)}
              onSaveToResearch={() => saveToResearchQueue(prediction)}
              onRequestExpertReview={() => submitForExpertReview(prediction)}
            />
          ))
        }
      </div>
      
    </div>
  );
}

// بطاقة الفرضية الواحدة
function PredictionCard({ prediction, onExploreFurther, onSaveToResearch, onRequestExpertReview }) {
  
  const TIER_STYLES = {
    "tier_0": { color: "#8A3A3A", label: "🔴 نمط خام" },
    "tier_1": { color: "#C0833A", label: "🟠 فرضية أولية" },
    "tier_2": { color: "#C0C030", label: "🟡 ارتباط محتمل" },
    "tier_3": { color: "#2A7A5A", label: "🟢 نتيجة أولية" },
    "tier_4": { color: "#1A5A3A", label: "✅ اكتشاف مؤكد" },
  };
  
  const tier = TIER_STYLES[prediction.initial_tier];
  
  return (
    <div className="prediction-card">
      
      {/* رأس البطاقة */}
      <div className="card-header">
        <span className="tier-badge" style={{ background: tier.color }}>
          {tier.label}
        </span>
        <span className="discipline-tag">{prediction.discipline}</span>
      </div>
      
      {/* الفرضية */}
      <h3 className="hypothesis-title">{prediction.hypothesis_ar}</h3>
      
      {/* الآيات المعنية */}
      <div className="verse-refs">
        {prediction.verse_ids.map(id => (
          <VerseChip key={id} verseId={id} />
        ))}
      </div>
      
      {/* مؤشرات التقييم */}
      <div className="score-indicators">
        <ScoreBar label="الجدة"              value={prediction.novelty_score}      />
        <ScoreBar label="قابلية الاختبار"    value={prediction.testability_score}  />
        <ScoreBar label="الدعم اللغوي"       value={prediction.linguistic_support} />
      </div>
      
      {/* التحذير الإلزامي */}
      <div className="honesty-box">
        <strong>⚠️ أقوى اعتراض:</strong>
        <p>{prediction.main_objection}</p>
        <strong>التفسير البديل الأبسط:</strong>
        <p>{prediction.alternative_explanation}</p>
      </div>
      
      {/* خارطة البحث المختصرة */}
      <details className="research-steps">
        <summary>📋 خارطة التحقق ({prediction.research_steps.length} خطوات)</summary>
        <ol>
          {prediction.research_steps.map((step, i) => (
            <li key={i}>{step}</li>
          ))}
        </ol>
        <div className="time-estimate">
          ⏱️ الوقت المقدر: {prediction.estimated_verification_time}
        </div>
      </details>
      
      {/* أزرار الإجراءات */}
      <div className="action-buttons">
        <button onClick={onExploreFurther}      className="btn-explore">
          🔍 استكشف أعمق
        </button>
        <button onClick={onSaveToResearch}      className="btn-save">
          📌 أضف لقائمة البحث
        </button>
        <button onClick={onRequestExpertReview} className="btn-review">
          👩‍🔬 اطلب مراجعة خبير
        </button>
      </div>
      
    </div>
  );
}
```

---

## 12.8 إضافة وكيل التنبؤ إلى LangGraph

```python
# تحديث build_discovery_graph() لإضافة وكيل التنبؤ

def build_discovery_graph_v3():
    """رسم الوكلاء المُحدَّث — الإصدار 3.0 مع التنبؤ"""
    
    graph = StateGraph(DiscoveryState)
    
    # الوكلاء الأصليون
    graph.add_node("route_query",    route_query_agent)
    graph.add_node("quran_rag",      quran_rag_agent)
    graph.add_node("linguistic",     linguistic_agent)
    graph.add_node("science",        science_agent)
    graph.add_node("tafseer",        tafseer_agent)
    graph.add_node("humanities",     humanities_agent)   # مع البروتوكول الجديد
    graph.add_node("synthesis",      synthesis_agent)
    graph.add_node("quality_review", quality_review_agent)
    graph.add_node("kg_update",      knowledge_graph_updater)
    graph.add_node("deepen_search",  deepen_search_agent)
    
    # ★ الوكلاء الجدد — التنبؤ والتوجيه
    graph.add_node("abductive_engine",    abductive_reasoning_agent)  # توليد الفرضيات
    graph.add_node("stat_safeguards",     statistical_safeguards_agent)  # التحقق الإحصائي
    graph.add_node("research_navigator",  research_navigator_agent)   # خارطة البحث
    graph.add_node("kg_prediction_update", kg_prediction_updater)     # حفظ التنبؤات
    
    # ═══════════════════════════════════
    # المسار الأصلي (الاستكشاف والتحليل)
    # ═══════════════════════════════════
    graph.set_entry_point("route_query")
    graph.add_edge("route_query", "quran_rag")
    graph.add_edge("quran_rag",   "linguistic")
    graph.add_edge("linguistic",  "science")
    graph.add_edge("linguistic",  "tafseer")
    graph.add_edge("linguistic",  "humanities")  # ← بروتوكول الإنسانيات الجديد
    graph.add_edge("science",     "synthesis")
    graph.add_edge("tafseer",     "synthesis")
    graph.add_edge("humanities",  "synthesis")
    graph.add_edge("synthesis",   "quality_review")
    
    # ★ المسار الجديد (التنبؤ والتوجيه) — يبدأ موازياً بعد التوليف
    graph.add_edge("synthesis",         "abductive_engine")     # موازٍ لـ quality_review
    graph.add_edge("abductive_engine",  "stat_safeguards")      # التحقق الإحصائي
    graph.add_edge("stat_safeguards",   "research_navigator")   # توليد خارطة البحث
    graph.add_edge("research_navigator","kg_prediction_update")  # حفظ التنبؤات
    graph.add_edge("kg_prediction_update", END)
    
    # المنطق الشرطي الأصلي
    def decide_next(state: DiscoveryState) -> str:
        if state["should_deepen"] and state["iteration_count"] < 3:
            return "deepen_search"
        elif state["quality_issues"]:
            return "quality_review"
        else:
            return "kg_update"
    
    graph.add_conditional_edges("quality_review", decide_next, {
        "deepen_search": "deepen_search",
        "quality_review": "quality_review",
        "kg_update":      "kg_update"
    })
    
    graph.add_edge("deepen_search", "synthesis")
    graph.add_edge("kg_update",     END)
    
    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)
```

---

## 12.9 أمر Claude Code لبناء محرك التنبؤ

```bash
# ══════════════════════════════════════════════════════
# الأمر 11: محرك التنبؤ بالمعجزات المحتملة
# ══════════════════════════════════════════════════════
claude "
أنشئ محرك التنبؤ بالمعجزات المحتملة (Predictive Miracles Engine):

1. AbductiveReasoningEngine الكامل مع System Prompt الاستنتاج الابتكاري
2. StatisticalSafeguards بالضمانات الأربعة (FDR + Control Corpus + Bayes + Sensitivity)
3. ResearchNavigator مع نظام VOI لترتيب الفرضيات
4. نظام المستويات الخمسة (tier_0 → tier_4) مع معايير الترقية
5. ResearchFrontierDashboard بالـ UI الكامل مع بطاقات الفرضيات
6. تحديث LangGraph لإضافة وكلاء التنبؤ الثلاثة موازياً
7. قاعدة بيانات predictions مع الحقول الكاملة

المطلوب أن يظهر في كل فرضية:
- مستواها الإحصائي الحالي (tier_0 إلى tier_4)
- درجات الثقة الثلاث (جدة، قابلية اختبار، دعم لغوي)
- خارطة البحث المخصصة (4 خطوات)
- أقوى اعتراض + التفسير البديل (إلزامي)
- أزرار: استكشف أعمق / أضف للبحث / اطلب مراجعة

الكود الأساسي موجود في وثيقة التوجيه القسم الثاني عشر.
"

# ══════════════════════════════════════════════════════
# الأمر 12: بروتوكول الإنسانيات + اختباره
# ══════════════════════════════════════════════════════
claude "
نفّذ وكيل HumanitiesAgent بالكامل مع HUMANITIES_SCHOLAR_SYSTEM_PROMPT
من وثيقة التوجيه القسم الحادي عشر.

اختبره على هذه الآيات:
1. 'أَلَا بِذِكْرِ اللَّهِ تَطْمَئِنُّ الْقُلُوبُ' (13:28) ← علم النفس
2. 'كَيْ لَا يَكُونَ دُولَةً بَيْنَ الْأَغْنِيَاءِ مِنكُمْ' (59:7) ← الاقتصاد
3. 'وَشَاوِرْهُمْ فِي الْأَمْرِ' (3:159) ← الإدارة والقيادة

تحقق أن الإخراج يتبع نموذج JSON المُحدَّد في الوثيقة
مع التصنيف الثلاثي: intersecting / parallel / inspirational
"
```

---

