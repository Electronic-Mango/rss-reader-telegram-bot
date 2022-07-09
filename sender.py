"""
Sender dedicated for Instagram feeds.
Sends images/videos directly, removes hashtags, etc.
"""

from logging import getLogger
from requests import get

from telegram import Bot, InputMedia, InputMediaPhoto, InputMediaVideo
from telegram.ext import ContextTypes

from settings import MAX_MEDIA_ITEMS_PER_MESSSAGE, MAX_MESSAGE_SIZE

_logger = getLogger(__name__)


async def send_update(
    bot: Bot,
    chat_id: int,
    feed_type: str,
    feed_name: str,
    link: str,
    summary: str,
    media: list[tuple[str, str]]
) -> None:
    _logger.info(f"[{chat_id}] Sending update [{feed_name}] [{feed_type}]")
    message = _format_message(chat_id, feed_type, feed_name, link, summary)
    if not media:
        await bot.send_message(chat_id, message)
    else:
        await _send_media_update(bot, chat_id, message, media)


async def _send_media_update(
    bot: Bot,
    chat_id: int,
    message: str,
    media: list[tuple[str, str]],
) -> None:
    media_groups = [
        media[x : x + MAX_MEDIA_ITEMS_PER_MESSSAGE]
        for x in range(0, len(media), MAX_MEDIA_ITEMS_PER_MESSSAGE)
    ]
    # Only the last group should have a message
    for media_group in media_groups[:-1]:
        await _handle_attachment_group(bot, chat_id, media_group)
    await _handle_attachment_group(bot, chat_id, media_groups[-1], message)


async def _handle_attachment_group(
    bot: Bot,
    chat_id: int,
    media_group: list[tuple[str, str]],
    message: str = None
) -> None:
    if len(media_group) == 1:
        await _send_single_media_based_on_type(bot, chat_id, *media_group[0], message)
    else:
        media_list = [_media_object(url, type) for url, type in media_group]
        # Only the first media should have a caption,
        # otherwise actual caption body won't be displayed directly in the message
        media_list[0].caption = message
        await bot.send_media_group(chat_id, media_list)


def _format_message(
    chat_id: int,
    feed_type: str,
    feed_name: str,
    entry_link: str,
    content: str
) -> str:
    message_text = f"{feed_name} on {feed_type}"
    if content:
        message_text += f":\n{content}"
    effective_max_message_size = MAX_MESSAGE_SIZE - len("\n") - len(entry_link)
    if len(message_text) > effective_max_message_size:
        _logger.info(f"[{chat_id}] Trimming message")
        effective_max_number_of_characters = effective_max_message_size - len("...")
        message_text = f"{message_text[:effective_max_number_of_characters]}..."
    message_text += f"\n{entry_link}"
    return message_text


async def _send_single_media_based_on_type(
    bot: Bot,
    chat_id: int,
    url: str,
    type: str,
    message: str
) -> None:
    if _is_video(url, type):
        await bot.send_video(chat_id, video=url, caption=message, supports_streaming=True)
    else:
        await bot.send_photo(chat_id, photo=url, caption=message)


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
