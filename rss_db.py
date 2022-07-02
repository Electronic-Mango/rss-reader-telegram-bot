from dotenv import load_dotenv
from os import getenv
from pymongo import MongoClient


def get_rss_database():
    load_dotenv()
    db_client = MongoClient(getenv("DB_HOST"), int(getenv("DB_PORT")))
    return db_client[str(getenv("DB_FEED_DATA_NAME"))]


def add_rss_to_db(channel_id, rss_feed, rss_name, latest_item_id):
    db = get_rss_database()
    channel_collection = db[str(channel_id)]
    insertion_result = channel_collection.insert_one(
        {
            "rss_name": rss_name,
            "rss_feed": rss_feed,
            "latest_item_id": latest_item_id
        }
    )
    print(f"Insert result: acknowledged={insertion_result.acknowledged} ID={insertion_result.inserted_id}")


def get_all_rss_from_db():
    db = get_rss_database()
    collection_names = db.list_collection_names()
    return {
        collection_name: list(db.get_collection(collection_name).find({}))
        for collection_name
        in collection_names
    }