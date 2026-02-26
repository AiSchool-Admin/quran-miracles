import { TierBadge } from "@/components/ui/TierBadge";
import type { Finding } from "@/types";

interface DiscoveryCardProps {
  finding: Finding;
}

export function DiscoveryCard({ finding }: DiscoveryCardProps) {
  return (
    <div
      style={{
        background: "var(--color-surface)",
        borderRadius: "8px",
        padding: "16px",
        marginBottom: "12px",
      }}
    >
      <TierBadge tier={finding.confidence_tier} />
      <p style={{ margin: "12px 0" }}>{finding.finding}</p>
      {finding.discipline && (
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
          {finding.discipline}
        </span>
      )}
      {finding.main_objection && (
        <p style={{ color: "#888", fontSize: "14px", marginTop: "8px" }}>
          اعتراض: {finding.main_objection}
        </p>
      )}
    </div>
  );
}
