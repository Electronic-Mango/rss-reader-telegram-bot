"""Data passed via inline keyboard buttons in the "subscriptions" command."""

from typing import NamedTuple


class TypesData(NamedTuple):
    chat_data: dict[str, list[str]]


class NamesData(NamedTuple):
    feed_type: str
    chat_data: dict[str, list[str]]


class DetailsData(NamedTuple):
    feed_type: str
    feed_name: str
    chat_data: dict[str, list[str]]


class RemoveFeedData(NamedTuple):
    feed_type: str
    feed_name: str
    chat_data: dict[str, list[str]]


class SendLatestUpdateData(NamedTuple):
    feed_type: str
    feed_name: str
    chat_data: dict[str, list[str]]
