"""
Module handling sending updates to a specific chat.

Only bot-specific parsing and formatting of the messages is done here,
more generic parsing out data from the RSS feed should be done beforehand.

This module will recognize and handle situations where:
 - there's only text message
 - there's only one media item (photo or video)
 - there are more than 10 media items, they will be split into multiple messages
Only one media item will have a caption, so it's correctly displayed in chat.
"""

from logging import getLogger

from more_itertools import sliced
from requests import get
from telegram import Bot, InputMediaPhoto, InputMediaVideo

from settings import MAX_MEDIA_ITEMS_PER_MESSSAGE, MAX_MESSAGE_SIZE

_logger = getLogger(__name__)


async def send_update(
    bot: Bot,
    chat_id: int,
    feed_type: str,
    feed_name: str,
    link: str,
    title: str,
    description: str,
    media_links: list[str] = None,
) -> None:
    message = _format_message(chat_id, feed_type, feed_name, link, title, description)
    if not media_links:
        _logger.info(f"[{chat_id}] Sending text only update [{feed_name}] [{feed_type}]")
        await bot.send_message(chat_id, message)
    else:
        _logger.info(f"[{chat_id}] Sending update [{feed_name}] [{feed_type}]")
        await _send_media_update(bot, chat_id, message, media_links)


def _format_message(
    chat_id: int,
    feed_type: str,
    feed_name: str,
    link: str,
    title: str,
    description: str,
) -> str:
    message_text = f"{feed_name} on {feed_type}"
    message_text += ":" if title or description else ""
    message_text += f" {title}" if title else ""
    message_text += f"\n\n{description}" if description else ""
    message_text = _trim_message(chat_id, message_text, len("\n\n") + len(link))
    message_text += f"\n\n{link}"
    return message_text


def _trim_message(chat_id: int, message: str, appended_size: int) -> str:
    effective_max_message_size = MAX_MESSAGE_SIZE - appended_size
    if len(message) > effective_max_message_size:
        _logger.info(f"[{chat_id}] Trimming message")
        effective_max_number_of_characters = effective_max_message_size - len("...")
        message = f"{message[:effective_max_number_of_characters]}..."
    return message


async def _send_media_update(bot: Bot, chat_id: int, message: str, media_links: list[str]) -> None:
    media = [_get_media_content_and_type(link) for link in media_links]
    media_groups = list(sliced(media, MAX_MEDIA_ITEMS_PER_MESSSAGE))
    # Only the last group should have a message
    for media_group in media_groups[:-1]:
        await _handle_attachment_group(bot, chat_id, media_group)
    await _handle_attachment_group(bot, chat_id, media_groups[-1], message)


def _get_media_content_and_type(link: str) -> tuple[bytes, str]:
    response = get(link)
    return response.content, response.headers["Content-Type"]


async def _handle_attachment_group(
    bot: Bot,
    chat_id: int,
    media_group: list[tuple[bytes, str]],
    message: str = None,
) -> None:
    # Technically single media elements don't have to be handled as media group,
    # but they can, so the same implementation can be used for both.
    input_media_list = [_media_object(media, media_type) for media, media_type in media_group]
    await bot.send_media_group(chat_id, input_media_list, caption=message)


def _media_object(media: bytes, media_type: str) -> InputMediaPhoto | InputMediaVideo:
    if _is_video(media_type):
        return InputMediaVideo(media, supports_streaming=True)
    else:
        return InputMediaPhoto(media)


def _is_video(media_type: str) -> bool:
    return "video" in media_type.lower()
