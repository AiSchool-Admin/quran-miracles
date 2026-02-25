import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "معجزات القرآن الكريم — منصة الاستكشاف بالذكاء الاصطناعي",
  description:
    "أول منصة في العالم تجمع الاستكشاف المستمر الآلي والتنبؤ بالمعجزات المحتملة وتوجيه الباحثين بالذكاء الاصطناعي",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ar" dir="rtl">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600;700&family=Scheherazade+New:wght@400;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
