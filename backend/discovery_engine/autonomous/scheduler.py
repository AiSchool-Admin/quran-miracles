"""المحرك المستقل — يعمل 24/7 في الخلفية.

الجدول الزمني:
- كل ساعة: فحص الأبحاث العلمية الجديدة
- كل 6 ساعات: MCTS على موضوع جديد
- يومياً الساعة 2 صباحاً: مسح الأنماط العددية
- كل أحد: تقرير أسبوعي

يستخدم AutonomousEngine لتنفيذ المهام الفعلية.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .engine import AutonomousEngine


class AutonomousDiscoveryScheduler:
    """يعمل 24/7 بدون تدخل المستخدم.

    يدير جدول المهام ويوكل التنفيذ لـ AutonomousEngine.
    """

    TOPICS_QUEUE = [
        {"topic": "نسبية الزمن", "discipline": "physics"},
        {"topic": "الأجنة في القرآن", "discipline": "biology"},
        {"topic": "الذكر والصحة النفسية", "discipline": "psychology"},
        {"topic": "العدل الاقتصادي", "discipline": "economics"},
        {"topic": "الكونيات القرآنية", "discipline": "astrophysics"},
        {"topic": "الطب الوقائي", "discipline": "medicine"},
        {"topic": "القيادة والشورى", "discipline": "management"},
        {"topic": "الأنظمة الاجتماعية", "discipline": "sociology"},
    ]

    def __init__(self, engine, db, notifier=None):
        self.graph_engine = engine
        self.db = db
        self.notifier = notifier
        self.scheduler = AsyncIOScheduler()
        self.topic_idx = 0

        # المحرك المستقل — ينفذ المهام الفعلية
        llm = engine.llm if hasattr(engine, "llm") else None
        self.autonomous = AutonomousEngine(db=db, llm=llm)

    def start(self):
        # كل ساعة: فحص الأبحاث
        self.scheduler.add_job(
            self._check_papers,
            "interval",
            hours=1,
            id="paper_check",
        )

        # كل 6 ساعات: MCTS
        self.scheduler.add_job(
            self._run_mcts_session,
            "interval",
            hours=6,
            id="mcts_exploration",
        )

        # يومياً الساعة 2 صباحاً: أنماط عددية
        self.scheduler.add_job(
            self._scan_numerical_patterns,
            "cron",
            hour=2,
            id="numerical_scan",
        )

        # كل أحد: تقرير أسبوعي
        self.scheduler.add_job(
            self._generate_weekly_report,
            "cron",
            day_of_week="sun",
            hour=8,
            id="weekly_report",
        )

        self.scheduler.start()
        print("✅ المحرك المستقل يعمل في الخلفية (4 مهام مجدولة)")

    async def _check_papers(self):
        """فحص الأبحاث العلمية الجديدة."""
        try:
            papers = await self.autonomous.check_new_papers()
            print(f"📄 فحص الأبحاث: {len(papers)} بحث جديد")
        except Exception as e:
            print(f"⚠️ خطأ في فحص الأبحاث: {e}")

    async def _run_mcts_session(self):
        """جلسة MCTS على موضوع من القائمة الدورية."""
        topic = self.TOPICS_QUEUE[
            self.topic_idx % len(self.TOPICS_QUEUE)
        ]
        self.topic_idx += 1

        print(f"🔍 MCTS: {topic['topic']}")

        try:
            result = await self.autonomous.run_mcts_exploration(
                topic["topic"], topic["discipline"]
            )
            count = result.get("hypothesis_count", 0)
            print(f"✅ MCTS أنتج {count} فرضية")
        except Exception as e:
            print(f"⚠️ خطأ في MCTS: {e}")

    async def _scan_numerical_patterns(self):
        """مسح الأنماط العددية."""
        try:
            patterns = await self.autonomous.scan_numerical_patterns()
            print(f"🔢 وُجد {len(patterns)} نمط عددي")
        except Exception as e:
            print(f"⚠️ خطأ في مسح الأنماط: {e}")

    async def _generate_weekly_report(self):
        """التقرير الأسبوعي."""
        try:
            report = await self.autonomous.generate_weekly_report()
            print(f"📊 التقرير: {report.get('new_discoveries', 0)} اكتشاف")
        except Exception as e:
            print(f"⚠️ خطأ في التقرير: {e}")
