# TODO Allow removing feed via a single command, rather than a conversation

from logging import info

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import CommandHandler, ConversationHandler, ContextTypes, MessageHandler
from telegram.ext.filters import COMMAND, TEXT

from db import get_rss_data_for_chat, remove_feed_link_id_db
from rss_checking import cancel_checking_job

REMOVE_HELP_MESSAGE = "/remove - remove subscription for a given feed"
CONFIRM_REMOVAL_YES = "Yes"
CONFIRM_REMOVAL_NO = "No"
REMOVE_NAME, CONFIRM = range(2)


def remove_conversation_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("remove", request_feed_name)],
        states={
            REMOVE_NAME: [MessageHandler(TEXT & ~COMMAND, confirm_removal)],
            CONFIRM: [MessageHandler(TEXT & ~COMMAND, remove_subscription)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info(f"User cancelled removing subscription chat ID=[{update.effective_chat.id}].")
    await update.message.reply_text(
        "Cancelled removing subscription", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def request_feed_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info(f"User requested cancellation of subscription.")
    all_feed_names = [
        [feed_data.feed_name]
        for feed_data in get_rss_data_for_chat(update.effective_chat.id)
    ]
    if not all_feed_names:
        await update.message.reply_text("No subscriptions to remove")
        return ConversationHandler.END
    await update.message.reply_text(
        "Select RSS feed to remove, or /cancel",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=all_feed_names,
            one_time_keyboard=True,
            resize_keyboard=True,
            input_field_placeholder="Select RSS feed to remove",
        ),
    )
    return REMOVE_NAME


async def confirm_removal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    feed_name = update.message.text
    info(f"User provided feed name to remove [{feed_name}]")
    context.user_data[REMOVE_NAME] = feed_name
    confirmation_keyboard = [[CONFIRM_REMOVAL_YES, CONFIRM_REMOVAL_NO]]
    await update.message.reply_text(
        f"Confirm removal of <b>{feed_name}</b>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=confirmation_keyboard,
            one_time_keyboard=True,
            resize_keyboard=True,
            input_field_placeholder="Confirm removal",
        ),
    )
    return CONFIRM


async def remove_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    confirmation = update.message.text
    if confirmation != CONFIRM_REMOVAL_YES:
        return await cancel(update, context)
    feed_name = context.user_data[REMOVE_NAME]
    info(f"User confirmed removal of feed=[{feed_name}]")
    chat_id = update.effective_chat.id
    cancel_checking_job(context, chat_id, feed_name)
    removed_count = remove_feed_link_id_db(chat_id, feed_name)
    if removed_count:
        info(f"RSS chat_id=[{chat_id}] name=[{feed_name}] was removed.")
        await update.message.reply_text(
            f"Removed subscription for <b>{feed_name}</b>!", parse_mode="HTML"
        )
        return ConversationHandler.END
    info(
        f"Removed no entries for chat_id=[{chat_id}] name=[{feed_name}], "
        f"most likely this RSS name doesn't exist."
    )
    await update.message.reply_text(
        f"No subscription with name <b>{feed_name}</b> to remove!",
        parse_mode="HTML",
    )
    return await request_feed_name(update, context)
