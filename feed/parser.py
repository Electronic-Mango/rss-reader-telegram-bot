from bs4 import BeautifulSoup
from feedparser.util import FeedParserDict


def parse_entry(entry: FeedParserDict) -> tuple[str, str, list[str]]:
    return (entry["link"], _parse_description(entry), _parse_media_urls(entry))


def _parse_description(entry: FeedParserDict) -> str:
    summary = BeautifulSoup(entry["summary"], "html.parser").find_all(text=True)
    return "".join(text.strip() for text in summary).strip()


def _parse_media_urls(entry: FeedParserDict) -> list[str]:
    if "media_content" in entry:
        return [media["url"] for media in entry["media_content"]]
    media_source = BeautifulSoup(entry["summary"], "html.parser")
    media_elements = media_source.find_all(["img", "source"])
    return [media["src"] for media in media_elements]
    