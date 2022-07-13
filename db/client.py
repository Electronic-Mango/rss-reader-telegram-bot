from logging import getLogger
from typing import Any, Mapping

from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.cursor import Cursor
from pymongo.results import DeleteResult, InsertOneResult

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


def insert_one(document: Mapping[str, Any]) -> InsertOneResult:
    return _feed_collection.insert_one(document)


def delete_many(filter: Mapping[str, Any]) -> DeleteResult:
    return _feed_collection.delete_many(filter)


def update_one(filter: Mapping[str, Any], update: Mapping[str, Any]) -> Any:
    return _feed_collection.find_one_and_update(filter, update)


def find_many(filter: Mapping[str, Any] = None) -> Cursor:
    return _feed_collection.find(filter=filter)


def exists(filter: Mapping[str, Any]) -> Cursor:
    return _feed_collection.count_documents(filter=filter, limit=1)
