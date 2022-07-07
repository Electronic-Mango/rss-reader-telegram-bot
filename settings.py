from dotenv import load_dotenv
from os import getenv
from yaml import safe_load

load_dotenv()

TOKEN = getenv("TOKEN")

LOG_PATH = getenv("LOG_PATH")

DB_HOST = getenv("DB_HOST")
DB_PORT = int(getenv("DB_PORT"))
DB_FEED_DATA_NAME = getenv("DB_FEED_DATA_NAME")

LOOKUP_INTERVAL_SECONDS = int(getenv("LOOKUP_INTERVAL_SECONDS"))

MAX_MESSAGE_SIZE = int(getenv("MAX_MESSAGE_SIZE"))
MAX_MEDIA_ITEMS_PER_MESSSAGE = int(getenv("MAX_MEDIA_ITEMS_PER_MESSSAGE"))

with open(getenv("RSS_FEEDS_YAML_FILENAME"), "r") as feeds_yaml:
    RSS_FEEDS = safe_load(feeds_yaml)
print(RSS_FEEDS)