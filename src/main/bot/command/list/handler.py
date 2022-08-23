from telegram.ext import CallbackQueryHandler, CommandHandler, ConversationHandler

from bot.command.list.conversation_state import State
from bot.command.list.fallback import fallback
from bot.command.list.feed_name import list_names
from bot.command.list.feed_type import followup_list_request, initial_list_request
from bot.command.list.query_data import ListNamesData
from bot.user_filter import USER_FILTER


def list_initial_handler() -> CommandHandler:
    return CommandHandler("list", initial_list_request, USER_FILTER)


def list_followup_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(list_names, lambda data: isinstance(data, ListNamesData))
        ],
        states={
            State.LIST_NAMES: [CallbackQueryHandler(followup_list_request)],
            State.LIST_TYPES: [CallbackQueryHandler(list_names)],
        },
        fallbacks=[CallbackQueryHandler(fallback)],
        per_message=True,
        name="list_followup_handler",
        persistent=True,
    )
