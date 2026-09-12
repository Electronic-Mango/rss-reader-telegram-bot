from time import strptime, struct_time

from pytest import mark

from feed.reader import get_not_handled_entries
from feed.types import RssEntry

ENTRIES = [
    {"published_parsed": strptime("01.01.01", "%d.%m.%y"), "id": "ID1"},
    {"published_parsed": strptime("02.02.02", "%d.%m.%y"), "id": "ID2"},
    {"published_parsed": strptime("03.03.03", "%d.%m.%y"), "id": "ID3"},
    {"published_parsed": strptime("04.04.04", "%d.%m.%y"), "id": "ID4"},
    {"published_parsed": strptime("05.05.05", "%d.%m.%y"), "id": "ID5"},
]


@mark.parametrize(
    argnames=("entries", "latest_id", "latest_date", "expected_entries"),
    argvalues=[
        (ENTRIES, "ID5", strptime("05.05.2005", "%d.%m.%Y"), []),
        (ENTRIES, "ID0", strptime("01.01.2000", "%d.%m.%Y"), ENTRIES),
        (ENTRIES, "ID3", strptime("03.03.2003", "%d.%m.%Y"), ENTRIES[3:]),
        (ENTRIES, "ID2.5", strptime("03.02.2003", "%d.%m.%Y"), ENTRIES[2:]),
        (
            [{"id": "NEW_ID"}, {"id": "LATEST_ID"}],
            "LATEST_ID",
            None,
            [{"id": "NEW_ID"}],
        ),
        (
            [{"published_parsed": strptime("02.02.02", "%d.%m.%y")}, ENTRIES[0]],
            "LATEST_ID",
            None,
            ENTRIES[0:1],
        ),
    ],
)
def test_get_not_handled_entries(
    entries: list[RssEntry],
    latest_id: str,
    latest_date: struct_time | None,
    expected_entries: list[RssEntry],
) -> None:
    feed = {"entries": entries}
    assert expected_entries == get_not_handled_entries(feed, latest_id, latest_date)
