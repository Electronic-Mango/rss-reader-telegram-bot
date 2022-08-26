"""
Module parsing data from the parsed RSS feed.

Extracted information contains:
 - link to the item
 - description, which will be used as a update's message
 - links to photos and videos
"""

from functools import reduce
from typing import Any

from bs4 import BeautifulSoup
from feedparser.util import FeedParserDict

from settings import RSS_FEEDS


def parse_link(entry: FeedParserDict) -> str:
    return entry.link


def parse_description(entry: FeedParserDict, feed_type: str) -> str:
    if (feed_params := RSS_FEEDS[feed_type]).get("show_description") and (summary := entry.summary):
        return BeautifulSoup(_filter_text(summary, feed_params), "html.parser").get_text().strip()


def parse_title(entry: FeedParserDict, feed_type: str) -> str:
    if (feed_params := RSS_FEEDS[feed_type]).get("show_title") and (title := entry.title):
        return f"<b>{_filter_text(title, feed_params).strip()}</b>"


def _filter_text(text: str, feed_params: dict[str, Any]) -> str:
    filters = feed_params.get("filters", [])
    return reduce(lambda text, filter: text.replace(filter, ""), filters, text)


def parse_media_links(entry: FeedParserDict) -> list[str]:
    if "media_content" in entry:
        return [media["url"] for media in entry.media_content if "url" in media]
    media_source = BeautifulSoup(entry.summary, "html.parser")
    media_elements = media_source.find_all(["img", "source"])
    media_links = [media.get("src") for media in media_elements]
    return [link for link in media_links if link]
