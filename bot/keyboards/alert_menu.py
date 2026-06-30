from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from database.models import DestinationSettings


def build_alert_settings_menu(
    destination_id: int, settings: DestinationSettings
) -> InlineKeyboardMarkup:
    def icon(value: bool) -> str:
        return "✅" if value else "❌"

    keyboard = [
        [InlineKeyboardButton(
            f"{icon(settings.alert_15min_enabled)} 15 minutes before release",
            callback_data=f"dest:{destination_id}:toggle_alert:15min",
        )],
        [InlineKeyboardButton(
            f"{icon(settings.alert_5min_enabled)} 5 minutes before release",
            callback_data=f"dest:{destination_id}:toggle_alert:5min",
        )],
        [InlineKeyboardButton(
            f"{icon(settings.alert_at_release_enabled)} At release time",
            callback_data=f"dest:{destination_id}:toggle_alert:at_release",
        )],
        [InlineKeyboardButton("⬅️ Back", callback_data=f"dest:{destination_id}:open")],
    ]
    return InlineKeyboardMarkup(keyboard)