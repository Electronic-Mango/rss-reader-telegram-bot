"""
Module wrapping a MongoDB client and functions modifying a collection within it.

Contains only DB-specific functions, none application-specific ones.
Application-specific functions are in the "wrapper" module.

This way it should be simple to switch to a different DB altogether,
only this module needs to be modified.

Additionally, this module is also creating needed database, collection and index in the database.
"""

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
    """Initialize MongoDB client, create relevant DB, collection and index."""
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
    """Wrapper for "insert_one" DB function."""
    return _feed_collection.insert_one(document)


def delete_many(filter: Mapping[str, Any]) -> DeleteResult:
    """Wrapper for "delete_many" DB function."""
    return _feed_collection.delete_many(filter)


def update_one(filter: Mapping[str, Any], update: Mapping[str, Any]) -> Any:
    """Wrapper for "find_one_and_update" DB function."""
    return _feed_collection.find_one_and_update(filter, update)


def find_many(filter: Mapping[str, Any] = None) -> Cursor:
    """Wrapper for "find" DB function."""
    return _feed_collection.find(filter)


def exists(filter: Mapping[str, Any]) -> Cursor:
    """Check if there are any documents from a given filter, using count_documents DB function."""
    return _feed_collection.count_documents(filter, limit=1)
