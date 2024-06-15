from unittest.mock import patch

from feedparser import FeedParserDict

from feed.reader import get_parsed_feed

FEED_TYPE = "FEED_TYPE"
FEED_NAME = "FEED_NAME"
FEED_LINK = "FEED_LINK_{source_pattern}"
EXPECTED_FEED_LINK = FEED_LINK.format(source_pattern=FEED_NAME)
MOCKED_FEED_PARSER_DICT = FeedParserDict({"id": "FEED-ID"})


def mocked_parse(url_file_stream_or_string: str) -> FeedParserDict | None:
    if url_file_stream_or_string == EXPECTED_FEED_LINK:
        return MOCKED_FEED_PARSER_DICT
    else:
        return None


@patch("feed.reader.RSS_FEEDS", {FEED_TYPE: {"url": FEED_LINK}})
@patch("feed.reader.parse", side_effect=mocked_parse)
def test_get_parsed_feed(_) -> None:
    parsed_feed = get_parsed_feed(FEED_TYPE, FEED_NAME)
    assert MOCKED_FEED_PARSER_DICT == parsed_feed
