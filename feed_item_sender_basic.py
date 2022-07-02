"""
Very basic sender for RSS feed items.
Doesn't do any formatting, just sends up to 2000 characters from 'content_html' field.
Used mostly for debugging and development purposes.
"""

async def send_message(channel, rss_name, item):
    await channel.send(format_item(rss_name, item))


def format_item(rss_name, item):
    message_text = f"{rss_name}: {item['content_html']}"
    if len(message_text) > 2000:
        message_text = f"{message_text[:1997]}..."
    return message_text
