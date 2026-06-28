from database.engine import get_session
from database.models import (
    ChannelManager,
    Destination,
    DestinationSettings,
    FilterSettings,
    GlobalSettings,
    ManagerDestinationLink,
    SentNews,
)
from services.news_provider.news_item import NewsItem

SUPPORTED_CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "NZD", "CHF"]

# گزینه‌های فاصله‌ی زمانی که در منوی Bot Settings نشان داده می‌شوند
SUPPORTED_CHECK_INTERVALS_MINUTES = [5, 10, 15, 30, 60, 120]



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


def update_check_interval(minutes: int) -> GlobalSettings:
    """Update the global news-check interval (in minutes).

    This is a single, shared setting: it affects every destination across
    every manager, since the scheduler only runs one news-check job. Any
    manager with at least one destination is allowed to change it (this
    is intentional per project decision, not an oversight).

    The caller is responsible for also calling
    scheduler.scheduler.reschedule_news_check(minutes) so the running job
    picks up the new interval immediately, instead of waiting for the bot
    to restart.
    """

    if minutes not in SUPPORTED_CHECK_INTERVALS_MINUTES:
        raise ValueError(
            f"Unsupported interval: {minutes}. "
            f"Must be one of {SUPPORTED_CHECK_INTERVALS_MINUTES}."
        )

    with get_session() as session:
        settings = session.query(GlobalSettings).first()

        if settings is None:
            settings = GlobalSettings(check_interval_minutes=minutes)
            session.add(settings)
        else:
            settings.check_interval_minutes = minutes

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

        if manager is None or destination is None:
            raise ValueError("Manager or destination not found")

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


def get_destination_by_id(destination_id: int) -> Destination | None:

    with get_session() as session:
        return session.get(Destination, destination_id)


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


def set_destination_active_state(destination_id: int, is_active: bool) -> Destination | None:
    """Soft-toggle a destination's active state (deactivate/reactivate).

    A deactivated destination is skipped by get_active_destinations(), so
    the bot simply stops sending news to it. This is reversible and does
    not touch any related rows (filters, settings, sent-news history).
    """

    with get_session() as session:
        destination = session.get(Destination, destination_id)

        if destination is not None:
            destination.is_active = is_active
            session.commit()
            session.refresh(destination)

        return destination


def deactivate_destination(destination_id: int) -> Destination | None:
    return set_destination_active_state(destination_id, is_active=False)


def reactivate_destination(destination_id: int) -> Destination | None:
    return set_destination_active_state(destination_id, is_active=True)


def delete_destination_permanently(destination_id: int) -> bool:
    """Permanently remove a destination and all related rows from the database.

    Filters and destination settings cascade-delete automatically (the
    Destination model defines cascade="all, delete-orphan" for both
    relationships). Manager-link rows and sent-news history aren't covered
    by that cascade, so they're deleted explicitly here. This is
    irreversible. Returns True if a destination was found and deleted,
    False if no such destination existed.
    """

    with get_session() as session:
        destination = session.get(Destination, destination_id)

        if destination is None:
            return False

        session.query(SentNews).filter(
            SentNews.destination_id == destination_id
        ).delete()

        session.execute(
            ManagerDestinationLink.__table__.delete().where(
                ManagerDestinationLink.destination_id == destination_id
            )
        )

        session.delete(destination)
        session.commit()
        return True