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
      <body className="font-ui antialiased">{children}</body>
    </html>
  );
}
