from logging import getLogger

from settings import TOKEN
from telegram.ext import Application, ApplicationBuilder, Defaults, JobQueue

from bot.command.add import add_conversation_handler
from bot.command.cancel import cancel_command_handler
from bot.command.hello import hello_command_handler
from bot.command.list import list_command_handler
from bot.command.remove import remove_conversation_handler
from bot.command.remove_all import remove_all_conversation_handler
from bot.command.start_help import start_help_command_handler
from bot.error_handler import handle_errors
from bot.update_checker import check_for_all_updates
from settings import LOOKUP_INITIAL_DELAY_SECONDS, LOOKUP_INTERVAL_SECONDS

_UPDATE_HANDLERS = [
    add_conversation_handler(),
    cancel_command_handler(),
    hello_command_handler(),
    list_command_handler(),
    remove_conversation_handler(),
    remove_all_conversation_handler(),
    start_help_command_handler(),
]

_logger = getLogger(__name__)


def run_bot() -> None:
    application = ApplicationBuilder().token(TOKEN).defaults(Defaults("HTML")).build()
    _configure_handlers(application)
    _start_checking_for_updates(application.job_queue)
    application.run_polling()


def _configure_handlers(application: Application) -> None:
    _logger.info("Configuring handlers...")
    application.add_handlers(_UPDATE_HANDLERS)
    application.add_error_handler(handle_errors)


def _start_checking_for_updates(job_queue: JobQueue) -> None:
    _logger.info("Starting checking for updates...")
    job_queue.run_repeating(
        callback=check_for_all_updates,
        interval=LOOKUP_INTERVAL_SECONDS,
        first=LOOKUP_INITIAL_DELAY_SECONDS,
    )
