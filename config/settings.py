

import os
from dotenv import load_dotenv

load_dotenv()


def _get_required_env(key: str) -> str:

    value = os.getenv(key)
    if not value:
        raise ValueError(
            f"Environment variable '{key}' is not set. "
            f"Please check your .env file and provide a value for '{key}'. "
            f"You can use .env.example as a reference template."

        )
    return value


TELEGRAM_BOT_TOKEN: str = _get_required_env("TELEGRAM_BOT_TOKEN")


def _parse_admin_ids(raw_value: str) -> list[int]:

    return [int(admin_id.strip()) for admin_id in raw_value.split(",") if admin_id.strip()]


TELEGRAM_ADMIN_IDS: list[int] = _parse_admin_ids(_get_required_env("TELEGRAM_ADMIN_IDS"))




DATABASE_PATH: str = os.getenv("DATABASE_PATH", "database/forex_news_bot.db")

NEWS_FEED_URL: str = os.getenv(
    "NEWS_FEED_URL",
    "https://nfs.faireconomy.media/ff_calendar_thisweek.json",
)

LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")