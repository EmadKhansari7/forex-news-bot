
import asyncio

from telegram import Bot
from telegram.error import RetryAfter, TelegramError

from config.logger import get_logger
from config.settings import TELEGRAM_BOT_TOKEN

logger = get_logger(__name__)

_bot = Bot(token=TELEGRAM_BOT_TOKEN)


async def send_message(chat_id: str, text: str) -> bool:

    try:
        await _bot.send_message(chat_id=chat_id, text=text)
        logger.info(f"Message sent successfully to chat_id={chat_id}")
        return True

    except RetryAfter as error:
        wait_seconds = error.retry_after
        logger.warning(
            f"Flood control hit for chat_id={chat_id}. "
            f"Waiting {wait_seconds}s before retrying once."
        )
        await asyncio.sleep(wait_seconds + 1)
        try:
            await _bot.send_message(chat_id=chat_id, text=text)
            logger.info(f"Message sent successfully to chat_id={chat_id} (after retry)")
            return True
        except TelegramError as retry_error:
            logger.error(f"Failed to send message to chat_id={chat_id} after retry: {retry_error}")
            return False

    except TelegramError as error:
        logger.error(f"Failed to send message to chat_id={chat_id}: {error}")
        return False