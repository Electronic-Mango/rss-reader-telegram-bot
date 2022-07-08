"""
Sender dedicated for Instagram feeds.
Sends images/videos directly, removes hashtags, etc.
"""

from logging import getLogger
from requests import get

from telegram import InputMedia, InputMediaPhoto, InputMediaVideo
from telegram.ext import ContextTypes

from feed_parser import FeedEntry, FeedMedia
from settings import MAX_MEDIA_ITEMS_PER_MESSSAGE, MAX_MESSAGE_SIZE

_logger = getLogger(__name__)


async def send_update(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    feed_type: str,
    feed_name: str,
    entry: FeedEntry,
) -> None:
    _logger.info(f"[{chat_id}] Sending update [{feed_name}] [{feed_type}]")
    entry_url, summary, media = entry
    message = _format_message(feed_type, feed_name, entry_url, summary)
    if not media:
        await context.bot.send_message(chat_id, message)
    else:
        await _send_media_update(context, chat_id, message, media)


async def _send_media_update(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    message: str,
    media: list[FeedMedia],
) -> None:
    media_groups = [
        media[x : x + MAX_MEDIA_ITEMS_PER_MESSSAGE]
        for x in range(0, len(media), MAX_MEDIA_ITEMS_PER_MESSSAGE)
    ]
    # Only the last group should have a message
    for media_group in media_groups[:-1]:
        await _handle_attachment_group(context, chat_id, media_group)
    await _handle_attachment_group(context, chat_id, media_groups[-1], message)


async def _handle_attachment_group(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    media_group: list[FeedMedia],
    message: str = None
) -> None:
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
def _format_message(feed_type: str, feed_name: str, entry_link: str, content: str) -> str:
    message_text = f"{feed_name} on {feed_type}"
    if content:
        message_text += f":\n{content}"
    max_message_size = MAX_MESSAGE_SIZE - 3 - 1 - len(entry_link) # 3 - "...",  1 - "\n"
    if len(message_text) > max_message_size:
        _logger.info(f"Trimming message")
        message_text = f"{message_text[:max_message_size]}..."
    message_text += f"\n{entry_link}"
    return message_text


async def _send_single_media_based_on_type(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    url: str,
    type: str,
    message: str
) -> None:
    if _is_video(url, type):
        await context.bot.send_video(chat_id, video=url, caption=message, supports_streaming=True)
    else:
        await context.bot.send_photo(chat_id, photo=url, caption=message)


def _media_object(url: str, type: str) -> InputMedia:
    if _is_video(url, type):
        return InputMediaVideo(media=url, supports_streaming=True)
    else:
        return InputMediaPhoto(media=url)


# TODO Is there a better way to do this? Perhaps some python-telegram built-in function?
def _is_video(url: str, type: str) -> bool:
    if type is not None and "image" in type:
        _logger.info(f"[{url}] [{type}] treated as image")
        return False
    response = get(url)
    content_type = response.headers["Content-Type"]
    if "video" in content_type:
        _logger.info(f"[{url}] [{type}] [{content_type}] treated as video")
        return True
    else:
        _logger.info(f"[{url}] [{type}] [{content_type}] treated as image")
        return False
