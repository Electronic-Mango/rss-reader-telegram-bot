from os import getenv
from typing import Any

from dotenv import load_dotenv
from toml import load
from yaml import safe_load

load_dotenv()

_SETTINGS_TOML = load(getenv("SETTINGS_TOML_PATH", "settings.toml"))


def _load_config(table: str, key: str) -> Any:
    env_name = f"{table}_{key}"
    env_value = getenv(env_name)
    return env_value if env_value is not None else _SETTINGS_TOML[table][key]

# TELEGRAM
TOKEN = _load_config("TELEGRAM", "TOKEN")

# UPDATES
LOOKUP_INTERVAL_SECONDS = float(_load_config("UPDATES", "LOOKUP_INTERVAL_SECONDS"))
LOOKUP_INITIAL_DELAY_SECONDS = float(_load_config("UPDATES", "LOOKUP_INITIAL_DELAY_SECONDS"))
LOOKUP_FEED_DELAY_SECONDS = float(_load_config("UPDATES", "LOOKUP_FEED_DELAY_SECONDS"))

# MESSAGES
MAX_MESSAGE_SIZE = int(_load_config("MESSAGES", "MAX_MESSAGE_SIZE"))
MAX_MEDIA_ITEMS_PER_MESSSAGE = int(_load_config("MESSAGES", "MAX_MEDIA_ITEMS_PER_MESSSAGE"))

# LOGGING
LOG_PATH = _load_config("LOGGING", "LOG_PATH")

# DATABASE
DB_HOST = _load_config("DATABASE", "DB_HOST")
DB_PORT = int(_load_config("DATABASE", "DB_PORT"))
DB_NAME = _load_config("DATABASE", "DB_NAME")
DB_COLLECTION_NAME = _load_config("DATABASE", "DB_COLLECTION_NAME")

# RSS
with open(_load_config("RSS", "FEEDS_YAML_FILENAME"), "r") as feeds_yaml:
    RSS_FEEDS = safe_load(feeds_yaml)
