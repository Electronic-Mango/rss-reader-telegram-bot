from unittest.mock import MagicMock, patch

from feedparser import FeedParserDict

from feed.reader import get_parsed_feed

FEED_TYPE = "FEED_TYPE"
FEED_NAME = "FEED_NAME"
FEED_LINK = "FEED_LINK_{source_pattern}"
FEED_CONTENT = b"FEED-CONTENT"
FEED_HEADERS = {"content-type": "application/xml"}
FEED_STATUS_CODE = 200
EXPECTED_FEED_LINK = FEED_LINK.format(source_pattern=FEED_NAME)
MOCKED_FEED_PARSER_DICT = FeedParserDict({"id": "FEED-ID"})


def mocked_parse(content: bytes, response_headers=None) -> FeedParserDict | None:
    if content == FEED_CONTENT and response_headers == FEED_HEADERS:
        return MOCKED_FEED_PARSER_DICT
    else:
        return None


@patch("feed.reader.RSS_FEEDS", {FEED_TYPE: {"url": FEED_LINK}})
@patch("feed.reader.parse", side_effect=mocked_parse)
@patch("feed.reader.aget")
async def test_get_parsed_feed(aget_mock: MagicMock, _) -> None:
    aget_mock.return_value = MagicMock(
        content=FEED_CONTENT,
        headers=FEED_HEADERS,
        status_code=FEED_STATUS_CODE,
        url=EXPECTED_FEED_LINK,
    )

    parsed_feed = await get_parsed_feed(FEED_TYPE, FEED_NAME)

    aget_mock.assert_called_once_with(EXPECTED_FEED_LINK)
    assert parsed_feed["id"] == "FEED-ID"
    assert parsed_feed["status"] == FEED_STATUS_CODE
    assert parsed_feed["href"] == EXPECTED_FEED_LINK
