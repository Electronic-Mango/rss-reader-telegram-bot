from logging import getLogger
from typing import Any, Mapping

from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.cursor import Cursor
from pymongo.results import DeleteResult, InsertOneResult

from settings import DB_COLLECTION_NAME, DB_HOST, DB_NAME, DB_PORT

_logger = getLogger(__name__)
_feed_collection: Collection = None


def initialize_db() -> None:
    _logger.info("Initalizing DB...")
    _initialize_collection()
    _create_index()


def _initialize_collection() -> None:
    global _feed_collection
    _feed_collection = MongoClient(DB_HOST, DB_PORT)[DB_NAME][DB_COLLECTION_NAME]


def _create_index() -> None:
    _logger.info("Creating DB index...")
    index = _feed_collection.create_index(
        keys=[("chat_id", ASCENDING), ("feed_name", ASCENDING), ("feed_type", ASCENDING)],
        unique=True,
    )
    _logger.info(f"Created index [{index}]")


def insert_one(document: Mapping[str, Any]) -> InsertOneResult:
    return _feed_collection.insert_one(document)


def delete_many(filter: Mapping[str, Any]) -> DeleteResult:
    return _feed_collection.delete_many(filter)


def update_one(filter: Mapping[str, Any], update: Mapping[str, Any]) -> Any:
    return _feed_collection.find_one_and_update(filter, update)


def find_many(filter: Mapping[str, Any] = None) -> Cursor:
    return _feed_collection.find(filter)


def exists(filter: Mapping[str, Any]) -> Cursor:
    return _feed_collection.count_documents(filter, limit=1)
