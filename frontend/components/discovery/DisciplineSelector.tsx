interface Discipline {
  id: string;
  label: string;
}

interface DisciplineSelectorProps {
  disciplines: Discipline[];
  selected: string[];
  onToggle: (id: string) => void;
}

export function DisciplineSelector({
  disciplines,
  selected,
  onToggle,
}: DisciplineSelectorProps) {
  return (
    <div
      style={{
        display: "flex",
        gap: "12px",
        flexWrap: "wrap",
      }}
    >
      {disciplines.map((d) => (
        <button
          key={d.id}
          onClick={() => onToggle(d.id)}
          style={{
            padding: "8px 16px",
            borderRadius: "20px",
            border: "1px solid var(--color-gold)",
            background: selected.includes(d.id)
              ? "var(--color-gold)"
              : "transparent",
            color: selected.includes(d.id) ? "#000" : "var(--color-gold)",
            cursor: "pointer",
            fontSize: "14px",
          }}
        >
          {d.label}
        </button>
      ))}
    </div>
  );
}
