import type { Metadata } from "next";
import "./globals.css";
import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";

export const metadata: Metadata = {
  title: "معجزات القرآن الكريم",
  description:
    "موقع شامل لعرض المعجزات العددية والعلمية واللغوية في القرآن الكريم",
  keywords: [
    "القرآن الكريم",
    "معجزات",
    "إعجاز عددي",
    "إعجاز علمي",
    "إعجاز لغوي",
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ar" dir="rtl">
      <body className="min-h-screen flex flex-col">
        <Header />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
