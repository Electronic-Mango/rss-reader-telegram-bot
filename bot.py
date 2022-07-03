# TODO How to handle situations where user removed conversation?
# TODO Perhaps add "details" command showing feed link, etc

from logging import INFO, FileHandler, StreamHandler, basicConfig, getLogger
from os import getenv
from sys import stdout

from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, JobQueue

from commands.add import add_conversation_handler
from commands.hello import hello_command_handler
from commands.list import list_command_handler
from commands.remove import remove_conversation_handler
from commands.remove_all import remove_all_conversation_handler
from commands.start_help import start_help_command_handler
from db import get_all_rss_from_db
from rss_checking import start_rss_checking

logger = getLogger("bot.main")


def main():
    load_dotenv()
    configure_logging()
    logger.info("Bot starting...")
    application = ApplicationBuilder().token(getenv("TOKEN")).build()
    logger.info("Bot started, setting handlers...")
    application.add_handler(start_help_command_handler())
    application.add_handler(hello_command_handler())
    application.add_handler(list_command_handler())
    application.add_handler(add_conversation_handler())
    application.add_handler(remove_conversation_handler())
    application.add_handler(remove_all_conversation_handler())
    logger.info("Handlers configured, starting RSS checking...")
    start_all_rss_checking_when_necessary(application.job_queue)
    logger.info("RSS checking triggered, starting polling...")
    application.run_polling()


def configure_logging():
    logging_handlers = [StreamHandler(stdout)]
    log_file_path = getenv("logger_PATH")
    if log_file_path:
        logging_handlers += [FileHandler(log_file_path)]
    basicConfig(
        format="%(asctime)s %(name)s %(levelname)s: %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S",
        level=INFO,
        handlers=logging_handlers,
    )


def start_all_rss_checking_when_necessary(job_queue: JobQueue):
    data_to_look_up = {chat_id: data for chat_id, data in get_all_rss_from_db().items() if data}
    for chat_id, data in data_to_look_up.items():
        if not data:
            logger.info(f"No RSS feeds to check for chat ID=[{chat_id}].")
            continue
        for rss_data in data:
            start_rss_checking(job_queue, chat_id, rss_data)


if __name__ == "__main__":
    main()
