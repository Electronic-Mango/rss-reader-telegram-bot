from unittest.mock import MagicMock, patch

from pymongo import ASCENDING
from pytest import mark

from db.client import (
    delete_many,
    exists,
    find_many,
    find_one,
    initialize_db,
    insert_one,
    update_one,
)
from settings import DB_COLLECTION_NAME, DB_HOST, DB_NAME, DB_PORT

collection_mock = MagicMock()
operation_result_mock = MagicMock()
document = MagicMock()
db_filter = MagicMock()


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
@mark.parametrize(
    argnames=["client_function", "db_function", "args"],
    argvalues=[
        (insert_one, "insert_one", (document,)),
        (delete_many, "delete_many", (db_filter,)),
        (update_one, "find_one_and_update", (db_filter, document)),
        (find_many, "find", (db_filter,)),
        (find_one, "find_one", (db_filter,)),
    ],
)
def test_db_operations(_, client_function, db_function, args) -> None:
    initialize_db()
    db_function = getattr(collection_mock, db_function)
    db_function.return_value = operation_result_mock
    operation_result = client_function(*args)
    assert db_function.call_count
    assert operation_result_mock == operation_result
    assert args == db_function.call_args.args


@patch("db.client.MongoClient", side_effect=mocked_mongo_client)
@mark.parametrize(argnames="document_count", argvalues=[0, 1, 2])
def test_element_exists(_, document_count: int) -> None:
    initialize_db()
    collection_mock.count_documents.return_value = document_count
    result = exists(db_filter)
    assert collection_mock.count_documents.call_count
    assert bool(document_count) == result
    assert (db_filter,) == collection_mock.count_documents.call_args.args
