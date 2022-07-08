from collections import namedtuple

from bs4 import BeautifulSoup
from feedparser.util import FeedParserDict

FeedEntry = namedtuple("FeedEntry", ["url", "summary", "media"])
FeedMedia = namedtuple("FeedMedia", ["url", "type"])


# TODO Should used type here be "FeedParserDict", or just "dict"?
def parse_entry(entry: FeedParserDict) -> FeedEntry:
    return FeedEntry(
        entry["link"],
        _parse_summary(entry),
        _parse_media(entry),
    )


def _parse_summary(entry: FeedParserDict) -> str:
    summary = BeautifulSoup(entry["summary"], "html.parser")
    all_text = summary.find_all(text=True)
    # TODO Handle links in some smarter way.
    # Perhaps appending them with "link: " would be better?
    # Right now some text in the form of a link will get removed.
    # Although appending "link" anywhere seem more like bot-related approach.
    return "".join(text for text in all_text if text.parent.name not in ["a"])


def _parse_media(entry: FeedParserDict) -> list[FeedMedia]:
    if "media_content" in entry:
        return [FeedMedia(media["url"], media["type"]) for media in entry["media_content"]]
    summary = BeautifulSoup(entry["summary"], "html.parser")
    raw_media = summary.find_all(["img", "source"])
    return [FeedMedia(media["src"], None) for media in raw_media]
