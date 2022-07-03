from logging import info

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes


def help_command_handler():
    return CommandHandler("help", help)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info(f"Help from chat ID=[{update.effective_chat.id}]")
    await update.message.reply_text(
        "/start - prints start message"
        "\n/list - list all subscriptions"
        "\n/add - adds subscription for a given feed"
        "\n/remove - remove subscription for a given feed"
        "\n/help - prints this help message",
        parse_mode="HTML",
    )
