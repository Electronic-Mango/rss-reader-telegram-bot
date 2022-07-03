from logging import getLogger
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

logger = getLogger(__name__)



def hello_command_handler():
    return CommandHandler("hello", hello)


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Hello from chat ID: [{update.effective_chat.id}]")
    await update.message.reply_text(choice(HELLO_RESPONSES))
