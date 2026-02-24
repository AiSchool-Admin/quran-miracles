import SectionTitle from "@/components/ui/SectionTitle";
import MiracleCard from "@/components/ui/MiracleCard";
import QuranVerse from "@/components/ui/QuranVerse";
import { numericalMiracles } from "@/lib/data/numerical";

export const metadata = {
  title: "المعجزات العددية | معجزات القرآن الكريم",
  description: "الأنماط الرياضية والتناسق العددي المذهل في القرآن الكريم",
};

export default function NumericalPage() {
  return (
    <div className="py-12">
      <div className="container-main">
        <SectionTitle
          title="المعجزات العددية"
          subtitle="الأنماط الرياضية والتناسق العددي المذهل في القرآن الكريم"
        />

        <QuranVerse
          verse="﴿ وَكُلَّ شَيْءٍ أَحْصَيْنَاهُ كِتَابًا ﴾"
          surah="سورة النبأ"
          ayah="٢٩"
        />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-10">
          {numericalMiracles.map((miracle) => (
            <MiracleCard
              key={miracle.id}
              title={miracle.title}
              description={miracle.description}
              icon="🔢"
            />
          ))}
        </div>
      </div>
    </div>
  );
}
