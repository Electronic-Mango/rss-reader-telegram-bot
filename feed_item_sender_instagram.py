"""
Sender dedicated for Instagram feeds.
Sends images/videos directly, removes hashtags, etc.
"""

# TODO Split platform specific formating (Instagram) with bot specific one (Telegram)

from logging import getLogger
from re import sub
from requests import get

from telegram import InputMediaPhoto, InputMediaVideo
from telegram.ext import ContextTypes

_MAX_MEDIA_SIZE_PER_MESSAGE = 10

_logger = getLogger(__name__)


async def send_message_instagram(context: ContextTypes.DEFAULT_TYPE, chat_id, rss_name, entry):
    entry_link = entry.url
    summary = _parse_entry_summary(entry.summary)
    message = _format_message(rss_name, entry_link, summary)
    media_groups = [
        entry.media[x : x + _MAX_MEDIA_SIZE_PER_MESSAGE]
        for x in range(0, len(entry.media), _MAX_MEDIA_SIZE_PER_MESSAGE)
    ]
    # Only the last group should have a message
    for media_group in media_groups[:-1]:
        await _handle_attachment_group(context, chat_id, rss_name, media_group)
    await _handle_attachment_group(context, chat_id, rss_name, media_groups[-1], message)


async def _handle_attachment_group(context: ContextTypes.DEFAULT_TYPE, chat_id, rss_name, attachments, message=None):
    if len(attachments) > 10:
        _logger.error(f"Cannot send more attachments than 10 ({rss_name})!")
        return
    if len(attachments) == 1:
        await _send_single_media_based_on_type(context, chat_id, *attachments[0], message)
    else:
        media_list = [_media_object(url, type) for url, type in attachments]
        # Only the first media should have a caption,
        # otherwise actual caption body won't be displayed directly in the message
        media_list[0].caption = message
        await context.bot.send_media_group(chat_id, media_list)


def _format_message(rss_name, entry_link, content):
    message_text = f"{rss_name} on Instagram"
    if content:
        message_text += f":\n{content}"
    max_message_size = 1024 - 3 - 1 - len(entry_link)  # 3 - "...",  1 - new line
    if len(message_text) > max_message_size:
        message_text = f"{message_text[:max_message_size]}..."
    message_text += f"\n{entry_link}"
    return message_text


def _parse_entry_summary(summary):
    summary = sub(r"(<a.+</a>)+", "", summary)
    summary = sub(r"(<video controls>.+</video>)+", "", summary)
    summary = summary.replace("&quot;", '"')
    summary = sub(r"<br( )?(/)?>", "\n", summary)
    summary = sub(r"</p>", "\n", summary)
    summary = summary.replace("(no text)", "")
    summary = "\n".join([line.strip() for line in summary.strip().splitlines() if line.strip()])
    return summary


async def _send_single_media_based_on_type(context: ContextTypes.DEFAULT_TYPE, chat_id, url, type, message):
    if _is_video(url, type):
        await context.bot.send_video(chat_id, video=url, caption=message, supports_streaming=True)
    else:
        await context.bot.send_photo(chat_id, photo=url, caption=message)


def _is_video(url, type):
    if "image" in type:
        _logger.info(f"Type '{type}' treated as image.")
        return False
    response = get(url)
    content_type = response.headers["Content-Type"]
    if "video" in content_type:
        _logger.info(f"Type '{type}' (content-type=[{content_type}]) treated as video.")
        return True
    else:
        _logger.info(f"Type '{type}' (content-type=[{content_type}]) treated as image.")
        return False


def _media_object(url, type):
    if _is_video(url, type):
        return InputMediaVideo(media=url, supports_streaming=True)
    else:
        return InputMediaPhoto(media=url)
