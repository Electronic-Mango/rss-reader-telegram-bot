from unittest.mock import MagicMock, patch

from pymongo import ASCENDING
from pytest import mark

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
@mark.parametrize(
    argnames=["client_function", "db_function", "args"],
    argvalues=[
        (insert_one, "insert_one", (document,)),
        (delete_many, "delete_many", (filter,)),
        (update_one, "find_one_and_update", (filter, document)),
        (find_many, "find", (filter,)),
        (exists, "count_documents", (filter,)),
    ],
)
def test_db_operations(_, client_function, db_function, args) -> None:
    initialize_db()
    db_function = getattr(collection_mock, db_function)
    db_function.return_value = operation_result_mock
    insertion_result = client_function(*args)
    assert db_function.call_count
    assert operation_result_mock == insertion_result
    assert args == db_function.call_args.args
