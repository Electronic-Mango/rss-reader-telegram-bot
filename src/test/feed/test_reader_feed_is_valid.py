from unittest.mock import patch

from pytest import mark
from pytest_mock import MockerFixture

from feed.reader import feed_is_valid

FEED_TYPE = "FEED_TYPE"
FEED_NAME = "FEED_NAME"
FEED_LINK = "FEED_LINK"


@patch("feed.reader.RSS_FEEDS", {FEED_TYPE: FEED_LINK})
@mark.parametrize(
    argnames=["parsed_rss", "expected_validity"],
    argvalues=[
        ({"status": 200, "entries": [None]}, True),
        ({"status": 301, "entries": [None]}, True),
        ({"status": 200, "entries": []}, False),
        ({"status": 301, "entries": []}, False),
        ({"status": 200}, False),
        ({"status": 301}, False),
        ({"status": 400, "entries": [None]}, False),
    ],
)
def test_feed_is_valid(parsed_rss: dict, expected_validity: bool, mocker: MockerFixture) -> None:
    mocker.patch("feed.reader.parse", return_value=parsed_rss)
    assert expected_validity == bool(feed_is_valid(FEED_TYPE, FEED_NAME))
