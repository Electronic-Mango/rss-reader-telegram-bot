"""
Main module, configures logging, intialized the DB and starts the bot.
"""

from logging import INFO, StreamHandler, basicConfig
from logging.handlers import RotatingFileHandler
from sys import stdout

from bot.bot import run_bot
from db.client import initialize_db
from settings import BACKUP_COUNT, LOG_PATH, MAX_BYTES


def _main() -> None:
    _configure_logging()
    initialize_db()
    run_bot()


def _configure_logging() -> None:
    basicConfig(
        format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
        level=INFO,
        handlers=[
            StreamHandler(stdout),
            RotatingFileHandler(LOG_PATH, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT),
        ],
    )


if __name__ == "__main__":
    _main()
