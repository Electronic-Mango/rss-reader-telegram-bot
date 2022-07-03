# TODO Can probably be just "json_feed_reader", since it's used for Instagram

from json import loads

from requests import get


def get_json_feed_response(feed_link):
    rss_response = get(feed_link)
    return loads(rss_response.text)


def get_json_feed_items(feed_link):
    json_feed_response = get_json_feed_response(feed_link)
    return json_feed_response["items"]


def get_not_handled_feed_items(feed_link, latest_handled_item_id):
    loaded_items = get_json_feed_items(feed_link)
    not_handled_items = list()
    for item in loaded_items:
        if item["id"] == latest_handled_item_id:
            break
        not_handled_items.append(item)
    not_handled_items.reverse()
    return not_handled_items
