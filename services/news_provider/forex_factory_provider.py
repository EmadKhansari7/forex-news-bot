

import hashlib
from datetime import datetime

import requests
from dateutil import parser as date_parser

from config.logger import get_logger
from config.settings import NEWS_FEED_URL
from services.news_provider.news_item import NewsItem

logger = get_logger(__name__)

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

REQUEST_TIMEOUT_SECONDS = 15


class NewsFeedError(Exception):

    pass


def _generate_unique_id(title: str, currency: str, event_time: datetime) -> str:

    raw_string = f"{title}_{currency}_{event_time.isoformat()}"
    return hashlib.sha256(raw_string.encode("utf-8")).hexdigest()


def _parse_single_event(raw_event: dict) -> NewsItem | None:

    try:
        title = raw_event["title"]
        currency = raw_event["country"]
        impact = raw_event["impact"]

        event_time = date_parser.parse(raw_event["date"])

        forecast = raw_event.get("forecast") or None
        previous = raw_event.get("previous") or None

        unique_id = _generate_unique_id(title, currency, event_time)

        return NewsItem(
            title=title,
            currency=currency,
            impact=impact,
            event_time=event_time,
            forecast=forecast,
            previous=previous,
            unique_id=unique_id,
        )

    except (KeyError, ValueError, TypeError) as error:

        logger.warning(f"Skipping malformed news event: {error}. Raw data: {raw_event}")
        return None


def fetch_news() -> list[NewsItem]:

    logger.info(f"Fetching news feed from {NEWS_FEED_URL}")

    try:
        response = requests.get(
            NEWS_FEED_URL,
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()  

    except requests.exceptions.RequestException as error:

        raise NewsFeedError(f"Failed to connect to news feed: {error}") from error

    try:
        raw_events = response.json()
    except ValueError as error:
        raise NewsFeedError(
            "News feed did not return valid JSON. "
            "This usually means the rate limit was exceeded "
            "(max 2 requests per 5 minutes) or the feed is temporarily down."
        ) from error

    logger.info(f"Received {len(raw_events)} raw events from the feed")

    # هر رویداد خام را تبدیل می‌کنیم، و رویدادهای خراب (None) را فیلتر می‌کنیم
    news_items = [
        item for raw_event in raw_events
        if (item := _parse_single_event(raw_event)) is not None
    ]

    logger.info(f"Successfully parsed {len(news_items)} valid news items")

    return news_items