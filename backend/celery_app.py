"""Celery application — مهام الخلفية غير المتزامنة.

يربط المهام طويلة المدة بنظام الطوابير:
- استكشاف MCTS (قد يستغرق دقائق)
- فحص الأبحاث العلمية
- حساب embeddings
- توليد التقارير

التشغيل:
    celery -A celery_app worker --loglevel=info
    celery -A celery_app beat --loglevel=info   # للمهام المجدولة
"""

import asyncio
import os

from celery import Celery
from celery.schedules import crontab

# إعداد Redis URL
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

app = Celery("quran_miracles", broker=REDIS_URL, backend=REDIS_URL)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 دقائق حد أقصى
    task_soft_time_limit=540,  # تحذير بعد 9 دقائق
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
)

# ── المهام المجدولة ────────────────────────────────
app.conf.beat_schedule = {
    "check-papers-hourly": {
        "task": "celery_app.check_new_papers",
        "schedule": crontab(minute=0),  # كل ساعة
    },
    "mcts-exploration-6h": {
        "task": "celery_app.run_mcts_exploration",
        "schedule": crontab(minute=0, hour="*/6"),  # كل 6 ساعات
    },
    "numerical-patterns-daily": {
        "task": "celery_app.scan_numerical_patterns",
        "schedule": crontab(minute=0, hour=2),  # يومياً الساعة 2 صباحاً
    },
    "weekly-report": {
        "task": "celery_app.generate_weekly_report",
        "schedule": crontab(minute=0, hour=8, day_of_week="sun"),  # كل أحد
    },
}


def _run_async(coro):
    """تشغيل coroutine في event loop جديد (Celery لا يدعم async مباشرة)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _get_engine():
    """إنشاء AutonomousEngine مع الخدمات المتاحة."""
    from discovery_engine.autonomous.engine import AutonomousEngine

    db = None
    llm = None

    try:
        from database.service import DatabaseService

        db_url = os.environ.get("DATABASE_URL")
        if db_url:
            db = DatabaseService(db_url)
            _run_async(db.connect(timeout=5))
    except Exception:
        pass

    try:
        import anthropic

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            llm = anthropic.AsyncAnthropic(api_key=api_key)
    except Exception:
        pass

    return AutonomousEngine(db=db, llm=llm)


# ── المهام ────────────────────────────────────────

@app.task(name="celery_app.check_new_papers", bind=True)
def check_new_papers(self):
    """فحص الأبحاث العلمية الجديدة."""
    engine = _get_engine()
    papers = _run_async(engine.check_new_papers())
    return {"paper_count": len(papers)}


@app.task(name="celery_app.run_mcts_exploration", bind=True)
def run_mcts_exploration(self, topic=None, discipline=None):
    """تشغيل جلسة MCTS."""
    engine = _get_engine()
    result = _run_async(engine.run_mcts_exploration(topic, discipline))
    return result


@app.task(name="celery_app.scan_numerical_patterns", bind=True)
def scan_numerical_patterns(self):
    """مسح الأنماط العددية."""
    engine = _get_engine()
    patterns = _run_async(engine.scan_numerical_patterns())
    return {"pattern_count": len(patterns)}


@app.task(name="celery_app.generate_weekly_report", bind=True)
def generate_weekly_report(self):
    """توليد التقرير الأسبوعي."""
    engine = _get_engine()
    report = _run_async(engine.generate_weekly_report())
    return report


@app.task(name="celery_app.run_discovery", bind=True)
def run_discovery(self, query: str, disciplines: list | None = None, mode: str = "guided"):
    """تشغيل استعلام اكتشاف كامل عبر LangGraph."""
    from discovery_engine.core.graph import build_discovery_graph
    from database.service import DatabaseService

    db = None
    try:
        db_url = os.environ.get("DATABASE_URL")
        if db_url:
            db = DatabaseService(db_url)
            _run_async(db.connect(timeout=5))
    except Exception:
        pass

    graph = build_discovery_graph(db=db)
    state = {
        "query": query,
        "disciplines": disciplines or ["physics", "biology", "psychology"],
        "mode": mode,
    }

    result = _run_async(graph.ainvoke(state))
    return {
        "synthesis": result.get("synthesis", ""),
        "confidence_tier": result.get("confidence_tier", "tier_2"),
        "quality_score": result.get("quality_score", 0),
    }


@app.task(name="celery_app.compute_embeddings", bind=True)
def compute_embeddings(self, surah_numbers: list | None = None):
    """حساب embeddings لآيات محددة أو كل القرآن."""
    from arabic_nlp.embeddings_service import EmbeddingsService

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        return {"error": "DATABASE_URL not set"}

    embeddings = EmbeddingsService()
    _run_async(embeddings.initialize(db_url))
    return {"status": "embeddings computed"}
