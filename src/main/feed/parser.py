"""
Module parsing data from the parsed RSS feed.

Extracted information contains:
 - link to the item
 - description, which will be used as an update's message
 - links to photos and videos
"""

from functools import reduce
from html import escape
from typing import Any

from bs4 import BeautifulSoup
from feedparser import FeedParserDict

from settings import RSS_FEEDS

ATTRS_FOR_DESCRIPTION = ["title", "alt"]


def parse_link(entry: FeedParserDict) -> str | None:
    return entry.get("link")


def parse_description(entry: FeedParserDict, feed_type: str) -> str | None:
    if not RSS_FEEDS[feed_type].get("show_description") or not entry.get("summary"):
        return None
    description = _get_description_from_summary(entry.summary)
    return escape(_filter_text(description, RSS_FEEDS[feed_type])) if description else None


def parse_title(entry: FeedParserDict, feed_type: str) -> str | None:
    if not RSS_FEEDS[feed_type].get("show_title") or not entry.get("title"):
        return None
    return f"<b>{escape(_filter_text(entry.title, RSS_FEEDS[feed_type]).strip())}</b>"


def _get_description_from_summary(summary: str) -> str | None:
    bs = BeautifulSoup(summary, "html.parser")
    return bs.get_text().strip() or next(
        (
            matching_tag.get(attribute).strip()
            for attribute in ATTRS_FOR_DESCRIPTION
            if (matching_tag := bs.find(lambda tag, attr=attribute: tag.has_attr(attr)))
        ),
        None,
    )


def _filter_text(text: str, feed_params: dict[str, Any]) -> str:
    filters = feed_params.get("filters", [])
    return reduce(lambda text, feed_filter: text.replace(feed_filter, ""), filters, text)


def parse_media_links(entry: FeedParserDict) -> list[str]:
    if media_content := entry.get("media_content"):
        return [media["url"] for media in media_content if "url" in media]
    if not (summary := entry.get("summary")):
        return []
    media_source = BeautifulSoup(summary, "html.parser")
    media_elements = media_source.find_all(["img", "source"])
    media_links = [media.get("src") for media in media_elements]
    return [link for link in media_links if link]
