from dotenv import load_dotenv
from os import getenv
from pymongo import MongoClient

def get_database():
    load_dotenv()
    db_client = MongoClient(getenv("DB_HOST"), int(getenv("DB_PORT")))
    return db_client[str(getenv("DB_FEED_DATA_NAME"))]


def add_rss_to_db(channel_id, rss_feed, rss_name):
    db = get_database()
    channel_collection = db[str(channel_id)]
    insertion_result = channel_collection.insert_one(
        {
            "rss_name": rss_name,
            "rss_feed": rss_feed
        }
    )
    print(f"Insert result: acknowledged={insertion_result.acknowledged} ID={insertion_result.inserted_id}")
