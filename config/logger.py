

import logging
import os
from logging.handlers import RotatingFileHandler

from config.settings import LOG_LEVEL


LOG_DIRECTORY = "logs"
os.makedirs(LOG_DIRECTORY, exist_ok=True)

LOG_FILE_PATH = os.path.join(LOG_DIRECTORY, "bot.log")


_numeric_log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)


def get_logger(module_name: str) -> logging.Logger:


    logger = logging.getLogger(module_name)



    if logger.handlers:
        return logger

    logger.setLevel(_numeric_log_level)


    log_format = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )



    file_handler = RotatingFileHandler(
        LOG_FILE_PATH,
        maxBytes=5 * 1024 * 1024,  
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(log_format)




    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger