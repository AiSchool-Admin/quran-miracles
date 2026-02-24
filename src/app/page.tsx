import Link from "next/link";
import SectionTitle from "@/components/ui/SectionTitle";
import MiracleCard from "@/components/ui/MiracleCard";

const categories = [
  {
    title: "المعجزات العددية",
    description:
      "اكتشف الأنماط الرياضية المذهلة والتناسق العددي في القرآن الكريم التي تثبت أنه كتاب من عند الله",
    href: "/numerical",
    icon: "🔢",
    count: "٢٠+",
  },
  {
    title: "المعجزات العلمية",
    description:
      "حقائق علمية ذُكرت في القرآن الكريم قبل أكثر من ١٤٠٠ عام وأثبتها العلم الحديث",
    href: "/scientific",
    icon: "🔬",
    count: "٣٠+",
  },
  {
    title: "المعجزات اللغوية",
    description:
      "بلاغة القرآن الكريم وفصاحته التي أعجزت العرب وتحداهم أن يأتوا بمثله",
    href: "/linguistic",
    icon: "📖",
    count: "١٥+",
  },
];

export default function HomePage() {
  return (
    <div>
      {/* Hero Section */}
      <section className="bg-gradient-to-bl from-primary-700 via-primary-600 to-primary-800 text-white py-20">
        <div className="container-main text-center">
          <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-tight">
            معجزات القرآن الكريم
          </h1>
          <p className="text-xl md:text-2xl text-primary-100 max-w-3xl mx-auto leading-relaxed mb-8">
            رحلة في آيات الله البينات واكتشاف الإعجاز في كتابه العظيم
          </p>
          <div className="quran-verse max-w-2xl mx-auto bg-white/10 border-white/20 text-white">
            <p className="text-2xl md:text-3xl leading-loose">
              ﴿ سَنُرِيهِمْ آيَاتِنَا فِي الْآفَاقِ وَفِي أَنفُسِهِمْ حَتَّىٰ
              يَتَبَيَّنَ لَهُمْ أَنَّهُ الْحَقُّ ﴾
            </p>
            <p className="text-sm mt-3 text-primary-200">سورة فصلت - الآية ٥٣</p>
          </div>
        </div>
      </section>

      {/* Categories Section */}
      <section className="py-16">
        <div className="container-main">
          <SectionTitle
            title="أقسام المعجزات"
            subtitle="استكشف الأنواع المختلفة من الإعجاز القرآني"
          />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-10">
            {categories.map((category) => (
              <Link key={category.href} href={category.href}>
                <MiracleCard
                  title={category.title}
                  description={category.description}
                  icon={category.icon}
                  badge={category.count}
                />
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* About Section */}
      <section className="py-16 bg-gray-50">
        <div className="container-main text-center">
          <h2 className="text-3xl font-bold text-primary-700 mb-6">
            عن هذا الموقع
          </h2>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto leading-relaxed">
            يهدف هذا الموقع إلى جمع وعرض معجزات القرآن الكريم بأسلوب علمي
            موثق، ليكون مرجعاً شاملاً للباحثين والمهتمين بالإعجاز القرآني.
            نسعى لتقديم المحتوى بطريقة سهلة ومنظمة تناسب جميع القراء.
          </p>
          <Link href="/about" className="btn-primary inline-block mt-8">
            اعرف المزيد
          </Link>
        </div>
      </section>
    </div>
  );
}
