"""
Sender dedicated for Instagram feeds.
Sends images/videos directly, removes hashtags, etc.
"""

from logging import getLogger
from requests import get

from telegram import InputMediaPhoto, InputMediaVideo

from formatter import parse_media, parse_summary
from settings import MAX_MEDIA_ITEMS_PER_MESSSAGE, MAX_MESSAGE_SIZE

_logger = getLogger(__name__)


async def send_message(context, chat_id, feed_type, feed_name, entry):
    entry_link = entry.url
    summary = parse_summary(entry)
    message = _format_message(feed_type, feed_name, entry_link, summary)
    media = parse_media(entry)
    max_media_items_per_message = MAX_MEDIA_ITEMS_PER_MESSSAGE
    media_groups = [
        media[x : x + max_media_items_per_message]
        for x in range(0, len(media), max_media_items_per_message)
    ]
    if not media_groups:
        await context.bot.send_message(chat_id, message)
        return
    # Only the last group should have a message
    for media_group in media_groups[:-1]:
        await _handle_attachment_group(context, chat_id, feed_name, media_group)
    await _handle_attachment_group(context, chat_id, feed_name, media_groups[-1], message)


async def _handle_attachment_group(context, chat_id, feed_name, media_group, message=None):
    if len(media_group) > 10:
        _logger.error(f"Cannot send more attachments than 10 ({feed_name})!")
        return
    if len(media_group) == 1:
        await _send_single_media_based_on_type(context, chat_id, *media_group[0], message)
    else:
        media_list = [_media_object(url, type) for url, type in media_group]
        # Only the first media should have a caption,
        # otherwise actual caption body won't be displayed directly in the message
        media_list[0].caption = message
        await context.bot.send_media_group(chat_id, media_list)


# TODO Consider extracting this to formatter.py,
# but at the same time other bots might allow for different formatting,
# like bolding feed name, etc.
def _format_message(feed_type, feed_name, entry_link, content):
    message_text = f"{feed_name} on {feed_type}"
    if content:
        message_text += f":\n{content}"
    max_message_size = MAX_MESSAGE_SIZE - 3 - 1 - len(entry_link)
    # 3 - "...",  1 - new line
    if len(message_text) > max_message_size:
        message_text = f"{message_text[:max_message_size]}..."
    message_text += f"\n{entry_link}"
    return message_text


async def _send_single_media_based_on_type(context, chat_id, url, type, message):
    if _is_video(url, type):
        await context.bot.send_video(chat_id, video=url, caption=message, supports_streaming=True)
    else:
        await context.bot.send_photo(chat_id, photo=url, caption=message)


def _media_object(url, type):
    if _is_video(url, type):
        return InputMediaVideo(media=url, supports_streaming=True)
    else:
        return InputMediaPhoto(media=url)


def _is_video(url, type):
    if type is not None and "image" in type:
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
