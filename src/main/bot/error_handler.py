"""
Module handling all errors within the bot.

It can also detect when chat is deleted and stopped,
after which all data related to this specific chat is deleted.
"""

from html import escape

from loguru import logger
from telegram import Update
from telegram.error import Forbidden
from telegram.ext import ContextTypes

from bot.sender import send_update
from db.wrapper import remove_stored_chat_data, update_latest_message_id


async def handle_errors(update: object | None, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update is None and context.job is None:
        logger.opt(exception=context.error).error("Unexpected error occurred: ")
    elif update and isinstance(update, Update) and update.effective_chat is not None:
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
    chat_id = context.job.chat_id
    error = context.error
    if chat_id is None:
        logger.opt(exception=error).error("Error occured when scheduling all update jobs: ")
    elif type(error) is Forbidden:
        await _handle_forbidden_error(chat_id)
    elif context.job.data is None:
        logger.opt(exception=error).error(f"[{chat_id}] Error occured when handling previous one: ")
    elif type(context.job.data) is int:
        await _handle_update_retry_error(context, chat_id, error)
    elif type(context.job.data) is tuple and len(context.job.data) == 7:
        await _handle_send_error(context, chat_id, error)
    elif type(context.job.data) is tuple and len(context.job.data) == 6:
        await _handle_prepare_update_error(context, chat_id, error)
    else:
        await _handle_unexpected_error(context, chat_id, error)


async def _handle_forbidden_error(chat_id: int) -> None:
    logger.warning(f"[{chat_id}] Cannot send updates to chat, removing chat data")
    await remove_stored_chat_data(chat_id)


async def _handle_update_retry_error(
    context: ContextTypes.DEFAULT_TYPE, chat_id: int, error: Exception
) -> None:
    logger.opt(exception=error).warning(f"[{chat_id}] Error occurred when handling previous one: ")
    context.job.data = None
    await context.bot.send_message(
        chat_id, f"Error occurred when handling a previous error:\n{error}", parse_mode=None
    )


async def _handle_send_error(
    context: ContextTypes.DEFAULT_TYPE, chat_id: int, error: Exception
) -> None:
    logger.opt(exception=error).warning(f"[{chat_id}] Trying to resend data without media due to: ")
    _, feed_type, feed_name, link, title, description, latest_message_id = context.job.data
    context.job.data = chat_id
    description = f"Error when sending update: <b>{escape(str(error))}</b>\n\n{description}"
    latest_message_id = await send_update(
        context.bot, chat_id, feed_type, feed_name, link, title, description, latest_message_id
    )
    await update_latest_message_id(chat_id, feed_type, feed_name, latest_message_id)


async def _handle_prepare_update_error(
    context: ContextTypes.DEFAULT_TYPE, chat_id: int, error: Exception
) -> None:
    logger.opt(exception=error).warning(f"[{chat_id}] Error when preparing an update: ")
    _, feed_type, feed_name, _, _, _ = context.job.data
    context.job.data = chat_id
    await context.bot.send_message(
        chat_id,
        f"Error when preparing an update for {feed_name} in {feed_type}:\n{error}",
        parse_mode=None,
    )


async def _handle_unexpected_error(
    context: ContextTypes.DEFAULT_TYPE, chat_id: int, error: Exception
) -> None:
    logger.opt(exception=error).warning(f"[{chat_id}] Unexpected error occurred: ")
    context.job.data = None
    await context.bot.send_message(chat_id, f"Unexpected error occurred:\n{error}", parse_mode=None)
