from unittest.mock import patch

from feedparser import FeedParserDict
from pytest import mark

from feed.parser import parse_media_links
from settings import Settings

FEED_NAME = "test-feed-name"

FEED_TYPE_NO_OVERRIDE = "test-feed-type-no-override"
FEED_TYPE_OVERRIDE = "test-feed-type"
FEED_TYPE_OVERRIDE_PARAMETRIZED = "test-feed-type-parametrized-override"
ENTRY_ID = "test-entry-id"
ENTRY_LINK = "test-entry-link"
OVERRIDE_PATTERN_NO_PARAMETERS = "override-pattern"
OVERRIDE_PATTERN = "{feed_type}_{feed_name}_{entry_id}_{entry_link}"
OVERRIDE_VALUE = OVERRIDE_PATTERN.format(
    feed_type=FEED_TYPE_OVERRIDE_PARAMETRIZED,
    feed_name=FEED_NAME,
    entry_id=ENTRY_ID,
    entry_link=ENTRY_LINK,
)
RSS_FEEDS = {
    FEED_TYPE_OVERRIDE: {"media_override": OVERRIDE_PATTERN_NO_PARAMETERS},
    FEED_TYPE_OVERRIDE_PARAMETRIZED: {"media_override": OVERRIDE_PATTERN},
    FEED_TYPE_NO_OVERRIDE: {"show_description": True},
}

ENTRY_WITH_MEDIA_CONTENT = FeedParserDict(
    {"media_content": [{"url": "link-1"}, {"url": "link-2"}]}
)
EXPECTED_LINKS_FROM_MEDIA_CONTENT = ["link-1", "link-2"]

MEDIA_LINKS_IN_SUMMARY = """
    <img src='expected-img-link' alt='not-expected-alt'>
    not expected raw text
    <source src='expected-source-link' type='not-expected-type'>
"""
ENTRY_WITHOUT_MEDIA_CONTENT = FeedParserDict({"summary": MEDIA_LINKS_IN_SUMMARY})
EXPECTED_LINKS_FROM_SUMMARY = ["expected-img-link", "expected-source-link"]

ENTRY_FOR_PARAMETRIZED_OVERRIDE = FeedParserDict(
    {
        "media_content": [{"url": "link-1"}, {"url": "link-2"}],
        "summary": MEDIA_LINKS_IN_SUMMARY,
        "id": ENTRY_ID,
        "link": ENTRY_LINK,
    }
)


@mark.parametrize(
    argnames=("feed_type", "entry", "expected_links"),
    argvalues=[
        (
            FEED_TYPE_NO_OVERRIDE,
            ENTRY_WITH_MEDIA_CONTENT,
            EXPECTED_LINKS_FROM_MEDIA_CONTENT,
        ),
        (
            FEED_TYPE_NO_OVERRIDE,
            ENTRY_WITHOUT_MEDIA_CONTENT,
            EXPECTED_LINKS_FROM_SUMMARY,
        ),
        (
            FEED_TYPE_OVERRIDE,
            ENTRY_WITH_MEDIA_CONTENT,
            [OVERRIDE_PATTERN_NO_PARAMETERS],
        ),
        (
            FEED_TYPE_OVERRIDE_PARAMETRIZED,
            ENTRY_FOR_PARAMETRIZED_OVERRIDE,
            [OVERRIDE_VALUE],
        ),
    ],
)
@patch.object(Settings, "RSS_FEEDS", RSS_FEEDS)
def test_parse_media_links(
    feed_type: str, entry: FeedParserDict, expected_links: list[str]
) -> None:
    assert expected_links == parse_media_links(entry, feed_type, FEED_NAME)
