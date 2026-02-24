import SectionTitle from "@/components/ui/SectionTitle";
import MiracleCard from "@/components/ui/MiracleCard";
import QuranVerse from "@/components/ui/QuranVerse";
import { linguisticMiracles } from "@/lib/data/linguistic";

export const metadata = {
  title: "المعجزات اللغوية | معجزات القرآن الكريم",
  description: "بلاغة القرآن الكريم وفصاحته التي أعجزت العرب",
};

export default function LinguisticPage() {
  return (
    <div className="py-12">
      <div className="container-main">
        <SectionTitle
          title="المعجزات اللغوية"
          subtitle="بلاغة القرآن الكريم وفصاحته التي أعجزت العرب وتحداهم أن يأتوا بمثله"
        />

        <QuranVerse
          verse="﴿ قُل لَّئِنِ اجْتَمَعَتِ الْإِنسُ وَالْجِنُّ عَلَىٰ أَن يَأْتُوا بِمِثْلِ هَٰذَا الْقُرْآنِ لَا يَأْتُونَ بِمِثْلِهِ وَلَوْ كَانَ بَعْضُهُمْ لِبَعْضٍ ظَهِيرًا ﴾"
          surah="سورة الإسراء"
          ayah="٨٨"
        />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-10">
          {linguisticMiracles.map((miracle) => (
            <MiracleCard
              key={miracle.id}
              title={miracle.title}
              description={miracle.description}
              icon="📖"
            />
          ))}
        </div>
      </div>
    </div>
  );
}
