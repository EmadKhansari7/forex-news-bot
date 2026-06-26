
from telegram import Update
from telegram.ext import ContextTypes

from bot.keyboards.alert_menu import build_alert_settings_menu
from bot.keyboards.filter_menu import build_currency_filter_menu
from bot.keyboards.main_menu import (
    build_channels_list_menu,
    build_destination_detail_menu,
    build_main_menu,
)
from config.logger import get_logger
from database.repository import (
    get_all_filters_for_destination,
    get_destination_by_id,
    get_destination_settings,
    get_destinations_for_manager,
    toggle_currency_filter,
    toggle_destination_alert,
)

logger = get_logger(__name__)


def _is_authorized_for_destination(telegram_user_id: int, destination_id: int) -> bool:
    allowed_destinations = get_destinations_for_manager(telegram_user_id)
    allowed_ids = {destination.id for destination in allowed_destinations}
    return destination_id in allowed_ids


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    logger.info(f"User {user_id} started the bot")

    await update.message.reply_text(
        "Welcome to Forex News Bot Admin Panel!\n\n"
        "Use the menu below to manage your channels and groups.",
        reply_markup=build_main_menu(),
    )


async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    data = query.data
    logger.info(f"User {user_id} clicked button with data: {data}")

    parts = data.split(":")

    if data == "menu:main":
        await query.edit_message_text(
            "Welcome to Forex News Bot Admin Panel!",
            reply_markup=build_main_menu(),
        )

    elif data == "menu:channels":
        await _show_channels_list(query, user_id)

    elif data == "menu:help":
        await query.edit_message_text(
            "This bot publishes ForexFactory economic news to your channels.\n"
            "Use 'Manage Channels' to configure filters and alerts.",
            reply_markup=build_main_menu(),
        )

    elif parts[0] == "dest":
        await _handle_destination_action(query, user_id, parts)

    else:
        logger.warning(f"Unknown callback_data received: {data}")


async def _show_channels_list(query, user_id: int) -> None:
    destinations = get_destinations_for_manager(user_id)

    if not destinations:
        await query.edit_message_text(
            "You don't manage any channels yet.\n"
            "Ask the bot owner to add you as a manager, or add a new channel.",
            reply_markup=build_channels_list_menu([]),
        )
        return

    await query.edit_message_text(
        f"You manage {len(destinations)} channel(s)/group(s):",
        reply_markup=build_channels_list_menu(destinations),
    )


async def _handle_destination_action(query, user_id: int, parts: list[str]) -> None:

    destination_id = int(parts[1])
    action = parts[2]

    if not _is_authorized_for_destination(user_id, destination_id):
        logger.warning(
            f"User {user_id} attempted unauthorized access to destination {destination_id}"
        )
        await query.edit_message_text("You don't have access to this channel.")
        return

    destination = get_destination_by_id(destination_id)
    if destination is None:
        await query.edit_message_text("This channel no longer exists.")
        return

    if action == "open":
        await query.edit_message_text(
            f"Managing: {destination.name}\nChat ID: {destination.chat_id}",
            reply_markup=build_destination_detail_menu(destination_id),
        )

    elif action == "filters":
        filters = get_all_filters_for_destination(destination_id)
        await query.edit_message_text(
            f"Currency filters for {destination.name}:\n"
            f"(tap a currency to toggle it on/off)",
            reply_markup=build_currency_filter_menu(destination_id, filters),
        )

    elif action == "toggle_currency":
        currency = parts[3]
        toggle_currency_filter(destination_id, currency)
        updated_filters = get_all_filters_for_destination(destination_id)
        await query.edit_message_text(
            f"Currency filters for {destination.name}:\n"
            f"(tap a currency to toggle it on/off)",
            reply_markup=build_currency_filter_menu(destination_id, updated_filters),
        )

    elif action == "alerts":
        settings = get_destination_settings(destination_id)
        await query.edit_message_text(
            f"Alert settings for {destination.name}:\n"
            f"(tap to toggle each alert on/off)",
            reply_markup=build_alert_settings_menu(destination_id, settings),
        )

    elif action == "toggle_alert":
        alert_type = parts[3]
        toggle_destination_alert(destination_id, alert_type)
        updated_settings = get_destination_settings(destination_id)
        await query.edit_message_text(
            f"Alert settings for {destination.name}:\n"
            f"(tap to toggle each alert on/off)",
            reply_markup=build_alert_settings_menu(destination_id, updated_settings),
        )

    else:
        logger.warning(f"Unknown destination action: {action}")