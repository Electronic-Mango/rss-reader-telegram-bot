from time import strptime

from pytest import mark

from feed.reader import get_latest_data
from feed.types import RssEntry
from settings import Settings

FEED_LINK = "FEED_LINK"

ENTRIES = [
    {"published_parsed": strptime("02.02.2002", "%d.%m.%Y")},
    {"published_parsed": strptime("01.01.2001", "%d.%m.%Y")},
    {"published_parsed": strptime("04.04.2004", "%d.%m.%Y")},
    {"published_parsed": strptime("03.03.2003", "%d.%m.%Y")},
]

EXPECTED_LATEST_ID = "LATEST_ID"
EXPECTED_LATEST_LINK = "LATEST_LINK"
EXPECTED_LATEST_DATE = strptime("06.06.2006", "%d.%m.%Y")
EXPECTED_LATEST_ENTRY_DATA = (
    EXPECTED_LATEST_ID,
    EXPECTED_LATEST_LINK,
    EXPECTED_LATEST_DATE,
)
LATEST_ENTRY = {
    "id": EXPECTED_LATEST_ID,
    "link": EXPECTED_LATEST_LINK,
    "published_parsed": EXPECTED_LATEST_DATE,
}

EXPECTED_SECOND_LATEST_ID = "SECOND_LATEST_ID"
EXPECTED_SECOND_LATEST_LINK = "SECOND_LATEST_LINK"
EXPECTED_SECOND_LATEST_DATE = strptime("05.05.2005", "%d.%m.%Y")
EXPECTED_SECOND_LATEST_ENTRY_DATA = (
    EXPECTED_SECOND_LATEST_ID,
    EXPECTED_SECOND_LATEST_LINK,
    EXPECTED_SECOND_LATEST_DATE,
)
SECOND_LATEST_ENTRY = {
    "id": EXPECTED_SECOND_LATEST_ID,
    "link": EXPECTED_SECOND_LATEST_LINK,
    "published_parsed": EXPECTED_SECOND_LATEST_DATE,
}


@mark.parametrize(
    argnames="entries",
    argvalues=[
        [*ENTRIES, SECOND_LATEST_ENTRY, LATEST_ENTRY],
        [*ENTRIES, LATEST_ENTRY, SECOND_LATEST_ENTRY],
        [LATEST_ENTRY, SECOND_LATEST_ENTRY, *ENTRIES],
        [SECOND_LATEST_ENTRY, LATEST_ENTRY, *ENTRIES],
        [*ENTRIES[:2], LATEST_ENTRY, SECOND_LATEST_ENTRY, *ENTRIES[2:]],
        [*ENTRIES[:2], SECOND_LATEST_ENTRY, LATEST_ENTRY, *ENTRIES[2:]],
    ],
)
def test_get_latest_data(entries: list[RssEntry]) -> None:
    feed = {"href": FEED_LINK, "entries": entries}

    Settings.SKIP_LATEST_ON_ADD = False
    assert get_latest_data(feed) == EXPECTED_LATEST_ENTRY_DATA

    Settings.SKIP_LATEST_ON_ADD = True
    assert get_latest_data(feed) == EXPECTED_SECOND_LATEST_ENTRY_DATA


def test_get_latest_data_selects_latest_on_feeds_with_one_entry() -> None:
    feed = {"href": FEED_LINK, "entries": [LATEST_ENTRY]}

    Settings.SKIP_LATEST_ON_ADD = False
    assert get_latest_data(feed) == EXPECTED_LATEST_ENTRY_DATA

    Settings.SKIP_LATEST_ON_ADD = True
    assert get_latest_data(feed) == EXPECTED_LATEST_ENTRY_DATA
