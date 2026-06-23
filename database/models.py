

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):

    pass


class SentNews(Base):

    __tablename__ = "sent_news"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    unique_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    title: Mapped[str] = mapped_column(String(255))
    currency: Mapped[str] = mapped_column(String(10))

    sent_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<SentNews(title='{self.title}', currency='{self.currency}')>"


class FilterSettings(Base):

    __tablename__ = "filter_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    currency: Mapped[str] = mapped_column(String(10), unique=True)

    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    min_impact: Mapped[str] = mapped_column(String(10), default="Low")

    def __repr__(self) -> str:
        return f"<FilterSettings(currency='{self.currency}', enabled={self.is_enabled})>"


class Destination(Base):

    __tablename__ = "destinations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<Destination(name='{self.name}', chat_id='{self.chat_id}')>"


class BotSettings(Base):

    __tablename__ = "bot_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    check_interval_minutes: Mapped[int] = mapped_column(Integer, default=15)

    alert_15min_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    alert_5min_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    alert_at_release_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<BotSettings(check_interval={self.check_interval_minutes}min)>"