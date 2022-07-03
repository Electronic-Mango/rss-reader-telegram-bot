"""
Sender dedicated for Instagram feeds.
Sends images/videos directly, removes hashtags, etc.
"""

from logging import info
from re import sub

from telegram import InputMediaPhoto, InputMediaVideo
from telegram.ext.callbackcontext import CallbackContext


def send_message_instagram(context: CallbackContext, chat_id, rss_name, item):
    item_url, title, content = parse_item(item)
    attachments = [(attachment["url"], attachment["mime_type"]) for attachment in item["attachments"]]
    message = format_message(rss_name, item_url, title, content, len(attachments) > 10)
    if len(attachments) == 1:
        url, type = attachments[0]
        if type != "application/octet-stream":
            info(f"Type 'application/octet-stream' treated as video.")
            context.bot.send_photo(chat_id, photo=url, caption=message)
        else:
            info(f"Type '{type}' treated as image.")
            context.bot.send_video(chat_id, video=url, caption=message, supports_streaming=True)
    else:
        media_list = [media_object(url, type) for url, type in attachments]
        # Only the first media should have a caption,
        # otherwise actual caption body won't be displayed directly in the message
        media_list[0].caption = message
        context.bot.send_media_group(chat_id, media_list)


def format_message(rss_name, item_url, title, content, too_many_images):
    message_text = f"{rss_name} on Instagram: {title}"
    if content:
        message_text += f"\n{content}"
    max_message_size = 1024 - 3 - 1 - len(item_url)  # 3 - "...",  1 - new line
    if too_many_images:
        max_message_size -= len("\nToo many images to send!")
    if len(message_text) > max_message_size:
        message_text = f"{message_text[:max_message_size]}..."
    if too_many_images:
        message_text += "\nToo many images to send!"
    message_text += f"\n{item_url}"
    return message_text


def parse_item(item):
    item_url = item["url"]
    title = parse_item_title(item)
    content = parse_item_content(item)
    return (item_url, title, content)


def parse_item_title(item):
    title = item["title"]
    title = title.replace("...", "")
    title = title.replace("(no text)", "")
    return title


def parse_item_content(item):
    content = item["content_html"]
    content = sub(r"(<a.+</a>)+", "", content)
    content = sub(r"(<video controls>.+</video>)+", "", content)
    content = content.replace("&quot;", '"')
    content = sub(r"<br( )?(/)?>", "\n", content)
    content = sub(r"#[\w]+", "", content)
    content = content.replace("(no text)", "")
    content = "\n".join([line.strip() for line in content.strip().splitlines()[1:] if line.strip()])
    return content


def media_object(url, type):
    if type != "application/octet-stream":
        return InputMediaPhoto(media=url)
    else:
        return InputMediaVideo(media=url, supports_streaming=True)
