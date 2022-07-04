"""
Sender dedicated for Instagram feeds.
Sends images/videos directly, removes hashtags, etc.
"""

from logging import getLogger
from re import findall, match, sub
from requests import get

from telegram import InputMediaPhoto, InputMediaVideo

_MAX_MEDIA_SIZE_PER_MESSAGE = 10

_logger = getLogger(__name__)


async def send_message(context, chat_id, feed_type, feed_name, entry):
    entry_link = entry.url
    summary = _parse_summary(entry)
    message = _format_message(feed_type, feed_name, entry_link, summary)
    media = _parse_media(entry)
    media_groups = [
        media[x : x + _MAX_MEDIA_SIZE_PER_MESSAGE]
        for x in range(0, len(media), _MAX_MEDIA_SIZE_PER_MESSAGE)
    ]
    # Only the last group should have a message
    for media_group in media_groups[:-1]:
        await _handle_attachment_group(context, chat_id, feed_name, media_group)
    await _handle_attachment_group(context, chat_id, feed_name, media_groups[-1], message)


def _parse_summary(entry):
    summary = entry.summary
    summary = sub(r"(<a.+</a>)+", "", summary)
    summary = sub(r"(<video controls>.+</video>)+", "", summary)
    summary = summary.replace("&quot;", '"')
    summary = sub(r"<br( )?(/)?>", "\n", summary)
    summary = sub(r"<p>", "", summary)
    summary = sub(r"</p>", "\n", summary)
    summary = sub(r"<img.+/>", "", summary)
    summary = summary.replace("(no text)", "")
    summary = "\n".join([line.strip() for line in summary.strip().splitlines() if line.strip()])
    return summary


def _parse_media(entry):
    if entry.media:
        return entry.media
    summary = entry.summary
    img_pattern = r"<img src=\"(.*?)\""
    match(img_pattern, summary)
    img_urls = findall(img_pattern, summary)
    return [(url, None) for url in img_urls]


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


def _format_message(feed_type, feed_name, entry_link, content):
    message_text = f"{feed_name} on {feed_type}"
    if content:
        message_text += f":\n{content}"
    max_message_size = 1024 - 3 - 1 - len(entry_link)  # 3 - "...",  1 - new line
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
