from feedparser import FeedParserDict
from pytest import mark

from feed.parser import parse_media_links

ENTRY_WITH_MEDIA_CONTENT = FeedParserDict({"media_content": [{"url": "link-1"}, {"url": "link-2"}]})
EXPECTED_LINKS_FROM_MEDIA_CONTENT = ["link-1", "link-2"]

MEDIA_LINKS_IN_SUMMARY = """
    <img src='expected-img-link' alt='not-expected-alt'>
    not expected raw text
    <source src='expected-source-link' type='not-expected-type'>
"""
ENTRY_WITHOUT_MEDIA_CONTENT = FeedParserDict({"summary": MEDIA_LINKS_IN_SUMMARY})
EXPECTED_LINKS_FROM_SUMMARY = ["expected-img-link", "expected-source-link"]


@mark.parametrize(
    argnames=["entry", "expected_links"],
    argvalues=[
        (ENTRY_WITH_MEDIA_CONTENT, EXPECTED_LINKS_FROM_MEDIA_CONTENT),
        (ENTRY_WITHOUT_MEDIA_CONTENT, EXPECTED_LINKS_FROM_SUMMARY),
    ],
)
def test_parse_media_links(entry: FeedParserDict, expected_links: list[str]) -> None:
    assert expected_links == parse_media_links(entry)
