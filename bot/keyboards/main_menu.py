

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
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="menu:main")])

    return InlineKeyboardMarkup(keyboard)


def build_destination_detail_menu(destination_id: int) -> InlineKeyboardMarkup:

    keyboard = [
        [InlineKeyboardButton("🎛 Currency Filters", callback_data=f"dest:{destination_id}:filters")],
        [InlineKeyboardButton("🔔 Alert Settings", callback_data=f"dest:{destination_id}:alerts")],
        [InlineKeyboardButton("⬅️ Back to channel list", callback_data="menu:channels")],
    ]
    return InlineKeyboardMarkup(keyboard)