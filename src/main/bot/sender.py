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

from io import BytesIO

from httpx import get
from loguru import logger
from more_itertools import sliced
from PIL import Image
from telegram import Bot, InputMediaPhoto, InputMediaVideo

from settings import MAX_MEDIA_ITEMS_PER_MESSAGE, MAX_MESSAGE_SIZE

MAX_IMAGE_SIZE = 10_000_000
MAX_IMAGE_DIMENSIONS = 10_000
MAX_IMAGE_THUMBNAIL = (MAX_IMAGE_DIMENSIONS // 2, MAX_IMAGE_DIMENSIONS // 2)


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
        logger.info(f"[{chat_id}] Sending text only update [{feed_name}] [{feed_type}]")
        await bot.send_message(chat_id, message)
    else:
        logger.info(f"[{chat_id}] Sending update [{feed_name}] [{feed_type}]")
        await _send_media_update(bot, chat_id, message, media_links)


def _format_message(
    chat_id: int,
    feed_type: str,
    feed_name: str,
    link: str,
    title: str,
    description: str,
) -> str:
    message_text = f"{title}" if title else ""
    message_text += f"\n\n{description}" if description else ""
    sender_text = "\n\n" if len(message_text) else ""
    sender_text += f"By <b>{feed_name}</b> on {feed_type}:\n{link}"
    message_text = _trim_message(chat_id, message_text, len(sender_text))
    message_text += sender_text
    return message_text


def _trim_message(chat_id: int, message: str, appended_size: int) -> str:
    effective_max_message_size = MAX_MESSAGE_SIZE - appended_size
    if len(message) > effective_max_message_size:
        logger.info(f"[{chat_id}] Trimming message")
        effective_max_number_of_characters = effective_max_message_size - len("...")
        message = f"{message[:effective_max_number_of_characters]}..."
    return message


async def _send_media_update(bot: Bot, chat_id: int, message: str, media_links: list[str]) -> None:
    media = [_get_media_content_and_type(link) for link in media_links]
    media_groups = list(sliced(media, MAX_MEDIA_ITEMS_PER_MESSAGE))
    # Only the last group should have a message
    for media_group in media_groups[:-1]:
        await _handle_attachment_group(bot, chat_id, media_group)
    await _handle_attachment_group(bot, chat_id, media_groups[-1], message)


def _get_media_content_and_type(link: str) -> tuple[bytes, str]:
    headers = {"user-agent": "rss-reader/1.0", "accept": "*/*"}
    response = get(link, headers=headers, timeout=600)
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
    await bot.send_media_group(chat_id, input_media_list, caption=message, write_timeout=180)


def _media_object(media: bytes, media_type: str) -> InputMediaPhoto | InputMediaVideo:
    if _is_video(media_type):
        return InputMediaVideo(media, supports_streaming=True)
    else:
        return InputMediaPhoto(_trim_image(media))


def _is_video(media_type: str) -> bool:
    return "video" in media_type.lower()


def _trim_image(media: bytes) -> bytes:
    image = Image.open(BytesIO(media))
    if (total_size := sum(image.size)) <= MAX_IMAGE_DIMENSIONS and len(media) <= MAX_IMAGE_SIZE:
        return media
    logger.info("Reducing image size...")
    if total_size > MAX_IMAGE_DIMENSIONS:
        logger.info(f"Total dimensions too large, reducing to {MAX_IMAGE_THUMBNAIL}...")
        # Technically image can have size larger than 5000 pixels,
        # as long as sum of both dimensions is lower than 10000 pixels.
        # However, this is the simplest solution and images up to 5000x5000 should be big enough.
        image.thumbnail(MAX_IMAGE_THUMBNAIL)
    image_bytes = BytesIO()
    image.save(image_bytes, format=image.format)
    image_raw = image_bytes.getvalue()
    while (bytes_size := len(image_raw)) > MAX_IMAGE_SIZE:
        max_dimension = max(image.size)
        new_dimensions = (max_dimension // 2, max_dimension // 2)
        logger.info(f"Total size ({bytes_size}) too large, reducing to {new_dimensions}...")
        image.thumbnail(new_dimensions)
        image_bytes.truncate(0)
        image.save(image_bytes, format=image.format)
        image_raw = image_bytes.getvalue()
    return image_raw
