from feedparser import FeedParserDict

from feed.parser import parse_link

EXPECTED_ENTRY_LINK = "entry_link"
ENTRY = FeedParserDict({"link": EXPECTED_ENTRY_LINK})


def test_parse_link() -> None:
    assert EXPECTED_ENTRY_LINK == parse_link(ENTRY)
