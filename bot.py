# TODO Perhaps add "details" command showing feed link, etc

from logging import INFO, FileHandler, StreamHandler, basicConfig, getLogger
from sys import stdout

from telegram.ext import ApplicationBuilder, JobQueue

from commands.add import add_conversation_handler
from commands.hello import hello_command_handler
from commands.list import list_command_handler
from commands.remove import remove_conversation_handler
from commands.remove_all import remove_all_conversation_handler
from commands.start_help import start_help_command_handler
from db import get_all_data_from_db
from settings import LOG_PATH, TOKEN
from update_checker import add_check_for_updates_job

_logger = getLogger("bot.main")


def _main() -> None:
    _configure_logging()
    _logger.info("Bot starting...")
    application = ApplicationBuilder().token(TOKEN).build()
    _logger.info("Bot started, setting handlers...")
    application.add_handler(start_help_command_handler())
    application.add_handler(hello_command_handler())
    application.add_handler(list_command_handler())
    application.add_handler(add_conversation_handler())
    application.add_handler(remove_conversation_handler())
    application.add_handler(remove_all_conversation_handler())
    _logger.info("Handlers configured, starting checking for updates...")
    _start_all_checking_for_updates(application.job_queue)
    _logger.info("Checking for updates started, starting polling...")
    application.run_polling()


def _configure_logging() -> None:
    logging_handlers = [StreamHandler(stdout)]
    log_file_path = LOG_PATH
    if log_file_path:
        logging_handlers += [FileHandler(log_file_path)]
    basicConfig(
        format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
        level=INFO,
        handlers=logging_handlers,
    )


def _start_all_checking_for_updates(job_queue: JobQueue) -> None:
    data_to_look_up = {chat_id: data for chat_id, data in get_all_data_from_db().items() if data}
    for chat_id, data in data_to_look_up.items():
        for feed_data in data:
            add_check_for_updates_job(job_queue, chat_id, feed_data)


if __name__ == "__main__":
    _main()
