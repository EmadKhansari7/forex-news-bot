
from database.engine import get_session
from database.models import BotSettings, Destination, FilterSettings, SentNews
from services.news_provider.news_item import NewsItem

SUPPORTED_CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "NZD", "CHF"]


def seed_default_filters() -> None:

    with get_session() as session:
        existing_currencies = {
            row.currency for row in session.query(FilterSettings).all()
        }

        for currency in SUPPORTED_CURRENCIES:
            if currency not in existing_currencies:

                session.add(
                    FilterSettings(
                        currency=currency,
                        is_enabled=True,
                        min_impact="Medium",
                    )
                )

        session.commit()


def is_news_already_sent(unique_id: str) -> bool:
 
    with get_session() as session:
        existing_record = (
            session.query(SentNews)
            .filter(SentNews.unique_id == unique_id)
            .first()
        )
        return existing_record is not None


def mark_news_as_sent(news_item: NewsItem) -> None:

    with get_session() as session:
        new_record = SentNews(
            unique_id=news_item.unique_id,
            title=news_item.title,
            currency=news_item.currency,
        )
        session.add(new_record)
        session.commit()


def get_enabled_currencies() -> list[str]:

    with get_session() as session:
        enabled_filters = (
            session.query(FilterSettings)
            .filter(FilterSettings.is_enabled == True)  
            .all()
        )
        return [item.currency for item in enabled_filters]


def get_active_destinations() -> list[Destination]:

    with get_session() as session:
        return (
            session.query(Destination)
            .filter(Destination.is_active == True)  
            .all()
        )


def get_bot_settings() -> BotSettings:

    with get_session() as session:
        settings = session.query(BotSettings).first()

        if settings is None:
            settings = BotSettings()  
            session.add(settings)
            session.commit()
            session.refresh(settings)  

        return settings