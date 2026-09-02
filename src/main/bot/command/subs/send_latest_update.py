from loguru import logger
from telegram import Bot, Update
from telegram.ext import ContextTypes

from bot.command.subs.conversation_state import ConversationState
from bot.sender import send_update
from db.wrapper import get_latest_message_id
from feed.parser import parse_description, parse_link, parse_media_links, parse_title
from feed.reader import get_parsed_feed, get_sorted_entries


async def send_latest_update(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> ConversationState:
    """Send latest entry for selected subscription, mostly meant for debugging purposes."""
    query = update.callback_query
    await query.answer()
    bot = context.bot
    chat_id = update.effective_chat.id
    type, name, _ = query.data
    await _handle_update(bot, chat_id, type, name)
    return ConversationState.SHOW_DETAILS


async def _handle_update(bot: Bot, chat_id: int, type: str, name: str) -> None:
    if not (entries := get_sorted_entries(await get_parsed_feed(type, name))):
        logger.warning(f"[{chat_id}] No entries found for [{type}] [{name}]")
        await bot.send_message(chat_id, f"No entries found for <b>{name}</b>!")
        return
    logger.info(f"[{chat_id}] Resending latest update for [{type}] [{name}]")
    latest_entry = entries[0]
    await send_update(
        bot,
        chat_id,
        type,
        name,
        parse_link(latest_entry),
        parse_title(latest_entry, type),
        parse_description(latest_entry, type),
        await get_latest_message_id(chat_id, type, name),
        parse_media_links(latest_entry),
        False,
    )
