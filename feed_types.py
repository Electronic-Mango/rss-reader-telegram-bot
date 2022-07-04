from os import getenv

_INSTAGRAM_TYPE = "Instagram"
_TUMBLR_TYPE = "Tumblr"


def feed_type_to_rss():
    return {
        _INSTAGRAM_TYPE: getenv("INSTAGRAM_RSS_FEED_LINK"),
        _TUMBLR_TYPE: f"https://{getenv('RSS_FEED_USER_PATTERN')}.tumblr.com/rss",
    }
