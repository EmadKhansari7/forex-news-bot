from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from bot.keyboards.main_menu import build_bot_settings_menu
from config.logger import get_logger
from config.settings import TELEGRAM_ADMIN_IDS
from database.repository import add_channel_manager, get_global_settings, is_authorized_user

logger = get_logger(__name__)

WAITING_FOR_NEW_MANAGER_ID = range(1)[0]


def _is_owner(telegram_user_id: int) -> bool:
    return telegram_user_id in TELEGRAM_ADMIN_IDS


async def start_add_manager(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    if not _is_owner(user_id):
        logger.warning(f"User {user_id} attempted to start add-manager flow (owner-only)")
        await query.edit_message_text("Only the bot owner can add new managers.")
        return ConversationHandler.END

    await query.edit_message_text(
        "Send the numeric Telegram user ID of the person you want to "
        "authorize as a manager.\n\n"
        "They can get their own ID by messaging @userinfobot or "
        "@RawDataBot.\n\n"
        "Send /cancel to abort."
    )
    return WAITING_FOR_NEW_MANAGER_ID


async def receive_new_manager_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    raw_text = update.message.text.strip()

    if not raw_text.isdigit():
        await update.message.reply_text(
            "Invalid format. Please send only the numeric Telegram user ID "
            "(no '@', no name), or /cancel to abort."
        )
        return WAITING_FOR_NEW_MANAGER_ID

    new_manager_telegram_id = int(raw_text)
    owner_user_id = update.effective_user.id

    if is_authorized_user(new_manager_telegram_id):
        await update.message.reply_text(
            f"User {new_manager_telegram_id} is already an authorized manager.\n"
            f"Nothing changed."
        )
        context.user_data.clear()
        return ConversationHandler.END

    new_manager = add_channel_manager(
        telegram_user_id=new_manager_telegram_id,
        display_name=f"Manager {new_manager_telegram_id}",
    )

    logger.info(
        f"Owner {owner_user_id} authorized new manager: "
        f"telegram_user_id={new_manager_telegram_id}"
    )

    await update.message.reply_text(
        f"✅ User {new_manager_telegram_id} is now an authorized manager.\n\n"
        f"They can now send /start to the bot and add their own "
        f"channels/groups.\n\n"
        f"Note: they don't have access to any existing channel yet -- "
        f"this only lets them use the bot and add new channels of their own."
    )

    settings = get_global_settings()
    await update.message.reply_text(
        "⏱ Bot Settings",
        reply_markup=build_bot_settings_menu(settings.check_interval_minutes),
    )

    context.user_data.clear()
    return ConversationHandler.END


async def cancel_add_manager(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END
