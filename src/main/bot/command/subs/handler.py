"""
Command and conversation handlers used by "subscriptions" command.
Handling of "subscriptions" command is split into two handlers.
Regular command handler only creates initial inline keyboard.
Conversation handler handles all inline keyboard queries.
This way whole conversation handler can be handle single message.
"""

from typing import Any
from telegram.ext import CallbackQueryHandler, CommandHandler, ConversationHandler

from bot.command.subs.conversation_state import ConversationState
from bot.command.subs.list_details import list_details
from bot.command.subs.list_names import list_names
from bot.command.subs.list_types import followup_list_feed_types, initial_list_feed_types
from bot.command.subs.query_data import DetailsData, NamesData, TypesData, RemoveFeedData
from bot.command.subs.remove_feed import request_confirmation, remove_subscription
from bot.user_filter import USER_FILTER


def subscriptions_initial_handler() -> CommandHandler:
    """Initial handler responding to "subscriptions" command itself, creates initial query"""
    return CommandHandler("subscriptions", initial_list_feed_types, USER_FILTER)


def subscriptions_followup_handler() -> ConversationHandler:
    """Followup conversation handler for inline keyboard queries"""
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(list_names, _is_list_names_data)],
        states={
            ConversationState.LIST_NAMES: [
                CallbackQueryHandler(list_details, _is_list_details_data),
                CallbackQueryHandler(followup_list_feed_types, _is_list_types_data),
            ],
            ConversationState.SHOW_DETAILS: [
                CallbackQueryHandler(request_confirmation, _is_remove_data),
                CallbackQueryHandler(list_names, _is_list_names_data),
                CallbackQueryHandler(followup_list_feed_types, _is_list_types_data),
            ],
            ConversationState.CONFIRM_REMOVAL: [
                CallbackQueryHandler(remove_subscription, _is_remove_data),
                CallbackQueryHandler(list_details, _is_list_details_data),
                CallbackQueryHandler(list_names, _is_list_names_data),
                CallbackQueryHandler(followup_list_feed_types, _is_list_types_data),
            ],
            ConversationState.LIST_TYPES: [CallbackQueryHandler(list_names, _is_list_names_data)],
        },
        fallbacks=[CallbackQueryHandler(followup_list_feed_types)],
        per_message=True,
        name="subscriptions_followup_handler",
        persistent=True,
    )


def _is_list_names_data(data: Any) -> bool:
    return isinstance(data, NamesData)


def _is_list_types_data(data: Any) -> bool:
    return isinstance(data, TypesData)


def _is_list_details_data(data: Any) -> bool:
    return isinstance(data, DetailsData)


def _is_remove_data(data: Any) -> bool:
    return isinstance(data, RemoveFeedData)
