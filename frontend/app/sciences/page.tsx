"use client";

import { useEffect, useState } from "react";
import { TierBadge } from "@/components/ui/TierBadge";
import type { Discovery } from "@/types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const TIER_FILTERS = [
  { value: "", label: "الكل" },
  { value: "tier_1", label: "فرضية أولية" },
  { value: "tier_2", label: "ارتباط محتمل" },
  { value: "tier_3", label: "نتيجة أولية" },
];

const FIELD_FILTERS = [
  { value: "", label: "جميع العلوم" },
  { value: "physics", label: "فيزياء" },
  { value: "biology", label: "أحياء" },
  { value: "medicine", label: "طب" },
  { value: "astronomy", label: "فلك" },
  { value: "geology", label: "جيولوجيا" },
  { value: "embryology", label: "علم الأجنة" },
  { value: "oceanography", label: "علم المحيطات" },
];

export default function SciencesPage() {
  const [discoveries, setDiscoveries] = useState<Discovery[]>([]);
  const [tierFilter, setTierFilter] = useState("");
  const [fieldFilter, setFieldFilter] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (tierFilter) params.set("tier", tierFilter);

    fetch(`${API_BASE}/api/discovery/discoveries?${params}`)
      .then((r) => r.json())
      .then((data) => setDiscoveries(data.discoveries || []))
      .catch(() => setDiscoveries([]))
      .finally(() => setLoading(false));
  }, [tierFilter]);

  const filteredDiscoveries = fieldFilter
    ? discoveries.filter((d) => d.discipline === fieldFilter)
    : discoveries;

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
          الإعجاز العلمي في القرآن الكريم
        </h1>
        <p style={{ color: "#888", fontSize: "16px", maxWidth: "600px", margin: "0 auto" }}>
          استكشاف الارتباطات بين النص القرآني والاكتشافات العلمية الحديثة — مع
          عرض الاعتراضات بجانب كل ادعاء
        </p>
      </div>

      {/* Filters */}
      <div
        style={{
          display: "flex",
          gap: "24px",
          marginBottom: "32px",
          flexWrap: "wrap",
        }}
      >
        {/* Tier filter */}
        <div>
          <label
            style={{
              display: "block",
              color: "#888",
              fontSize: "13px",
              marginBottom: "8px",
            }}
          >
            مستوى الثقة
          </label>
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            {TIER_FILTERS.map((f) => (
              <button
                key={f.value}
                onClick={() => setTierFilter(f.value)}
                style={{
                  padding: "6px 16px",
                  borderRadius: "20px",
                  border: "1px solid rgba(212, 175, 55, 0.3)",
                  background:
                    tierFilter === f.value
                      ? "var(--color-gold)"
                      : "transparent",
                  color:
                    tierFilter === f.value ? "#000" : "var(--color-text)",
                  cursor: "pointer",
                  fontSize: "13px",
                  fontWeight: tierFilter === f.value ? 600 : 400,
                }}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        {/* Field filter */}
        <div>
          <label
            style={{
              display: "block",
              color: "#888",
              fontSize: "13px",
              marginBottom: "8px",
            }}
          >
            التخصص العلمي
          </label>
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            {FIELD_FILTERS.map((f) => (
              <button
                key={f.value}
                onClick={() => setFieldFilter(f.value)}
                style={{
                  padding: "6px 16px",
                  borderRadius: "20px",
                  border: "1px solid rgba(212, 175, 55, 0.3)",
                  background:
                    fieldFilter === f.value
                      ? "var(--color-gold)"
                      : "transparent",
                  color:
                    fieldFilter === f.value ? "#000" : "var(--color-text)",
                  cursor: "pointer",
                  fontSize: "13px",
                  fontWeight: fieldFilter === f.value ? 600 : 400,
                }}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Stats summary */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: "16px",
          marginBottom: "40px",
        }}
      >
        {[
          {
            label: "اكتشافات مسجلة",
            value: filteredDiscoveries.length,
            color: "var(--color-gold)",
          },
          {
            label: "نتائج أولية (tier_3)",
            value: filteredDiscoveries.filter(
              (d) => d.confidence_tier === "tier_3",
            ).length,
            color: "#2A7A5A",
          },
          {
            label: "ارتباطات محتملة (tier_2)",
            value: filteredDiscoveries.filter(
              (d) => d.confidence_tier === "tier_2",
            ).length,
            color: "#C0C030",
          },
          {
            label: "قيد التحقق",
            value: filteredDiscoveries.filter(
              (d) => d.verification_status === "pending",
            ).length,
            color: "#C0833A",
          },
        ].map((stat) => (
          <div
            key={stat.label}
            style={{
              background: "var(--color-surface)",
              borderRadius: "12px",
              padding: "20px",
              textAlign: "center",
            }}
          >
            <div
              style={{
                fontSize: "32px",
                fontWeight: 700,
                color: stat.color,
                marginBottom: "4px",
              }}
            >
              {stat.value}
            </div>
            <div style={{ fontSize: "13px", color: "#888" }}>{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Loading state */}
      {loading && (
        <p style={{ textAlign: "center", color: "#888" }}>
          جاري تحميل الاكتشافات...
        </p>
      )}

      {/* Empty state */}
      {!loading && filteredDiscoveries.length === 0 && (
        <div
          style={{
            background: "var(--color-surface)",
            borderRadius: "12px",
            padding: "48px",
            textAlign: "center",
          }}
        >
          <h3
            style={{
              color: "var(--color-gold)",
              fontSize: "20px",
              marginBottom: "12px",
            }}
          >
            لا توجد اكتشافات مسجلة بعد
          </h3>
          <p style={{ color: "#888", fontSize: "14px", marginBottom: "8px" }}>
            استخدم محرك الاستكشاف لتوليد ارتباطات علمية جديدة
          </p>
          <p style={{ color: "#666", fontSize: "13px" }}>
            يعمل المحرك المستقل في الخلفية 24/7 لاكتشاف أنماط جديدة
          </p>
        </div>
      )}

      {/* Discovery cards */}
      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {filteredDiscoveries.map((d) => (
          <div
            key={d.id}
            style={{
              background: "var(--color-surface)",
              borderRadius: "12px",
              padding: "24px",
              borderRight: "4px solid",
              borderRightColor:
                d.confidence_tier === "tier_3"
                  ? "#2A7A5A"
                  : d.confidence_tier === "tier_2"
                    ? "#C0C030"
                    : "#C0833A",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
                marginBottom: "12px",
              }}
            >
              <h3
                style={{
                  color: "var(--color-text)",
                  fontSize: "18px",
                  fontWeight: 600,
                }}
              >
                {d.title_ar}
              </h3>
              <TierBadge tier={d.confidence_tier} />
            </div>

            <p
              style={{
                color: "#aaa",
                lineHeight: "1.8",
                marginBottom: "12px",
              }}
            >
              {d.description_ar}
            </p>

            {d.discipline && (
              <span
                style={{
                  display: "inline-block",
                  padding: "4px 12px",
                  borderRadius: "12px",
                  background: "rgba(212, 175, 55, 0.1)",
                  color: "var(--color-gold)",
                  fontSize: "12px",
                  marginLeft: "8px",
                }}
              >
                {d.discipline}
              </span>
            )}

            {d.counter_arguments && (
              <div
                style={{
                  marginTop: "12px",
                  padding: "12px",
                  background: "rgba(138, 58, 58, 0.1)",
                  borderRadius: "8px",
                  fontSize: "13px",
                  color: "#caa",
                }}
              >
                <strong>اعتراض:</strong>{" "}
                {typeof d.counter_arguments === "string"
                  ? d.counter_arguments
                  : JSON.stringify(d.counter_arguments)}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
