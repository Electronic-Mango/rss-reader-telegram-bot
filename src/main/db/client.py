"""
Module wrapping a MongoDB client and functions modifying a collection within it.

Contains only DB-specific functions, none application-specific ones.
Application-specific functions are in the "wrapper" module.

This way it should be simple to switch to a different DB altogether,
only this module needs to be modified.

Additionally, this module is also creating needed database, collection and index in the database.
"""

from collections.abc import Mapping
from typing import Any

from loguru import logger
from pymongo import ASCENDING, AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.cursor import AsyncCursor
from pymongo.results import DeleteResult, InsertOneResult

from settings import DB_FEEDS_NAME, DB_HOST, DB_NAME, DB_PORT

_feeds_collection: AsyncCollection | None = None


async def initialize_db() -> None:
    """Initialize MongoDB client, create relevant DB, collection and index."""
    if _feeds_collection is not None:
        logger.warning("DB already initialized!")
        return
    logger.info("Initializing DB...")
    _initialize_collections()
    await _create_indexes()


def _initialize_collections() -> None:
    database = AsyncMongoClient(DB_HOST, DB_PORT)[DB_NAME]
    global _feeds_collection
    _feeds_collection = database[DB_FEEDS_NAME]


async def _create_indexes() -> None:
    logger.info("Creating DB indexes...")
    feed_index = await _feeds_collection.create_index(
        keys=[("chat_id", ASCENDING), ("feed_name", ASCENDING), ("feed_type", ASCENDING)],
        unique=True,
    )
    logger.info(f"Created indexes [{feed_index}]")


async def insert_one(
    document: Mapping[str, Any], collection_name: str = DB_FEEDS_NAME
) -> InsertOneResult:
    """Wrap "insert_one" DB function."""
    collection = _get_collection(collection_name)
    return await collection.insert_one(document)


async def delete_many(
    db_filter: Mapping[str, Any], collection_name: str = DB_FEEDS_NAME
) -> DeleteResult:
    """Wrap "delete_many" DB function."""
    collection = _get_collection(collection_name)
    return await collection.delete_many(db_filter)


async def update_one(
    db_filter: Mapping[str, Any], update: Mapping[str, Any], collection_name: str = DB_FEEDS_NAME
) -> Any:
    """Wrap "find_one_and_update" DB function."""
    collection = _get_collection(collection_name)
    return await collection.find_one_and_update(db_filter, update)


async def find_many(
    db_filter: Mapping[str, Any] | None = None, collection_name: str = DB_FEEDS_NAME
) -> AsyncCursor:
    """Wrap "find" DB function."""
    collection = _get_collection(collection_name)
    return collection.find(db_filter)


async def find_one(
    db_filter: Mapping[str, Any] | None = None, collection_name: str = DB_FEEDS_NAME
) -> Mapping[str, Any] | None:
    """Wrap "find_one" DB function."""
    collection = _get_collection(collection_name)
    return await collection.find_one(db_filter)


async def exists(db_filter: Mapping[str, Any], collection_name: str = DB_FEEDS_NAME) -> bool:
    """Check if there are any documents from a given filter, using count_documents DB function."""
    collection = _get_collection(collection_name)
    return bool(await collection.count_documents(db_filter, limit=1))


def _get_collection(name: str) -> AsyncCollection:
    if name != DB_FEEDS_NAME:
        error_msg = f"Unknown collection name: {name}"
        raise ValueError(error_msg)
    if _feeds_collection is None:
        error_msg = "DB is not initialized!"
        raise RuntimeError(error_msg)
    return _feeds_collection
