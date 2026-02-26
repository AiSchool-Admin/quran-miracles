"use client";

import { useState } from "react";
import { VerseCard } from "@/components/quran/VerseCard";
import { TierBadge } from "@/components/ui/TierBadge";

const DISCIPLINES = [
  { id: "physics", label: "فيزياء" },
  { id: "biology", label: "أحياء" },
  { id: "psychology", label: "نفس" },
  { id: "economics", label: "اقتصاد" },
  { id: "sociology", label: "اجتماع" },
  { id: "medicine", label: "طب" },
];

interface Verse {
  surah_number: number;
  verse_number: number;
  text_uthmani: string;
  similarity?: number;
  confidence_tier?: "tier_1" | "tier_2" | "tier_3";
}

interface Finding {
  finding: string;
  confidence_tier: string;
  main_objection?: string;
}

export default function DiscoveryPage() {
  const [query, setQuery] = useState("");
  const [disciplines, setDisciplines] = useState(["physics"]);
  const [stage, setStage] = useState("");
  const [verses, setVerses] = useState<Verse[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [synthesis, setSynthesis] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [qualityScore, setQualityScore] = useState<number | null>(null);

  const toggleDiscipline = (id: string) => {
    setDisciplines((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  };

  const startDiscovery = async () => {
    if (!query.trim()) return;

    setIsLoading(true);
    setVerses([]);
    setFindings([]);
    setSynthesis("");
    setQualityScore(null);
    setStage("جاري البحث...");

    try {
      const response = await fetch(`/api/discovery/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, disciplines, mode: "guided" }),
      });

      const reader = response.body?.getReader();
      if (!reader) return;

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;

          try {
            const data = JSON.parse(line.slice(6));

            switch (data.stage) {
              case "quran_search":
                setStage("أبحث في الآيات القرآنية...");
                break;
              case "quran_found":
                setVerses(data.verses || []);
                setStage(`وجدت ${data.verses?.length || 0} آية`);
                break;
              case "linguistic":
                setStage("أحلل الجذور والبلاغة...");
                break;
              case "science_finding":
                setFindings((prev) => [...prev, data.finding]);
                break;
              case "synthesis_token":
                setSynthesis((prev) => prev + data.token);
                break;
              case "quality_done":
                setQualityScore(data.score);
                break;
              case "complete":
                setStage("اكتمل الاستكشاف");
                if (data.synthesis) setSynthesis(data.synthesis);
                if (data.quality_score) setQualityScore(data.quality_score);
                setIsLoading(false);
                break;
              case "error":
                setStage(data.message || "حدث خطأ في الاتصال بالخادم");
                setIsLoading(false);
                break;
            }
          } catch {
            /* skip malformed lines */
          }
        }
      }
    } catch {
      setStage("حدث خطأ في الاتصال");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "var(--color-bg)",
        padding: "32px",
        maxWidth: "1200px",
        margin: "0 auto",
      }}
    >
      {/* العنوان */}
      <h1
        style={{
          color: "var(--color-gold)",
          fontSize: "32px",
          textAlign: "center",
          marginBottom: "8px",
          fontFamily: "var(--font-quran)",
        }}
      >
        معجزات القرآن الكريم
      </h1>
      <p
        style={{
          color: "#888",
          textAlign: "center",
          marginBottom: "40px",
        }}
      >
        استكشاف مستمر بالذكاء الاصطناعي
      </p>

      {/* مربع الاستعلام */}
      <div style={{ marginBottom: "24px" }}>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="اكتب موضوع البحث... مثال: الماء في القرآن الكريم"
          rows={3}
          style={{
            width: "100%",
            background: "var(--color-surface)",
            border: "1px solid var(--color-gold)",
            borderRadius: "8px",
            padding: "16px",
            color: "var(--color-text)",
            fontSize: "18px",
            resize: "vertical",
            direction: "rtl",
            outline: "none",
          }}
        />
      </div>

      {/* اختيار التخصصات */}
      <div
        style={{
          display: "flex",
          gap: "12px",
          flexWrap: "wrap",
          marginBottom: "24px",
        }}
      >
        {DISCIPLINES.map((d) => (
          <button
            key={d.id}
            onClick={() => toggleDiscipline(d.id)}
            style={{
              padding: "8px 16px",
              borderRadius: "20px",
              border: "1px solid var(--color-gold)",
              background: disciplines.includes(d.id)
                ? "var(--color-gold)"
                : "transparent",
              color: disciplines.includes(d.id) ? "#000" : "var(--color-gold)",
              cursor: "pointer",
              fontSize: "14px",
            }}
          >
            {d.label}
          </button>
        ))}
      </div>

      {/* زر البدء */}
      <button
        onClick={startDiscovery}
        disabled={isLoading || !query.trim()}
        style={{
          width: "100%",
          padding: "16px",
          background: isLoading ? "#333" : "var(--color-gold)",
          color: isLoading ? "#888" : "#000",
          border: "none",
          borderRadius: "8px",
          fontSize: "18px",
          fontWeight: 700,
          cursor: isLoading ? "not-allowed" : "pointer",
          marginBottom: "32px",
        }}
      >
        {isLoading ? `⏳ ${stage}` : "ابدأ الاستكشاف"}
      </button>

      {/* الآيات */}
      {verses.length > 0 && (
        <section style={{ marginBottom: "32px" }}>
          <h2 style={{ color: "var(--color-gold)", marginBottom: "16px" }}>
            الآيات ({verses.length})
          </h2>
          {verses.map((v, i) => (
            <VerseCard key={i} {...v} />
          ))}
        </section>
      )}

      {/* الاكتشافات */}
      {findings.length > 0 && (
        <section style={{ marginBottom: "32px" }}>
          <h2 style={{ color: "var(--color-gold)", marginBottom: "16px" }}>
            الاكتشافات ({findings.length})
          </h2>
          {findings.map((f, i) => (
            <div
              key={i}
              style={{
                background: "var(--color-surface)",
                borderRadius: "8px",
                padding: "16px",
                marginBottom: "12px",
              }}
            >
              <TierBadge tier={f.confidence_tier} />
              <p style={{ margin: "12px 0" }}>{f.finding}</p>
              {f.main_objection && (
                <p style={{ color: "#888", fontSize: "14px" }}>
                  اعتراض: {f.main_objection}
                </p>
              )}
            </div>
          ))}
        </section>
      )}

      {/* التوليف */}
      {synthesis && (
        <section style={{ marginBottom: "32px" }}>
          <h2 style={{ color: "var(--color-gold)", marginBottom: "16px" }}>
            التوليف النهائي
          </h2>
          <div
            style={{
              background: "var(--color-surface)",
              borderRadius: "8px",
              padding: "24px",
              lineHeight: "2",
              whiteSpace: "pre-wrap",
            }}
          >
            {synthesis}
          </div>
          {qualityScore != null && (
            <p
              style={{
                color: "var(--color-gold)",
                marginTop: "8px",
                fontSize: "14px",
              }}
            >
              درجة الجودة: {(qualityScore * 100).toFixed(0)}%
            </p>
          )}
        </section>
      )}
    </div>
  );
}
