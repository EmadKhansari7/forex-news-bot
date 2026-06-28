from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config.logger import get_logger
from database.repository import get_global_settings
from scheduler.news_job import run_news_check

logger = get_logger(__name__)

_scheduler = AsyncIOScheduler()

_JOB_ID = "news_check_job"


def start_scheduler() -> None:

    settings = get_global_settings()
    interval_minutes = settings.check_interval_minutes

    logger.info(f"Scheduling news check job to run every {interval_minutes} minutes")

    from datetime import datetime

    _scheduler.add_job(
        run_news_check,
        trigger="interval",
        minutes=interval_minutes,
        id=_JOB_ID,
    
        next_run_time=datetime.now(),
    )

    _scheduler.start()
    logger.info("Scheduler started successfully")


def reschedule_news_check(minutes: int) -> bool:
    """Change the interval of the already-running news-check job.

    Unlike start_scheduler(), this does NOT touch next_run_time, so it
    won't trigger an immediate extra check -- it only changes how often
    the job fires from now on. Returns True if the job was found and
    rescheduled, False if the scheduler hasn't started yet or the job
    doesn't exist (which would mean start_scheduler() was never called).
    """

    existing_job = _scheduler.get_job(_JOB_ID)

    if existing_job is None:
        logger.warning(
            f"reschedule_news_check called but job '{_JOB_ID}' does not exist. "
            f"The scheduler may not have started yet."
        )
        return False

    _scheduler.reschedule_job(_JOB_ID, trigger="interval", minutes=minutes)
    logger.info(f"News check job rescheduled to run every {minutes} minutes")
    return True


def stop_scheduler() -> None:

    _scheduler.shutdown()
    logger.info("Scheduler stopped")