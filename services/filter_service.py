
from database.repository import get_filter_settings
from services.news_provider.news_item import NewsItem

IMPACT_LEVELS = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
}


def should_send_news(news_item: NewsItem, destination_id: int) -> bool:

    filter_settings = get_filter_settings(destination_id, news_item.currency)

    if filter_settings is None:
        return False

    if not filter_settings.is_enabled:
        return False

    news_impact_level = IMPACT_LEVELS.get(news_item.impact, 0)
    required_impact_level = IMPACT_LEVELS.get(filter_settings.min_impact, 0)

    if news_impact_level < required_impact_level:
        return False

    return True


def filter_news_list_for_destination(
    news_items: list[NewsItem], destination_id: int
) -> list[NewsItem]:

    return [
        item for item in news_items
        if should_send_news(item, destination_id)
    ]