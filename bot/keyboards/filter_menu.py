from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from database.models import DestinationSettings, FilterSettings


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


_ALERT_TYPE_LABELS = {
    "15min": "15 minutes before release",
    "5min": "5 minutes before release",
    "at_release": "At release time",
}


def build_alert_settings_menu(
    destination_id: int, settings: DestinationSettings
) -> InlineKeyboardMarkup:

    alert_states = {
        "15min": settings.alert_15min_enabled,
        "5min": settings.alert_5min_enabled,
        "at_release": settings.alert_at_release_enabled,
    }

    keyboard = []

    for alert_type, label in _ALERT_TYPE_LABELS.items():
        is_enabled = alert_states[alert_type]
        status_icon = "✅" if is_enabled else "❌"
        button_text = f"{status_icon} {label}"
        callback_data = f"dest:{destination_id}:toggle_alert:{alert_type}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

    keyboard.append(
        [InlineKeyboardButton(
            "⬅️ Back",
            callback_data=f"dest:{destination_id}:open",
        )]
    )

    return InlineKeyboardMarkup(keyboard)