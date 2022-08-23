"""
Command and conversation handlers used by "list" command.
Handling of "list" command is split into two handlers.
Regular command handler only creates initial inline keyboard.
Conversation handler handles inline keyboard queries.
This way whole conversation handler can be handler per each message.
"""

from telegram.ext import CallbackQueryHandler, CommandHandler, ConversationHandler

from bot.command.list.conversation_state import State
from bot.command.list.fallback import fallback
from bot.command.list.feed_name import list_names
from bot.command.list.feed_type import followup_list_feed_types, initial_list_feed_types
from bot.command.list.query_data import ListNamesData
from bot.user_filter import USER_FILTER


def list_initial_handler() -> CommandHandler:
    """Initial handler responding to "list" command itself, creates initial query"""
    return CommandHandler("list", initial_list_feed_types, USER_FILTER)


def list_followup_handler() -> ConversationHandler:
    """Followup conversation handler handling inline keyboard queries"""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(list_names, lambda data: isinstance(data, ListNamesData))
        ],
        states={
            State.LIST_NAMES: [CallbackQueryHandler(followup_list_feed_types)],
            State.LIST_TYPES: [CallbackQueryHandler(list_names)],
        },
        fallbacks=[CallbackQueryHandler(fallback)],
        per_message=True,
        name="list_followup_handler",
        persistent=True,
    )
