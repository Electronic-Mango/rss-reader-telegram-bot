"""
NamedTuples storing data passed via inline keyboard buttons in the "subscriptions" command.
"""

from typing import NamedTuple


class TypesData(NamedTuple):
    chat_data: dict[str, list[str]]


class NamesData(NamedTuple):
    type: str
    chat_data: dict[str, list[str]]


class DetailsData(NamedTuple):
    type: str
    name: str
    chat_data: dict[str, list[str]]


class RemoveFeedData(NamedTuple):
    type: str
    name: str
    chat_data: dict[str, list[str]]
