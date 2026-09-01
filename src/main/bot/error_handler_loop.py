"""
Module handling all errors within the bot.

It can also detect when chat is deleted and stopped,
after which all data related to this specific chat is deleted.
"""

from loguru import logger
from telegram import Update
from telegram.error import Forbidden
from telegram.ext import ContextTypes

from db.wrapper import remove_stored_chat_data


async def handle_errors(update: object | None, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update and isinstance(update, Update) and update.effective_chat is not None:
        await _handle_update_error(update, context)
    elif context.job is not None:
        await _handle_job_error(context)
    else:
        logger.opt(exception=context.error).error("Unexpected error occurred: ")


async def _handle_update_error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    error = context.error
    if type(error) is Forbidden and chat_id:
        await _handle_forbidden_error(chat_id)
    elif chat_id:
        logger.opt(exception=error).warning(f"[{chat_id}] Error when handling an update: ")
        await context.bot.send_message(
            chat_id, f"Error when handling an update:\n{error}", parse_mode=None
        )


async def _handle_job_error(context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.job.chat_id is None or context.job.data is None:
        logger.opt(exception=context.error).error("Unexpected error occurred: ")
    elif type(context.error) is Forbidden:
        await _handle_forbidden_error(context.job.chat_id)
    else:
        await _handle_unexpected_error(context)


async def _handle_forbidden_error(chat_id: int) -> None:
    logger.warning(f"[{chat_id}] Cannot send updates to chat, removing chat data")
    await remove_stored_chat_data(chat_id)


async def _handle_unexpected_error(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = context.job.chat_id
    job_data = context.job.data
    context.job.data = None
    logger.opt(exception=context.error).warning(
        f"[{chat_id}] Unexpected error occurred when checking [{job_data}]: "
    )
    await context.bot.send_message(
        chat_id,
        f"Unexpected error occurred when checking {job_data}:\n{context.error}",
        parse_mode=None,
    )
