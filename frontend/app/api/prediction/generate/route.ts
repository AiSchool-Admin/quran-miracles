/**
 * POST /api/prediction/generate
 *
 * Strategy:
 *  1. Try the Python backend for real AI-powered prediction
 *  2. Fall back to demo mode with realistic pre-built hypotheses
 */

import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
  let body: Record<string, unknown>;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  // ── 1. Try backend ────────────────────────────────────────
  try {
    const res = await fetch(`${BACKEND_URL}/api/prediction/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(30_000),
    });

    if (res.ok) {
      const data = await res.json();
      return NextResponse.json(data);
    }
  } catch {
    // Backend unavailable — fall through to demo mode
  }

  // ── 2. Demo mode — return pre-built predictions ──────────
  const verses = (body.verses as string[]) || [];
  const discipline = String(body.discipline || "physics");

  const predictions = getDemoPredictions(verses, discipline);
  const research_maps = getDemoResearchMaps(predictions);

  return NextResponse.json({
    predictions,
    research_maps,
    total: predictions.length,
    demo: true,
    disclaimer:
      "⚠️ وضع عرض توضيحي — هذه فرضيات مُعدّة مسبقاً للتوضيح. لنتائج حقيقية بالذكاء الاصطناعي، يجب ربط الخادم الخلفي.",
  });
}

/* ═══════════ Demo data generators ═══════════ */

interface DemoPrediction {
  id: string;
  verse_text: string;
  hypothesis: string;
  discipline: string;
  confidence_tier: string;
  statistical_score: number;
  research_steps: string[];
  disclaimer: string;
}

function getDemoPredictions(
  verses: string[],
  discipline: string,
): DemoPrediction[] {
  const hasWater = verses.some(
    (v) => v.includes("ماء") || v.includes("الماء") || v.includes("الْمَآءِ"),
  );

  if (hasWater) {
    return getWaterPredictions(discipline);
  }

  // Discipline-specific defaults
  const byDiscipline: Record<string, () => DemoPrediction[]> = {
    physics: getPhysicsPredictions,
    biology: getBiologyPredictions,
    medicine: getMedicinePredictions,
    psychology: getPsychologyPredictions,
    astronomy: getAstronomyPredictions,
    geology: getGeologyPredictions,
    oceanography: getOceanographyPredictions,
    embryology: getEmbryologyPredictions,
  };

  return (byDiscipline[discipline] || getPhysicsPredictions)();
}

function getWaterPredictions(discipline: string): DemoPrediction[] {
  return [
    {
      id: "demo-water-1",
      verse_text:
        "وَجَعَلْنَا مِنَ ٱلْمَآءِ كُلَّ شَىْءٍ حَىٍّ ۖ أَفَلَا يُؤْمِنُونَ",
      hypothesis:
        "فرضية: الماء ليس فقط وسطاً للتفاعلات الحيوية بل عامل نشط في نشأة الحياة — دراسة حديثة (2023) أظهرت أن الماء في الظروف الحرمائية يحفّز تكوين الببتيدات تلقائياً بدون إنزيمات",
      discipline: discipline || "biology",
      confidence_tier: "tier_2",
      statistical_score: 0.72,
      research_steps: [
        "مراجعة منهجية لأبحاث الكيمياء الحرمائية (hydrothermal chemistry) 2018–2024",
        "تحليل لغوي مقارن لكلمة 'جعلنا' — هل تدل على السببية المباشرة أم الوساطة؟",
        "اختبار فرضية العامل النشط: هل الماء محفّز (catalyst) أم مذيب (solvent) في تجارب Miller-Urey المحدّثة؟",
        "قياس إحصائي: مقارنة الوصف القرآني مع إجماع علمي حالي (meta-analysis)",
        "مراجعة الاعتراضات: ربط الماء بالحياة ملاحظة حسية متاحة لجميع الحضارات",
      ],
      disclaimer:
        "⚠️ فرضية آلية — لم تُراجَع بشريا بعد. الاعتراض الرئيسي: طاليس الملطي (624 ق.م) قال: الماء أصل كل شيء.",
    },
    {
      id: "demo-water-2",
      verse_text:
        "وَٱللَّهُ خَلَقَ كُلَّ دَآبَّةٍ مِّن مَّآءٍ ۖ فَمِنْهُم مَّن يَمْشِى عَلَىٰ بَطْنِهِۦ وَمِنْهُم مَّن يَمْشِى عَلَىٰ رِجْلَيْنِ وَمِنْهُم مَّن يَمْشِى عَلَىٰٓ أَرْبَعٍ",
      hypothesis:
        "فرضية: تصنيف الحركة الثلاثي في الآية (بطن / رجلين / أربع) يُطابق التصنيف البيولوجي الحديث لأنماط locomotion — ولكنه يُغفل الطيران والسباحة عمداً لأن السياق يخص 'الدواب' (ما يدبّ على الأرض)",
      discipline: discipline || "biology",
      confidence_tier: "tier_1",
      statistical_score: 0.58,
      research_steps: [
        "تحليل دلالي لكلمة 'دابة' في القرآن — هل تشمل الطيور والأسماك؟",
        "مقارنة مع تصنيف أرسطو (384 ق.م) لأنماط الحركة الحيوانية",
        "إحصاء: كم نسبة أنواع الحيوانات التي تغطيها الأنماط الثلاثة فعلاً؟",
        "مراجعة تفاسير ابن كثير والرازي لهذه الآية",
      ],
      disclaimer:
        "⚠️ فرضية آلية — التصنيف بسيط ولا يتطلب معرفة متقدمة. أرسطو صنّف الحيوانات بشكل مشابه.",
    },
    {
      id: "demo-water-3",
      verse_text:
        "وَهُوَ ٱلَّذِى خَلَقَ مِنَ ٱلْمَآءِ بَشَرًا فَجَعَلَهُۥ نَسَبًا وَصِهْرًا",
      hypothesis:
        "فرضية: الانتقال من 'الماء' إلى 'نسباً وصهراً' يُشير إلى أن الأساس المائي للخلية هو ما يُمكّن التكاثر الجنسي — 70% من كتلة الخلية ماء، وبدونه لا انقسام خلوي",
      discipline: discipline || "biology",
      confidence_tier: "tier_1",
      statistical_score: 0.45,
      research_steps: [
        "دراسة دور الماء في الانقسام الخلوي (cytokinesis) — هل هو ضروري أم مساعد؟",
        "تحليل بلاغي: هل 'من الماء' تعني المادة الأصلية أم النطفة؟",
        "مقارنة مع معرفة جالينوس (129 م) عن دور السوائل في التكاثر",
        "مراجعة تفسير الشعراوي لدقة التفريق بين 'نسباً' و'صهراً'",
      ],
      disclaimer:
        "⚠️ فرضية آلية — العلاقة بين السوائل والتكاثر معروفة في الطب القديم (جالينوس).",
    },
  ];
}

function getPhysicsPredictions(): DemoPrediction[] {
  return [
    {
      id: "demo-phys-1",
      verse_text:
        "وَٱلسَّمَآءَ بَنَيْنَـٰهَا بِأَيْيدٍ وَإِنَّا لَمُوسِعُونَ",
      hypothesis:
        "فرضية: الصيغة الاسمية 'لَمُوسِعُونَ' تدل على استمرارية التوسع — وهذا يتوافق مع نموذج ΛCDM الذي يُثبت أن تمدد الكون يتسارع بفعل الطاقة المظلمة (اكتشاف 1998، جائزة نوبل 2011)",
      discipline: "physics",
      confidence_tier: "tier_2",
      statistical_score: 0.68,
      research_steps: [
        "تحليل صرفي: مقارنة 'مُوسِعُونَ' (اسم فاعل) مع 'نُوَسِّعُ' (فعل مضارع) — الفرق الدلالي",
        "مراجعة تفاسير ما قبل Hubble (1929): هل فسّر أحد 'موسعون' بمعنى التمدد المستمر؟",
        "تحليل الاعتراض اللغوي: 'موسعون' بمعنى 'قادرون' — مراجعة المعاجم الكلاسيكية",
        "مقارنة إحصائية: احتمال التوافق العشوائي مع نموذج ΛCDM",
        "مراجعة أبحاث الطاقة المظلمة 2020–2024 (DESI results)",
      ],
      disclaimer:
        "⚠️ فرضية آلية — الاعتراض الرئيسي: بعض المفسرين القدامى فسّروا 'موسعون' بمعنى 'قادرون' لا 'نوسّع'.",
    },
    {
      id: "demo-phys-2",
      verse_text:
        "أَوَلَمْ يَرَ ٱلَّذِينَ كَفَرُوٓا۟ أَنَّ ٱلسَّمَـٰوَٰتِ وَٱلْأَرْضَ كَانَتَا رَتْقًا فَفَتَقْنَـٰهُمَا",
      hypothesis:
        "فرضية: وصف 'رتقاً ففتقناهما' (كتلة واحدة ففصلناهما) يتوافق بنيوياً مع نظرية الانفجار العظيم — لكن التفاسير الكلاسيكية فسّرتها بفصل السماء عن الأرض أو نزول المطر",
      discipline: "physics",
      confidence_tier: "tier_1",
      statistical_score: 0.52,
      research_steps: [
        "تحليل لغوي: 'رتق' (الإغلاق/الالتحام) و'فتق' (الفصل/الشق) في المعاجم العربية",
        "مسح شامل للتفاسير الكلاسيكية: كم مفسّراً فسّرها بالانفصال الكوني؟",
        "مقارنة مع أساطير الخلق الأخرى (بابلية، مصرية) — هل الفكرة فريدة؟",
        "تقييم إحصائي: مدى تطابق الوصف مع Big Bang vs تفسيرات أخرى",
      ],
      disclaimer:
        "⚠️ فرضية آلية — أساطير خلق كثيرة تصف فصل السماء عن الأرض (إينوما إيليش البابلية مثلاً).",
    },
  ];
}

function getBiologyPredictions(): DemoPrediction[] {
  return [
    {
      id: "demo-bio-1",
      verse_text:
        "وَأَنزَلَ مِنَ ٱلسَّمَآءِ مَآءً فَأَخْرَجْنَا بِهِۦ أَزْوَٰجًا مِّن نَّبَاتٍ شَتَّىٰ",
      hypothesis:
        "فرضية: وصف النباتات بـ'أزواجاً' يُشير إلى ازدواجية التكاثر النباتي (ذكر/أنثى) — وهو مفهوم لم يُثبت علمياً حتى أعمال Camerarius (1694)",
      discipline: "biology",
      confidence_tier: "tier_2",
      statistical_score: 0.65,
      research_steps: [
        "تحليل لغوي: هل 'أزواج' تعني 'أنواع/أصناف' أم 'ذكر وأنثى'؟ مراجعة المعاجم",
        "مسح التفاسير: كيف فسّر ابن كثير والرازي كلمة 'أزواجاً' هنا؟",
        "مراجعة تاريخية: هل عرف العرب التلقيح النخلي قبل الإسلام؟",
        "تقييم: نسبة النباتات ذات التكاثر الجنسي من إجمالي المملكة النباتية",
      ],
      disclaimer:
        "⚠️ فرضية آلية — العرب عرفوا تلقيح النخل قبل الإسلام، فالفكرة ليست غريبة تماماً عن البيئة.",
    },
  ];
}

function getMedicinePredictions(): DemoPrediction[] {
  return [
    {
      id: "demo-med-1",
      verse_text:
        "يَخْرُجُ مِنۢ بُطُونِهَا شَرَابٌ مُّخْتَلِفٌ أَلْوَٰنُهُۥ فِيهِ شِفَآءٌ لِّلنَّاسِ",
      hypothesis:
        "فرضية: وصف العسل بأنه 'شفاء' يتوافق مع الأبحاث الحديثة عن خصائصه المضادة للبكتيريا (Manuka honey) — لكن استخدام العسل طبياً معروف منذ الحضارة المصرية",
      discipline: "medicine",
      confidence_tier: "tier_1",
      statistical_score: 0.48,
      research_steps: [
        "مراجعة منهجية: أبحاث العسل كمضاد حيوي 2015–2024",
        "تحليل: هل 'شفاء' تعني علاجاً شاملاً أم مساعداً؟",
        "مقارنة تاريخية: استخدام العسل في الطب المصري واليوناني",
        "تقييم إحصائي لفاعلية العسل مقارنة بالمضادات الحيوية التقليدية",
      ],
      disclaimer:
        "⚠️ فرضية آلية — استخدام العسل طبياً موثّق في بردية إيبرس المصرية (1550 ق.م).",
    },
  ];
}

function getPsychologyPredictions(): DemoPrediction[] {
  return [
    {
      id: "demo-psych-1",
      verse_text:
        "أَلَا بِذِكْرِ ٱللَّهِ تَطْمَئِنُّ ٱلْقُلُوبُ",
      hypothesis:
        "فرضية: تأثير الذكر/التأمل الروحي على تقليل القلق يتوافق مع أبحاث mindfulness-based stress reduction (MBSR) — وجدت meta-analysis (2019) أن التأمل يُقلل الكورتيزول بنسبة 23%",
      discipline: "psychology",
      confidence_tier: "tier_1",
      statistical_score: 0.55,
      research_steps: [
        "مراجعة أبحاث MBSR وتأثيرها على مستويات القلق والكورتيزول",
        "تحليل: هل 'طمأنينة القلوب' تعادل مفهوم stress reduction؟",
        "مقارنة تأثير الذكر الإسلامي تحديداً مع أشكال التأمل الأخرى",
        "مراجعة الاعتراض: كل الديانات تدّعي تأثيراً نفسياً إيجابياً للعبادة",
      ],
      disclaimer:
        "⚠️ فرضية آلية — تأثير العبادة على الصحة النفسية مشترك بين جميع الديانات.",
    },
  ];
}

function getAstronomyPredictions(): DemoPrediction[] {
  return [
    {
      id: "demo-astro-1",
      verse_text:
        "وَهُوَ ٱلَّذِى خَلَقَ ٱلَّيْلَ وَٱلنَّهَارَ وَٱلشَّمْسَ وَٱلْقَمَرَ ۖ كُلٌّ فِى فَلَكٍ يَسْبَحُونَ",
      hypothesis:
        "فرضية: استخدام 'يسبحون' (حركة ذاتية سلسة في وسط) يتوافق مع مفهوم المدارات الفلكية — واستخدام ضمير الجمع العاقل 'يسبحون' بدل 'تسبح' قد يُشير إلى قوانين فيزيائية محكمة تحكم الحركة",
      discipline: "astronomy",
      confidence_tier: "tier_1",
      statistical_score: 0.56,
      research_steps: [
        "تحليل بلاغي: دلالة 'يسبحون' في المعاجم — هل تدل على المدار الدائري؟",
        "مراجعة: هل 'فلك' في العربية تعني المدار أم القبة السماوية؟",
        "مقارنة مع نموذج بطليموس (150 م) للأفلاك الدائرية",
        "تقييم: مدى تفرّد الوصف القرآني مقارنة بالنماذج الفلكية القديمة",
      ],
      disclaimer:
        "⚠️ فرضية آلية — مفهوم الأفلاك الدائرية معروف منذ بطليموس (القرن الثاني الميلادي).",
    },
  ];
}

function getGeologyPredictions(): DemoPrediction[] {
  return [
    {
      id: "demo-geo-1",
      verse_text:
        "وَأَلْقَىٰ فِى ٱلْأَرْضِ رَوَٰسِىَ أَن تَمِيدَ بِكُمْ",
      hypothesis:
        "فرضية: وصف الجبال بأنها 'رواسي' (مثبّتات) تمنع الأرض من الميد (الاهتزاز) يتوافق مع نظرية isostasy — جذور الجبال تمتد في الوشاح وتُثبّت القشرة الأرضية",
      discipline: "geology",
      confidence_tier: "tier_2",
      statistical_score: 0.62,
      research_steps: [
        "مراجعة نظرية isostasy (Airy-Heiskanen) ودور جذور الجبال",
        "تحليل: هل 'تميد بكم' تعني الزلازل أم دوران الأرض أم شيئاً آخر؟",
        "مراجعة التفاسير الكلاسيكية لمفهوم 'الرواسي'",
        "تقييم علمي: هل الجبال فعلاً تُقلل الزلازل أم أن معظم الزلازل تقع في المناطق الجبلية؟",
      ],
      disclaimer:
        "⚠️ فرضية آلية — الاعتراض العلمي: الزلازل الكبرى تحدث غالباً في المناطق الجبلية (حزام النار).",
    },
  ];
}

function getOceanographyPredictions(): DemoPrediction[] {
  return [
    {
      id: "demo-ocean-1",
      verse_text:
        "مَرَجَ ٱلْبَحْرَيْنِ يَلْتَقِيَانِ ﴿١٩﴾ بَيْنَهُمَا بَرْزَخٌ لَّا يَبْغِيَانِ",
      hypothesis:
        "فرضية: وصف 'البرزخ' بين البحرين يتوافق مع ظاهرة halocline — الحاجز الطبيعي بين مياه مختلفة الملوحة الذي اكتشفه Cousteau",
      discipline: "oceanography",
      confidence_tier: "tier_2",
      statistical_score: 0.66,
      research_steps: [
        "دراسة ظاهرة halocline وpycnocline في مناطق التقاء الأنهار بالبحار",
        "تحليل: هل 'بحرين' تعني بحرين مالحين أم مالح وعذب؟ (الآيات 25:53 vs 55:19)",
        "مراجعة: هل وصف عدم اختلاط المياه معروف لدى البحّارة العرب قبل الإسلام؟",
        "تقييم علمي: مدى دقة وصف 'لا يبغيان' مع الواقع (المياه تختلط فعلاً لكن ببطء)",
      ],
      disclaimer:
        "⚠️ فرضية آلية — البحّارة لاحظوا عدم اختلاط المياه في مصبّات الأنهار قبل الإسلام.",
    },
  ];
}

function getEmbryologyPredictions(): DemoPrediction[] {
  return [
    {
      id: "demo-embryo-1",
      verse_text:
        "ثُمَّ خَلَقْنَا ٱلنُّطْفَةَ عَلَقَةً فَخَلَقْنَا ٱلْعَلَقَةَ مُضْغَةً فَخَلَقْنَا ٱلْمُضْغَةَ عِظَـٰمًا فَكَسَوْنَا ٱلْعِظَـٰمَ لَحْمًا",
      hypothesis:
        "فرضية: تسلسل المراحل الجنينية (نطفة → علقة → مضغة → عظام → لحم) يتوافق جزئياً مع مراحل التطور الجنيني — لكن العظام والعضلات تتكون معاً لا بالتتابع",
      discipline: "embryology",
      confidence_tier: "tier_1",
      statistical_score: 0.50,
      research_steps: [
        "مقارنة مراحل الآية مع مراحل Carnegie للتطور الجنيني",
        "تحليل لغوي: معاني 'علقة' و'مضغة' في المعاجم العربية القديمة",
        "مراجعة: أعمال جالينوس في علم الأجنة ومدى تشابهها مع الوصف القرآني",
        "تقييم الاعتراض الرئيسي: تكوّن العظام والعضلات متزامن في الأسبوع 7–8",
      ],
      disclaimer:
        "⚠️ فرضية آلية — جالينوس وصف مراحل مشابهة. العظام والعضلات تتكون معاً لا بالتتابع.",
    },
  ];
}

/* ═══════════ Research Maps ═══════════ */

function getDemoResearchMaps(
  predictions: DemoPrediction[],
): { hypothesis_id: string; steps: { order: number; title: string; description: string; methodology: string; expected_outcome: string }[] }[] {
  return predictions.map((p) => ({
    hypothesis_id: p.id,
    steps: p.research_steps.map((step, i) => ({
      order: i + 1,
      title: `الخطوة ${i + 1}`,
      description: step,
      methodology:
        i === 0
          ? "مراجعة منهجية للأدبيات"
          : i === 1
            ? "تحليل لغوي مقارن"
            : i === 2
              ? "مقارنة تاريخية"
              : "تقييم إحصائي",
      expected_outcome:
        i < p.research_steps.length - 1
          ? "بيانات تدعم أو تنفي الفرضية"
          : "تحديد مستوى الثقة النهائي",
    })),
  }));
}
