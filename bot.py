# TODO Perhaps add "details" command showing feed link, etc.
# TODO Was removing the FeedEntry/FeedMedia/FeedData namedtuples actually a good idea?
# Perhaps a DataClass would be better? At least for FeedMedia, to avoid complex return types.

from logging import INFO, FileHandler, StreamHandler, basicConfig, getLogger
from sys import stdout

from telegram.ext import Application, ApplicationBuilder, JobQueue

from commands.add import add_conversation_handler
from commands.hello import hello_command_handler
from commands.list import list_command_handler
from commands.remove import remove_conversation_handler
from commands.remove_all import remove_all_conversation_handler
from commands.start_help import start_help_command_handler
from db import initialize_db
from error_handler import handle_errors
from settings import LOG_PATH, LOOKUP_INTERVAL_SECONDS, TOKEN
from update_checker import check_for_all_updates

_logger = getLogger("bot.main")


def _main() -> None:
    _configure_logging()
    initialize_db()
    _logger.info("Creating application...")
    application = ApplicationBuilder().token(TOKEN).build()
    _logger.info("Configuring handlers...")
    _configure_handlers(application)
    _logger.info("Starting checking for updates...")
    # TODO Add a faster initial trigger for checking updates
    application.job_queue.run_repeating(check_for_all_updates, LOOKUP_INTERVAL_SECONDS)
    _logger.info("Starting polling...")
    application.run_polling()


def _configure_logging() -> None:
    logging_handlers = [StreamHandler(stdout)]
    if LOG_PATH:
        logging_handlers += [FileHandler(LOG_PATH)]
    basicConfig(
        format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
        level=INFO,
        handlers=logging_handlers,
    )


def _configure_handlers(application: Application) -> None:
    application.add_handler(start_help_command_handler())
    application.add_handler(hello_command_handler())
    application.add_handler(list_command_handler())
    application.add_handler(add_conversation_handler())
    application.add_handler(remove_conversation_handler())
    application.add_handler(remove_all_conversation_handler())
    application.add_error_handler(handle_errors)


if __name__ == "__main__":
    _main()
