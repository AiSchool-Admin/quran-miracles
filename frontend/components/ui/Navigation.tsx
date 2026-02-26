"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "الرئيسية" },
  { href: "/quran", label: "القرآن الكريم" },
  { href: "/discovery", label: "الاستكشاف" },
  { href: "/sciences", label: "الإعجاز العلمي" },
  { href: "/prediction", label: "محرك التنبؤ" },
];

export function Navigation() {
  const pathname = usePathname();

  return (
    <nav
      style={{
        background: "var(--color-surface)",
        borderBottom: "1px solid rgba(212, 175, 55, 0.2)",
        padding: "0 32px",
        position: "sticky",
        top: 0,
        zIndex: 50,
      }}
    >
      <div
        style={{
          maxWidth: "1400px",
          margin: "0 auto",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          height: "64px",
        }}
      >
        {/* Logo */}
        <Link
          href="/"
          style={{
            fontFamily: "var(--font-quran)",
            color: "var(--color-gold)",
            fontSize: "20px",
            textDecoration: "none",
            fontWeight: 700,
          }}
        >
          معجزات القرآن
        </Link>

        {/* Nav links */}
        <div style={{ display: "flex", gap: "8px" }}>
          {NAV_ITEMS.map((item) => {
            const isActive =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                style={{
                  padding: "8px 16px",
                  borderRadius: "8px",
                  fontSize: "14px",
                  textDecoration: "none",
                  color: isActive ? "#000" : "var(--color-text)",
                  background: isActive ? "var(--color-gold)" : "transparent",
                  fontWeight: isActive ? 600 : 400,
                  transition: "all 0.2s",
                }}
              >
                {item.label}
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
