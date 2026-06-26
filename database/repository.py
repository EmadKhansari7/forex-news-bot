

from database.engine import get_session
from database.models import (
    ChannelManager,
    Destination,
    DestinationSettings,
    FilterSettings,
    GlobalSettings,
    SentNews,
)
from services.news_provider.news_item import NewsItem

SUPPORTED_CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "NZD", "CHF"]


def is_news_already_sent(unique_id: str, destination_id: int) -> bool:
    with get_session() as session:
        existing_record = (
            session.query(SentNews)
            .filter(
                SentNews.unique_id == unique_id,
                SentNews.destination_id == destination_id,
            )
            .first()
        )
        return existing_record is not None


def mark_news_as_sent(news_item: NewsItem, destination_id: int) -> None:
    with get_session() as session:
        new_record = SentNews(
            destination_id=destination_id,
            unique_id=news_item.unique_id,
            title=news_item.title,
            currency=news_item.currency,
        )
        session.add(new_record)
        session.commit()


def get_global_settings() -> GlobalSettings:
    with get_session() as session:
        settings = session.query(GlobalSettings).first()
        if settings is None:
            settings = GlobalSettings()
            session.add(settings)
            session.commit()
            session.refresh(settings)
        return settings



def add_channel_manager(telegram_user_id: int, display_name: str) -> ChannelManager:
    with get_session() as session:
        existing = (
            session.query(ChannelManager)
            .filter(ChannelManager.telegram_user_id == telegram_user_id)
            .first()
        )
        if existing is not None:
            return existing

        new_manager = ChannelManager(
            telegram_user_id=telegram_user_id,
            display_name=display_name,
        )
        session.add(new_manager)
        session.commit()
        session.refresh(new_manager)
        return new_manager


def grant_manager_access(telegram_user_id: int, destination_id: int) -> None:

    with get_session() as session:
        manager = (
            session.query(ChannelManager)
            .filter(ChannelManager.telegram_user_id == telegram_user_id)
            .first()
        )
        destination = session.get(Destination, destination_id)

        if manager is None:
            raise ValueError(f"Manager with telegram_user_id={telegram_user_id} not found")
        if destination is None:
            raise ValueError(f"Destination with id={destination_id} not found")

        if destination not in manager.destinations:
            manager.destinations.append(destination)
            session.commit()


def get_destinations_for_manager(telegram_user_id: int) -> list[Destination]:

    with get_session() as session:
        manager = (
            session.query(ChannelManager)
            .filter(ChannelManager.telegram_user_id == telegram_user_id)
            .first()
        )
        if manager is None:
            return []
        return list(manager.destinations)



def add_destination(chat_id: str, name: str) -> Destination:

    with get_session() as session:
        existing = (
            session.query(Destination)
            .filter(Destination.chat_id == chat_id)
            .first()
        )
        if existing is not None:
            return existing

        new_destination = Destination(chat_id=chat_id, name=name, is_active=True)

        for currency in SUPPORTED_CURRENCIES:
            new_destination.filters.append(
                FilterSettings(currency=currency, is_enabled=True, min_impact="Medium")
            )

        new_destination.settings = DestinationSettings()

        session.add(new_destination)
        session.commit()
        session.refresh(new_destination)
        return new_destination


def get_active_destinations() -> list[Destination]:
    with get_session() as session:
        return (
            session.query(Destination)
            .filter(Destination.is_active == True)  # noqa: E712
            .all()
        )


def get_destination_by_id(destination_id: int) -> Destination | None:
    with get_session() as session:
        return session.get(Destination, destination_id)



def get_enabled_filters_for_destination(destination_id: int) -> list[FilterSettings]:
    with get_session() as session:
        return (
            session.query(FilterSettings)
            .filter(
                FilterSettings.destination_id == destination_id,
                FilterSettings.is_enabled == True,  # noqa: E712
            )
            .all()
        )


def get_all_filters_for_destination(destination_id: int) -> list[FilterSettings]:
    with get_session() as session:
        return (
            session.query(FilterSettings)
            .filter(FilterSettings.destination_id == destination_id)
            .all()
        )


def toggle_currency_filter(destination_id: int, currency: str) -> FilterSettings:
    with get_session() as session:
        filter_row = (
            session.query(FilterSettings)
            .filter(
                FilterSettings.destination_id == destination_id,
                FilterSettings.currency == currency,
            )
            .first()
        )
        if filter_row is not None:
            filter_row.is_enabled = not filter_row.is_enabled
            session.commit()
            session.refresh(filter_row)
        return filter_row



def get_destination_settings(destination_id: int) -> DestinationSettings | None:
    with get_session() as session:
        return (
            session.query(DestinationSettings)
            .filter(DestinationSettings.destination_id == destination_id)
            .first()
        )


def toggle_destination_alert(destination_id: int, alert_type: str) -> DestinationSettings | None:
    field_map = {
        "15min": "alert_15min_enabled",
        "5min": "alert_5min_enabled",
        "at_release": "alert_at_release_enabled",
    }
    field_name = field_map.get(alert_type)
    if field_name is None:
        return None

    with get_session() as session:
        settings_row = (
            session.query(DestinationSettings)
            .filter(DestinationSettings.destination_id == destination_id)
            .first()
        )
        if settings_row is not None:
            current_value = getattr(settings_row, field_name)
            setattr(settings_row, field_name, not current_value)
            session.commit()
            session.refresh(settings_row)
        return settings_row