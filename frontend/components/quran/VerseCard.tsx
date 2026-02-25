import { TierBadge } from "@/components/ui/TierBadge";

interface VerseCardProps {
  surah_number: number;
  verse_number: number;
  text_uthmani: string;
  similarity?: number;
  confidence_tier?: "tier_1" | "tier_2" | "tier_3";
}

export function VerseCard({
  surah_number,
  verse_number,
  text_uthmani,
  similarity,
  confidence_tier,
}: VerseCardProps) {
  return (
    <div
      style={{
        background: "var(--color-surface)",
        border: "1px solid var(--color-gold)",
        borderRadius: "12px",
        padding: "24px",
        marginBottom: "16px",
      }}
    >
      {/* رقم الآية */}
      <div style={{ color: "var(--color-gold)", fontSize: "14px" }}>
        سورة {surah_number} — آية {verse_number}
      </div>

      {/* النص القرآني */}
      <p className="quran-text" style={{ margin: "16px 0" }}>
        {text_uthmani}
      </p>

      {/* درجة التشابه + مستوى الثقة */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "12px",
          flexWrap: "wrap",
        }}
      >
        {similarity != null && (
          <span style={{ fontSize: "12px", color: "#888" }}>
            التشابه: {(similarity * 100).toFixed(1)}%
          </span>
        )}
        {confidence_tier && <TierBadge tier={confidence_tier} />}
      </div>
    </div>
  );
}
