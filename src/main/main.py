"""
Main module, configures logging, initialized the DB and starts the bot.
"""

from logging.handlers import RotatingFileHandler

from loguru import logger

from bot.telegram_bot import run_bot
from db.client import initialize_db
from settings import BACKUP_COUNT, LOG_PATH, MAX_BYTES


def _main() -> None:
    _configure_logging()
    initialize_db()
    run_bot()


def _configure_logging() -> None:
    logger.add(RotatingFileHandler(LOG_PATH, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT))


if __name__ == "__main__":
    _main()
