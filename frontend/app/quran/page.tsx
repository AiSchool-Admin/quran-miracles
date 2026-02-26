"use client";

import { useEffect, useState } from "react";
import { VerseCard } from "@/components/quran/VerseCard";
import type { Verse } from "@/types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/** Static surah metadata — used as the source of truth for the index. */
const SURAH_NAMES: { number: number; name: string; verses: number; type: string }[] = [
  { number: 1, name: "الفاتحة", verses: 7, type: "مكية" },
  { number: 2, name: "البقرة", verses: 286, type: "مدنية" },
  { number: 3, name: "آل عمران", verses: 200, type: "مدنية" },
  { number: 4, name: "النساء", verses: 176, type: "مدنية" },
  { number: 5, name: "المائدة", verses: 120, type: "مدنية" },
  { number: 6, name: "الأنعام", verses: 165, type: "مكية" },
  { number: 7, name: "الأعراف", verses: 206, type: "مكية" },
  { number: 8, name: "الأنفال", verses: 75, type: "مدنية" },
  { number: 9, name: "التوبة", verses: 129, type: "مدنية" },
  { number: 10, name: "يونس", verses: 109, type: "مكية" },
  { number: 11, name: "هود", verses: 123, type: "مكية" },
  { number: 12, name: "يوسف", verses: 111, type: "مكية" },
  { number: 13, name: "الرعد", verses: 43, type: "مدنية" },
  { number: 14, name: "إبراهيم", verses: 52, type: "مكية" },
  { number: 15, name: "الحجر", verses: 99, type: "مكية" },
  { number: 16, name: "النحل", verses: 128, type: "مكية" },
  { number: 17, name: "الإسراء", verses: 111, type: "مكية" },
  { number: 18, name: "الكهف", verses: 110, type: "مكية" },
  { number: 19, name: "مريم", verses: 98, type: "مكية" },
  { number: 20, name: "طه", verses: 135, type: "مكية" },
  { number: 21, name: "الأنبياء", verses: 112, type: "مكية" },
  { number: 22, name: "الحج", verses: 78, type: "مدنية" },
  { number: 23, name: "المؤمنون", verses: 118, type: "مكية" },
  { number: 24, name: "النور", verses: 64, type: "مدنية" },
  { number: 25, name: "الفرقان", verses: 77, type: "مكية" },
  { number: 26, name: "الشعراء", verses: 227, type: "مكية" },
  { number: 27, name: "النمل", verses: 93, type: "مكية" },
  { number: 28, name: "القصص", verses: 88, type: "مكية" },
  { number: 29, name: "العنكبوت", verses: 69, type: "مكية" },
  { number: 30, name: "الروم", verses: 60, type: "مكية" },
  { number: 31, name: "لقمان", verses: 34, type: "مكية" },
  { number: 32, name: "السجدة", verses: 30, type: "مكية" },
  { number: 33, name: "الأحزاب", verses: 73, type: "مدنية" },
  { number: 34, name: "سبأ", verses: 54, type: "مكية" },
  { number: 35, name: "فاطر", verses: 45, type: "مكية" },
  { number: 36, name: "يس", verses: 83, type: "مكية" },
  { number: 37, name: "الصافات", verses: 182, type: "مكية" },
  { number: 38, name: "ص", verses: 88, type: "مكية" },
  { number: 39, name: "الزمر", verses: 75, type: "مكية" },
  { number: 40, name: "غافر", verses: 85, type: "مكية" },
  { number: 41, name: "فصلت", verses: 54, type: "مكية" },
  { number: 42, name: "الشورى", verses: 53, type: "مكية" },
  { number: 43, name: "الزخرف", verses: 89, type: "مكية" },
  { number: 44, name: "الدخان", verses: 59, type: "مكية" },
  { number: 45, name: "الجاثية", verses: 37, type: "مكية" },
  { number: 46, name: "الأحقاف", verses: 35, type: "مكية" },
  { number: 47, name: "محمد", verses: 38, type: "مدنية" },
  { number: 48, name: "الفتح", verses: 29, type: "مدنية" },
  { number: 49, name: "الحجرات", verses: 18, type: "مدنية" },
  { number: 50, name: "ق", verses: 45, type: "مكية" },
  { number: 51, name: "الذاريات", verses: 60, type: "مكية" },
  { number: 52, name: "الطور", verses: 49, type: "مكية" },
  { number: 53, name: "النجم", verses: 62, type: "مكية" },
  { number: 54, name: "القمر", verses: 55, type: "مكية" },
  { number: 55, name: "الرحمن", verses: 78, type: "مدنية" },
  { number: 56, name: "الواقعة", verses: 96, type: "مكية" },
  { number: 57, name: "الحديد", verses: 29, type: "مدنية" },
  { number: 58, name: "المجادلة", verses: 22, type: "مدنية" },
  { number: 59, name: "الحشر", verses: 24, type: "مدنية" },
  { number: 60, name: "الممتحنة", verses: 13, type: "مدنية" },
  { number: 61, name: "الصف", verses: 14, type: "مدنية" },
  { number: 62, name: "الجمعة", verses: 11, type: "مدنية" },
  { number: 63, name: "المنافقون", verses: 11, type: "مدنية" },
  { number: 64, name: "التغابن", verses: 18, type: "مدنية" },
  { number: 65, name: "الطلاق", verses: 12, type: "مدنية" },
  { number: 66, name: "التحريم", verses: 12, type: "مدنية" },
  { number: 67, name: "الملك", verses: 30, type: "مكية" },
  { number: 68, name: "القلم", verses: 52, type: "مكية" },
  { number: 69, name: "الحاقة", verses: 52, type: "مكية" },
  { number: 70, name: "المعارج", verses: 44, type: "مكية" },
  { number: 71, name: "نوح", verses: 28, type: "مكية" },
  { number: 72, name: "الجن", verses: 28, type: "مكية" },
  { number: 73, name: "المزمل", verses: 20, type: "مكية" },
  { number: 74, name: "المدثر", verses: 56, type: "مكية" },
  { number: 75, name: "القيامة", verses: 40, type: "مكية" },
  { number: 76, name: "الإنسان", verses: 31, type: "مدنية" },
  { number: 77, name: "المرسلات", verses: 50, type: "مكية" },
  { number: 78, name: "النبأ", verses: 40, type: "مكية" },
  { number: 79, name: "النازعات", verses: 46, type: "مكية" },
  { number: 80, name: "عبس", verses: 42, type: "مكية" },
  { number: 81, name: "التكوير", verses: 29, type: "مكية" },
  { number: 82, name: "الانفطار", verses: 19, type: "مكية" },
  { number: 83, name: "المطففين", verses: 36, type: "مكية" },
  { number: 84, name: "الانشقاق", verses: 25, type: "مكية" },
  { number: 85, name: "البروج", verses: 22, type: "مكية" },
  { number: 86, name: "الطارق", verses: 17, type: "مكية" },
  { number: 87, name: "الأعلى", verses: 19, type: "مكية" },
  { number: 88, name: "الغاشية", verses: 26, type: "مكية" },
  { number: 89, name: "الفجر", verses: 30, type: "مكية" },
  { number: 90, name: "البلد", verses: 20, type: "مكية" },
  { number: 91, name: "الشمس", verses: 15, type: "مكية" },
  { number: 92, name: "الليل", verses: 21, type: "مكية" },
  { number: 93, name: "الضحى", verses: 11, type: "مكية" },
  { number: 94, name: "الشرح", verses: 8, type: "مكية" },
  { number: 95, name: "التين", verses: 8, type: "مكية" },
  { number: 96, name: "العلق", verses: 19, type: "مكية" },
  { number: 97, name: "القدر", verses: 5, type: "مكية" },
  { number: 98, name: "البينة", verses: 8, type: "مدنية" },
  { number: 99, name: "الزلزلة", verses: 8, type: "مدنية" },
  { number: 100, name: "العاديات", verses: 11, type: "مكية" },
  { number: 101, name: "القارعة", verses: 11, type: "مكية" },
  { number: 102, name: "التكاثر", verses: 8, type: "مكية" },
  { number: 103, name: "العصر", verses: 3, type: "مكية" },
  { number: 104, name: "الهمزة", verses: 9, type: "مكية" },
  { number: 105, name: "الفيل", verses: 5, type: "مكية" },
  { number: 106, name: "قريش", verses: 4, type: "مكية" },
  { number: 107, name: "الماعون", verses: 7, type: "مكية" },
  { number: 108, name: "الكوثر", verses: 3, type: "مكية" },
  { number: 109, name: "الكافرون", verses: 6, type: "مكية" },
  { number: 110, name: "النصر", verses: 3, type: "مدنية" },
  { number: 111, name: "المسد", verses: 5, type: "مكية" },
  { number: 112, name: "الإخلاص", verses: 4, type: "مكية" },
  { number: 113, name: "الفلق", verses: 5, type: "مكية" },
  { number: 114, name: "الناس", verses: 6, type: "مكية" },
];

export default function QuranPage() {
  const [selectedSurah, setSelectedSurah] = useState<number | null>(null);
  const [verses, setVerses] = useState<Verse[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<Verse[]>([]);
  const [searching, setSearching] = useState(false);

  const filteredSurahs = SURAH_NAMES.filter(
    (s) =>
      s.name.includes(searchQuery) ||
      String(s.number).includes(searchQuery),
  );

  useEffect(() => {
    if (selectedSurah === null) return;

    setLoading(true);
    setVerses([]);

    fetch(`${API_BASE}/api/quran/surahs/${selectedSurah}/verses`)
      .then((r) => r.json())
      .then((data) => setVerses(data.verses || []))
      .catch(() => setVerses([]))
      .finally(() => setLoading(false));
  }, [selectedSurah]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setSearching(true);
    setSelectedSurah(null);
    setSearchResults([]);

    try {
      const res = await fetch(
        `${API_BASE}/api/quran/search?q=${encodeURIComponent(searchQuery)}`,
      );
      const data = await res.json();
      setSearchResults(data.results || []);
    } catch {
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const selectedSurahInfo = SURAH_NAMES.find(
    (s) => s.number === selectedSurah,
  );

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "var(--color-bg)",
        display: "flex",
      }}
    >
      {/* Sidebar — Surah list */}
      <aside
        style={{
          width: "320px",
          borderLeft: "1px solid rgba(212, 175, 55, 0.2)",
          padding: "24px",
          overflowY: "auto",
          maxHeight: "calc(100vh - 64px)",
          position: "sticky",
          top: "64px",
        }}
      >
        <h2
          style={{
            color: "var(--color-gold)",
            fontSize: "20px",
            marginBottom: "16px",
            fontFamily: "var(--font-quran)",
          }}
        >
          فهرس السور
        </h2>

        {/* Search input */}
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          placeholder="ابحث في السور أو الآيات..."
          style={{
            width: "100%",
            padding: "10px 14px",
            background: "var(--color-surface)",
            border: "1px solid rgba(212, 175, 55, 0.3)",
            borderRadius: "8px",
            color: "var(--color-text)",
            fontSize: "14px",
            marginBottom: "16px",
            outline: "none",
            direction: "rtl",
          }}
        />

        {/* Surah list */}
        <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
          {filteredSurahs.map((surah) => (
            <button
              key={surah.number}
              onClick={() => {
                setSelectedSurah(surah.number);
                setSearchResults([]);
              }}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
                padding: "10px 12px",
                borderRadius: "8px",
                border: "none",
                background:
                  selectedSurah === surah.number
                    ? "rgba(212, 175, 55, 0.15)"
                    : "transparent",
                color:
                  selectedSurah === surah.number
                    ? "var(--color-gold)"
                    : "var(--color-text)",
                cursor: "pointer",
                textAlign: "right",
                fontSize: "14px",
                width: "100%",
                transition: "background 0.15s",
              }}
            >
              <span
                style={{
                  width: "32px",
                  height: "32px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  borderRadius: "50%",
                  border: "1px solid rgba(212, 175, 55, 0.3)",
                  fontSize: "12px",
                  flexShrink: 0,
                  color: "var(--color-gold)",
                }}
              >
                {surah.number}
              </span>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 500 }}>{surah.name}</div>
                <div style={{ fontSize: "12px", opacity: 0.6 }}>
                  {surah.type} — {surah.verses} آية
                </div>
              </div>
            </button>
          ))}
        </div>
      </aside>

      {/* Main content */}
      <main style={{ flex: 1, padding: "32px", maxWidth: "900px" }}>
        {/* No surah selected */}
        {!selectedSurah && searchResults.length === 0 && (
          <div style={{ textAlign: "center", marginTop: "120px" }}>
            <h1
              style={{
                fontFamily: "var(--font-quran)",
                color: "var(--color-gold)",
                fontSize: "36px",
                marginBottom: "16px",
              }}
            >
              القرآن الكريم
            </h1>
            <p style={{ color: "#888", fontSize: "18px" }}>
              اختر سورة من الفهرس للبدء في القراءة
            </p>
          </div>
        )}

        {/* Search results */}
        {searchResults.length > 0 && (
          <section>
            <h2
              style={{
                color: "var(--color-gold)",
                fontSize: "24px",
                marginBottom: "24px",
                fontFamily: "var(--font-quran)",
              }}
            >
              نتائج البحث ({searchResults.length})
            </h2>
            {searchResults.map((v, i) => (
              <VerseCard key={i} {...v} />
            ))}
          </section>
        )}

        {searching && (
          <p style={{ textAlign: "center", color: "#888", marginTop: "40px" }}>
            جاري البحث...
          </p>
        )}

        {/* Surah verses */}
        {selectedSurahInfo && (
          <section>
            <div style={{ marginBottom: "32px" }}>
              <h2
                style={{
                  fontFamily: "var(--font-quran)",
                  color: "var(--color-gold)",
                  fontSize: "28px",
                  marginBottom: "8px",
                }}
              >
                سورة {selectedSurahInfo.name}
              </h2>
              <p style={{ color: "#888", fontSize: "14px" }}>
                {selectedSurahInfo.type} — {selectedSurahInfo.verses} آية
              </p>
            </div>

            {loading && (
              <p style={{ textAlign: "center", color: "#888" }}>
                جاري تحميل الآيات...
              </p>
            )}

            {!loading && verses.length === 0 && (
              <div
                style={{
                  background: "var(--color-surface)",
                  borderRadius: "12px",
                  padding: "32px",
                  textAlign: "center",
                }}
              >
                <p style={{ color: "#888", marginBottom: "8px" }}>
                  لم يتم تحميل بيانات الآيات بعد
                </p>
                <p style={{ color: "#666", fontSize: "14px" }}>
                  تحتاج إلى تشغيل الخادم الخلفي واستيراد بيانات القرآن من
                  tanzil.net
                </p>
              </div>
            )}

            {verses.map((v, i) => (
              <VerseCard key={i} {...v} />
            ))}
          </section>
        )}
      </main>
    </div>
  );
}
