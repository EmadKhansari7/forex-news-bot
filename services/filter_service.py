from dataclasses import dataclass

from database.engine import get_session
from database.models import FilterSettings
from services.news_provider.news_item import NewsItem

IMPACT_LEVELS = {"Low": 1, "Medium": 2, "High": 3}


OIL_KEYWORDS = ["Crude Oil", "Natural Gas"]


GOLD_KEYWORDS: list[str] = []


@dataclass
class MatchedNewsItem:

    news_item: NewsItem
    matched_currency: str


def _get_filter_settings(destination_id: int, currency: str) -> FilterSettings | None:
    with get_session() as session:
        return (
            session.query(FilterSettings)
            .filter(
                FilterSettings.destination_id == destination_id,
                FilterSettings.currency == currency,
            )
            .first()
        )


def _matches_keyword_currency(news_item: NewsItem, keywords: list[str]) -> bool:
    title_lower = news_item.title.lower()
    return any(keyword.lower() in title_lower for keyword in keywords)


def _get_applicable_currencies(news_item: NewsItem) -> list[str]:

    applicable = [news_item.currency]

    if _matches_keyword_currency(news_item, OIL_KEYWORDS):
        applicable.append("OIL")

    if GOLD_KEYWORDS and _matches_keyword_currency(news_item, GOLD_KEYWORDS):
        applicable.append("GOLD")

    return applicable


def _passes_filter(news_item: NewsItem, destination_id: int, currency: str) -> bool:
    filter_settings = _get_filter_settings(destination_id, currency)

    if filter_settings is None or not filter_settings.is_enabled:
        return False

    news_level = IMPACT_LEVELS.get(news_item.impact, 0)
    required_level = IMPACT_LEVELS.get(filter_settings.min_impact, 0)
    return news_level >= required_level


def should_send_news(news_item: NewsItem, destination_id: int) -> bool:

    return any(
        _passes_filter(news_item, destination_id, currency)
        for currency in _get_applicable_currencies(news_item)
    )


def get_matched_news_for_destination(
    news_items: list[NewsItem], destination_id: int
) -> list[MatchedNewsItem]:

    matched: list[MatchedNewsItem] = []

    for item in news_items:
        for currency in _get_applicable_currencies(item):
            if _passes_filter(item, destination_id, currency):
                matched.append(MatchedNewsItem(news_item=item, matched_currency=currency))

    return matched


def filter_news_list_for_destination(
    news_items: list[NewsItem], destination_id: int
) -> list[NewsItem]:

    return [item for item in news_items if should_send_news(item, destination_id)]