
from database.engine import get_session
from database.models import FilterSettings
from services.news_provider.news_item import NewsItem


IMPACT_LEVELS = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
}


def _get_filter_settings_for_currency(currency: str) -> FilterSettings | None:

    with get_session() as session:
        return (
            session.query(FilterSettings)
            .filter(FilterSettings.currency == currency)
            .first()
        )


def should_send_news(news_item: NewsItem) -> bool:

    filter_settings = _get_filter_settings_for_currency(news_item.currency)

    if filter_settings is None:
        return False

    if not filter_settings.is_enabled:
        return False

    news_impact_level = IMPACT_LEVELS.get(news_item.impact, 0)
    required_impact_level = IMPACT_LEVELS.get(filter_settings.min_impact, 0)

    if news_impact_level < required_impact_level:
        return False

    return True


def filter_news_list(news_items: list[NewsItem]) -> list[NewsItem]:

    return [item for item in news_items if should_send_news(item)]