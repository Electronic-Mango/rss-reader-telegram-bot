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

from asyncio import gather, to_thread
from functools import lru_cache
from html import escape
from http import HTTPStatus
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile

from cv2 import CAP_PROP_FRAME_HEIGHT, CAP_PROP_FRAME_WIDTH, VideoCapture
from loguru import logger
from more_itertools import sliced
from niquests import aget
from PIL import Image
from telegram import Bot, InputMediaPhoto, InputMediaVideo, ReplyParameters

from settings import (
    CONCURRENCY,
    DEFAULT_IMAGE_PATH,
    MAX_MEDIA_ITEMS_PER_MESSAGE,
    MAX_MESSAGE_SIZE,
    PIN_VIDEOS,
    RSS_FEEDS,
    SEND_MEDIA_TIMEOUT,
    UPDATES_AS_REPLIES,
)

DEFAULT_SENDER_TEXT_FORMAT = "By <b>{name}</b> on {type}"
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
    latest_message_id: int | None,
    media_links: list[str] = None,
) -> int:
    message = _format_message(chat_id, feed_type, feed_name, link, title, description)
    reply_params = _prepare_reply_params(latest_message_id)
    if not media_links:
        logger.info(f"[{chat_id}] Sending text only update [{feed_name}] [{feed_type}]")
        return await _send_text_message(bot, chat_id, message, reply_params)
    else:
        logger.info(f"[{chat_id}] Sending update [{feed_name}] [{feed_type}]")
        return await _send_media_update(bot, chat_id, message, reply_params, media_links)


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
    sender_text += f"<a href='{escape(link)}'>" if link else ""
    sender_text += f"{_prepare_sender_text(feed_type, feed_name)}"
    sender_text += "</a>" if link else ""
    message_text = _trim_message(chat_id, message_text, len(sender_text))
    message_text += sender_text
    return message_text


def _prepare_sender_text(feed_type: str, feed_name: str) -> str:
    text_format = RSS_FEEDS[feed_type].get("sender_text_format", None) or DEFAULT_SENDER_TEXT_FORMAT
    return str(text_format).format(name=escape(feed_name), type=escape(feed_type))


def _trim_message(chat_id: int, message: str, appended_size: int) -> str:
    effective_max_message_size = MAX_MESSAGE_SIZE - appended_size
    if len(message) > effective_max_message_size:
        logger.info(f"[{chat_id}] Trimming message")
        effective_max_number_of_characters = effective_max_message_size - len("...")
        message = f"{message[:effective_max_number_of_characters]}..."
    return message


def _prepare_reply_params(latest_message_id: int | None) -> ReplyParameters | None:
    if not UPDATES_AS_REPLIES or latest_message_id is None:
        return None
    return ReplyParameters(latest_message_id, allow_sending_without_reply=True)


async def _send_text_message(
    bot: Bot, chat_id: int, message: str, reply_params: ReplyParameters | None
) -> int:
    if (default_image := _load_image(DEFAULT_IMAGE_PATH)) is None:
        logger.info(f"[{chat_id}] No default media [{DEFAULT_IMAGE_PATH}], sending only text")
        sent_message = await bot.send_message(chat_id, message, reply_parameters=reply_params)
        return sent_message.id
    logger.info(f"[{chat_id}] Sending default image [{DEFAULT_IMAGE_PATH}]")
    image_bytes = BytesIO()
    await to_thread(default_image.save, image_bytes, format=default_image.format or "PNG")
    media_group = [(image_bytes.getvalue(), default_image.format or "PNG")]
    return await _handle_attachment_group(bot, chat_id, media_group, message, reply_params)


@lru_cache(maxsize=1)
def _load_image(image_path: str | None) -> Image.Image | None:
    try:
        if not image_path or not Path(image_path).is_file():
            return None
        image = Image.open(image_path)
        # Force the read now, so the file is loaded and closed only once, not on every call.
        image.load()
        return image
    except OSError as e:
        logger.opt(exception=e).warning(f"Failed to load image at [{image_path}]: ")
        return None


async def _send_media_update(
    bot: Bot,
    chat_id: int,
    message: str,
    reply_params: ReplyParameters | None,
    media_links: list[str],
) -> int:
    if CONCURRENCY:
        downloaded = await gather(*(_get_media_content_and_type(link) for link in media_links))
    else:
        downloaded = [await _get_media_content_and_type(link) for link in media_links]
    media = [data for data in downloaded if data]
    if not media:
        logger.info(f"[{chat_id}] No media downloaded from [{media_links}]")
        return await _send_text_message(bot, chat_id, message, reply_params)
    if len(media) <= MAX_MEDIA_ITEMS_PER_MESSAGE:
        return await _handle_attachment_group(bot, chat_id, media, message, reply_params)
    media_groups = list(sliced(media, MAX_MEDIA_ITEMS_PER_MESSAGE))
    # Only the last group should have a message, but ID should be from the first group
    message_id = await _handle_attachment_group(
        bot, chat_id, media_groups[0], reply_params=reply_params
    )
    for media_group in media_groups[1:-1]:
        await _handle_attachment_group(bot, chat_id, media_group)
    await _handle_attachment_group(bot, chat_id, media_groups[-1], message)
    return message_id


async def _get_media_content_and_type(link: str) -> tuple[bytes, str] | None:
    logger.info(f"Downloading media from [{link}]")
    headers = {"user-agent": "rss-reader/1.0", "accept": "*/*"}
    response = await aget(link, headers=headers, timeout=600)
    if response.status_code != HTTPStatus.OK:
        logger.warning(f"Could download media at [{link}], status code [{response.status_code}]")
        return None
    return response.content, response.headers["Content-Type"]


async def _handle_attachment_group(
    bot: Bot,
    chat_id: int,
    media_group: list[tuple[bytes, str]],
    message: str = None,
    reply_params: ReplyParameters | None = None,
) -> int:
    # Technically single media elements don't have to be handled as media group,
    # but they can, so the same implementation can be used for both.
    input_media_list = [await _media_object(media, media_type) for media, media_type in media_group]
    is_video_list = [isinstance(m, InputMediaVideo) for m in input_media_list]
    logger.info(f"{chat_id} Sending media group is_video={is_video_list}")
    if len(input_media_list) == 1 and isinstance(video := input_media_list[0], InputMediaVideo):
        # Workaround for videos with skewed aspect ratio.
        return await _handle_single_video(bot, chat_id, video, message, reply_params)
    else:
        sent_message = await bot.send_media_group(
            chat_id,
            input_media_list,
            caption=message,
            reply_parameters=reply_params,
            read_timeout=SEND_MEDIA_TIMEOUT,
            write_timeout=SEND_MEDIA_TIMEOUT,
        )
        return sent_message[0].message_id


async def _media_object(media: bytes, media_type: str) -> InputMediaPhoto | InputMediaVideo:
    if _is_video(media_type):
        return InputMediaVideo(media, supports_streaming=True)
    else:
        return InputMediaPhoto(await to_thread(_trim_image, media))


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
        image_bytes.seek(0)
        image.save(image_bytes, format=image.format)
        image_raw = image_bytes.getvalue()
    return image_raw


async def _handle_single_video(
    bot: Bot,
    chat_id: int,
    video: InputMediaVideo,
    message: str = None,
    reply_params: ReplyParameters | None = None,
) -> int:
    width, height = await to_thread(_probe_video_size, video.media.input_file_content)
    sent_message = await bot.send_video(
        chat_id,
        video.media,
        width=width,
        height=height,
        caption=message,
        supports_streaming=True,
        reply_parameters=reply_params,
        read_timeout=SEND_MEDIA_TIMEOUT,
        write_timeout=SEND_MEDIA_TIMEOUT,
    )
    if PIN_VIDEOS:
        await sent_message.pin()
    return sent_message.id


def _probe_video_size(video_bytes: bytes) -> tuple[int | None, int | None]:
    with NamedTemporaryFile() as tmp_file:
        tmp_file.write(video_bytes)
        tmp_file.flush()
        video_capture = VideoCapture(tmp_file.name)
        width = int(video_capture.get(CAP_PROP_FRAME_WIDTH))
        height = int(video_capture.get(CAP_PROP_FRAME_HEIGHT))
        video_capture.release()
    return (width, height) if width > 0 and height > 0 else (None, None)
