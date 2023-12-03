"""
Module handling application-specific DB functions.

Contains only application-specific functions, none DB-specific ones.
DB-specific functions are in the "client" module.

This way it should be simple to switch to a different DB altogether,
since this module won't have to be modified.
"""

from collections import defaultdict
from time import struct_time

from loguru import logger
from pymongo.results import DeleteResult

from db.client import delete_many, exists, find_many, find_one, insert_one, update_one


def get_all_stored_data() -> list[tuple[int, str, str, str, struct_time]]:
    """Returns all data stored in the DB."""
    logger.info("Getting all data for all chats")
    return [
        (
            document["chat_id"],
            document["feed_type"],
            document["feed_name"],
            document["latest_id"],
            _parse_date(document.get("latest_date")),
        )
        for document in find_many()
    ]


def get_stored_feed_type_to_names(chat_id: int) -> dict[str, list[str]]:
    """Get all data for a given chat_id stored in the DB."""
    logger.info(f"[{chat_id}] Getting data")
    feed_type_to_names = defaultdict(list)
    for document in find_many({"chat_id": chat_id}):
        feed_type_to_names[document["feed_type"]].append(document["feed_name"])
    return feed_type_to_names


def get_latest_entry_data(chat_id: int, feed_type: str, feed_name: str) -> tuple[str, struct_time]:
    """Return latest stored entry ID for given feed"""
    logger.info(f"[{chat_id}] Getting latest entry ID for [{feed_type}] [{feed_name}]")
    document = find_one({"chat_id": chat_id, "feed_type": feed_type, "feed_name": feed_name})
    return document.get("latest_link"), _parse_date(document.get("latest_date"))


def feed_is_already_stored(chat_id: int, feed_type: str, feed_name: str) -> bool:
    """Check if given feed is already stored in the DB."""
    logger.info(f"[{chat_id}] Checking for [{feed_type}] [{feed_name}]")
    return exists({"chat_id": chat_id, "feed_type": feed_type, "feed_name": feed_name})


def chat_has_stored_feeds(chat_id: int) -> bool:
    """Check if given chat has any data stored in the DB."""
    logger.info(f"[{chat_id}] Checking if chat has any feeds")
    return exists({"chat_id": chat_id})


def store_feed_data(
    chat_id: int,
    feed_name: str,
    feed_type: str,
    latest_id: str,
    latest_link: str,
    latest_date: struct_time,
) -> None:
    """Store a given feed data in the DB."""
    logger.info(f"[{chat_id}] Insert name=[{feed_name}] type=[{feed_type}] latest=[{latest_id}]")
    document = {
        "chat_id": chat_id,
        "feed_name": feed_name,
        "feed_type": feed_type,
        "latest_id": latest_id,
        "latest_link": latest_link,
        "latest_date": latest_date,
    }
    insert_result = insert_one(document)
    logger.info(f"[{chat_id}] Insert acknowledged=[{insert_result.acknowledged}]")


def update_stored_latest_data(
    chat_id: int,
    feed_type: str,
    feed_name: str,
    latest_id: str,
    latest_link: str,
    latest_date: struct_time,
) -> None:
    """Update "latest_id" for a given feed in the DB."""
    logger.info(f"[{chat_id}] Updating latest item ID [{feed_type}] [{feed_name}] [{latest_id}]")
    update_one(
        {"chat_id": chat_id, "feed_type": feed_type, "feed_name": feed_name},
        {"$set": {"latest_id": latest_id, "latest_link": latest_link, "latest_date": latest_date}},
    )


def remove_stored_feed(chat_id: int, feed_type: str, feed_name: str) -> None:
    """Remove given feed from the DB."""
    logger.info(f"[{chat_id}] Deleting [{feed_type}] [{feed_name}]")
    result = delete_many({"chat_id": chat_id, "feed_type": feed_type, "feed_name": feed_name})
    _log_delete_result(chat_id, result)


def remove_stored_chat_data(chat_id: int) -> None:
    """Remove all data for a given chat from the DB."""
    logger.info(f"[{chat_id}] Deleting all data for chat")
    result = delete_many({"chat_id": chat_id})
    _log_delete_result(chat_id, result)


def _parse_date(raw_date: list[int]) -> struct_time:
    return struct_time(raw_date) if raw_date else None


def _log_delete_result(chat_id: int, delete_result: DeleteResult) -> None:
    logger.info(
        f"[{chat_id}] Delete result: "
        f"acknowledged=[{delete_result.acknowledged}] "
        f"count=[{delete_result.deleted_count}]"
    )
