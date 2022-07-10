from logging import getLogger

from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.results import DeleteResult

from settings import DB_COLLECTION_NAME, DB_HOST, DB_NAME, DB_PORT

_logger = getLogger(__name__)
_feed_collection: Collection = None


# TODO Is it a good idea to set _feed_collection here and even store collection as a global var?
# It does work and allows for control when MongoClient is created, but I'm not sure.
def initialize_db() -> None:
    _logger.info("Initalizing DB...")
    global _feed_collection
    _feed_collection = MongoClient(DB_HOST, DB_PORT)[DB_NAME][DB_COLLECTION_NAME]
    _logger.info("Creating DB index...")
    index = _feed_collection.create_index(
        [("chat_id", ASCENDING), ("feed_name", ASCENDING), ("feed_type", ASCENDING)],
        unique=True,
    )
    _logger.info(f"Created index [{index}]")


def get_all_stored_data() -> list[tuple[int, str, str, str]]:
    _logger.info(f"Getting all data for all chats")
    return [
        (document["chat_id"], document["feed_type"], document["feed_name"], document["latest_id"])
        for document in _feed_collection.find({})
    ]


def get_stored_feed_type_and_name(chat_id: int) -> list[tuple[str, str]]:
    _logger.info(f"[{chat_id}] Getting data")
    return [
        (document["feed_type"], document["feed_name"])
        for document in _feed_collection.find({"chat_id": chat_id})
    ]


def feed_is_already_stored(chat_id: int, feed_type: str, feed_name: str) -> bool:
    _logger.info(f"[{chat_id}] Checking for [{feed_type}] [{feed_name}]")
    return _feed_collection.count_documents(
        limit=1, filter={"chat_id": chat_id, "feed_type": feed_type, "feed_name": feed_name}
    )


def chat_has_stored_feeds(chat_id: int) -> bool:
    _logger.info(f"[{chat_id}] Checking if chat has any feeds")
    return _feed_collection.count_documents(limit=1, filter={"chat_id": chat_id})


def store_feed_data(chat_id: int, feed_name: str, feed_type: str, latest_id: str) -> None:
    _logger.info(f"[{chat_id}] Insert name=[{feed_name}] type=[{feed_type}] latest=[{latest_id}]")
    feed_document = {
        "chat_id": chat_id,
        "feed_name": feed_name,
        "feed_type": feed_type,
        "latest_id": latest_id,
    }
    insert_result = _feed_collection.insert_one(feed_document)
    _logger.info(f"[{chat_id}] Insert acknowledged=[{insert_result.acknowledged}]")


def update_stored_latest_id(chat_id: int, feed_type: str, feed_name: str, latest_id: str) -> None:
    _logger.info(f"[{chat_id}] Updating latest item ID [{feed_type}] [{feed_name}] [{latest_id}]")
    _feed_collection.find_one_and_update(
        {"chat_id": chat_id, "feed_type": feed_type, "feed_name": feed_name},
        {"$set": {"latest_id": latest_id}},
    )


def remove_stored_feed(chat_id: int, feed_type: str, feed_name: str) -> None:
    _logger.info(f"[{chat_id}] Deleting [{feed_type}] [{feed_name}]")
    delete_result = _feed_collection.delete_many(
        {"chat_id": chat_id, "feed_type": feed_type, "feed_name": feed_name}
    )
    _log_delete_result(chat_id, delete_result)


def remove_stored_chat_data(chat_id: int) -> None:
    _logger.info(f"[{chat_id}] Deleting all data for chat")
    delete_result = _feed_collection.delete_many({"chat_id": chat_id})
    _log_delete_result(chat_id, delete_result)


def _log_delete_result(chat_id: int, delete_result: DeleteResult) -> None:
    _logger.info(
        f"[{chat_id}] Delete result: "
        f"acknowledged=[{delete_result.acknowledged}] "
        f"count=[{delete_result.deleted_count}]"
    )
