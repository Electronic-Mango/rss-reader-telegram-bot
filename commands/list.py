from logging import getLogger

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from db import get_feed_data_for_chat

LIST_HELP_MESSAGE = "/list - list all subscriptions"

_logger = getLogger(__name__)


def list_command_handler() -> CommandHandler:
    return CommandHandler("list", _list)


async def _list(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    _logger.info(f"[{chat_id}] Listing all subscriptions")
    feed_data = get_feed_data_for_chat(chat_id)
    if not feed_data:
        await update.message.reply_text("No feeds subscribed.")
    else:
        await _seed_feed_data(update, feed_data)


async def _seed_feed_data(update: Update, feed_data: list[tuple[str, str, str]]) -> None:
    formatted_feed_data = [
        f"<b>{feed_name}</b> - {feed_type}"
        for feed_type, feed_name, _ in feed_data
    ]
    response = "Following feeds are subscribed:\n\n"
    response += "\n".join(sorted(formatted_feed_data))
    await update.message.reply_text(response, parse_mode="HTML")
