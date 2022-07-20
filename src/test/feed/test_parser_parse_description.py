from feedparser import FeedParserDict

from feed.parser import parse_description

ENTRY = FeedParserDict({"summary": "\n\n\n<b>bold text</b><a>\n\nlink text</a> raw\ntext\n\n\n"})
EXPECTED_DESCRIPTION = "bold text\n\nlink text raw\ntext"


def test_parse_description() -> None:
    assert EXPECTED_DESCRIPTION == parse_description(ENTRY)
