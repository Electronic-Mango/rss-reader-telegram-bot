from logging import getLogger
from requests import get

from more_itertools import sliced
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
    media_urls: list[str]
) -> None:
    _logger.info(f"[{chat_id}] Sending update [{feed_name}] [{feed_type}]")
    message = _format_message(chat_id, feed_type, feed_name, link, summary)
    if not media_urls:
        await bot.send_message(chat_id, message)
    else:
        await _send_media_update(bot, chat_id, message, media_urls)


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


async def _send_media_update(bot: Bot, chat_id: int, message: str, media_urls: list[str]) -> None:
    media = [_get_media_content_and_type(url) for url in media_urls]
    media_groups = list(sliced(media, MAX_MEDIA_ITEMS_PER_MESSSAGE))
    # Only the last group should have a message
    for media_group in media_groups[:-1]:
        await _handle_attachment_group(bot, chat_id, media_group)
    await _handle_attachment_group(bot, chat_id, media_groups[-1], message)


def _get_media_content_and_type(url: str) -> tuple[bytes, str]:
    response = get(url)
    return response.content, response.headers["Content-Type"]


async def _handle_attachment_group(
    bot: Bot,
    chat_id: int,
    media_group: list[tuple[bytes, str]],
    message: str = None
) -> None:
    if len(media_group) == 1:
        await _send_single_media(bot, chat_id, *media_group[0], message)
    else:
        input_media_list = [_media_object(media, type) for media, type in media_group]
        # Only the first media should have a caption,
        # otherwise actual caption body won't be displayed directly in the message.
        input_media_list[0].caption = message
        await bot.send_media_group(chat_id, input_media_list)


async def _send_single_media(bot: Bot, chat_id: int, media: bytes, type: str, message: str) -> None:
    if _is_video(type):
        await bot.send_video(chat_id, video=media, caption=message, supports_streaming=True)
    else:
        await bot.send_photo(chat_id, photo=media, caption=message)


def _media_object(media: bytes, type: str) -> InputMedia:
    if _is_video(type):
        return InputMediaVideo(media=media, supports_streaming=True)
    else:
        return InputMediaPhoto(media=media)


def _is_video(type: str) -> bool:
    return "video" in type.lower()
