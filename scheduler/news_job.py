import asyncio
from datetime import datetime, timezone

from config.logger import get_logger
from database.repository import (
    get_active_destinations,
    get_destination_settings,
    get_last_sent_time,
    is_news_already_sent,
    mark_news_as_sent,
)
from services.filter_service import filter_news_list_for_destination
from services.news_provider.forex_factory_provider import NewsFeedError, fetch_news
from services.news_provider.news_item import NewsItem
from services.telegram_service import send_message

logger = get_logger(__name__)

DELAY_BETWEEN_MESSAGES_SECONDS = 1.5


async def run_news_check() -> None:
    logger.info("Starting news check cycle")

    try:
        all_news = fetch_news()
    except NewsFeedError as error:
        logger.error(f"News check cycle aborted: {error}")
        return

    if not all_news:
        logger.info("No news items received from the feed. Cycle finished.")
        return

    destinations = get_active_destinations()

    if not destinations:
        logger.warning("No active destinations configured. Cannot send any news.")
        return

    for destination in destinations:
        await _process_destination(destination, all_news)

    logger.info("News check cycle finished successfully")


def _is_throttled(destination_id: int, destination_name: str) -> bool:
    """چک می‌کند آیا این مقصد هنوز در فاصله‌ی انتظار است یا نه.

    اگر posting_interval_minutes روی ۰ باشد (پیش‌فرض)، throttle فعال نیست.
    در غیر این صورت، بررسی می‌کند آیا از آخرین ارسال به اندازه‌ی کافی گذشته.
    """
    settings = get_destination_settings(destination_id)

    if settings is None or settings.posting_interval_minutes == 0:
        return False

    last_sent = get_last_sent_time(destination_id)

    if last_sent is None:
        return False

    now = datetime.now(timezone.utc)
    if last_sent.tzinfo is None:
        last_sent = last_sent.replace(tzinfo=timezone.utc)

    elapsed_minutes = (now - last_sent).total_seconds() / 60
    required_minutes = settings.posting_interval_minutes

    if elapsed_minutes < required_minutes:
        remaining = required_minutes - elapsed_minutes
        logger.info(
            f"Destination '{destination_name}' is throttled. "
            f"Next send in {remaining:.1f} min "
            f"(interval: {required_minutes} min)."
        )
        return True

    return False


async def _process_destination(destination, all_news: list[NewsItem]) -> None:

    # اول throttle چک می‌شه — اگر throttle باشه، کل این مقصد skip می‌شه
    if _is_throttled(destination.id, destination.name):
        return

    filtered_news = filter_news_list_for_destination(all_news, destination.id)

    if not filtered_news:
        logger.info(f"No news passed filters for destination '{destination.name}'")
        return

    new_news = [
        item for item in filtered_news
        if not is_news_already_sent(item.unique_id, destination.id)
    ]

    if not new_news:
        logger.info(f"All filtered news already sent to '{destination.name}'")
        return

    logger.info(f"Sending {len(new_news)} new news item(s) to '{destination.name}'")

    for news_item in new_news:
        message_text = _format_news_message(news_item)

        success = await send_message(
            chat_id=destination.chat_id,
            text=message_text,
        )

        if success:
            mark_news_as_sent(news_item, destination.id)

        await asyncio.sleep(DELAY_BETWEEN_MESSAGES_SECONDS)


def _format_news_message(news_item: NewsItem) -> str:
    forecast_line = f"\nForecast: {news_item.forecast}" if news_item.forecast else ""
    previous_line = f"\nPrevious: {news_item.previous}" if news_item.previous else ""

    return (
        f"📰 {news_item.title}\n"
        f"💱 Currency: {news_item.currency}\n"
        f"⚡ Impact: {news_item.impact}\n"
        f"🕐 Time: {news_item.event_time.strftime('%Y-%m-%d %H:%M %Z')}"
        f"{forecast_line}{previous_line}"
    )