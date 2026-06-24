
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):

    pass


class ChannelManager(Base):

    __tablename__ = "channel_managers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    telegram_user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)

    display_name: Mapped[str] = mapped_column(String(100), default="")
    is_owner: Mapped[bool] = mapped_column(Boolean, default=False)

    managed_destinations: Mapped[list["Destination"]] = relationship(
        secondary="manager_destination_links",
        back_populates="managers",
    )

    def __repr__(self) -> str:
        return f"<ChannelManager(telegram_user_id={self.telegram_user_id}, owner={self.is_owner})>"


class Destination(Base):

    __tablename__ = "destinations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    managers: Mapped[list["ChannelManager"]] = relationship(
        secondary="manager_destination_links",
        back_populates="managed_destinations",
    )

    def __repr__(self) -> str:
        return f"<Destination(name='{self.name}', chat_id='{self.chat_id}')>"


class ManagerDestinationLink(Base):

    __tablename__ = "manager_destination_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    manager_id: Mapped[int] = mapped_column(ForeignKey("channel_managers.id"))
    destination_id: Mapped[int] = mapped_column(ForeignKey("destinations.id"))


class SentNews(Base):

    __tablename__ = "sent_news"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    destination_id: Mapped[int] = mapped_column(ForeignKey("destinations.id"))
    unique_id: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(255))
    currency: Mapped[str] = mapped_column(String(10))

    sent_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return (
            f"<SentNews(title='{self.title}', "
            f"destination_id={self.destination_id})>"
        )


class FilterSettings(Base):

    __tablename__ = "filter_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    destination_id: Mapped[int] = mapped_column(ForeignKey("destinations.id"))

    currency: Mapped[str] = mapped_column(String(10))
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    min_impact: Mapped[str] = mapped_column(String(10), default="Medium")

    def __repr__(self) -> str:
        return (
            f"<FilterSettings(destination_id={self.destination_id}, "
            f"currency='{self.currency}', enabled={self.is_enabled})>"
        )


class DestinationSettings(Base):

    __tablename__ = "destination_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    destination_id: Mapped[int] = mapped_column(
        ForeignKey("destinations.id"), unique=True
    )

    alert_15min_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    alert_5min_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    alert_at_release_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<DestinationSettings(destination_id={self.destination_id})>"


class GlobalSettings(Base):

    __tablename__ = "global_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # مقادیر مجاز طبق پرامپت اولیه‌ی پروژه: 5, 15, 30, 60
    check_interval_minutes: Mapped[int] = mapped_column(Integer, default=15)

    def __repr__(self) -> str:
        return f"<GlobalSettings(check_interval={self.check_interval_minutes}min)>"