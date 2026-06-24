

from database.engine import get_session
from database.models import FilterSettings
from services.news_provider.news_item import NewsItem

IMPACT_LEVELS = {"Low": 1, "Medium": 2, "High": 3}


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


def should_send_news(news_item: NewsItem, destination_id: int) -> bool:
    filter_settings = _get_filter_settings(destination_id, news_item.currency)

    if filter_settings is None or not filter_settings.is_enabled:
        return False

    news_level = IMPACT_LEVELS.get(news_item.impact, 0)
    required_level = IMPACT_LEVELS.get(filter_settings.min_impact, 0)
    return news_level >= required_level


def filter_news_list_for_destination(
    news_items: list[NewsItem], destination_id: int
) -> list[NewsItem]:
    return [item for item in news_items if should_send_news(item, destination_id)]