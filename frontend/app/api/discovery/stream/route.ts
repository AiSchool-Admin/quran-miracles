/**
 * POST /api/discovery/stream
 *
 * Strategy:
 *  1. Try the Python backend for real AI-powered discovery
 *  2. Fall back to demo mode with realistic pre-built results
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
    const res = await fetch(`${BACKEND_URL}/api/discovery/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(55_000),
    });

    if (res.ok) {
      return new Response(res.body, {
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache",
          Connection: "keep-alive",
        },
      });
    }
  } catch {
    // Backend unavailable — fall through to demo mode
  }

  // ── 2. Demo mode — simulate SSE stream ────────────────────
  const query = String(body.query || "");
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      const send = (data: Record<string, unknown>) => {
        controller.enqueue(
          encoder.encode(`data: ${JSON.stringify(data)}\n\n`),
        );
      };
      const delay = (ms: number) =>
        new Promise((resolve) => setTimeout(resolve, ms));

      send({ stage: "quran_search" });
      await delay(800);

      const verses = getDemoVerses(query);
      send({ stage: "quran_found", verses });
      await delay(600);

      send({ stage: "linguistic" });
      await delay(1000);

      for (const finding of getDemoFindings(query)) {
        send({ stage: "science_finding", finding });
        await delay(700);
      }

      const synthesis = getDemoSynthesis(query);
      const words = synthesis.split(" ");
      for (let i = 0; i < words.length; i++) {
        send({ stage: "synthesis_token", token: (i > 0 ? " " : "") + words[i] });
        await delay(40);
      }
      await delay(300);

      send({ stage: "quality_done", score: 0.78 });
      await delay(200);

      send({ stage: "complete", synthesis, quality_score: 0.78, demo: true });
      controller.close();
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}

/* ═══════════ Demo data ═══════════ */

function getDemoVerses(query: string) {
  if (query.includes("ماء") || query.includes("الماء")) {
    return [
      { surah_number: 21, verse_number: 30, text_uthmani: "أَوَلَمْ يَرَ ٱلَّذِينَ كَفَرُوٓا۟ أَنَّ ٱلسَّمَـٰوَٰتِ وَٱلْأَرْضَ كَانَتَا رَتْقًا فَفَتَقْنَـٰهُمَا ۖ وَجَعَلْنَا مِنَ ٱلْمَآءِ كُلَّ شَىْءٍ حَىٍّ ۖ أَفَلَا يُؤْمِنُونَ", similarity: 0.95 },
      { surah_number: 24, verse_number: 45, text_uthmani: "وَٱللَّهُ خَلَقَ كُلَّ دَآبَّةٍ مِّن مَّآءٍ ۖ فَمِنْهُم مَّن يَمْشِى عَلَىٰ بَطْنِهِۦ وَمِنْهُم مَّن يَمْشِى عَلَىٰ رِجْلَيْنِ وَمِنْهُم مَّن يَمْشِى عَلَىٰٓ أَرْبَعٍ", similarity: 0.91 },
      { surah_number: 25, verse_number: 54, text_uthmani: "وَهُوَ ٱلَّذِى خَلَقَ مِنَ ٱلْمَآءِ بَشَرًا فَجَعَلَهُۥ نَسَبًا وَصِهْرًا ۗ وَكَانَ رَبُّكَ قَدِيرًا", similarity: 0.88 },
    ];
  }
  return [
    { surah_number: 51, verse_number: 47, text_uthmani: "وَٱلسَّمَآءَ بَنَيْنَـٰهَا بِأَيْيدٍ وَإِنَّا لَمُوسِعُونَ", similarity: 0.92 },
    { surah_number: 21, verse_number: 33, text_uthmani: "وَهُوَ ٱلَّذِى خَلَقَ ٱلَّيْلَ وَٱلنَّهَارَ وَٱلشَّمْسَ وَٱلْقَمَرَ ۖ كُلٌّ فِى فَلَكٍ يَسْبَحُونَ", similarity: 0.89 },
    { surah_number: 36, verse_number: 40, text_uthmani: "لَا ٱلشَّمْسُ يَنۢبَغِى لَهَآ أَن تُدْرِكَ ٱلْقَمَرَ وَلَا ٱلَّيْلُ سَابِقُ ٱلنَّهَارِ ۚ وَكُلٌّ فِى فَلَكٍ يَسْبَحُونَ", similarity: 0.86 },
  ];
}

function getDemoFindings(query: string) {
  if (query.includes("ماء") || query.includes("الماء")) {
    return [
      { finding: "تعبير 'من الماء كل شيء حي' يتوافق مع الاكتشاف العلمي أن الماء ضروري لجميع أشكال الحياة المعروفة — وهو أساس بحث NASA عن الحياة خارج الأرض", confidence_tier: "tier_2", main_objection: "ربط الماء بالحياة ملاحظة حسية متاحة لأي حضارة زراعية — طاليس الملطي (624 ق.م) قال: الماء أصل كل شيء" },
      { finding: "تصنيف الكائنات في الآية 24:45 (يمشي على بطنه / رجلين / أربع) يتوافق مع التصنيف البيولوجي الحديث لأنماط الحركة", confidence_tier: "tier_1", main_objection: "تصنيف بسيط بالملاحظة المباشرة — لا يتطلب معرفة علمية متقدمة" },
      { finding: "خلق البشر 'من الماء' ثم 'نسباً وصهراً' (25:54) يلمح إلى الأساس المائي للتكاثر الجنسي", confidence_tier: "tier_1", main_objection: "العلاقة بين السوائل والتكاثر معروفة في الطب اليوناني (جالينوس)" },
    ];
  }
  return [
    { finding: "تعبير 'وإنا لموسعون' (51:47) يتوافق مع اكتشاف Hubble (1929) لتمدد الكون — الصيغة الاسمية تدل على استمرارية التمدد", confidence_tier: "tier_2", main_objection: "بعض المفسرين فسّروا 'موسعون' بمعنى 'قادرون' — الخلاف اللغوي قائم" },
    { finding: "وصف الأجرام بأنها 'في فلك يسبحون' (21:33) يتوافق مع مفهوم المدارات — 'يسبحون' تصف حركة دائرية في وسط", confidence_tier: "tier_1", main_objection: "الفلك في اللغة يعني المدار الدائري — وصف بلاغي للحركة السلسة" },
  ];
}

function getDemoSynthesis(query: string) {
  if (query.includes("ماء") || query.includes("الماء")) {
    return "التحليل يكشف ثلاثة محاور تربط الآيات القرآنية المتعلقة بالماء بالعلم الحديث:\n\nالأول: مبدأ الماء كأساس للحياة — يتوافق مع البيولوجيا الفلكية التي تضع الماء السائل كشرط أول للبحث عن الحياة. لكن هذا المفهوم كان متاحاً للملاحظة الحسية.\n\nالثاني: تصنيف الكائنات حسب أنماط الحركة — تصنيف بسيط لكنه دقيق بيولوجياً.\n\nالثالث: الربط بين الماء والتكاثر البشري — إشارة لطيفة لكن لا ترقى لمستوى الإعجاز المؤكد.\n\nالخلاصة: ارتباطات علمية حقيقية (tier_1 إلى tier_2) مع اعتراضات مشروعة تمنع الجزم.\n\n⚠️ وضع عرض توضيحي — لنتائج حقيقية بالذكاء الاصطناعي، يجب ربط الخادم الخلفي.";
  }
  return "التحليل يُظهر ارتباطات بين الآيات المدروسة والاكتشافات الحديثة.\n\nالارتباط الأبرز: وصف توسع الكون في سورة الذاريات بصيغة اسمية تدل على الاستمرارية. لكن الاعتراض اللغوي بأن 'موسعون' قد تعني 'قادرون' يظل قائماً.\n\nالمستوى الحالي: فرضية أولية (tier_1) تستحق البحث المتعمق.\n\n⚠️ وضع عرض توضيحي — لنتائج حقيقية بالذكاء الاصطناعي، يجب ربط الخادم الخلفي.";
}
