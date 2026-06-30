from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from database.models import FilterSettings


def build_currency_filter_menu(
    destination_id: int, filters: list[FilterSettings]
) -> InlineKeyboardMarkup:

    keyboard = []

    sorted_filters = sorted(filters, key=lambda item: item.currency)

    for filter_item in sorted_filters:
        status_icon = "✅" if filter_item.is_enabled else "❌"
        button_text = f"{status_icon} {filter_item.currency} (min: {filter_item.min_impact})"
        callback_data = f"dest:{destination_id}:toggle_currency:{filter_item.currency}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

    keyboard.append(
        [InlineKeyboardButton(
            "⬅️ Back",
            callback_data=f"dest:{destination_id}:open",
        )]
    )

    return InlineKeyboardMarkup(keyboard)