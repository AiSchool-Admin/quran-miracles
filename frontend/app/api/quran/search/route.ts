/**
 * GET /api/quran/search?q=...&limit=20
 *
 * Strategy:
 *  1. Try the Python backend (has tsvector + pgvector hybrid search)
 *  2. Fall back to alquran.cloud keyword search (basic)
 */

import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

interface AlQuranMatch {
  number: number;
  text: string;
  numberInSurah: number;
  juz: number;
  page: number;
  surah: { number: number; name: string };
}

export async function GET(request: NextRequest) {
  const q = request.nextUrl.searchParams.get("q") || "";
  const limit = request.nextUrl.searchParams.get("limit") || "20";

  if (q.length < 2) {
    return NextResponse.json(
      { error: "نص البحث يجب أن يكون حرفين على الأقل" },
      { status: 400 },
    );
  }

  // ── 1. Try backend ────────────────────────────────────────
  try {
    const res = await fetch(
      `${BACKEND_URL}/api/quran/search?q=${encodeURIComponent(q)}&limit=${limit}`,
      { signal: AbortSignal.timeout(5000) },
    );
    if (res.ok) {
      const data = await res.json();
      return NextResponse.json(data);
    }
  } catch {
    // Backend unavailable — fall through
  }

  // ── 2. Fallback: alquran.cloud search ─────────────────────
  try {
    const res = await fetch(
      `https://api.alquran.cloud/v1/search/${encodeURIComponent(q)}/all/quran-uthmani`,
      { next: { revalidate: 3600 } },
    );

    if (!res.ok) {
      return NextResponse.json({
        query: q,
        results: [],
        total: 0,
        note: "البحث المتقدم يتطلب تشغيل الخادم الخلفي",
      });
    }

    const json = await res.json();
    const matches: AlQuranMatch[] = json.data?.matches || [];

    const results = matches.slice(0, parseInt(limit, 10)).map((m) => ({
      id: m.number,
      surah_number: m.surah.number,
      verse_number: m.numberInSurah,
      verse_key: `${m.surah.number}:${m.numberInSurah}`,
      text_uthmani: m.text,
      text_simple: m.text,
      text_clean: "",
      similarity: 0.9,
    }));

    return NextResponse.json({
      query: q,
      results,
      total: results.length,
      source: "alquran.cloud",
    });
  } catch {
    return NextResponse.json({
      query: q,
      results: [],
      total: 0,
      error: "فشل الاتصال بجميع المصادر",
    });
  }
}
