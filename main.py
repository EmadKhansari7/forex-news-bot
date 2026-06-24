

from telegram.ext import Application, CallbackQueryHandler, CommandHandler

from bot.handlers.admin_handlers import button_callback_handler, start_command
from config.logger import get_logger
from config.settings import TELEGRAM_ADMIN_IDS, TELEGRAM_BOT_TOKEN
from database.engine import init_database
from database.repository import add_channel_manager, get_global_settings
from scheduler.scheduler import start_scheduler

logger = get_logger(__name__)


def _seed_owner_as_manager() -> None:
    for admin_id in TELEGRAM_ADMIN_IDS:
        add_channel_manager(telegram_user_id=admin_id, display_name="Owner")
        logger.info(f"Ensured owner {admin_id} exists as a channel manager")


async def _on_startup(application) -> None:

    settings = get_global_settings()
    logger.info(f"News check interval: {settings.check_interval_minutes} minutes")
    start_scheduler()


def main() -> None:
    logger.info("Starting Forex News Bot...")

    init_database()
    _seed_owner_as_manager()

    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(_on_startup)
        .build()
    )

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_callback_handler))

    logger.info("Bot is now running. Press Ctrl+C to stop.")
    application.run_polling()


if __name__ == "__main__":
    main()