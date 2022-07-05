from os import getenv
from yaml import safe_load


def feed_type_to_rss():
    return safe_load(getenv("RSS_FEEDS"))
