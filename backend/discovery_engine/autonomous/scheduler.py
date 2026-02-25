"""المحرك المستقل — يعمل 24/7 في الخلفية.

الجدول الزمني:
- كل 6 ساعات: MCTS على موضوع جديد
- يومياً الساعة 2 صباحاً: مسح الأنماط العددية
- كل أحد: تقرير أسبوعي
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler


class AutonomousDiscoveryScheduler:
    """يعمل 24/7 بدون تدخل المستخدم."""

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
        self.engine = engine
        self.db = db
        self.notifier = notifier
        self.scheduler = AsyncIOScheduler()
        self.topic_idx = 0

    def start(self):
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
        print("✅ المحرك المستقل يعمل في الخلفية")

    async def _run_mcts_session(self):
        topic = self.TOPICS_QUEUE[
            self.topic_idx % len(self.TOPICS_QUEUE)
        ]
        self.topic_idx += 1

        print(f"🔍 MCTS: {topic['topic']}")

        try:
            from discovery_engine.mcts.hypothesis_explorer import (
                MCTSHypothesisExplorer,
            )
            from discovery_engine.prediction.statistical_safeguards import (
                StatisticalSafeguards,
            )

            llm = self.engine.llm if hasattr(self.engine, "llm") else self.engine

            explorer = MCTSHypothesisExplorer(
                llm, self.db, StatisticalSafeguards()
            )

            results = await explorer.run_exploration(
                topic["topic"],
                topic["discipline"],
                n_iterations=15,
            )

            # احفظ في DB
            if self.db is not None and hasattr(self.db, "pool") and self.db.pool:
                for r in results:
                    if r["score"] > 0.7:
                        await self.db.pool.execute(
                            """
                            INSERT INTO discoveries
                              (query, confidence_tier,
                               synthesis, quality_score)
                            VALUES ($1, $2, $3, $4)
                            ON CONFLICT DO NOTHING
                            """,
                            topic["topic"],
                            "tier_1",
                            str(r["hypothesis"]),
                            r["score"],
                        )

            print(f"✅ MCTS أنتج {len(results)} فرضية")
        except Exception as e:
            print(f"⚠️ خطأ في MCTS: {e}")

    async def _scan_numerical_patterns(self):
        print("🔢 مسح الأنماط العددية...")
        # placeholder للتنفيذ المستقبلي

    async def _generate_weekly_report(self):
        print("📊 تقرير أسبوعي...")
        try:
            if self.db is not None and hasattr(self.db, "pool") and self.db.pool:
                count = await self.db.pool.fetchval(
                    "SELECT COUNT(*) FROM discoveries "
                    "WHERE created_at > NOW() - INTERVAL '7 days'"
                )
                print(f"✅ اكتشافات هذا الأسبوع: {count}")
            else:
                print("⚠️ قاعدة البيانات غير متاحة — تخطي التقرير")
        except Exception as e:
            print(f"⚠️ خطأ في التقرير: {e}")
