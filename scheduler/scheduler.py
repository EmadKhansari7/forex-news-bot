
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config.logger import get_logger
from database.repository import get_bot_settings
from scheduler.news_job import run_news_check

logger = get_logger(__name__)

_scheduler = AsyncIOScheduler()


def start_scheduler() -> None:

    settings = get_bot_settings()
    interval_minutes = settings.check_interval_minutes

    logger.info(f"Scheduling news check job to run every {interval_minutes} minutes")

    from datetime import datetime

    _scheduler.add_job(
        run_news_check,
        trigger="interval",
        minutes=interval_minutes,
        id="news_check_job",

        next_run_time=datetime.now(),
    )

    _scheduler.start()
    logger.info("Scheduler started successfully")


def stop_scheduler() -> None:

    _scheduler.shutdown()
    logger.info("Scheduler stopped")