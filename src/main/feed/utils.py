from time import strftime, struct_time

from feedparser import FeedParserDict


def get_entry_date(entry: FeedParserDict) -> struct_time | None:
    """
    Retrieve the date of the given feed entry.

    By default, it tries to retrieve the published date.
    If that is not available, it falls back to the updated date.
    """
    return entry.get("published_parsed") or entry.get("updated_parsed")


def format_date(date: struct_time | None) -> str | None:
    """Format the given date as a string in "%Y-%m-%d %H:%M:%S" format."""
    return strftime("%Y-%m-%d %H:%M:%S", date) if date is not None else None
