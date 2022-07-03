from logging import info

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes


def start_command_handler():
    return CommandHandler("start", start)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info(f"Start from chat ID=[{update.effective_chat.id}]")
    await update.message.reply_text("Simple Web Comics bot based on RSS feeds!")
