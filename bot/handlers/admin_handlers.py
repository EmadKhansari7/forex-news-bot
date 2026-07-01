from telegram import Update
from telegram.ext import ContextTypes

from bot.keyboards.alert_menu import build_alert_settings_menu
from bot.keyboards.filter_menu import build_currency_filter_menu
from bot.keyboards.main_menu import (
    build_bot_settings_menu,
    build_channels_list_menu,
    build_delete_confirmation_menu,
    build_destination_detail_menu,
    build_interval_selection_menu,
    build_main_menu,
    build_manager_remove_confirmation_menu,
    build_manager_selection_menu,
    build_posting_interval_menu,
)
from config.logger import get_logger
from config.settings import BOT_OWNER_USERNAME, TELEGRAM_ADMIN_IDS
from database.repository import (
    SUPPORTED_CHECK_INTERVALS_MINUTES,
    deactivate_destination,
    delete_destination_permanently,
    get_all_filters_for_destination,
    get_all_managers,
    get_destination_by_id,
    get_destination_settings,
    get_destinations_for_manager,
    get_global_settings,
    is_authorized_user,
    reactivate_destination,
    remove_manager,
    set_posting_interval,
    toggle_currency_filter,
    toggle_destination_alert,
    update_check_interval,
)
from scheduler.scheduler import reschedule_news_check

logger = get_logger(__name__)


def _is_authorized_for_destination(telegram_user_id: int, destination_id: int) -> bool:

    allowed_destinations = get_destinations_for_manager(telegram_user_id)
    allowed_ids = {destination.id for destination in allowed_destinations}
    return destination_id in allowed_ids


def _is_owner(telegram_user_id: int) -> bool:
    """Bot Settings (e.g. the news-check interval, manager management)
    affects every channel across every manager, since it touches global
    state. Restricting it to the owner (TELEGRAM_ADMIN_IDS) avoids one
    manager's change silently affecting everyone else."""

    return telegram_user_id in TELEGRAM_ADMIN_IDS


def _build_welcome_message() -> str:

    base_message = (
        "Welcome to Forex News Bot Admin Panel!\n\n"
        "Use the menu below to manage your channels and groups."
    )

    if BOT_OWNER_USERNAME:
        base_message += f"\n\nBot owner: @{BOT_OWNER_USERNAME}"

    return base_message


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    user_id = update.effective_user.id

    if not is_authorized_user(user_id):
        logger.warning(f"Unauthorized user {user_id} attempted to start the bot")
        denial_message = "🚫 You are not authorized to use this bot."
        if BOT_OWNER_USERNAME:
            denial_message += f"\n\nContact @{BOT_OWNER_USERNAME} for access."
        await update.message.reply_text(denial_message)
        return

    logger.info(f"User {user_id} started the bot")

    await update.message.reply_text(
        _build_welcome_message(),
        reply_markup=build_main_menu(),
    )


async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    query = update.callback_query
    await query.answer()  

    user_id = update.effective_user.id
    data = query.data

    if not is_authorized_user(user_id):
        logger.warning(f"Unauthorized user {user_id} attempted to click a button: {data}")
        await query.edit_message_text("🚫 You are not authorized to use this bot.")
        return

    logger.info(f"User {user_id} clicked button with data: {data}")

    parts = data.split(":")

    if data == "menu:main":
        await query.edit_message_text(
            _build_welcome_message(),
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

    elif data == "menu:bot_settings":
        await _show_bot_settings(query, user_id)

    elif data == "menu:remove_manager":
        await _show_manager_selection(query, user_id)

    elif parts[0] == "manager":
        await _handle_manager_action(query, user_id, parts)

    elif parts[0] == "settings":
        await _handle_settings_action(query, user_id, parts)

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


async def _show_bot_settings(query, user_id: int) -> None:

    if not _is_owner(user_id):
        logger.warning(f"User {user_id} attempted to access bot settings (owner-only)")
        await query.edit_message_text("Only the bot owner can access Bot Settings.")
        return

    settings = get_global_settings()
    await query.edit_message_text(
        f"⏱ Bot Settings\n\n"
        f"Current news check interval: every {settings.check_interval_minutes} minutes\n\n"
        f"Note: this setting is global and applies to all channels managed "
        f"by all managers.",
        reply_markup=build_bot_settings_menu(settings.check_interval_minutes),
    )


async def _show_manager_selection(query, user_id: int) -> None:

    if not _is_owner(user_id):
        logger.warning(f"User {user_id} attempted to access manager removal (owner-only)")
        await query.edit_message_text("Only the bot owner can remove managers.")
        return

    all_managers = get_all_managers()
    removable_count = len(
        [m for m in all_managers if m.telegram_user_id not in TELEGRAM_ADMIN_IDS]
    )

    if removable_count == 0:
        await query.edit_message_text(
            "There are no managers to remove (only the owner exists so far).",
            reply_markup=build_bot_settings_menu(get_global_settings().check_interval_minutes),
        )
        return

    await query.edit_message_text(
        "Select a manager to remove:\n\n"
        "⚠️ Removing a manager revokes their access to the bot. Any "
        "channel that only they managed will be deactivated (paused, "
        "not deleted) -- channels shared with you or another manager "
        "are left untouched.",
        reply_markup=build_manager_selection_menu(all_managers, TELEGRAM_ADMIN_IDS),
    )


async def _handle_manager_action(query, user_id: int, parts: list[str]) -> None:

    if not _is_owner(user_id):
        logger.warning(f"User {user_id} attempted manager management (owner-only)")
        await query.edit_message_text("Only the bot owner can manage other managers.")
        return

    target_telegram_id = int(parts[1])
    action = parts[2]

    if target_telegram_id in TELEGRAM_ADMIN_IDS:
        logger.warning(f"User {user_id} attempted to remove the owner ({target_telegram_id})")
        await query.edit_message_text("The bot owner cannot be removed.")
        return

    if action == "confirm_remove":
        await query.edit_message_text(
            f"⚠️ Remove manager {target_telegram_id}?\n\n"
            f"This revokes their access to the bot immediately. Any "
            f"channel only they managed will be deactivated.",
            reply_markup=build_manager_remove_confirmation_menu(target_telegram_id),
        )

    elif action == "remove":
        logger.warning(f"Owner {user_id} removed manager {target_telegram_id}")
        deactivated = remove_manager(target_telegram_id)

        result_message = f"✅ Manager {target_telegram_id} has been removed."
        if deactivated:
            names = ", ".join(d.name for d in deactivated)
            result_message += f"\n\n🔴 Deactivated (no manager left): {names}"

        await query.edit_message_text(
            result_message,
            reply_markup=build_bot_settings_menu(get_global_settings().check_interval_minutes),
        )

    else:
        logger.warning(f"Unknown manager action: {action}")


async def _handle_settings_action(query, user_id: int, parts: list[str]) -> None:

    if not _is_owner(user_id):
        logger.warning(f"User {user_id} attempted to change bot settings (owner-only)")
        await query.edit_message_text("Only the bot owner can access Bot Settings.")
        return

    action = parts[1]

    if action == "interval" and len(parts) == 3 and parts[2] == "menu":
        settings = get_global_settings()
        await query.edit_message_text(
            f"Select how often the bot should check for news "
            f"(currently every {settings.check_interval_minutes} minutes):",
            reply_markup=build_interval_selection_menu(settings.check_interval_minutes),
        )

    elif action == "interval" and len(parts) == 3:
        try:
            minutes = int(parts[2])
        except ValueError:
            logger.warning(f"Invalid interval value received: {parts[2]}")
            return

        if minutes not in SUPPORTED_CHECK_INTERVALS_MINUTES:
            logger.warning(f"Unsupported interval requested: {minutes}")
            return

        logger.info(f"User {user_id} changed news check interval to {minutes} minutes")
        update_check_interval(minutes)
        reschedule_news_check(minutes)

        await query.edit_message_text(
            f"⏱ Bot Settings\n\n"
            f"Current news check interval: every {minutes} minutes\n\n"
            f"Note: this setting is global and applies to all channels managed "
            f"by all managers.",
            reply_markup=build_bot_settings_menu(minutes),
        )

    else:
        logger.warning(f"Unknown settings action: {':'.join(parts)}")


async def _show_destination_detail(query, destination) -> None:

    status_line = (
        "🟢 Active — currently sending news"
        if destination.is_active
        else "🔴 Deactivated — news sending is paused"
    )

    await query.edit_message_text(
        f"Managing: {destination.name}\n"
        f"Chat ID: {destination.chat_id}\n"
        f"Status: {status_line}",
        reply_markup=build_destination_detail_menu(
            destination.id, is_active=destination.is_active
        ),
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
        await _show_destination_detail(query, destination)

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
        if settings is None:
            await query.edit_message_text("Alert settings not found for this channel.")
            return

        await query.edit_message_text(
            f"🔔 Alert settings for {destination.name}:\n"
            f"(tap to toggle a pre-release alert on/off)",
            reply_markup=build_alert_settings_menu(destination_id, settings),
        )

    elif action == "toggle_alert":
        alert_type = parts[3]
        toggle_destination_alert(destination_id, alert_type)

        updated_settings = get_destination_settings(destination_id)
        if updated_settings is None:
            await query.edit_message_text("Alert settings not found for this channel.")
            return

        await query.edit_message_text(
            f"🔔 Alert settings for {destination.name}:\n"
            f"(tap to toggle a pre-release alert on/off)",
            reply_markup=build_alert_settings_menu(destination_id, updated_settings),
        )

    elif action == "deactivate":
        logger.info(f"User {user_id} deactivated destination {destination_id}")
        updated_destination = deactivate_destination(destination_id)
        await _show_destination_detail(query, updated_destination)

    elif action == "reactivate":
        logger.info(f"User {user_id} reactivated destination {destination_id}")
        updated_destination = reactivate_destination(destination_id)
        await _show_destination_detail(query, updated_destination)

    elif action == "confirm_delete":
        await query.edit_message_text(
            f"⚠️ Permanently delete '{destination.name}'?\n\n"
            f"This cannot be undone. All currency filters, alert settings, "
            f"and sent-news history for this channel will be erased, and "
            f"every manager (not just you) will lose access to it.",
            reply_markup=build_delete_confirmation_menu(destination_id),
        )

    elif action == "delete_permanent":
        logger.warning(
            f"User {user_id} permanently deleted destination {destination_id} "
            f"({destination.name})"
        )
        delete_destination_permanently(destination_id)
        await query.edit_message_text(
            f"'{destination.name}' has been permanently deleted.",
            reply_markup=build_main_menu(),
        )

    elif action == "posting_interval":
        settings = get_destination_settings(destination_id)
        current_minutes = settings.posting_interval_minutes if settings else 0

        await query.edit_message_text(
            f"📬 Posting interval for {destination.name}:\n\n"
            f"If set, the bot will wait at least X minutes after the last "
            f"sent news before sending to this channel again.\n\n"
            f"This affects ALL currencies together (not per-currency).\n"
            f"Current setting: {'Off' if current_minutes == 0 else f'{current_minutes} min'}",
            reply_markup=build_posting_interval_menu(destination_id, current_minutes),
        )

    elif action == "set_interval":
        minutes = int(parts[3])
        set_posting_interval(destination_id, minutes)

        label = "Off (no limit)" if minutes == 0 else f"{minutes} minutes"
        logger.info(
            f"User {user_id} set posting interval for destination {destination_id} to {minutes} min"
        )

        await query.edit_message_text(
            f"📬 Posting interval for {destination.name}:\n\n"
            f"If set, the bot will wait at least X minutes after the last "
            f"sent news before sending to this channel again.\n\n"
            f"This affects ALL currencies together (not per-currency).\n"
            f"Current setting: {label}",
            reply_markup=build_posting_interval_menu(destination_id, minutes),
        )

    else:
        logger.warning(f"Unknown destination action: {action}")