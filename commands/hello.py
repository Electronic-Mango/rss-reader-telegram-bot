from logging import info
from random import choice

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

HELLO_HELP_MESSAGE = "/hello - say hello to the bot"
HELLO_RESPONSES = [
    "Hello there!",
    "Hello!",
    "Hi!",
    "Greetings!",
    "Howdy!",
    "Hey!",
]


def hello_command_handler():
    return CommandHandler("hello", hello)


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info(f"Hello from chat ID: [{update.effective_chat.id}]")
    await update.message.reply_text(choice(HELLO_RESPONSES))
