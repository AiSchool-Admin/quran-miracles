"use client";

import { useState } from "react";
import { TierBadge } from "@/components/ui/TierBadge";
import type { Prediction, ResearchMap } from "@/types";

const DISCIPLINES = [
  { id: "physics", label: "فيزياء" },
  { id: "biology", label: "أحياء" },
  { id: "medicine", label: "طب" },
  { id: "psychology", label: "علم النفس" },
  { id: "astronomy", label: "فلك" },
  { id: "geology", label: "جيولوجيا" },
  { id: "oceanography", label: "علم المحيطات" },
  { id: "embryology", label: "علم الأجنة" },
];

export default function PredictionPage() {
  const [verseInput, setVerseInput] = useState("");
  const [discipline, setDiscipline] = useState("physics");
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [researchMaps, setResearchMaps] = useState<ResearchMap[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [expandedMap, setExpandedMap] = useState<string | null>(null);

  const generatePredictions = async () => {
    if (!verseInput.trim()) return;

    setLoading(true);
    setError("");
    setPredictions([]);
    setResearchMaps([]);

    try {
      const verses = verseInput
        .split("\n")
        .map((v) => v.trim())
        .filter(Boolean);

      const res = await fetch(`/api/prediction/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ verses, discipline }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();
      setPredictions(data.predictions || []);
      setResearchMaps(data.research_maps || []);
    } catch {
      setError("تعذر الاتصال بمحرك التنبؤ — تأكد من تشغيل الخادم الخلفي");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "var(--color-bg)",
        padding: "32px",
        maxWidth: "1000px",
        margin: "0 auto",
      }}
    >
      {/* Header */}
      <div style={{ textAlign: "center", marginBottom: "48px" }}>
        <h1
          style={{
            fontFamily: "var(--font-quran)",
            color: "var(--color-gold)",
            fontSize: "36px",
            marginBottom: "12px",
          }}
        >
          محرك التنبؤ بالمعجزات
        </h1>
        <p
          style={{
            color: "#888",
            fontSize: "16px",
            maxWidth: "600px",
            margin: "0 auto",
            lineHeight: "1.8",
          }}
        >
          توليد فرضيات بحثية من آيات قرآنية باستخدام الاستدلال الاستنتاجي
          (Abductive Reasoning) — مع خرائط بحث وضوابط إحصائية
        </p>
      </div>

      {/* Disclaimer */}
      <div
        style={{
          background: "rgba(192, 131, 58, 0.1)",
          border: "1px solid rgba(192, 131, 58, 0.3)",
          borderRadius: "12px",
          padding: "16px 20px",
          marginBottom: "32px",
          fontSize: "14px",
          color: "#caa",
          lineHeight: "1.8",
        }}
      >
        هذه فرضيات آلية — لم تُراجَع بشريا بعد. كل فرضية تحمل مستواها
        الإحصائي وخارطة التحقق منها. الاعتراضات تُعرض بجانب كل ادعاء.
      </div>

      {/* Input area */}
      <div style={{ marginBottom: "24px" }}>
        <label
          style={{
            display: "block",
            color: "var(--color-gold)",
            fontSize: "14px",
            marginBottom: "8px",
            fontWeight: 500,
          }}
        >
          الآيات القرآنية (آية واحدة في كل سطر)
        </label>
        <textarea
          value={verseInput}
          onChange={(e) => setVerseInput(e.target.value)}
          placeholder={"أدخل نص الآيات هنا...\nمثال: وَجَعَلْنَا مِنَ الْمَاءِ كُلَّ شَيْءٍ حَيٍّ"}
          rows={5}
          style={{
            width: "100%",
            background: "var(--color-surface)",
            border: "1px solid rgba(212, 175, 55, 0.3)",
            borderRadius: "8px",
            padding: "16px",
            color: "var(--color-text)",
            fontSize: "18px",
            fontFamily: "var(--font-quran)",
            lineHeight: "2",
            resize: "vertical",
            direction: "rtl",
            outline: "none",
          }}
        />
      </div>

      {/* Discipline selector */}
      <div style={{ marginBottom: "24px" }}>
        <label
          style={{
            display: "block",
            color: "var(--color-gold)",
            fontSize: "14px",
            marginBottom: "8px",
            fontWeight: 500,
          }}
        >
          التخصص العلمي
        </label>
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
          {DISCIPLINES.map((d) => (
            <button
              key={d.id}
              onClick={() => setDiscipline(d.id)}
              style={{
                padding: "8px 16px",
                borderRadius: "20px",
                border: "1px solid rgba(212, 175, 55, 0.3)",
                background:
                  discipline === d.id ? "var(--color-gold)" : "transparent",
                color: discipline === d.id ? "#000" : "var(--color-text)",
                cursor: "pointer",
                fontSize: "14px",
                fontWeight: discipline === d.id ? 600 : 400,
              }}
            >
              {d.label}
            </button>
          ))}
        </div>
      </div>

      {/* Generate button */}
      <button
        onClick={generatePredictions}
        disabled={loading || !verseInput.trim()}
        style={{
          width: "100%",
          padding: "16px",
          background: loading ? "#333" : "var(--color-gold)",
          color: loading ? "#888" : "#000",
          border: "none",
          borderRadius: "8px",
          fontSize: "18px",
          fontWeight: 700,
          cursor: loading ? "not-allowed" : "pointer",
          marginBottom: "40px",
        }}
      >
        {loading ? "جاري توليد الفرضيات..." : "توليد الفرضيات البحثية"}
      </button>

      {/* Error */}
      {error && (
        <div
          style={{
            background: "rgba(138, 58, 58, 0.15)",
            border: "1px solid rgba(138, 58, 58, 0.3)",
            borderRadius: "8px",
            padding: "16px",
            marginBottom: "24px",
            color: "#e88",
            fontSize: "14px",
          }}
        >
          {error}
        </div>
      )}

      {/* Predictions */}
      {predictions.length > 0 && (
        <section>
          <h2
            style={{
              color: "var(--color-gold)",
              fontSize: "24px",
              marginBottom: "24px",
              fontFamily: "var(--font-quran)",
            }}
          >
            الفرضيات المُولّدة ({predictions.length})
          </h2>

          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "20px",
            }}
          >
            {predictions.map((p, i) => (
              <div
                key={p.id || i}
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
                    فرضية #{i + 1} — {p.discipline}
                  </span>
                  <TierBadge tier={p.confidence_tier} />
                </div>

                {/* Verse */}
                {p.verse_text && (
                  <p
                    className="quran-text"
                    style={{
                      fontSize: "20px",
                      marginBottom: "12px",
                      textAlign: "right",
                    }}
                  >
                    {p.verse_text}
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
                  {p.hypothesis}
                </p>

                {/* Statistical score */}
                {p.statistical_score != null && (
                  <div
                    style={{
                      fontSize: "13px",
                      color: "#888",
                      marginBottom: "12px",
                    }}
                  >
                    الدرجة الإحصائية:{" "}
                    <span style={{ color: "var(--color-gold)" }}>
                      {(p.statistical_score * 100).toFixed(0)}%
                    </span>
                  </div>
                )}

                {/* Research steps */}
                {p.research_steps && p.research_steps.length > 0 && (
                  <div style={{ marginTop: "12px" }}>
                    <button
                      onClick={() =>
                        setExpandedMap(
                          expandedMap === (p.id || String(i))
                            ? null
                            : p.id || String(i),
                        )
                      }
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
                      {expandedMap === (p.id || String(i))
                        ? "إخفاء خطوات البحث"
                        : `خطوات البحث (${p.research_steps.length})`}
                    </button>

                    {expandedMap === (p.id || String(i)) && (
                      <ol
                        style={{
                          marginTop: "12px",
                          paddingRight: "20px",
                          color: "#aaa",
                          fontSize: "14px",
                          lineHeight: "2",
                        }}
                      >
                        {p.research_steps.map((step, j) => (
                          <li key={j} style={{ marginBottom: "4px" }}>
                            {step}
                          </li>
                        ))}
                      </ol>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* MCTS section */}
      <section style={{ marginTop: "64px" }}>
        <div
          style={{
            background: "var(--color-surface)",
            borderRadius: "12px",
            padding: "32px",
            textAlign: "center",
          }}
        >
          <h3
            style={{
              color: "var(--color-gold)",
              fontSize: "20px",
              marginBottom: "8px",
            }}
          >
            استكشاف MCTS المتقدم
          </h3>
          <p
            style={{
              color: "#888",
              fontSize: "14px",
              maxWidth: "500px",
              margin: "0 auto",
              lineHeight: "1.8",
            }}
          >
            يستخدم خوارزمية Monte Carlo Tree Search لاستكشاف مساحة الفرضيات
            بعمق أكبر — يعمل تلقائيا في الخلفية عبر المحرك المستقل
          </p>
        </div>
      </section>
    </div>
  );
}
