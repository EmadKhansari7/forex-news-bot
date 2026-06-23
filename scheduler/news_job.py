
from config.logger import get_logger
from database.repository import (
    get_active_destinations,
    is_news_already_sent,
    mark_news_as_sent,
)
from services.filter_service import filter_news_list
from services.news_provider.forex_factory_provider import NewsFeedError, fetch_news
from services.telegram_service import send_message

logger = get_logger(__name__)


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

    filtered_news = filter_news_list(all_news)
    logger.info(f"{len(filtered_news)} out of {len(all_news)} news items passed the filter")

    if not filtered_news:
        logger.info("No news items passed the filter. Cycle finished.")
        return


    new_news = [item for item in filtered_news if not is_news_already_sent(item.unique_id)]
    logger.info(f"{len(new_news)} of those are genuinely new (not sent before)")

    if not new_news:
        logger.info("All filtered news items were already sent before. Cycle finished.")
        return

    destinations = get_active_destinations()

    if not destinations:

        logger.warning("No active destinations configured. Cannot send any news.")
        return


    for news_item in new_news:
        message_text = _format_news_message(news_item)


        at_least_one_success = False

        for destination in destinations:
            success = await send_message(
                chat_id=destination.chat_id,
                text=message_text,
            )
            if success:
                at_least_one_success = True

        if at_least_one_success:
            mark_news_as_sent(news_item)

    logger.info("News check cycle finished successfully")


def _format_news_message(news_item) -> str:

    forecast_line = f"\nForecast: {news_item.forecast}" if news_item.forecast else ""
    previous_line = f"\nPrevious: {news_item.previous}" if news_item.previous else ""

    return (
        f"📰 {news_item.title}\n"
        f"💱 Currency: {news_item.currency}\n"
        f"⚡ Impact: {news_item.impact}\n"
        f"🕐 Time: {news_item.event_time.strftime('%Y-%m-%d %H:%M %Z')}"
        f"{forecast_line}{previous_line}"
    )