import { TierBadge } from "@/components/ui/TierBadge";
import type { Prediction } from "@/types";

interface PredictionCardProps {
  prediction: Prediction;
  index: number;
  expanded: boolean;
  onToggleExpand: () => void;
}

export function PredictionCard({
  prediction,
  index,
  expanded,
  onToggleExpand,
}: PredictionCardProps) {
  return (
    <div
      style={{
        background: "var(--color-surface)",
        borderRadius: "12px",
        padding: "24px",
        borderRight: "4px solid var(--color-gold)",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          marginBottom: "12px",
        }}
      >
        <span
          style={{
            color: "var(--color-gold)",
            fontSize: "13px",
            fontWeight: 600,
          }}
        >
          فرضية #{index + 1} — {prediction.discipline}
        </span>
        <TierBadge tier={prediction.confidence_tier} />
      </div>

      {/* Verse */}
      {prediction.verse_text && (
        <p
          className="quran-text"
          style={{
            fontSize: "20px",
            marginBottom: "12px",
            textAlign: "right",
          }}
        >
          {prediction.verse_text}
        </p>
      )}

      {/* Hypothesis */}
      <p
        style={{
          color: "var(--color-text)",
          lineHeight: "1.8",
          marginBottom: "12px",
        }}
      >
        {prediction.hypothesis}
      </p>

      {/* Statistical score */}
      {prediction.statistical_score != null && (
        <div
          style={{
            fontSize: "13px",
            color: "#888",
            marginBottom: "12px",
          }}
        >
          الدرجة الإحصائية:{" "}
          <span style={{ color: "var(--color-gold)" }}>
            {(prediction.statistical_score * 100).toFixed(0)}%
          </span>
        </div>
      )}

      {/* Research steps */}
      {prediction.research_steps && prediction.research_steps.length > 0 && (
        <div style={{ marginTop: "12px" }}>
          <button
            onClick={onToggleExpand}
            style={{
              background: "transparent",
              border: "1px solid rgba(212, 175, 55, 0.3)",
              borderRadius: "6px",
              color: "var(--color-gold)",
              padding: "6px 14px",
              fontSize: "13px",
              cursor: "pointer",
            }}
          >
            {expanded
              ? "إخفاء خطوات البحث"
              : `خطوات البحث (${prediction.research_steps.length})`}
          </button>

          {expanded && (
            <ol
              style={{
                marginTop: "12px",
                paddingRight: "20px",
                color: "#aaa",
                fontSize: "14px",
                lineHeight: "2",
              }}
            >
              {prediction.research_steps.map((step, j) => (
                <li key={j} style={{ marginBottom: "4px" }}>
                  {step}
                </li>
              ))}
            </ol>
          )}
        </div>
      )}

      {/* Disclaimer */}
      {prediction.disclaimer && (
        <div
          style={{
            marginTop: "12px",
            padding: "10px 14px",
            background: "rgba(138, 100, 58, 0.1)",
            borderRadius: "6px",
            fontSize: "13px",
            color: "#a98",
            lineHeight: "1.8",
          }}
        >
          {prediction.disclaimer}
        </div>
      )}
    </div>
  );
}
