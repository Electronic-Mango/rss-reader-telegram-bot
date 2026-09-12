"""
Module parsing data from the parsed RSS feed.

Extracted information contains:
 - link to the item
 - description, which will be used as an update's message
 - links to photos and videos
"""

from functools import partial, reduce
from html import escape
from typing import Any
from urllib.parse import quote

from bs4 import BeautifulSoup
from loguru import logger

from feed.types import RssEntry
from feed.utils import format_date, get_entry_date
from settings import Settings

ATTRS_FOR_DESCRIPTION = ["title", "alt"]


def parse_link(entry: RssEntry) -> str | None:
    return entry.get("link")


def parse_description(entry: RssEntry, feed_type: str) -> str | None:
    feed_data = Settings.RSS_FEEDS[feed_type]
    if not feed_data.get("show_description") or not (summary := entry.get("summary")):
        return None
    desc = _get_description_from_summary(summary)
    return escape(_filter_text(desc, feed_data)) if desc else None


def parse_title(entry: RssEntry, feed_type: str) -> str | None:
    feed_data = Settings.RSS_FEEDS[feed_type]
    if not feed_data.get("show_title") or not (title := entry.get("title")):
        return None
    return f"<b>{escape(_filter_text(title, feed_data).strip())}</b>"


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
    return reduce(lambda text, pattern: text.replace(pattern, ""), filters, text)


def parse_media_links(entry: RssEntry, feed_type: str, feed_name: str) -> list[str]:
    media_override = Settings.RSS_FEEDS[feed_type].get("media_override")
    if media_override is not None and (pattern := media_override.get("pattern")):
        encode_http = media_override.get("encode_http", False)
        return _media_override(entry, pattern, feed_type, feed_name, encode_http)
    if media_content := entry.get("media_content"):
        return [media["url"] for media in media_content if "url" in media]
    if not (summary := entry.get("summary")):
        return []
    media_source = BeautifulSoup(summary, "html.parser")
    media_elements = media_source.find_all(["img", "source"])
    media_links = [media.get("src") for media in media_elements]
    return [link for link in media_links if link]


def _media_override(
    entry: RssEntry,
    pattern: str,
    feed_type: str,
    feed_name: str,
    encode_http: bool,
) -> list[str]:
    try:
        encode = partial(_percent_encode, encode_http=encode_http)
        return [
            pattern.format(
                feed_type=encode(feed_type),
                feed_name=encode(feed_name),
                entry_id=encode(entry.get("id")),
                entry_link=encode(entry.get("link")),
                entry_date=encode(format_date(get_entry_date(entry))),
            )
        ]
    except (AttributeError, IndexError, KeyError, TypeError, ValueError) as e:
        warning_message = f"Failed to apply media override pattern to [{pattern}]: "
        logger.opt(exception=e).warning(warning_message)
        return []


def _percent_encode(value: Any, encode_http: bool) -> str:
    return quote(str(value), safe="") if encode_http else str(value)
