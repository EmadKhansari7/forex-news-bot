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
from services.filter_service import (
    MatchedNewsItem,
    get_matched_news_for_destination,
)
from services.news_provider.forex_factory_provider import NewsFeedError, fetch_news
from services.news_provider.news_item import NewsItem
from services.telegram_service import send_message

logger = get_logger(__name__)

DELAY_BETWEEN_MESSAGES_SECONDS = 1.5

_CURRENCY_LABELS = {
    "OIL": "🛢️ OIL",
    "GOLD": "🥇 GOLD",
}


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


def _make_unique_id_for_match(matched: MatchedNewsItem) -> str:

    if matched.matched_currency == matched.news_item.currency:
        return matched.news_item.unique_id
    return f"{matched.news_item.unique_id}_{matched.matched_currency}"


async def _process_destination(destination, all_news: list[NewsItem]) -> None:

    if _is_throttled(destination.id, destination.name):
        return

    matched_items = get_matched_news_for_destination(all_news, destination.id)

    if not matched_items:
        logger.info(f"No news passed filters for destination '{destination.name}'")
        return

    new_matches = [
        matched for matched in matched_items
        if not is_news_already_sent(_make_unique_id_for_match(matched), destination.id)
    ]

    if not new_matches:
        logger.info(f"All filtered news already sent to '{destination.name}'")
        return

    logger.info(f"Sending {len(new_matches)} new news item(s) to '{destination.name}'")

    for matched in new_matches:
        message_text = _format_news_message(matched)
        unique_id = _make_unique_id_for_match(matched)

        success = await send_message(
            chat_id=destination.chat_id,
            text=message_text,
        )

        if success:
            mark_news_as_sent(matched.news_item, destination.id, unique_id_override=unique_id)

        await asyncio.sleep(DELAY_BETWEEN_MESSAGES_SECONDS)


def _format_news_message(matched: MatchedNewsItem) -> str:
    news_item = matched.news_item

    forecast_line = f"\nForecast: {news_item.forecast}" if news_item.forecast else ""
    previous_line = f"\nPrevious: {news_item.previous}" if news_item.previous else ""


    display_label = _CURRENCY_LABELS.get(matched.matched_currency, news_item.currency)

    return (
        f"📰 {news_item.title}\n"
        f"💱 Currency: {display_label}\n"
        f"⚡ Impact: {news_item.impact}\n"
        f"🕐 Time: {news_item.event_time.strftime('%Y-%m-%d %H:%M %Z')}"
        f"{forecast_line}{previous_line}"
    )