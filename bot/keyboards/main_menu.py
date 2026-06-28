from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from database.models import Destination


def build_main_menu() -> InlineKeyboardMarkup:

    keyboard = [
        [InlineKeyboardButton("📡 Manage Channels", callback_data="menu:channels")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="menu:help")],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_channels_list_menu(destinations: list[Destination]) -> InlineKeyboardMarkup:

    keyboard = []

    for destination in destinations:
        status_icon = "🟢" if destination.is_active else "🔴"
        button_text = f"{status_icon} {destination.name}"
        callback_data = f"dest:{destination.id}:open"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

    keyboard.append(
        [InlineKeyboardButton("➕ Add new channel/group", callback_data="menu:add_channel")]
    )

    keyboard.append(
        [InlineKeyboardButton("⏱ Bot Settings", callback_data="menu:bot_settings")]
    )

    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="menu:main")])

    return InlineKeyboardMarkup(keyboard)


def build_bot_settings_menu(current_interval_minutes: int) -> InlineKeyboardMarkup:

    keyboard = [
        [InlineKeyboardButton(
            "🕐 Change news check interval",
            callback_data="settings:interval:menu",
        )],
        [InlineKeyboardButton("⬅️ Back to channel list", callback_data="menu:channels")],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_interval_selection_menu(current_interval_minutes: int) -> InlineKeyboardMarkup:

    interval_options = [5, 10, 15, 30, 60, 120]

    keyboard = []
    for minutes in interval_options:
        is_current = minutes == current_interval_minutes
        label = f"✅ {minutes} minutes" if is_current else f"{minutes} minutes"
        keyboard.append(
            [InlineKeyboardButton(label, callback_data=f"settings:interval:{minutes}")]
        )

    keyboard.append(
        [InlineKeyboardButton("⬅️ Back", callback_data="menu:bot_settings")]
    )

    return InlineKeyboardMarkup(keyboard)


def build_destination_detail_menu(
    destination_id: int, is_active: bool = True
) -> InlineKeyboardMarkup:

    if is_active:
        lifecycle_button = InlineKeyboardButton(
            "⏸ Deactivate (stop sending news)",
            callback_data=f"dest:{destination_id}:deactivate",
        )
    else:
        lifecycle_button = InlineKeyboardButton(
            "▶️ Reactivate (resume sending news)",
            callback_data=f"dest:{destination_id}:reactivate",
        )

    keyboard = [
        [InlineKeyboardButton("🎛 Currency Filters", callback_data=f"dest:{destination_id}:filters")],
        [InlineKeyboardButton("🔔 Alert Settings", callback_data=f"dest:{destination_id}:alerts")],
        [lifecycle_button],
        [InlineKeyboardButton(
            "🗑 Remove this channel",
            callback_data=f"dest:{destination_id}:confirm_delete",
        )],
        [InlineKeyboardButton("⬅️ Back to channel list", callback_data="menu:channels")],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_delete_confirmation_menu(destination_id: int) -> InlineKeyboardMarkup:

    keyboard = [
        [InlineKeyboardButton(
            "⚠️ Yes, permanently delete",
            callback_data=f"dest:{destination_id}:delete_permanent",
        )],
        [InlineKeyboardButton(
            "Cancel",
            callback_data=f"dest:{destination_id}:open",
        )],
    ]
    return InlineKeyboardMarkup(keyboard)