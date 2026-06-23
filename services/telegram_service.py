
from telegram import Bot
from telegram.error import TelegramError

from config.logger import get_logger
from config.settings import TELEGRAM_BOT_TOKEN

logger = get_logger(__name__)

_bot = Bot(token=TELEGRAM_BOT_TOKEN)


async def send_message(chat_id: str, text: str) -> bool:

    try:
        await _bot.send_message(chat_id=chat_id, text=text)
        logger.info(f"Message sent successfully to chat_id={chat_id}")
        return True

    except TelegramError as error:

        logger.error(f"Failed to send message to chat_id={chat_id}: {error}")
        return False