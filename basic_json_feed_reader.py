from json import loads
from requests import get


def get_json_feed_response(feed_link):
    rss_response = get(feed_link)
    return loads(rss_response.text)


def get_json_feed_items(feed_link):
    json_feed_response = get_json_feed_response(feed_link)
    return json_feed_response["items"]


def get_unhandled_feed_items(feed_link, latest_handled_item_id):
    loaded_items = get_json_feed_items(feed_link)
    unhandled_items = list()
    for item in loaded_items:
        if item["id"] == latest_handled_item_id:
            break
        unhandled_items.append(item)
    return unhandled_items
