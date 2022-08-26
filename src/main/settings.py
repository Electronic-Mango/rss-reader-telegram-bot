"""
Module holding all configuration parameters for the project based on "settings.yml" file.
Additional parameters, overwritting the default ones can be loaded from a file defined in
"CUSTOM_SETTINGS_PATH" environment variable.
This overwritting file doesn't have to contain everything, only values to overwrite.
"""

from functools import reduce
from dotenv import load_dotenv
from os import getenv
from typing import Any

from mergedeep import merge
from yaml import safe_load

load_dotenv()
_DEFAULT_SETTINGS_PATH = "settings.yml"
_CUSTOM_SETTINGS_PATH_VARIABLE_NAME = "CUSTOM_SETTINGS_PATH"
_CUSTOM_SETTINGS_PATH = getenv(_CUSTOM_SETTINGS_PATH_VARIABLE_NAME)


def _load_settings(settings_path: str) -> dict[str, Any]:
    with open(settings_path) as settings_yaml:
        return safe_load(settings_yaml)


_SETTINGS = merge(
    _load_settings(_DEFAULT_SETTINGS_PATH),
    _load_settings(_CUSTOM_SETTINGS_PATH) if _CUSTOM_SETTINGS_PATH else {},
)


def _load_config(*keys: tuple[str]) -> Any:
    return reduce(lambda table, key: table[key], keys, _SETTINGS)


# telegram
TOKEN = _load_config("telegram", "token")
ALLOWED_USERNAMES = _load_config("telegram", "allowed_usernames")
PERSISTENCE_FILE = _load_config("telegram", "persistence_file")

# telegram updates
LOOKUP_INTERVAL = _load_config("telegram", "updates", "lookup_interval")
LOOKUP_INTERVAL_RANDOMNESS = _load_config("telegram", "updates", "lookup_interval_randomness")
LOOKUP_INITIAL_DELAY = _load_config("telegram", "updates", "lookup_initial_delay")
LOOKUP_FEED_DELAY = _load_config("telegram", "updates", "lookup_feed_delay")
LOOKUP_FEED_DELAY_RANDOMNESS = _load_config("telegram", "updates", "lookup_feed_delay_randomness")
QUIET_HOURS = _load_config("telegram", "updates", "quiet_hours")

# telegram messages
MAX_MESSAGE_SIZE = _load_config("telegram", "messages", "max_message_size")
MAX_MEDIA_ITEMS_PER_MESSSAGE = _load_config("telegram", "messages", "max_media_items_per_message")

# logging
LOG_PATH = _load_config("logging", "log_path")
MAX_BYTES = _load_config("logging", "max_bytes")
BACKUP_COUNT = _load_config("logging", "backup_count")

# database
DB_HOST = _load_config("database", "host")
DB_PORT = _load_config("database", "port")
DB_NAME = _load_config("database", "name")
DB_COLLECTION_NAME = _load_config("database", "collection_name")

# rss
with open(_load_config("rss", "feeds_yaml_filename"), "r") as feeds_yml:
    RSS_FEEDS = {name: data for name, data in safe_load(feeds_yml).items() if "url" in data}
