from logging import getLogger

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

_logger = getLogger(__name__)


async def fallback(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    _logger.info(f"[{update.effective_chat.id}] Cancelling conversation due to a fallback")
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Cancelled listing subscriptions due to an error")
    return ConversationHandler.END
