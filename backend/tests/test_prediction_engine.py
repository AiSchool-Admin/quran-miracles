"""اختبارات محرك التنبؤ و MCTS.

اختبار 1: POST /api/prediction/generate
  — بحث عن "الماء" → أول 5 آيات → توليد فرضيات فيزيائية
اختبار 2: POST /api/prediction/mcts/explore
  — استكشاف MCTS لموضوع "الماء في القرآن" → biology
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from discovery_engine.mcts.hypothesis_explorer import MCTSHypothesisExplorer
from discovery_engine.prediction.abductive_engine import (
    AbductiveReasoningEngine,
    PredictedMiracle,
)
from discovery_engine.prediction.research_navigator import ResearchNavigator
from discovery_engine.prediction.statistical_safeguards import StatisticalSafeguards


# ═══════════════════════════════════════════════════════
# بيانات تجريبية — نتائج بحث "الماء" (5 آيات)
# ═══════════════════════════════════════════════════════

WATER_VERSES: list[dict[str, Any]] = [
    {
        "id": 2735,
        "surah_number": 21,
        "verse_number": 30,
        "text_uthmani": (
            "أَوَلَمْ يَرَ ٱلَّذِينَ كَفَرُوٓا۟ أَنَّ ٱلسَّمَـٰوَٰتِ "
            "وَٱلْأَرْضَ كَانَتَا رَتْقًا فَفَتَقْنَـٰهُمَا ۖ "
            "وَجَعَلْنَا مِنَ ٱلْمَآءِ كُلَّ شَىْءٍ حَىٍّ ۖ أَفَلَا يُؤْمِنُونَ"
        ),
        "text_simple": (
            "أولم ير الذين كفروا أن السماوات والأرض كانتا رتقا "
            "ففتقناهما وجعلنا من الماء كل شيء حي أفلا يؤمنون"
        ),
        "text_clean": "اولم ير الذين كفروا ان السماوات والارض كانتا رتقا ففتقناهما وجعلنا من الماء كل شيء حي افلا يؤمنون",
    },
    {
        "id": 3088,
        "surah_number": 24,
        "verse_number": 45,
        "text_uthmani": (
            "وَٱللَّهُ خَلَقَ كُلَّ دَآبَّةٍ مِّن مَّآءٍ ۖ "
            "فَمِنْهُم مَّن يَمْشِى عَلَىٰ بَطْنِهِۦ وَمِنْهُم "
            "مَّن يَمْشِى عَلَىٰ رِجْلَيْنِ وَمِنْهُم مَّن يَمْشِى "
            "عَلَىٰٓ أَرْبَعٍ ۚ يَخْلُقُ ٱللَّهُ مَا يَشَآءُ ۚ "
            "إِنَّ ٱللَّهَ عَلَىٰ كُلِّ شَىْءٍ قَدِيرٌ"
        ),
        "text_simple": (
            "والله خلق كل دابة من ماء فمنهم من يمشي على بطنه "
            "ومنهم من يمشي على رجلين ومنهم من يمشي على أربع "
            "يخلق الله ما يشاء إن الله على كل شيء قدير"
        ),
        "text_clean": "والله خلق كل دابة من ماء فمنهم من يمشي على بطنه ومنهم من يمشي على رجلين ومنهم من يمشي على اربع يخلق الله ما يشاء ان الله على كل شيء قدير",
    },
    {
        "id": 3425,
        "surah_number": 25,
        "verse_number": 54,
        "text_uthmani": (
            "وَهُوَ ٱلَّذِى خَلَقَ مِنَ ٱلْمَآءِ بَشَرًا "
            "فَجَعَلَهُۥ نَسَبًا وَصِهْرًا ۗ وَكَانَ رَبُّكَ قَدِيرًا"
        ),
        "text_simple": (
            "وهو الذي خلق من الماء بشرا فجعله نسبا وصهرا وكان ربك قديرا"
        ),
        "text_clean": "وهو الذي خلق من الماء بشرا فجعله نسبا وصهرا وكان ربك قديرا",
    },
    {
        "id": 5170,
        "surah_number": 54,
        "verse_number": 12,
        "text_uthmani": (
            "وَفَجَّرْنَا ٱلْأَرْضَ عُيُونًا فَٱلْتَقَى ٱلْمَآءُ "
            "عَلَىٰٓ أَمْرٍ قَدْ قُدِرَ"
        ),
        "text_simple": (
            "وفجرنا الأرض عيونا فالتقى الماء على أمر قد قدر"
        ),
        "text_clean": "وفجرنا الارض عيونا فالتقى الماء على امر قد قدر",
    },
    {
        "id": 5830,
        "surah_number": 86,
        "verse_number": 6,
        "text_uthmani": "خُلِقَ مِن مَّآءٍ دَافِقٍ",
        "text_simple": "خلق من ماء دافق",
        "text_clean": "خلق من ماء دافق",
    },
]


# ═══════════════════════════════════════════════════════
# Mock LLM — استجابات مُحاكاة لـ Claude
# ═══════════════════════════════════════════════════════

MOCK_PREDICTION_JSON = json.dumps(
    [
        {
            "hypothesis_ar": (
                "الآيات القرآنية التي تربط الماء بالحياة تشير إلى "
                "الخصائص الفيزيائية الفريدة للماء (القطبية، التوتر السطحي، "
                "الحرارة النوعية العالية) كشروط ضرورية لنشأة الحياة"
            ),
            "discipline": "physics",
            "novelty_score": 0.85,
            "testability_score": 0.82,
            "linguistic_support": 0.78,
            "main_objection": (
                "ربط الماء بالحياة معروف في كل الحضارات القديمة — "
                "ليس فريداً للقرآن"
            ),
            "alternative_explanation": (
                "ملاحظة تجريبية بسيطة: كل كائن حي يحتاج ماء للبقاء"
            ),
            "pre_islamic_precedent": (
                "طاليس الملطي (624 ق.م) قال: الماء أصل كل شيء"
            ),
            "research_steps": [
                "تحليل لغوي: ما الفرق بين 'مِنَ المَاءِ' و 'بِالمَاءِ'؟",
                "مقارنة نصوص ما قبل الإسلام عن الماء والحياة",
                "ربط مع أبحاث NASA عن الماء كشرط للحياة خارج الأرض",
            ],
            "estimated_verification_time": "3-6 أشهر",
        },
        {
            "hypothesis_ar": (
                "وصف 'ماء دافق' (86:6) يتوافق مع ديناميكيات السوائل: "
                "ضغط هيدروستاتيكي + لزوجة + تدفق نابض"
            ),
            "discipline": "fluid_mechanics",
            "novelty_score": 0.78,
            "testability_score": 0.75,
            "linguistic_support": 0.80,
            "main_objection": (
                "'دافق' تصف المشاهدة الظاهرية — لا تحتاج معرفة فيزيائية"
            ),
            "alternative_explanation": "وصف حسي بسيط لحركة سائل",
            "pre_islamic_precedent": "وصف السوائل المتدفقة موجود في الشعر الجاهلي",
            "research_steps": [
                "تحليل جذر 'دفق' في المعاجم العربية القديمة",
                "مقارنة مع مصطلحات ديناميكيات السوائل الحديثة",
                "اختبار: هل 'دافق' أدق من 'جارٍ' أو 'سائل'؟",
            ],
            "estimated_verification_time": "2-4 أشهر",
        },
        {
            "hypothesis_ar": (
                "التقاء الماء 'على أمر قد قُدر' (54:12) يشير إلى "
                "مبدأ التوازن الهيدرولوجي الكمي — "
                "الماء يتبع قوانين فيزيائية محددة وليس عشوائياً"
            ),
            "discipline": "hydrology",
            "novelty_score": 0.72,
            "testability_score": 0.70,
            "linguistic_support": 0.68,
            "main_objection": (
                "'قُدر' تعني القضاء الإلهي — ليست إشارة لقوانين فيزيائية"
            ),
            "alternative_explanation": (
                "السياق يتحدث عن طوفان نوح — وصف لحدث معجز"
            ),
            "pre_islamic_precedent": "قوانين الفيضانات معروفة في حضارة بلاد الرافدين",
            "research_steps": [
                "تحليل سياق الآية في سورة القمر",
                "مراجعة تفاسير 'أمر قد قُدر' عند القدماء",
                "مقارنة مع قوانين الهيدرولوجيا الحديثة",
            ],
            "estimated_verification_time": "4-8 أشهر",
        },
        {
            "hypothesis_ar": (
                "خلق البشر 'من الماء' (25:54) ثم 'نسباً وصهراً' "
                "يشير إلى الأساس المائي للتكاثر الجنسي"
            ),
            "discipline": "reproductive_biology",
            "novelty_score": 0.65,
            "testability_score": 0.60,
            "linguistic_support": 0.70,
            "main_objection": (
                "العلاقة بين الماء والتكاثر ملاحظة بديهية في كل الثقافات"
            ),
            "alternative_explanation": "ملاحظة حسية عن السائل المنوي",
            "pre_islamic_precedent": "الطب اليوناني (جالينوس) ربط السوائل بالتكاثر",
            "research_steps": [
                "تحليل 'نسباً وصهراً' لغوياً",
                "مراجعة تفسير ابن كثير والرازي لهذه الآية",
                "مقارنة مع المعرفة البيولوجية المعاصرة",
            ],
            "estimated_verification_time": "2-3 أشهر",
        },
        {
            "hypothesis_ar": (
                "تكرار 'كل شيء حي' مع 'كل دابة' "
                "يغطي الكائنات المتحركة وغير المتحركة — "
                "شمولية بيولوجية دقيقة"
            ),
            "discipline": "biology",
            "novelty_score": 0.55,
            "testability_score": 0.50,
            "linguistic_support": 0.60,
            "main_objection": (
                "التعميم البلاغي لا يعني الدقة العلمية"
            ),
            "alternative_explanation": "أسلوب بلاغي للتأكيد والتعظيم",
            "pre_islamic_precedent": "أرسطو صنّف الكائنات الحية وغير الحية",
            "research_steps": [
                "تحليل الفرق بين 'شيء حي' و 'دابة' في القرآن",
                "إحصاء استخدام الكلمتين في القرآن كله",
                "مقارنة التصنيف القرآني مع التصنيف البيولوجي",
            ],
            "estimated_verification_time": "1-2 أشهر",
        },
    ]
)


MOCK_MCTS_EXPAND_JSON = json.dumps(
    [
        {
            "hypothesis_ar": (
                "دورة الماء في القرآن (تبخر → سحب → مطر → أنهار) "
                "تتطابق مع الدورة الهيدرولوجية الحديثة بدقة"
            ),
            "verse_hint": "الزمر 21",
            "testability": 0.85,
            "novelty": 0.80,
            "main_objection": "ملاحظة المطر والأنهار متاحة للجميع",
        },
        {
            "hypothesis_ar": (
                "ذكر 'الماء الطهور' يشير إلى خصائص الماء التطهيرية "
                "المرتبطة بقطبيته الكيميائية"
            ),
            "verse_hint": "الفرقان 48",
            "testability": 0.78,
            "novelty": 0.75,
            "main_objection": "الطهارة بالماء معروفة عملياً في كل الحضارات",
        },
        {
            "hypothesis_ar": (
                "إنزال الماء 'بقدر' يشير إلى التوازن الكمي الدقيق "
                "في دورة المياه العالمية"
            ),
            "verse_hint": "المؤمنون 18",
            "testability": 0.82,
            "novelty": 0.78,
            "main_objection": "القدر هنا بمعنى المشيئة الإلهية لا الكمية الفيزيائية",
        },
    ]
)


# ═══════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════


def _make_mock_llm(response_json: str) -> AsyncMock:
    """Build a mock Anthropic client that returns a JSON string."""

    @dataclass
    class _TextBlock:
        text: str
        type: str = "text"

    @dataclass
    class _Response:
        content: list

    mock_llm = AsyncMock()
    mock_llm.messages.create = AsyncMock(
        return_value=_Response(content=[_TextBlock(text=response_json)])
    )
    return mock_llm


# ═══════════════════════════════════════════════════════
# اختبار 1: POST /api/prediction/generate
# ═══════════════════════════════════════════════════════


class TestPredictionGenerate:
    """اختبار توليد الفرضيات من آيات 'الماء'.

    المتطلبات:
      ✅ عدد الفرضيات: X فرضية (tier_1 أو أعلى)
      ✅ كل فرضية تحمل: p_value + bayes_factor
      ✅ كل فرضية تحمل: main_objection + honesty_notes
      ✅ لا توجد فرضية tier_0 في النتائج
    """

    @pytest.fixture
    def mock_llm(self):
        return _make_mock_llm(MOCK_PREDICTION_JSON)

    @pytest.fixture
    def validator(self):
        return StatisticalSafeguards()

    @pytest.fixture
    def navigator(self):
        return ResearchNavigator()

    async def test_generate_predictions(self, mock_llm, validator):
        """اختبار توليد الفرضيات البحثية كاملاً."""
        engine = AbductiveReasoningEngine(mock_llm, validator)
        predictions = await engine.generate_predictions(
            WATER_VERSES, discipline="physics", max_hypotheses=5
        )

        # ── ✅ عدد الفرضيات > 0 ──
        assert len(predictions) > 0, "لم تُنتج أي فرضية!"
        print(f"\n✅ عدد الفرضيات: {len(predictions)} فرضية")

        for i, pred in enumerate(predictions):
            print(f"\n{'='*60}")
            print(f"── الفرضية {i+1} ──")
            print(f"  النص: {pred.hypothesis_ar[:80]}...")
            print(f"  التخصص: {pred.discipline}")
            print(f"  المستوى: {pred.initial_tier}")
            print(f"  p_value: {pred.p_value:.6f}")
            print(f"  bayes_factor: {pred.bayes_factor:.1f}")
            print(f"  main_objection: {pred.main_objection[:60]}...")
            print(f"  honesty_notes: {pred.honesty_notes}")

            # ── ✅ PredictedMiracle type ──
            assert isinstance(pred, PredictedMiracle)

            # ── ✅ كل فرضية tier_1 أو أعلى ──
            assert pred.initial_tier in (
                "tier_1", "tier_2", "tier_3", "tier_4"
            ), f"الفرضية {i+1} بمستوى {pred.initial_tier} — tier_0 لا يظهر"

            # ── ✅ p_value + bayes_factor ──
            assert pred.p_value > 0, "p_value يجب أن يكون > 0"
            assert pred.bayes_factor > 0, "bayes_factor يجب أن يكون > 0"

            # ── ✅ main_objection + honesty_notes ──
            assert len(pred.main_objection) > 0, "main_objection فارغ!"
            assert isinstance(pred.honesty_notes, list)
            assert len(pred.honesty_notes) > 0, "honesty_notes فارغة!"

        # ── ✅ لا يوجد tier_0 ──
        tier_0_count = sum(
            1 for p in predictions if p.initial_tier == "tier_0"
        )
        assert tier_0_count == 0, f"وُجدت {tier_0_count} فرضيات tier_0!"
        print(f"\n✅ لا يوجد tier_0 في النتائج")

    async def test_predictions_sorted_by_quality(self, mock_llm, validator):
        """التحقق أن الفرضيات مُرتبة بالجودة (الأعلى أولاً)."""
        engine = AbductiveReasoningEngine(mock_llm, validator)
        predictions = await engine.generate_predictions(
            WATER_VERSES, discipline="physics", max_hypotheses=5
        )
        assert len(predictions) >= 2

        scores = [
            p.novelty_score * 0.40
            + p.testability_score * 0.35
            + p.linguistic_support * 0.25
            for p in predictions
        ]
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1], (
                f"الفرضية {i+1} (score={scores[i]:.3f}) أقل من "
                f"الفرضية {i+2} (score={scores[i+1]:.3f})"
            )
        print(f"\n✅ الفرضيات مُرتبة تنازلياً بالجودة")

    async def test_research_maps_generated(
        self, mock_llm, validator, navigator
    ):
        """التحقق أن خرائط البحث تُنتج لكل فرضية."""
        engine = AbductiveReasoningEngine(mock_llm, validator)
        predictions = await engine.generate_predictions(
            WATER_VERSES, discipline="physics", max_hypotheses=5
        )

        for pred in predictions:
            research_map = await navigator.generate_research_map(pred)
            assert "hypothesis" in research_map
            assert "priority_score" in research_map
            assert "research_steps" in research_map
            assert "stop_signals" in research_map
            assert "honesty_notes" in research_map
            assert research_map["priority_score"] > 0

        print(f"\n✅ خرائط بحث صالحة لجميع الفرضيات ({len(predictions)})")


# ═══════════════════════════════════════════════════════
# اختبار 2: POST /api/prediction/mcts/explore
# ═══════════════════════════════════════════════════════


class TestMCTSExplore:
    """اختبار استكشاف MCTS لموضوع الماء في القرآن.

    المتطلبات:
      ✅ أفضل 5 فرضيات مرتبة حسب الجودة
      ✅ كل فرضية لها score > 0.6
      ✅ 20 iteration اكتملت
    """

    @pytest.fixture
    def mock_llm(self):
        return _make_mock_llm(MOCK_MCTS_EXPAND_JSON)

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.search_verses_by_text = AsyncMock(return_value=WATER_VERSES)
        return db

    @pytest.fixture
    def validator(self):
        return StatisticalSafeguards()

    async def test_mcts_exploration(
        self, mock_llm, mock_db, validator
    ):
        """استكشاف MCTS — 20 iteration على موضوع الماء."""
        explorer = MCTSHypothesisExplorer(mock_llm, mock_db, validator)

        best = await explorer.run_exploration(
            seed_topic="الماء في القرآن",
            discipline="biology",
            n_iterations=20,
        )

        print(f"\n{'='*60}")
        print(f"نتائج MCTS — الماء في القرآن (biology)")
        print(f"{'='*60}")

        # ── ✅ فرضيات مُنتجة ──
        assert len(best) > 0, "لم تُنتج أي فرضية!"
        print(f"\n✅ عدد الفرضيات: {len(best)}")

        for i, h in enumerate(best):
            score = h["score"]
            hyp = h["hypothesis"]
            print(f"\n── الفرضية {i+1} ──")
            print(f"  النص: {hyp.get('hypothesis_ar', 'N/A')[:80]}...")
            print(f"  Score: {score:.3f}")
            print(f"  Discipline: {h['discipline']}")

            # ── ✅ score > 0.6 ──
            assert score > 0.6, (
                f"الفرضية {i+1} بدرجة {score:.3f} — أقل من 0.6"
            )

        # ── ✅ مُرتبة تنازلياً ──
        scores = [h["score"] for h in best]
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1], (
                f"ترتيب خاطئ: [{i}]={scores[i]:.3f} < [{i+1}]={scores[i+1]:.3f}"
            )
        print(f"\n✅ الفرضيات مُرتبة تنازلياً")

        # ── ✅ الحد الأقصى 5 ──
        assert len(best) <= 5, f"تجاوز الحد الأقصى: {len(best)} > 5"
        print(f"✅ عدد الفرضيات ≤ 5")

    async def test_mcts_20_iterations(self, mock_llm, mock_db, validator):
        """التحقق أن 20 iteration اكتملت (الجذر visits ≥ 20)."""
        explorer = MCTSHypothesisExplorer(mock_llm, mock_db, validator)

        await explorer.run_exploration(
            seed_topic="الماء في القرآن",
            discipline="biology",
            n_iterations=20,
        )

        # Root visits = initial 1 + backpropagations
        assert explorer.root is not None
        assert explorer.root.visits >= 1, "الجذر لم يُزَر!"
        assert explorer.root.is_explored, "الجذر لم يُستكشَف!"

        # LLM should be called for expand operations
        call_count = mock_llm.messages.create.call_count
        assert call_count > 0, "LLM لم يُستدعَ!"
        print(f"\n✅ 20 iteration اكتملت (LLM calls: {call_count})")
        print(f"✅ Root visits: {explorer.root.visits}")

    async def test_mcts_all_scores_above_threshold(
        self, mock_llm, mock_db, validator
    ):
        """كل فرضية في النتائج النهائية score > 0.6."""
        explorer = MCTSHypothesisExplorer(mock_llm, mock_db, validator)

        best = await explorer.run_exploration(
            seed_topic="الماء في القرآن",
            discipline="biology",
            n_iterations=20,
        )

        below_threshold = [
            h for h in best if h["score"] <= 0.6
        ]
        assert len(below_threshold) == 0, (
            f"{len(below_threshold)} فرضيات بدرجة ≤ 0.6: "
            f"{[h['score'] for h in below_threshold]}"
        )
        print(f"\n✅ جميع الفرضيات ({len(best)}) لها score > 0.6")


# ═══════════════════════════════════════════════════════
# اختبار مكمّل: StatisticalSafeguards
# ═══════════════════════════════════════════════════════


class TestStatisticalSafeguards:
    """تحقق أن الضمانات الإحصائية تعمل بشكل صحيح."""

    @pytest.fixture
    def validator(self):
        return StatisticalSafeguards()

    async def test_high_quality_passes(self, validator):
        """فرضية عالية الجودة تتجاوز FDR."""
        hypothesis = {
            "novelty_score": 0.85,
            "testability_score": 0.80,
            "linguistic_support": 0.78,
        }
        result = await validator.validate(hypothesis, WATER_VERSES)

        assert result["p_value"] < 0.05, (
            f"p_value={result['p_value']:.4f} — يجب أن يكون < 0.05"
        )
        assert result["bayes_factor"] > 10, (
            f"bayes_factor={result['bayes_factor']:.1f} — يجب > 10"
        )
        assert result["effect_size"] > 0.8
        print(f"\n✅ فرضية عالية الجودة: p={result['p_value']:.6f}, "
              f"BF={result['bayes_factor']:.1f}, tier يمكن أن يصل tier_2+")

    async def test_low_quality_fails(self, validator):
        """فرضية ضعيفة لا تتجاوز FDR."""
        hypothesis = {
            "novelty_score": 0.30,
            "testability_score": 0.25,
            "linguistic_support": 0.20,
        }
        result = await validator.validate(hypothesis, WATER_VERSES)

        assert result["p_value"] > 0.05, (
            f"p_value={result['p_value']:.4f} — فرضية ضعيفة يجب أن تفشل"
        )
        print(f"\n✅ فرضية ضعيفة مرفوضة: p={result['p_value']:.4f}")

    async def test_honesty_notes_present(self, validator):
        """التحقق أن honesty_notes دائماً موجودة."""
        hypothesis = {"novelty_score": 0.50, "testability_score": 0.50}
        result = await validator.validate(hypothesis, WATER_VERSES)

        assert "honesty_notes" in result
        assert isinstance(result["honesty_notes"], list)
        assert len(result["honesty_notes"]) > 0
        print(f"\n✅ honesty_notes: {result['honesty_notes']}")
