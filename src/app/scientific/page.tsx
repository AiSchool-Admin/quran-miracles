import SectionTitle from "@/components/ui/SectionTitle";
import MiracleCard from "@/components/ui/MiracleCard";
import QuranVerse from "@/components/ui/QuranVerse";
import { scientificMiracles } from "@/lib/data/scientific";

export const metadata = {
  title: "المعجزات العلمية | معجزات القرآن الكريم",
  description: "حقائق علمية ذُكرت في القرآن الكريم وأثبتها العلم الحديث",
};

export default function ScientificPage() {
  return (
    <div className="py-12">
      <div className="container-main">
        <SectionTitle
          title="المعجزات العلمية"
          subtitle="حقائق علمية ذُكرت في القرآن قبل أكثر من ١٤٠٠ عام وأثبتها العلم الحديث"
        />

        <QuranVerse
          verse="﴿ أَفَلَا يَتَدَبَّرُونَ الْقُرْآنَ وَلَوْ كَانَ مِنْ عِندِ غَيْرِ اللَّهِ لَوَجَدُوا فِيهِ اخْتِلَافًا كَثِيرًا ﴾"
          surah="سورة النساء"
          ayah="٨٢"
        />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-10">
          {scientificMiracles.map((miracle) => (
            <MiracleCard
              key={miracle.id}
              title={miracle.title}
              description={miracle.description}
              icon="🔬"
            />
          ))}
        </div>
      </div>
    </div>
  );
}
