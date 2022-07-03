from logging import info, warn

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import CommandHandler, ConversationHandler, ContextTypes, MessageHandler
from telegram.ext.filters import COMMAND, TEXT

from db import get_rss_data_for_chat, remove_rss_feed_id_db
from rss_checking import rss_checking_job_name

REMOVE_HELP_MESSAGE = "/remove - remove subscription for a given feed"
REMOVE_NAME = range(1)


def remove_conversation_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("remove", request_feed_name)],
        states={
            REMOVE_NAME: [MessageHandler(TEXT & ~COMMAND, remove_subscription)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info(f"User cancelled removing subscription chat ID=[{update.effective_chat.id}].")
    await update.message.reply_text(
        "Cancelled removing subscription.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def request_feed_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info(f"User requested cancellation of subscription.")
    all_feeds = [
        [feed_data.rss_name]
        for feed_data in get_rss_data_for_chat(update.effective_chat.id)
    ]
    await update.message.reply_text(
        "Select RSS feed to remove, or /cancel.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=all_feeds,
            one_time_keyboard=True,
            resize_keyboard=True,
            input_field_placeholder="Select RSS feed to remove",
        ),
    )
    return REMOVE_NAME


async def remove_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    feed_name = update.message.text
    info(f"User provided feed name to remove [{feed_name}]")
    chat_id = update.effective_chat.id
    cancel_checking_job(context, chat_id, feed_name)
    removed_count = remove_rss_feed_id_db(chat_id, feed_name)
    if removed_count:
        info(f"RSS chat_id=[{chat_id}] name=[{feed_name}] was removed.")
        await update.message.reply_text(
            f"Removed subscription for <b>{feed_name}</b>!",
            parse_mode="HTML"
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


def cancel_checking_job(context: ContextTypes.DEFAULT_TYPE, chat_id, feed_name):
    job_name = rss_checking_job_name(chat_id, feed_name)
    jobs = context.job_queue.get_jobs_by_name(job_name)
    for job in jobs:
        job.schedule_removal()
    if len(jobs) > 1:
        warn(f"Found [{len(jobs)}] jobs with name [{job_name}]!")
