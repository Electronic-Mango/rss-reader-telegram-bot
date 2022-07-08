from collections import namedtuple
from logging import getLogger
from typing import Any

from pymongo import MongoClient
from settings import DB_HOST, DB_PORT, DB_FEED_DATA_NAME

# TODO Is this namedtuple needed? Can this be normal tuple?
FeedData = namedtuple("FeedData", ["feed_name", "feed_type", "feed_link", "latest_item_id"])

_logger = getLogger(__name__)


def get_feed_data_for_chat(chat_id: str) -> list[FeedData]:
    _logger.info(f"[{chat_id}] Getting data")
    chat_collection = _get_collection(chat_id)
    return [_parse_document(document) for document in chat_collection.find({})]


def feed_is_in_db(chat_id: str, feed_type: str, feed_name: str) -> int:
    _logger.info(f"[{chat_id}] Checking for [{feed_type}] [{feed_name}]")
    chat_collection = _get_collection(chat_id)
    return chat_collection.count_documents({"feed_type": feed_type, "feed_name": feed_name})


def chat_has_feeds(chat_id: str) -> bool:
    _logger.info(f"[{chat_id}] Checking if chat has any feeds")
    chat_collection = _get_collection(chat_id)
    return chat_collection.count_documents({})


def add_feed_to_db(
    chat_id: str,
    feed_name: str,
    feed_type: str,
    feed_link: str,
    latest_entry_id: str
) -> FeedData:
    _logger.info(
        f"[{chat_id}] "
        f"Inserting feed data "
        f"name=[{feed_name}] "
        f"type=[{feed_type}] "
        f"feed=[{feed_link}] "
        f"latest=[{latest_entry_id}]"
    )
    chat_collection = _get_collection(chat_id)
    feed_link_data = FeedData(feed_name, feed_type, feed_link, latest_entry_id)
    insert_result = chat_collection.insert_one(feed_link_data._asdict())
    _logger.info(f"[{chat_id}] Insert acknowledged=[{insert_result.acknowledged}]")
    return feed_link_data


def get_all_data_from_db() -> dict[str, list[FeedData]]:
    _logger.info(f"Getting all data for all chats")
    db = _get_db()
    collection_names = db.list_collection_names()
    return {
        collection_name: [
            _parse_document(document)
            for document in db.get_collection(collection_name).find({})
        ]
        for collection_name in collection_names
    }


def update_latest_item_id_in_db(
    chat_id: str,
    feed_type: str,
    feed_name: str,
    new_latest_item_id: str
) -> None:
    _logger.info(f"[{chat_id}] Updating latest item ID [{feed_type}] [{feed_name}]")
    chat_collection = _get_collection(chat_id)
    chat_collection.find_one_and_update(
        {"feed_type": feed_type, "feed_name": feed_name},
        {"$set": {"latest_item_id": new_latest_item_id}},
    )


# TODO Is returning deleted count needed?
def remove_feed_link_id_db(chat_id: str, feed_type: str, feed_name: str) -> int:
    _logger.info(f"[{chat_id}] Deleting [{feed_type}] [{feed_name}]")
    chat_collection = _get_collection(chat_id)
    delete_result = chat_collection.delete_many({"feed_type": feed_type, "feed_name": feed_name})
    _logger.info(
        f"[{chat_id}] Delete result: "
        f"acknowledged=[{delete_result.acknowledged}] "
        f"count=[{delete_result.deleted_count}]"
    )
    return delete_result.deleted_count


def remove_chat_collection(chat_id: str) -> None:
    _logger.info(f"[{chat_id}] Deleting all data for chat")
    chat_collection = _get_collection(chat_id)
    chat_collection.drop()


# TODO Add return type
def _get_db():
    db_client = MongoClient(DB_HOST, DB_PORT)
    return db_client[DB_FEED_DATA_NAME]


# TODO Add return type
def _get_collection(collection_name: str):
    db = _get_db()
    return db[str(collection_name)]


# TODO Add return type
def _parse_document(document: Any) -> FeedData:
    if document is None:
        return None
    return FeedData(
        document["feed_name"],
        document["feed_type"],
        document["feed_link"],
        document["latest_item_id"],
    )
