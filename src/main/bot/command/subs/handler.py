"""
Command and conversation handlers used by "subscriptions" command.
Handling of "subscriptions" command is split into two handlers.
Regular command handler only creates initial inline keyboard.
Conversation handler handles all inline keyboard queries.
This way whole conversation handler can handle single message.
"""

from telegram.ext import CallbackQueryHandler, CommandHandler, ConversationHandler

from bot.command.subs.conversation_state import ConversationState
from bot.command.subs.list_details import list_details
from bot.command.subs.list_names import list_names
from bot.command.subs.list_types import followup_list_feed_types, initial_list_feed_types
from bot.command.subs.query_data import DetailsData, NamesData, RemoveFeedData, TypesData
from bot.command.subs.remove_feed import remove_subscription, request_confirmation
from bot.user_filter import USER_FILTER


def subscriptions_initial_handler() -> CommandHandler:
    """Initial handler responding to "subscriptions" command itself, creates initial query"""
    return CommandHandler("subscriptions", initial_list_feed_types, USER_FILTER)


def subscriptions_followup_handler() -> ConversationHandler:
    """Followup conversation handler for inline keyboard queries"""
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(list_names, NamesData)],
        states={
            ConversationState.LIST_NAMES: [
                CallbackQueryHandler(list_details, DetailsData),
                CallbackQueryHandler(followup_list_feed_types, TypesData),
            ],
            ConversationState.SHOW_DETAILS: [
                CallbackQueryHandler(request_confirmation, RemoveFeedData),
                CallbackQueryHandler(list_names, NamesData),
                CallbackQueryHandler(followup_list_feed_types, TypesData),
            ],
            ConversationState.CONFIRM_REMOVAL: [
                CallbackQueryHandler(remove_subscription, RemoveFeedData),
                CallbackQueryHandler(list_details, DetailsData),
                CallbackQueryHandler(list_names, NamesData),
                CallbackQueryHandler(followup_list_feed_types, TypesData),
            ],
            ConversationState.LIST_TYPES: [CallbackQueryHandler(list_names, NamesData)],
        },
        fallbacks=[CallbackQueryHandler(followup_list_feed_types)],
        per_message=True,
        name="subscriptions_followup_handler",
        persistent=True,
    )
