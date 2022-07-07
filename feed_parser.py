from collections import namedtuple

from bs4 import BeautifulSoup

FeedEntry = namedtuple("FeedEntry", ["id", "url", "summary", "media"])
FeedMedia = namedtuple("FeedMedia", ["url", "type"])


def parse_entry(entry):
    return FeedEntry(
        entry["id"],
        entry["link"],
        _parse_summary(entry),
        _parse_media(entry),
    )


def _parse_summary(entry):
    summary = BeautifulSoup(entry["summary"], "html.parser")
    all_text = summary.find_all(text=True)
    # TODO Handle links in some smarter way.
    # Perhaps appending them with "link: " would be better?
    # Right now some text in the form of a link will get removed.
    return "".join(text for text in all_text if text.parent.name not in ["a"])


def _parse_media(entry):
    if "media_content" in entry:
        return [
            FeedMedia(media["url"], media["type"]) for media in entry["media_content"]
        ]
    summary = BeautifulSoup(entry["summary"], "html.parser")
    raw_media = summary.find_all(["img", "source"])
    return [FeedMedia(media["src"], None) for media in raw_media]
