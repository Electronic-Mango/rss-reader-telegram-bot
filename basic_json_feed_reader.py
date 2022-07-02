from json import loads
from requests import get


def get_json_feed_response(feed_link):
    rss_response = get(feed_link)
    return loads(rss_response.text)


def get_json_feed_items(feed_link):
    json_feed_response = get_json_feed_response(feed_link)
    return json_feed_response["items"]
