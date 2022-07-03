from collections import namedtuple
from logging import info
from os import getenv

from dotenv import load_dotenv
from pymongo import MongoClient

RssFeedData = namedtuple("RssFeedData", ["rss_name", "rss_feed", "latest_item_id"])


def db_document_to_rss_data(document):
    if document is None:
        return None
    return RssFeedData(document["rss_name"], document["rss_feed"], document["latest_item_id"])


def get_db():
    load_dotenv()
    db_client = MongoClient(getenv("DB_HOST"), int(getenv("DB_PORT")))
    return db_client[str(getenv("DB_FEED_DATA_NAME"))]


def get_collection(collection_name):
    db = get_db()
    return db[str(collection_name)]


def get_rss_data_for_chat(chat_id):
    chat_collection = get_collection(chat_id)
    return [db_document_to_rss_data(document) for document in chat_collection.find({})]


def get_rss_feed(chat_id, rss_name):
    chat_collection = get_collection(chat_id)
    found_document = chat_collection.find_one({"rss_name": rss_name})
    return db_document_to_rss_data(found_document)


def add_rss_to_db(chat_id, rss_feed, rss_name, latest_item_id):
    chat_collection = get_collection(chat_id)
    rss_feed_data = RssFeedData(rss_name, rss_feed, latest_item_id)
    insert_result = chat_collection.insert_one(rss_feed_data._asdict())
    info(f"Insert result: acknowledged={insert_result.acknowledged} ID={insert_result.inserted_id}")
    return rss_feed_data


def get_all_rss_from_db():
    db = get_db()
    collection_names = db.list_collection_names()
    return {
        collection_name: [
            db_document_to_rss_data(document)
            for document in db.get_collection(collection_name).find({})
        ]
        for collection_name in collection_names
    }


def update_rss_feed_in_db(chat_id, rss_feed, rss_name, new_latest_item_id):
    chat_collection = get_collection(chat_id)
    chat_collection.find_one_and_update(
        {"rss_feed": rss_feed, "rss_name": rss_name},
        {"$set": {"latest_item_id": new_latest_item_id}},
    )


def remove_rss_feed_id_db(chat_id, rss_name):
    chat_collection = get_collection(chat_id)
    delete_result = chat_collection.delete_many({"rss_name": rss_name})
    info(f"Delete result: acknowledged={delete_result.acknowledged} count={delete_result.deleted_count}")
    return delete_result.deleted_count
