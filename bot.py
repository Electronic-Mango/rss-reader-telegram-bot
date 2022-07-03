from logging import INFO, basicConfig, info
from os import getenv

from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, JobQueue

from commands.add import add_conversation_handler
from commands.hello import hello_command_handler
from commands.help import help_command_handler
from commands.list import list_command_handler
from commands.remove import remove_conversation_handler
from commands.remove_all import remove_all_command_handler
from commands.start import start_command_handler
from db import get_all_rss_from_db
from rss_checking import start_rss_checking


def main():
    load_dotenv()
    configure_logging()
    info("Bot starting...")
    application = ApplicationBuilder().token(getenv("TOKEN")).build()
    info("Bot started, setting handlers...")
    application.add_handler(start_command_handler())
    application.add_handler(help_command_handler())
    application.add_handler(hello_command_handler())
    application.add_handler(list_command_handler())
    application.add_handler(add_conversation_handler())
    application.add_handler(remove_conversation_handler())
    application.add_handler(remove_all_command_handler())
    info("Handlers configured, starting RSS checking...")
    start_all_rss_checking_when_necessary(application.job_queue)
    info("RSS checking triggered, starting polling...")
    application.run_polling()


def configure_logging():
    basicConfig(
        format="%(asctime)s %(name)s %(levelname)s: %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S",
        level=INFO,
    )


def start_all_rss_checking_when_necessary(job_queue: JobQueue):
    data_to_look_up = {chat_id: data for chat_id, data in get_all_rss_from_db().items() if data}
    for chat_id, data in data_to_look_up.items():
        if not data:
            info(f"No RSS feeds to check for chat ID=[{chat_id}].")
            continue
        for rss_data in data:
            start_rss_checking(job_queue, chat_id, rss_data)


if __name__ == "__main__":
    main()
