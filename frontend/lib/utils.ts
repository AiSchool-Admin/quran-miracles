import { type ClassValue, clsx } from "clsx";

export function cn(...inputs: ClassValue[]) {
  return inputs.join(" ");
}

export function formatArabicNumber(num: number): string {
  return num.toLocaleString("ar-SA");
}

export function getTierLabel(tier: string): string {
  const labels: Record<string, string> = {
    tier_0: "نمط أولي",
    tier_1: "فرضية مبدئية",
    tier_2: "ارتباط محتمل",
    tier_3: "نتيجة موثقة",
    tier_4: "اكتشاف مؤكد",
  };
  return labels[tier] || tier;
}

export function getTierColor(tier: string): string {
  const colors: Record<string, string> = {
    tier_0: "text-red-500",
    tier_1: "text-orange-500",
    tier_2: "text-yellow-500",
    tier_3: "text-green-500",
    tier_4: "text-emerald-600",
  };
  return colors[tier] || "text-gray-500";
}
