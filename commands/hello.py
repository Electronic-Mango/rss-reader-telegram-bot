from logging import info

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

HELLO_HELP_MESSAGE = "/hello - say hello to the bot"


def hello_command_handler():
    return CommandHandler("hello", hello)


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info(f"Hello from chat ID: [{update.effective_chat.id}]")
    await update.message.reply_text("Hello there!")
