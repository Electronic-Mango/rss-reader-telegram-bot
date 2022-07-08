from collections import namedtuple
from logging import getLogger

from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.results import DeleteResult

from settings import DB_HOST, DB_PORT, DB_COLLECTION_NAME, DB_NAME

# TODO Is this namedtuple needed? Can this be normal tuple?
FeedData = namedtuple("FeedData", ["feed_name", "feed_type", "feed_link", "latest_item_id"])

_logger = getLogger(__name__)
_feed_collection = None


# TODO Is it a good idea to set _feed_collection here and even store collection as a global var?
# It does work and allows for control when MongoClient is created, but I'm not sure.
def initialize_db() -> None:
    _logger.info("Initalizing DB...")
    global _feed_collection
    _feed_collection = MongoClient(DB_HOST, DB_PORT)[DB_NAME][DB_COLLECTION_NAME]
    _logger.info("Creating DB index...")
    index = _feed_collection.create_index(
        [("chat_id", ASCENDING), ("feed_name", ASCENDING), ("feed_type", ASCENDING)],
        unique=True
    )
    _logger.info(f"Created index [{index}]")


def get_feed_data_for_chat(chat_id: int) -> list[FeedData]:
    _logger.info(f"[{chat_id}] Getting data")
    return [_parse_document(document) for document in _feed_collection.find({"chat_id": chat_id})]


def feed_is_in_db(chat_id: int, feed_type: str, feed_name: str) -> bool:
    _logger.info(f"[{chat_id}] Checking for [{feed_type}] [{feed_name}]")
    return _feed_collection.count_documents(
        {"chat_id": chat_id, "feed_type": feed_type, "feed_name": feed_name},
        limit=1
    )


def chat_has_feeds(chat_id: int) -> bool:
    _logger.info(f"[{chat_id}] Checking if chat has any feeds")
    return _feed_collection.count_documents({"chat_id": chat_id}, limit=1)


# TODO Does this need to return anything?
def add_feed_to_db(
    chat_id: int,
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
    insert_result = _feed_collection.insert_one({
        "chat_id": chat_id,
        "feed_name": feed_name,
        "feed_type": feed_type,
        "feed_link": feed_link,
        "latest_item_id": latest_entry_id
    })
    _logger.info(f"[{chat_id}] Insert acknowledged=[{insert_result.acknowledged}]")
    return FeedData(feed_name, feed_type, feed_link, latest_entry_id)


def get_all_data_from_db() -> list[tuple[int, FeedData]]:
    _logger.info(f"Getting all data for all chats")
    return [
        (document["chat_id"], _parse_document(document))
        for document in _feed_collection.find({})
    ]


def update_latest_item_id_in_db(
    chat_id: int,
    feed_type: str,
    feed_name: str,
    new_latest_item_id: str
) -> None:
    _logger.info(f"[{chat_id}] Updating latest item ID [{feed_type}] [{feed_name}]")
    _feed_collection.find_one_and_update(
        {"chat_id": chat_id, "feed_type": feed_type, "feed_name": feed_name},
        {"$set": {"latest_item_id": new_latest_item_id}},
    )


# TODO Is returning deleted count needed?
def remove_feed_link_id_db(chat_id: int, feed_type: str, feed_name: str) -> int:
    _logger.info(f"[{chat_id}] Deleting [{feed_type}] [{feed_name}]")
    delete_result = _feed_collection.delete_many(
        {"chat_id": chat_id, "feed_type": feed_type, "feed_name": feed_name}
    )
    _log_delete_result(chat_id, delete_result)
    return delete_result.deleted_count


def remove_chat_data(chat_id: int) -> None:
    _logger.info(f"[{chat_id}] Deleting all data for chat")
    delete_result = _feed_collection.delete_many({"chat_id": chat_id})
    _log_delete_result(chat_id, delete_result)


def _log_delete_result(chat_id: int, delete_result: DeleteResult) -> None:
    _logger.info(
        f"[{chat_id}] Delete result: "
        f"acknowledged=[{delete_result.acknowledged}] "
        f"count=[{delete_result.deleted_count}]"
    )


def _parse_document(document: dict) -> FeedData:
    return FeedData(
        document["feed_name"],
        document["feed_type"],
        document["feed_link"],
        document["latest_item_id"],
    )
