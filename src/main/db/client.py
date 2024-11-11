"""
Module wrapping a MongoDB client and functions modifying a collection within it.

Contains only DB-specific functions, none application-specific ones.
Application-specific functions are in the "wrapper" module.

This way it should be simple to switch to a different DB altogether,
only this module needs to be modified.

Additionally, this module is also creating needed database, collection and index in the database.
"""

from typing import Any, Mapping

from loguru import logger
from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.cursor import Cursor
from pymongo.results import DeleteResult, InsertOneResult

from settings import DB_FEEDS_NAME, DB_HOST, DB_NAME, DB_PINNED_NAME, DB_PORT

_feeds_collection: Collection | None = None
_pinned_collection: Collection | None = None


def initialize_db() -> None:
    """Initialize MongoDB client, create relevant DB, collection and index."""
    if _feeds_collection is not None and _pinned_collection is not None:
        logger.warning("DB already initialized!")
        return
    logger.info("Initializing DB...")
    _initialize_collections()
    _create_indexes()


def _initialize_collections() -> None:
    database = MongoClient(DB_HOST, DB_PORT)[DB_NAME]
    global _feeds_collection
    _feeds_collection = database[DB_FEEDS_NAME]
    global _pinned_collection
    _pinned_collection = database[DB_PINNED_NAME]


def _create_indexes() -> None:
    logger.info("Creating DB indexes...")
    feed_index = _feeds_collection.create_index(
        keys=[("chat_id", ASCENDING), ("feed_name", ASCENDING), ("feed_type", ASCENDING)],
        unique=True,
    )
    pinned_index = _pinned_collection.create_index(keys=[("chat_id", ASCENDING)], unique=True)
    logger.info(f"Created indexes [{feed_index}] [{pinned_index}]")


def insert_one(document: Mapping[str, Any], collection: str = DB_FEEDS_NAME) -> InsertOneResult:
    """Wrapper for "insert_one" DB function."""
    collection = _get_collection(collection)
    assert collection is not None, "DB is not initialized!"
    return collection.insert_one(document)


def delete_many(db_filter: Mapping[str, Any], collection: str = DB_FEEDS_NAME) -> DeleteResult:
    """Wrapper for "delete_many" DB function."""
    collection = _get_collection(collection)
    assert collection is not None, "DB is not initialized!"
    return collection.delete_many(db_filter)


def update_one(
    db_filter: Mapping[str, Any], update: Mapping[str, Any], collection: str = DB_FEEDS_NAME
) -> Any:
    """Wrapper for "find_one_and_update" DB function."""
    collection = _get_collection(collection)
    assert collection is not None, "DB is not initialized!"
    return collection.find_one_and_update(db_filter, update)


def find_many(db_filter: Mapping[str, Any] = None, collection: str = DB_FEEDS_NAME) -> Cursor:
    """Wrapper for "find" DB function."""
    collection = _get_collection(collection)
    assert collection is not None, "DB is not initialized!"
    return collection.find(db_filter)


def find_one(db_filter: Mapping[str, Any] = None, collection: str = DB_FEEDS_NAME) -> Cursor:
    """Wrapper for "find_one" DB function."""
    collection = _get_collection(collection)
    assert collection is not None, "DB is not initialized!"
    return collection.find_one(db_filter)


def exists(db_filter: Mapping[str, Any], collection: str = DB_FEEDS_NAME) -> bool:
    """Check if there are any documents from a given filter, using count_documents DB function."""
    collection = _get_collection(collection)
    assert collection is not None, "DB is not initialized!"
    return bool(collection.count_documents(db_filter, limit=1))


def _get_collection(name: str) -> Collection:
    return _pinned_collection if name == DB_PINNED_NAME else _feeds_collection
