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

MAX_MEDIA_SIZE_PER_MESSAGE = 10

logger = getLogger(__name__)


async def send_message_instagram(context: ContextTypes.DEFAULT_TYPE, chat_id, rss_name, item):
    item_url, content = parse_item(item)
    message = format_message(rss_name, item_url, content)
    attachments = [
        (attachment["url"], attachment["mime_type"])
        for attachment in item["attachments"]
    ]
    attachment_groups = [
        attachments[x : x + MAX_MEDIA_SIZE_PER_MESSAGE]
        for x in range(0, len(attachments), MAX_MEDIA_SIZE_PER_MESSAGE)
    ]
    # Only the last group should have a message
    for attachment_group in attachment_groups[:-1]:
        await handle_attachment_group(context, chat_id, rss_name, attachment_group)
    await handle_attachment_group(context, chat_id, rss_name, attachment_groups[-1], message)


async def handle_attachment_group(context: ContextTypes.DEFAULT_TYPE, chat_id, rss_name, attachments, message=None):
    if len(attachments) > 10:
        logger.error(f"Cannot send more attachments than 10 ({rss_name})!")
        return
    if len(attachments) == 1:
        await send_single_media_based_on_type(context, chat_id, *attachments[0], message)
    else:
        media_list = [media_object(url, type) for url, type in attachments]
        # Only the first media should have a caption,
        # otherwise actual caption body won't be displayed directly in the message
        media_list[0].caption = message
        await context.bot.send_media_group(chat_id, media_list)


def format_message(rss_name, item_url, content):
    message_text = f"{rss_name} on Instagram"
    if content:
        message_text += f":\n{content}"
    max_message_size = 1024 - 3 - 1 - len(item_url)  # 3 - "...",  1 - new line
    if len(message_text) > max_message_size:
        message_text = f"{message_text[:max_message_size]}..."
    message_text += f"\n{item_url}"
    return message_text


def parse_item(item):
    item_url = item["url"]
    content = parse_item_content(item)
    return item_url, content


def parse_item_content(item):
    content = item["content_html"]
    content = sub(r"(<a.+</a>)+", "", content)
    content = sub(r"(<video controls>.+</video>)+", "", content)
    content = content.replace("&quot;", '"')
    content = sub(r"<br( )?(/)?>", "\n", content)
    content = content.replace("(no text)", "")
    content = "\n".join([line.strip() for line in content.strip().splitlines() if line.strip()])
    return content


async def send_single_media_based_on_type(context: ContextTypes.DEFAULT_TYPE, chat_id, url, type, message):
    if is_video(url, type):
        await context.bot.send_video(chat_id, video=url, caption=message, supports_streaming=True)
    else:
        await context.bot.send_photo(chat_id, photo=url, caption=message)


def is_video(url, type):
    if "image" in type:
        logger.info(f"Type '{type}' treated as image.")
        return False
    response = get(url)
    content_type = response.headers["Content-Type"]
    if "video" in content_type:
        logger.info(f"Type '{type}' (content-type=[{content_type}]) treated as video.")
        return True
    else:
        logger.info(f"Type '{type}' (content-type=[{content_type}]) treated as image.")
        return False


def media_object(url, type):
    if is_video(url, type):
        return InputMediaVideo(media=url, supports_streaming=True)
    else:
        return InputMediaPhoto(media=url)
