"""Main module, configures logging, initializes the DB and starts the bot."""

from argparse import ArgumentParser, Namespace
from logging.handlers import RotatingFileHandler
from pathlib import Path

from loguru import logger

from bot.telegram_bot import run_bot
from settings_new import Settings


def _main() -> None:
    args = _parse_arguments()
    Settings.init(args.default_settings_path, args.custom_settings_path)
    _configure_logging()
    run_bot()


def _parse_arguments() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument(
        "--default-settings-path",
        type=Path,
        help="Path to the default settings YAML file",
    )
    parser.add_argument(
        "--custom-settings-path",
        type=Path,
        nargs="+",
        help="Paths to the custom settings YAML file",
    )
    return parser.parse_args()


def _configure_logging() -> None:
    logger.add(
        RotatingFileHandler(
            Settings.LOG_PATH,
            maxBytes=Settings.MAX_BYTES,
            backupCount=Settings.BACKUP_COUNT,
        )
    )


if __name__ == "__main__":
    _main()
