from logging import info

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ConversationHandler, CommandHandler, ContextTypes, MessageHandler
from telegram.ext.filters import COMMAND, TEXT

from db import get_rss_data_for_chat, remove_chat_collection
from rss_checking import cancel_checking_job

REMOVE_ALL_HELP_MESSAGE = "/remove_all - remove all subscriptions"
CONFIRM_1_YES = "Yes"
CONFIRM_2_YES = "Yes, I'm sure"
CONFIRM_1, CONFIRM_2 = range(2)


def remove_all_conversation_handler():
    return ConversationHandler("remove_all", remove_all)


def remove_all_conversation_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("remove_all", request_confirmation_1)],
        states={
            CONFIRM_1: [MessageHandler(TEXT & ~COMMAND, request_confirmation_2)],
            CONFIRM_2: [MessageHandler(TEXT & ~COMMAND, remove_all)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info(f"User cancelled removing all subscriptions chat ID=[{update.effective_chat.id}].")
    await update.message.reply_text(
        "Cancelled removing all subscriptions", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def request_confirmation_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info(f"User requested removal of all subscriptions")
    feed_data_for_this_chat = get_rss_data_for_chat(update.effective_chat.id)
    if not feed_data_for_this_chat:
        await update.message.reply_text("There are no subscriptions to remove")
        return ConversationHandler.END
    confirmation_keyboard = [[CONFIRM_1_YES, "No"]]
    await update.message.reply_text(
        "Confirm removal of all feeds",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=confirmation_keyboard,
            # Intentionally is not a one time keyboard.
            # Confirming removal will trigger a second keyboard, which is one time.
            # Cancellation will hide the keyboard.
            resize_keyboard=True,
            input_field_placeholder="Confirm removal",
        ),
    )
    return CONFIRM_1


async def request_confirmation_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    confirmation_1 = update.message.text
    if confirmation_1 != CONFIRM_1_YES:
        info("User cancelled the removal for first confirmation")
        return await cancel(update, context)
    info(f"User confirmed removal of all subscriptions for the first time")
    confirmation_keyboard = [[CONFIRM_2_YES, "No, don't remove"]]
    await update.message.reply_text(
        "Are you sure you want to remove <b>all</b> subscriptions?",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=confirmation_keyboard,
            one_time_keyboard=True,
            resize_keyboard=True,
            input_field_placeholder="Confirm removal",
        ),
    )
    return CONFIRM_2


async def remove_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    confirmation_2 = update.message.text
    if confirmation_2 != CONFIRM_2_YES:
        info("User cancelled the removal for second confirmation")
        return await cancel(update, context)
    chat_id = update.effective_chat.id
    info(f"Remove all from chat ID: [{chat_id}]")
    for feed_data in get_rss_data_for_chat(chat_id):
        cancel_checking_job(context, chat_id, feed_data.feed_name)
    remove_chat_collection(chat_id)
    await update.message.reply_text("Removed all subscriptions")
    return ConversationHandler.END
