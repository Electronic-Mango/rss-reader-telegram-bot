from dotenv import load_dotenv
from logging import info
from os import getenv
from pymongo import MongoClient


def get_rss_database():
    load_dotenv()
    db_client = MongoClient(getenv("DB_HOST"), int(getenv("DB_PORT")))
    return db_client[str(getenv("DB_FEED_DATA_NAME"))]


def add_rss_to_db(channel_id, rss_feed, rss_name, latest_item_id):
    db = get_rss_database()
    channel_collection = db[str(channel_id)]
    insert_result = channel_collection.insert_one(
        {
            "rss_name": rss_name,
            "rss_feed": rss_feed,
            "latest_item_id": latest_item_id
        }
    )
    info(f"Insert result: acknowledged={insert_result.acknowledged} ID={insert_result.inserted_id}")


def get_all_rss_from_db():
    db = get_rss_database()
    collection_names = db.list_collection_names()
    return {
        collection_name: list(db.get_collection(collection_name).find({}))
        for collection_name in collection_names
    }


def update_rss_feed_in_db(channel_id, rss_feed, rss_name, new_latest_item_id):
    db = get_rss_database()
    channel_collection = db[str(channel_id)]
    channel_collection.find_one_and_update(
        {"rss_feed": rss_feed, "rss_name": rss_name},
        {"$set": {"latest_item_id": new_latest_item_id}},
    )


def remove_rss_feed_id_db(channel_id, rss_name):
    db = get_rss_database()
    channel_collection = db[str(channel_id)]
    delete_result = channel_collection.delete_many({"rss_name": rss_name})
    info(f"Delete result: acknowledged={delete_result.acknowledged} count={delete_result.deleted_count}")
    return delete_result.deleted_count
