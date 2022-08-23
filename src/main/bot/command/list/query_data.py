from typing import NamedTuple


class ListNamesData(NamedTuple):
    type: str
    names: list[str]
    all_data: dict[str, list[str]]


class ListTypesData(NamedTuple):
    all_data: dict[str, list[str]]
