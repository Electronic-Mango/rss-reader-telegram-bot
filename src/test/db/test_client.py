from unittest.mock import MagicMock, patch

from pymongo import ASCENDING
from pytest import fixture, mark, raises

from db.client import (
    delete_many,
    exists,
    find_many,
    find_one,
    initialize_db,
    insert_one,
    update_one,
)
from settings import DB_FEEDS_NAME, DB_HOST, DB_NAME, DB_PINNED_NAME, DB_PORT

feeds_collection_mock = MagicMock()
pinned_collection_mock = MagicMock()
operation_result_mock = MagicMock()
document = MagicMock()
db_filter = MagicMock()


def mocked_mongo_client(host: str, port: str):
    assert DB_HOST == host
    assert DB_PORT == port
    return {DB_NAME: {DB_FEEDS_NAME: feeds_collection_mock, DB_PINNED_NAME: pinned_collection_mock}}


@fixture(autouse=True)
def clear_initialized_collection() -> None:
    import db.client as dbc

    dbc._feeds_collection = None
    dbc._pinned_collection = None
    yield


@fixture(autouse=True)
def clear_mocks() -> None:
    feeds_collection_mock.reset_mock()
    pinned_collection_mock.reset_mock()
    yield


@patch("db.client.MongoClient", side_effect=mocked_mongo_client)
def test_initialize_db(mongo_client_mock: MagicMock) -> None:
    feeds_collection_mock.create_index.return_value = operation_result_mock
    pinned_collection_mock.create_index.return_value = operation_result_mock

    initialize_db()

    mongo_client_mock.assert_called()

    create_feeds_index = feeds_collection_mock.create_index
    create_feeds_index.assert_called()
    create_feeds_index_kwargs = create_feeds_index.call_args.kwargs
    expected_feeds_keys = [
        ("chat_id", ASCENDING),
        ("feed_name", ASCENDING),
        ("feed_type", ASCENDING),
    ]
    assert expected_feeds_keys == create_feeds_index_kwargs.get("keys")
    assert create_feeds_index_kwargs.get("unique")

    create_pinned_index = pinned_collection_mock.create_index
    create_pinned_index.assert_called()
    create_pinned_index_kwargs = create_pinned_index.call_args.kwargs
    expected_pinned_keys = [("chat_id", ASCENDING), ("message_id", ASCENDING)]
    assert expected_pinned_keys == create_pinned_index_kwargs.get("keys")
    assert create_pinned_index_kwargs.get("unique")


@patch("db.client.MongoClient", side_effect=mocked_mongo_client)
def test_db_is_not_initialized_again(mongo_client_mock: MagicMock) -> None:
    feeds_collection_mock.create_index.return_value = operation_result_mock
    pinned_collection_mock.create_index.return_value = operation_result_mock
    initialize_db()
    initialize_db()
    mongo_client_mock.assert_called_once()
    feeds_collection_mock.create_index.assert_called_once()
    pinned_collection_mock.create_index.assert_called_once()


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
    db_function = getattr(feeds_collection_mock, db_function)
    db_function.return_value = operation_result_mock
    operation_result = client_function(*args)
    db_function.assert_called()
    assert operation_result_mock == operation_result
    assert args == db_function.call_args.args


@patch("db.client.MongoClient", side_effect=mocked_mongo_client)
@mark.parametrize(argnames="document_count", argvalues=[0, 1, 2])
def test_element_exists(_, document_count: int) -> None:
    initialize_db()
    feeds_collection_mock.count_documents.return_value = document_count
    result = exists(db_filter)
    feeds_collection_mock.count_documents.assert_called()
    assert bool(document_count) == result
    assert (db_filter,) == feeds_collection_mock.count_documents.call_args.args


@patch("db.client.MongoClient", side_effect=mocked_mongo_client)
@mark.parametrize(
    argnames=["client_function", "db_function", "args"],
    argvalues=[
        (insert_one, "insert_one", (document,)),
        (delete_many, "delete_many", (db_filter,)),
        (update_one, "find_one_and_update", (db_filter, document)),
        (find_many, "find", (db_filter,)),
        (find_one, "find_one", (db_filter,)),
        (exists, "count_documents", (db_filter,)),
    ],
)
def test_correct_collection_is_selected(_, client_function, db_function, args) -> None:
    initialize_db()
    client_function(*args, collection=DB_PINNED_NAME)
    getattr(feeds_collection_mock, db_function).assert_not_called()
    getattr(pinned_collection_mock, db_function).assert_called_once()


@patch("db.client.MongoClient", side_effect=mocked_mongo_client)
@mark.parametrize(
    argnames=["client_function", "args"],
    argvalues=[
        (insert_one, (document,)),
        (delete_many, (db_filter,)),
        (update_one, (db_filter, document)),
        (find_many, (db_filter,)),
        (find_one, (db_filter,)),
        (exists, (db_filter,)),
    ],
)
def test_db_operations_fail_on_uninitialized_db(_, client_function, args) -> None:
    with raises(AssertionError) as exception_info:
        client_function(*args)
    assert str(exception_info.value) == "DB is not initialized!"
