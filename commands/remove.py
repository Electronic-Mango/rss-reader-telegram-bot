from logging import info

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from rss_checking import rss_checking_job_name
from rss_db import remove_rss_feed_id_db


def remove_command_handler():
    return CommandHandler("remove", remove)


async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info(f"Remove from chat ID: [{update.effective_chat.id}]")
    if len(context.args) != 1:
        await update.message.reply_text("Incorrect number of arguments! Pass RSS feed name.")
        return
    rss_name = context.args[0]
    chat_id = update.effective_chat.id
    jobs = context.job_queue.get_jobs_by_name(rss_checking_job_name(chat_id, rss_name))
    for job in jobs:
        job.schedule_removal()
    removed_count = remove_rss_feed_id_db(chat_id, rss_name)
    if removed_count:
        info(f"RSS chat_id=[{chat_id}] name=[{rss_name}] was removed.")
        await update.message.reply_text(f'Removed subscription for "{rss_name}"!')
    else:
        info(
            f"Removed no entries for chat_id=[{chat_id}] name=[{rss_name}], "
            f"most likely this RSS name doesn't exist."
        )
        await update.message.reply_text(f'No subscription with name "{rss_name}" to remove!')
