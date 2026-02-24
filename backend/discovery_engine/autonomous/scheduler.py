"""APScheduler configuration for autonomous engine tasks."""

from apscheduler.schedulers.asyncio import AsyncIOScheduler


def create_scheduler() -> AsyncIOScheduler:
    """Create and configure the autonomous engine scheduler."""
    scheduler = AsyncIOScheduler()

    # Hourly: check new scientific papers
    # scheduler.add_job(check_new_papers, "interval", hours=1)

    # Every 6 hours: MCTS exploration
    # scheduler.add_job(run_mcts, "interval", hours=6)

    # Daily at 2 AM: numerical pattern scanning
    # scheduler.add_job(scan_patterns, "cron", hour=2)

    # Weekly Sunday 8 AM: weekly report
    # scheduler.add_job(weekly_report, "cron", day_of_week="sun", hour=8)

    return scheduler
