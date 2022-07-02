"""
Sender dedicated for Instagram feeds.
Sends images/videos directly, removes hashtags, etc.
"""

from io import BytesIO
from logging import info
from mimetypes import guess_extension
from os import linesep
from re import sub

from aiohttp import ClientSession
from discord import File


async def send_message_instagram(channel, rss_name, item):
    item_url, title, content = parse_item(item)
    attachments = [(attachment["url"], attachment["mime_type"]) for attachment in item["attachments"]]
    files = [await download_attachment(title, url, type) for url, type in attachments]
    issues_with_downloading_files = any(not file for file in files)
    message = format_message(rss_name, item_url, title, content, issues_with_downloading_files)
    await channel.send(message, files=list(filter(None, files)))


def format_message(rss_name, item_url, title, content, issues_with_downloading_attachments):
    message_text = f"{rss_name} on Instagram: {title}"
    if content:
        message_text += f"\n{content}"
    if issues_with_downloading_attachments:
        message_text += "\nCouldn't download some images/videos."
    max_message_size = 2000 - 3 - 1 - len(item_url)  # 3 - "...",  1 - new line
    if len(message_text) > max_message_size:
        message_text = f"{message_text[:max_message_size]}..."
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
    content = sub(r"<br( )?(/)?>", linesep, content)
    content = sub(r"#[\w]+", "", content)
    content = content.replace("(no text)", "")
    content = linesep.join([line.strip() for line in content.strip().splitlines()[1:] if line.strip()])
    return content


async def download_attachment(filename, url, type):
    async with ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return None
            data = BytesIO(await response.read())
            file = File(data, f"{filename}{convert_mime_to_extension(type)}")
            return file


def convert_mime_to_extension(type):
    if type == "application/octet-stream":
        info(f"Assuming that [application/octet-stream] type is mp4.")
        return ".mp4"
    extension = guess_extension(type)
    info(f"Guessed extension=[{extension}] based on type=[{type}].")
    return extension
