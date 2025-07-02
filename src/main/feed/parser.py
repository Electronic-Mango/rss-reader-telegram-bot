"""
Module parsing data from the parsed RSS feed.

Extracted information contains:
 - link to the item
 - description, which will be used as an update's message
 - links to photos and videos
"""

from functools import reduce
from typing import Any

from bs4 import BeautifulSoup
from feedparser.util import FeedParserDict

from settings import RSS_FEEDS

ATTRS_FOR_DESCRIPTION = ["title", "alt"]


def parse_link(entry: FeedParserDict) -> str:
    return entry.link


def parse_description(entry: FeedParserDict, feed_type: str) -> str | None:
    if not (feed_params := RSS_FEEDS[feed_type]).get("show_description") or not (summary := entry.summary):
        return None
    description = _get_description_from_summary(summary)
    return _filter_text(description, feed_params)


def parse_title(entry: FeedParserDict, feed_type: str) -> str:
    if (feed_params := RSS_FEEDS[feed_type]).get("show_title") and (title := entry.title):
        return f"<b>{_filter_text(title, feed_params).strip()}</b>"


def _get_description_from_summary(summary: str) -> str | None:
    bs = BeautifulSoup(summary, "html.parser")
    return bs.get_text().strip() or next(
        (
            matching_tag.get(attribute).strip()
            for attribute in ATTRS_FOR_DESCRIPTION
            if (matching_tag := bs.find(lambda tag: tag.has_attr(attribute)))
        ),
        None,
    )


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
