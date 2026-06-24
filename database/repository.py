

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



def get_active_destinations() -> list[Destination]:
    
    with get_session() as session:
        return (
            session.query(Destination)
            .filter(Destination.is_active == True)  # noqa: E712
            .all()
        )


def get_or_create_destination(chat_id: str, name: str) -> Destination:

    with get_session() as session:
        destination = (
            session.query(Destination)
            .filter(Destination.chat_id == chat_id)
            .first()
        )

        if destination is None:
            destination = Destination(chat_id=chat_id, name=name, is_active=True)
            session.add(destination)
            session.commit()
            session.refresh(destination)

            _seed_default_filters_for_destination(session, destination.id)
            session.add(DestinationSettings(destination_id=destination.id))
            session.commit()

        return destination


def _seed_default_filters_for_destination(session, destination_id: int) -> None:

    for currency in SUPPORTED_CURRENCIES:
        session.add(
            FilterSettings(
                destination_id=destination_id,
                currency=currency,
                is_enabled=True,
                min_impact="Medium",
            )
        )




def get_enabled_currencies_for_destination(destination_id: int) -> list[str]:

    with get_session() as session:
        enabled_filters = (
            session.query(FilterSettings)
            .filter(
                FilterSettings.destination_id == destination_id,
                FilterSettings.is_enabled == True,  # noqa: E712
            )
            .all()
        )
        return [item.currency for item in enabled_filters]


def get_filter_settings(destination_id: int, currency: str) -> FilterSettings | None:

    with get_session() as session:
        return (
            session.query(FilterSettings)
            .filter(
                FilterSettings.destination_id == destination_id,
                FilterSettings.currency == currency,
            )
            .first()
        )



def get_destination_settings(destination_id: int) -> DestinationSettings:

    with get_session() as session:
        settings = (
            session.query(DestinationSettings)
            .filter(DestinationSettings.destination_id == destination_id)
            .first()
        )

        if settings is None:
            settings = DestinationSettings(destination_id=destination_id)
            session.add(settings)
            session.commit()
            session.refresh(settings)

        return settings


def get_global_settings() -> GlobalSettings:

    with get_session() as session:
        settings = session.query(GlobalSettings).first()

        if settings is None:
            settings = GlobalSettings()
            session.add(settings)
            session.commit()
            session.refresh(settings)

        return settings



def get_or_create_manager(telegram_user_id: int, is_owner: bool = False) -> ChannelManager:

    with get_session() as session:
        manager = (
            session.query(ChannelManager)
            .filter(ChannelManager.telegram_user_id == telegram_user_id)
            .first()
        )

        if manager is None:
            manager = ChannelManager(
                telegram_user_id=telegram_user_id,
                is_owner=is_owner,
            )
            session.add(manager)
            session.commit()
            session.refresh(manager)

        return manager


def link_manager_to_destination(manager_id: int, destination_id: int) -> None:

    with get_session() as session:
        existing_link = (
            session.query(ManagerDestinationLink)
            .filter(
                ManagerDestinationLink.manager_id == manager_id,
                ManagerDestinationLink.destination_id == destination_id,
            )
            .first()
        )

        if existing_link is None:
            session.add(
                ManagerDestinationLink(
                    manager_id=manager_id,
                    destination_id=destination_id,
                )
            )
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

        if manager.is_owner:
            return (
                session.query(Destination)
                .filter(Destination.is_active == True)  # noqa: E712
                .all()
            )

        return manager.managed_destinations