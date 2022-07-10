from bs4 import BeautifulSoup
from feedparser.util import FeedParserDict


# TODO Should used type here be "FeedParserDict", or just "dict"?
def parse_entry(entry: FeedParserDict) -> tuple[str, str, list[str]]:
    return (entry["link"], _parse_summary(entry), _parse_media_urls(entry))


def _parse_summary(entry: FeedParserDict) -> str:
    summary = BeautifulSoup(entry["summary"], "html.parser")
    all_text = summary.find_all(text=True)
    # TODO Handle links in some smarter way.
    # Perhaps appending them with "link: " would be better?
    # Right now some text in the form of a link will get removed.
    # Although appending "link" anywhere seem more like bot-related approach.
    return "".join(text for text in all_text if text.parent.name not in ["a"])


def _parse_media_urls(entry: FeedParserDict) -> list[str]:
    if "media_content" in entry:
        return [media["url"] for media in entry["media_content"]]
    summary = BeautifulSoup(entry["summary"], "html.parser")
    raw_media = summary.find_all(["img", "source"])
    return [media["src"] for media in raw_media]
