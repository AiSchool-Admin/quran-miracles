import SectionTitle from "@/components/ui/SectionTitle";
import QuranVerse from "@/components/ui/QuranVerse";

export const metadata = {
  title: "عن الموقع | معجزات القرآن الكريم",
  description: "تعرف على موقع معجزات القرآن الكريم وأهدافه",
};

export default function AboutPage() {
  return (
    <div className="py-12">
      <div className="container-main max-w-4xl">
        <SectionTitle
          title="عن الموقع"
          subtitle="تعرف على رسالتنا وأهدافنا"
        />

        <QuranVerse
          verse="﴿ إِنَّا نَحْنُ نَزَّلْنَا الذِّكْرَ وَإِنَّا لَهُ لَحَافِظُونَ ﴾"
          surah="سورة الحجر"
          ayah="٩"
        />

        <div className="mt-10 space-y-8">
          <div className="miracle-card">
            <h3 className="text-2xl font-bold text-primary-700 mb-4">
              رسالتنا
            </h3>
            <p className="text-lg text-gray-600 leading-relaxed">
              نسعى لتقديم معجزات القرآن الكريم بأسلوب علمي موثق وسهل الفهم،
              ليكون هذا الموقع مرجعاً شاملاً لكل باحث ومهتم بالإعجاز القرآني.
              نؤمن بأن القرآن الكريم كتاب لا تنتهي عجائبه، وأن كل اكتشاف علمي
              جديد يزيدنا يقيناً بعظمته.
            </p>
          </div>

          <div className="miracle-card">
            <h3 className="text-2xl font-bold text-primary-700 mb-4">
              أهدافنا
            </h3>
            <ul className="space-y-3 text-lg text-gray-600">
              <li className="flex items-start gap-3">
                <span className="text-gold-500 mt-1">●</span>
                <span>
                  جمع وتوثيق المعجزات القرآنية من مصادر موثوقة
                </span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-gold-500 mt-1">●</span>
                <span>
                  تقديم المحتوى بطريقة علمية منظمة وسهلة الفهم
                </span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-gold-500 mt-1">●</span>
                <span>
                  إتاحة المحتوى للباحثين والطلاب والمهتمين بالإعجاز القرآني
                </span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-gold-500 mt-1">●</span>
                <span>
                  المساهمة في نشر الوعي بعظمة القرآن الكريم
                </span>
              </li>
            </ul>
          </div>

          <div className="miracle-card">
            <h3 className="text-2xl font-bold text-primary-700 mb-4">
              منهجنا
            </h3>
            <p className="text-lg text-gray-600 leading-relaxed">
              نعتمد في جمع المعلومات على المصادر العلمية الموثوقة وأبحاث
              العلماء المتخصصين في الإعجاز القرآني. نحرص على التدقيق والتحقق
              من كل معلومة قبل نشرها، ونسعى لتحديث المحتوى باستمرار وفقاً
              لأحدث الاكتشافات العلمية.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
