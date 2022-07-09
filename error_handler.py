from logging import getLogger

from telegram import Update
from telegram.error import Forbidden
from telegram.ext import ContextTypes, JobQueue

from db import remove_chat_data
from update_checker import cancel_checking_for_chat

_logger = getLogger(__name__)


async def handle_errors(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    error = context.error
    if update is None and context.job is None:
        _logger.error(f"Unexpected error occured:", exc_info=error)
        return
    chat_id = update.effective_chat.id if update is not None else context.job.chat_id
    _logger.warn(f"[{chat_id}] Error when handling update:", exc_info=error)
    if type(error) is Forbidden:
        _logger.warn(f"[{chat_id}] Cannot send updates to chat, removing data and stopping jobs")
        stop_jobs_and_remove_data(context.job_queue, chat_id)
    else:
        await context.bot.send_message(chat_id, f"Error when handling an update:\n{context.error}")


def stop_jobs_and_remove_data(job_queue: JobQueue, chat_id: int) -> None:
    cancel_checking_for_chat(job_queue, chat_id)
    remove_chat_data(chat_id)
