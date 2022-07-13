from logging import getLogger

from pymongo.results import DeleteResult

from db.client import delete_many, exists, find_many, insert_one, update_one

_logger = getLogger(__name__)


def get_all_stored_data() -> list[tuple[int, str, str, str]]:
    _logger.info(f"Getting all data for all chats")
    return [
        (document["chat_id"], document["feed_type"], document["feed_name"], document["latest_id"])
        for document in find_many()
    ]


def get_stored_feed_type_and_name(chat_id: int) -> list[tuple[str, str]]:
    _logger.info(f"[{chat_id}] Getting data")
    return [
        (document["feed_type"], document["feed_name"])
        for document in find_many({"chat_id": chat_id})
    ]


def feed_is_already_stored(chat_id: int, feed_type: str, feed_name: str) -> bool:
    _logger.info(f"[{chat_id}] Checking for [{feed_type}] [{feed_name}]")
    return exists({"chat_id": chat_id, "feed_type": feed_type, "feed_name": feed_name})


def chat_has_stored_feeds(chat_id: int) -> bool:
    _logger.info(f"[{chat_id}] Checking if chat has any feeds")
    return exists({"chat_id": chat_id})


def store_feed_data(chat_id: int, feed_name: str, feed_type: str, latest_id: str) -> None:
    _logger.info(f"[{chat_id}] Insert name=[{feed_name}] type=[{feed_type}] latest=[{latest_id}]")
    document = {
        "chat_id": chat_id,
        "feed_name": feed_name,
        "feed_type": feed_type,
        "latest_id": latest_id,
    }
    insert_result = insert_one(document)
    _logger.info(f"[{chat_id}] Insert acknowledged=[{insert_result.acknowledged}]")


def update_stored_latest_id(chat_id: int, feed_type: str, feed_name: str, latest_id: str) -> None:
    _logger.info(f"[{chat_id}] Updating latest item ID [{feed_type}] [{feed_name}] [{latest_id}]")
    update_one(
        {"chat_id": chat_id, "feed_type": feed_type, "feed_name": feed_name},
        {"$set": {"latest_id": latest_id}},
    )


def remove_stored_feed(chat_id: int, feed_type: str, feed_name: str) -> None:
    _logger.info(f"[{chat_id}] Deleting [{feed_type}] [{feed_name}]")
    result = delete_many({"chat_id": chat_id, "feed_type": feed_type, "feed_name": feed_name})
    _log_delete_result(chat_id, result)


def remove_stored_chat_data(chat_id: int) -> None:
    _logger.info(f"[{chat_id}] Deleting all data for chat")
    result = delete_many({"chat_id": chat_id})
    _log_delete_result(chat_id, result)


def _log_delete_result(chat_id: int, delete_result: DeleteResult) -> None:
    _logger.info(
        f"[{chat_id}] Delete result: "
        f"acknowledged=[{delete_result.acknowledged}] "
        f"count=[{delete_result.deleted_count}]"
    )
