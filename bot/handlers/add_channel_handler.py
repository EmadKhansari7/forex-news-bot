
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from bot.keyboards.main_menu import build_channels_list_menu
from config.logger import get_logger
from database.engine import get_session
from database.models import ChannelManager, Destination
from database.repository import add_channel_manager, add_destination, get_destinations_for_manager

logger = get_logger(__name__)

WAITING_FOR_CHAT_ID, WAITING_FOR_NAME = range(2)


async def start_add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Forward any message from the channel/group to @userinfobot or "
        "@RawDataBot to get its chat_id. It must look like -1001234567890 "
        "(channels/groups always start with -100).\n\n"
        "Send that chat_id here, or /cancel to abort."
    )
    return WAITING_FOR_CHAT_ID


async def receive_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id_text = update.message.text.strip()
    is_valid = chat_id_text.startswith("-") and chat_id_text[1:].isdigit()

    if not is_valid:
        await update.message.reply_text(
            "Invalid format. The chat_id must start with '-' "
            "(e.g. -1001234567890). Please try again, or /cancel."
        )
        return WAITING_FOR_CHAT_ID

    context.user_data["new_channel_chat_id"] = chat_id_text
    await update.message.reply_text("Got it. Now send a display name for this channel/group:")
    return WAITING_FOR_NAME


def _link_manager_to_destination_directly(telegram_user_id: int, destination_id: int) -> None:

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


async def receive_channel_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    channel_name = update.message.text.strip()
    chat_id = context.user_data["new_channel_chat_id"]
    user_id = update.effective_user.id

    try:
        destination = add_destination(chat_id=chat_id, name=channel_name)

        add_channel_manager(
            telegram_user_id=user_id,
            display_name=update.effective_user.first_name or "Manager",
        )

        _link_manager_to_destination_directly(user_id, destination.id)

    except Exception as error:
        logger.error(f"Failed to add channel for user {user_id}: {error}")
        await update.message.reply_text(
            f"Something went wrong while adding this channel: {error}\n"
            f"Please try /start again."
        )
        context.user_data.clear()
        return ConversationHandler.END

    logger.info(f"User {user_id} added new destination: {destination}")

    await update.message.reply_text(
        f"Channel '{channel_name}' added successfully!\n"
        f"Don't forget to make the bot an admin in that channel/group "
        f"so it can post messages."
    )

    destinations = get_destinations_for_manager(user_id)
    await update.message.reply_text(
        "Your channels:",
        reply_markup=build_channels_list_menu(destinations),
    )

    context.user_data.clear()
    return ConversationHandler.END


async def cancel_add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END