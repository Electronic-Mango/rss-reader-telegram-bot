from unittest.mock import MagicMock, patch

from pymongo import ASCENDING

from db.client import delete_many, exists, find_many, initialize_db, insert_one, update_one
from settings import DB_COLLECTION_NAME, DB_HOST, DB_NAME, DB_PORT

collection_mock = MagicMock()
operation_result_mock = MagicMock()
document = MagicMock()
filter = MagicMock()


def mocked_mongo_client(host: str, port: str):
    assert DB_HOST == host
    assert DB_PORT == port
    return {DB_NAME: {DB_COLLECTION_NAME: collection_mock}}


@patch("db.client.MongoClient", side_effect=mocked_mongo_client)
def test_initialize_db(mongo_client_mock: MagicMock) -> None:
    collection_mock.create_index.return_value = operation_result_mock
    initialize_db()
    assert mongo_client_mock.call_count
    create_index = collection_mock.create_index
    assert create_index.call_count
    create_index_kwargs = create_index.call_args.kwargs
    expected_keys = [("chat_id", ASCENDING), ("feed_name", ASCENDING), ("feed_type", ASCENDING)]
    assert expected_keys == create_index_kwargs.get("keys")
    assert create_index_kwargs.get("unique")


@patch("db.client.MongoClient", side_effect=mocked_mongo_client)
def test_insert_one(_) -> None:
    initialize_db()
    collection_mock.insert_one.return_value = operation_result_mock
    insertion_result = insert_one(document)
    assert operation_result_mock == insertion_result
    assert (document,) == collection_mock.insert_one.call_args.args


@patch("db.client.MongoClient", side_effect=mocked_mongo_client)
def test_delete_many(_) -> None:
    initialize_db()
    collection_mock.delete_many.return_value = operation_result_mock
    insertion_result = delete_many(filter)
    assert operation_result_mock == insertion_result
    assert (filter,) == collection_mock.delete_many.call_args.args


@patch("db.client.MongoClient", side_effect=mocked_mongo_client)
def test_update_one(_) -> None:
    initialize_db()
    collection_mock.find_one_and_update.return_value = operation_result_mock
    insertion_result = update_one(filter, document)
    assert operation_result_mock == insertion_result
    assert (filter, document) == collection_mock.find_one_and_update.call_args.args


@patch("db.client.MongoClient", side_effect=mocked_mongo_client)
def test_find_many(_) -> None:
    initialize_db()
    collection_mock.find.return_value = operation_result_mock
    insertion_result = find_many(filter)
    assert operation_result_mock == insertion_result
    assert (filter,) == collection_mock.find.call_args.args


@patch("db.client.MongoClient", side_effect=mocked_mongo_client)
def test_exists(_) -> None:
    initialize_db()
    collection_mock.count_documents.return_value = operation_result_mock
    insertion_result = exists(filter)
    assert operation_result_mock == insertion_result
    assert (filter,) == collection_mock.count_documents.call_args.args
