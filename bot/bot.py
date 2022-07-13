# TODO Perhaps add "details" command showing feed link, etc.
# TODO Was removing the FeedEntry/FeedMedia/FeedData namedtuples actually a good idea?
# Perhaps a DataClass would be better? At least for FeedMedia, to avoid complex return types.
# TODO Perhaps add a "get" command, which will just dump a feed to a user

from logging import getLogger

from settings import TOKEN
from telegram.ext import Application, ApplicationBuilder, Defaults

from bot.command.add import add_conversation_handler
from bot.command.hello import hello_command_handler
from bot.command.list import list_command_handler
from bot.command.remove import remove_conversation_handler
from bot.command.remove_all import remove_all_conversation_handler
from bot.command.start_help import start_help_command_handler
from bot.error_handler import handle_errors
from bot.update_checker import start_checking_for_updates

_UPDATE_HANDLERS = [
    start_help_command_handler(),
    hello_command_handler(),
    list_command_handler(),
    add_conversation_handler(),
    remove_conversation_handler(),
    remove_all_conversation_handler(),
]

_logger = getLogger(__name__)


def run_bot() -> None:
    application = ApplicationBuilder().token(TOKEN).defaults(Defaults("HTML")).build()
    _configure_handlers(application)
    start_checking_for_updates(application.job_queue)
    application.run_polling()


def _configure_handlers(application: Application) -> None:
    _logger.info("Configuring handlers...")
    application.add_handlers(_UPDATE_HANDLERS)
    application.add_error_handler(handle_errors)
