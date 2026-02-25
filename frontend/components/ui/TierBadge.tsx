const TIER_CONFIG: Record<string, { label: string; color: string }> = {
  tier_0: { label: "نمط خام", color: "#8A3A3A" },
  tier_1: { label: "فرضية أولية", color: "#C0833A" },
  tier_2: { label: "ارتباط محتمل", color: "#C0C030" },
  tier_3: { label: "نتيجة أولية", color: "#2A7A5A" },
  tier_4: { label: "اكتشاف مؤكد", color: "#1A5A3A" },
};

export function TierBadge({ tier }: { tier: string }) {
  const config = TIER_CONFIG[tier] || TIER_CONFIG["tier_1"];
  return (
    <span
      style={{
        background: config.color,
        color: "white",
        padding: "4px 12px",
        borderRadius: "20px",
        fontSize: "12px",
        fontWeight: 600,
      }}
    >
      {config.label}
    </span>
  );
}
