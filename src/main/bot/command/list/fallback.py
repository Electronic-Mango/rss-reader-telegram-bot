"""
Fallback used by "list" command conversation handler.
It's executed when no function can be run in current state.
"""

from logging import getLogger

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

_logger = getLogger(__name__)


# TODO Is this actually needed in case of "list" command?
async def fallback(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    """Print information about an error to the user and end the conversation"""
    _logger.info(f"[{update.effective_chat.id}] Cancelling conversation due to a fallback")
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Cancelled listing subscriptions due to an error")
    return ConversationHandler.END
