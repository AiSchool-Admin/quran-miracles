import Link from "next/link";

export default function HomePage() {
  return (
    <main
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        position: "relative",
      }}
    >
      <div className="stars-bg" />

      <div style={{ position: "relative", zIndex: 1, textAlign: "center" }}>
        <h1
          className="quran-text"
          style={{
            fontSize: "48px",
            color: "var(--color-gold)",
            marginBottom: "16px",
          }}
        >
          معجزات القرآن الكريم
        </h1>

        <p
          style={{
            fontSize: "20px",
            color: "var(--color-text)",
            opacity: 0.7,
            marginBottom: "48px",
          }}
        >
          استكشاف مستمر بالذكاء الاصطناعي
        </p>

        <Link
          href="/discovery"
          style={{
            display: "inline-block",
            padding: "16px 48px",
            background: "var(--color-gold)",
            color: "#000",
            borderRadius: "8px",
            fontSize: "20px",
            fontWeight: 700,
            textDecoration: "none",
            transition: "opacity 0.2s",
          }}
        >
          ابدأ الاستكشاف
        </Link>
      </div>
    </main>
  );
}
