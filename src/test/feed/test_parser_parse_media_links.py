from time import strftime, struct_time
from unittest.mock import patch
from urllib.parse import quote

from pytest import mark

from feed.parser import parse_media_links
from feed.types import RssEntry
from settings import Settings

FEED_NAME = "test-feed-name"

FEED_TYPE_NO_OVERRIDE = "test-feed-type-no-override"
FEED_TYPE_OVERRIDE = "test-feed-type"
FEED_TYPE_OVERRIDE_PARAMETRIZED = "test-feed-type-parametrized-override"
FEED_TYPE_OVERRIDE_MALFORMED_NO_CLOSING_BRACE = "test-feed-type-malformed-brace"
FEED_TYPE_OVERRIDE_MALFORMED_UNEXPECTED_PLACEHOLDER = "test-feed-type-placeholder"
FEED_TYPE_INVALID_OVERRIDE = "test-feed-type-invalid-override"

ENTRY_ID = "test-entry-id"
ENTRY_LINK = "test-entry-link"

DATE_STRUCT = struct_time([2024, 6, 6, 0, 0, 0, 0, 0, 0])
OVERRIDE_PATTERN_NO_PARAMETERS = "override-pattern"
OVERRIDE_PATTERN = "{feed_type}_{feed_name}_{entry_id}_{entry_link}_{entry_date}"
OVERRIDE_VALUE = OVERRIDE_PATTERN.format(
    feed_type=FEED_TYPE_OVERRIDE_PARAMETRIZED,
    feed_name=FEED_NAME,
    entry_id=ENTRY_ID,
    entry_link=ENTRY_LINK,
    entry_date=strftime("%Y-%m-%d %H:%M:%S", DATE_STRUCT),
)
OVERRIDE_VALUE_MISSING_FIELDS = OVERRIDE_PATTERN.format(
    feed_type=FEED_TYPE_OVERRIDE_PARAMETRIZED,
    feed_name=FEED_NAME,
    entry_id=None,
    entry_link=None,
    entry_date=None,
)
OVERRIDE_MALFORMED_PATTERN_NO_CLOSING_BRACE = "{entry_id}_{entry_link"
OVERRIDE_MALFORMED_PATTERN_UNEXPECTED_PLACEHOLDER = "{entry_type}_{feed_name}"

ENTRY_WITH_MEDIA_CONTENT = {"media_content": [{"url": "link-1"}, {"url": "link-2"}]}
EXPECTED_LINKS_FROM_MEDIA_CONTENT = ["link-1", "link-2"]

MEDIA_LINKS_IN_SUMMARY = """
    <img src='expected-img-link' alt='not-expected-alt'>
    not expected raw text
    <source src='expected-source-link' type='not-expected-type'>
"""
ENTRY_WITHOUT_MEDIA_CONTENT = {"summary": MEDIA_LINKS_IN_SUMMARY}
EXPECTED_LINKS_FROM_SUMMARY = ["expected-img-link", "expected-source-link"]

ENTRY_FOR_PARAMETRIZED_OVERRIDE = {
    "media_content": [{"url": "link-1"}, {"url": "link-2"}],
    "summary": MEDIA_LINKS_IN_SUMMARY,
    "id": ENTRY_ID,
    "link": ENTRY_LINK,
    "published_parsed": DATE_STRUCT,
}
ENTRY_FOR_PARAMETRIZED_OVERRIDE_MISSING_FIELDS = {
    "media_content": [{"url": "link-1"}, {"url": "link-2"}],
    "summary": MEDIA_LINKS_IN_SUMMARY,
}

RSS_FEEDS = {
    FEED_TYPE_OVERRIDE: {"media_override": {"pattern": OVERRIDE_PATTERN_NO_PARAMETERS}},
    FEED_TYPE_OVERRIDE_PARAMETRIZED: {
        "media_override": {"pattern": OVERRIDE_PATTERN, "encode_http": True}
    },
    FEED_TYPE_NO_OVERRIDE: {"show_description": True},
    FEED_TYPE_INVALID_OVERRIDE: {"media_override": {}},
    FEED_TYPE_OVERRIDE_MALFORMED_NO_CLOSING_BRACE: {
        "media_override": {"pattern": OVERRIDE_MALFORMED_PATTERN_NO_CLOSING_BRACE}
    },
    FEED_TYPE_OVERRIDE_MALFORMED_UNEXPECTED_PLACEHOLDER: {
        "media_override": {
            "pattern": OVERRIDE_MALFORMED_PATTERN_UNEXPECTED_PLACEHOLDER,
            "encode_http": True,
        }
    },
}


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
            [quote(OVERRIDE_VALUE, safe="")],
        ),
        (
            FEED_TYPE_INVALID_OVERRIDE,
            ENTRY_WITH_MEDIA_CONTENT,
            EXPECTED_LINKS_FROM_MEDIA_CONTENT,
        ),
        (
            FEED_TYPE_OVERRIDE_PARAMETRIZED,
            ENTRY_FOR_PARAMETRIZED_OVERRIDE_MISSING_FIELDS,
            [quote(OVERRIDE_VALUE_MISSING_FIELDS, safe="")],
        ),
        (
            FEED_TYPE_OVERRIDE_MALFORMED_NO_CLOSING_BRACE,
            ENTRY_FOR_PARAMETRIZED_OVERRIDE,
            [],
        ),
        (
            FEED_TYPE_OVERRIDE_MALFORMED_UNEXPECTED_PLACEHOLDER,
            ENTRY_FOR_PARAMETRIZED_OVERRIDE,
            [],
        ),
    ],
)
@patch.object(Settings, "RSS_FEEDS", RSS_FEEDS)
def test_parse_media_links(
    feed_type: str, entry: RssEntry, expected_links: list[str]
) -> None:
    parsed_links = parse_media_links(entry, feed_type, FEED_NAME)
    assert expected_links == parsed_links
