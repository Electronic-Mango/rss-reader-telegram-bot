"""
Module handling the "unpinall" command, allowing users to unpin all messages.
Can be useful when bot is pinning all sent video messages.
"""

from typing import Any, NamedTuple

from loguru import logger
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler

from bot.user_filter import USER_FILTER

UNPIN_ALL_HELP_MESSAGE = "/unpinall - unpin all messages"


class _UnpinAllMessages(NamedTuple):
    cnf: bool


def unpin_all_initial_handler() -> CommandHandler:
    return CommandHandler("unpinall", _request_confirmation, USER_FILTER)


def unpin_all_followup_handlers() -> list[CallbackQueryHandler]:
    return [
        CallbackQueryHandler(_unpin_all_messages, _data_confirmed),
        CallbackQueryHandler(_cancel, _data_rejected),
    ]


def _data_confirmed(data: Any) -> bool:
    return isinstance(data, _UnpinAllMessages) and data.cnf


def _data_rejected(data: Any) -> bool:
    return isinstance(data, _UnpinAllMessages) and not data.cnf


async def _request_confirmation(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    full_chat_info = await update.get_bot().get_chat(chat_id)
    logger.info(f"[{chat_id}] User requested unpinning of all videos")
    if not full_chat_info.pinned_message:
        logger.info(f"[{chat_id}] No messages to unpin")
        await update.message.reply_text("No messages to unpin")
    else:
        await update.message.reply_text(
            "Do you want to unpin all messages?",
            reply_markup=_prepare_keyboard(("Yes", True), ("No", False)),
        )


async def _unpin_all_messages(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    logger.info(f"[{update.effective_chat.id}] Unpinning all messages")
    await update.effective_chat.unpin_all_messages()
    await query.edit_message_text("Unpinned all messages")
    return ConversationHandler.END


async def _cancel(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"[{update.effective_chat.id}] User cancelled unpinning messages")
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("No messages have been unpinned")
    return ConversationHandler.END


def _prepare_keyboard(*keyboard_data: tuple[str, bool]) -> InlineKeyboardMarkup:
    keyboard = [[_prepare_keyboard_button(name, cnf) for name, cnf in keyboard_data]]
    return InlineKeyboardMarkup(keyboard)


def _prepare_keyboard_button(name: str, cnf: bool) -> InlineKeyboardButton:
    return InlineKeyboardButton(name, callback_data=_UnpinAllMessages(cnf))
