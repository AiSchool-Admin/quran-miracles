/**
 * GET /api/quran/surahs/[surahNumber]/verses
 *
 * Strategy:
 *  1. Try the Python backend first (if BACKEND_URL is set)
 *  2. Fall back to alquran.cloud API (data sourced from tanzil.net)
 */

import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

interface AlQuranAyah {
  number: number;
  text: string;
  numberInSurah: number;
  juz: number;
  manzil: number;
  page: number;
  ruku: number;
  hizbQuarter: number;
  sajda: boolean | { id: number; recommended: boolean; obligatory: boolean };
}

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ surahNumber: string }> },
) {
  const { surahNumber } = await params;
  const num = parseInt(surahNumber, 10);

  if (isNaN(num) || num < 1 || num > 114) {
    return NextResponse.json(
      { error: "رقم السورة يجب أن يكون بين 1 و 114" },
      { status: 400 },
    );
  }

  // ── 1. Try backend ────────────────────────────────────────
  try {
    const res = await fetch(
      `${BACKEND_URL}/api/quran/surahs/${num}/verses`,
      { signal: AbortSignal.timeout(4000) },
    );
    if (res.ok) {
      const data = await res.json();
      if (data.verses && data.verses.length > 0) {
        return NextResponse.json(data);
      }
    }
  } catch {
    // Backend unavailable — fall through to CDN
  }

  // ── 2. Fallback: alquran.cloud (tanzil.net source) ────────
  try {
    const res = await fetch(
      `https://api.alquran.cloud/v1/surah/${num}/quran-uthmani`,
      { next: { revalidate: 86400 } }, // Cache 24h
    );

    if (!res.ok) {
      return NextResponse.json(
        { error: "فشل في جلب البيانات من المصدر الاحتياطي" },
        { status: 502 },
      );
    }

    const json = await res.json();
    const ayahs: AlQuranAyah[] = json.data?.ayahs || [];

    const verses = ayahs.map((a) => ({
      id: a.number,
      surah_number: num,
      verse_number: a.numberInSurah,
      text_uthmani: a.text,
      text_simple: a.text,
      text_clean: null,
      juz: a.juz,
      page_number: a.page,
      word_count: a.text.split(/\s+/).length,
      letter_count: a.text.replace(/\s/g, "").length,
    }));

    return NextResponse.json({
      surah: num,
      verses,
      total: verses.length,
      source: "alquran.cloud",
    });
  } catch {
    return NextResponse.json(
      { error: "فشل الاتصال بجميع المصادر" },
      { status: 503 },
    );
  }
}
