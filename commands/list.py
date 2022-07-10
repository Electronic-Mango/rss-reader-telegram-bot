# TODO Unify how feeds are printed when listing and when removing
from logging import getLogger

from telegram import Message, Update
from telegram.ext import CommandHandler, ContextTypes

from db import chat_has_stored_feeds, get_stored_feed_type_and_name

LIST_HELP_MESSAGE = "/list - list all subscriptions"

_logger = getLogger(__name__)


def list_command_handler() -> CommandHandler:
    return CommandHandler("list", _list)


async def _list(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    _logger.info(f"[{chat_id}] Listing all subscriptions")
    if not chat_has_stored_feeds(chat_id):
        await update.message.reply_text("No feeds subscribed")
    else:
        await _send_feed_data(update.message, chat_id)


async def _send_feed_data(message: Message, chat_id: int) -> None:
    formatted_feed_data = [
        f"<b>{feed_name}</b> - {feed_type}"
        for feed_type, feed_name in get_stored_feed_type_and_name(chat_id)
    ]
    response = "Following feeds are subscribed:\n"
    response += "\n".join(sorted(formatted_feed_data))
    await message.reply_text(response, parse_mode="HTML")
