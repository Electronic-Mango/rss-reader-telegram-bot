"""
Module storing all configuration data used by the bot.

All information can be either read from a "settings.toml" file, or from environment variables,
where environment variables will be used with higher priority.

"settings.toml" is loaded either from the execution environment root,
or from a path given by "SETTINGS_TOML_PATH" environment variable.

In order to overwrite values from .toml the varialbe must follow a specific naming convention of
<TABLE NAME>_<FIELD NAME>, e.g. TELEGRAM_TOKEN, UPDATES_LOOKUP_INTERVAL, etc.
"""

from os import getenv

from dotenv import load_dotenv
from toml import load
from yaml import safe_load

load_dotenv()

_SETTINGS_TOML = load(getenv("SETTINGS_TOML_PATH", "settings.toml"))


def _load_config(table: str, key: str) -> str:
    env_name = f"{table}_{key}"
    env_value = getenv(env_name)
    return env_value if env_value is not None else _SETTINGS_TOML[table][key]


# TELEGRAM
TOKEN = _load_config("TELEGRAM", "TOKEN")
ALLOWED_USERNAMES_DELIMITER = _load_config("TELEGRAM", "ALLOWED_USERNAMES_DELIMITER")
ALLOWED_USERNAMES = [
    username.strip()
    for username in _load_config("TELEGRAM", "ALLOWED_USERNAMES").split(ALLOWED_USERNAMES_DELIMITER)
    if username.strip()
]

# UPDATES
LOOKUP_INTERVAL = float(_load_config("UPDATES", "LOOKUP_INTERVAL"))
LOOKUP_INTERVAL_RANDOMNESS = int(_load_config("UPDATES", "LOOKUP_INTERVAL_RANDOMNESS"))
LOOKUP_INITIAL_DELAY = float(_load_config("UPDATES", "LOOKUP_INITIAL_DELAY"))
LOOKUP_FEED_DELAY = float(_load_config("UPDATES", "LOOKUP_FEED_DELAY"))
LOOKUP_FEED_DELAY_RANDOMNESS = int(_load_config("UPDATES", "LOOKUP_FEED_DELAY_RANDOMNESS"))
QUIET_HOURS = {int(hour) for hour in _load_config("UPDATES", "QUIET_HOURS").split()}

# MESSAGES
MAX_MESSAGE_SIZE = int(_load_config("MESSAGES", "MAX_MESSAGE_SIZE"))
MAX_MEDIA_ITEMS_PER_MESSSAGE = int(_load_config("MESSAGES", "MAX_MEDIA_ITEMS_PER_MESSSAGE"))

# LOGGING
LOG_PATH = _load_config("LOGGING", "LOG_PATH")
MAX_BYTES = _load_config("LOGGING", "MAX_BYTES")
BACKUP_COUNT = _load_config("LOGGING", "BACKUP_COUNT")

# DATABASE
DB_HOST = _load_config("DATABASE", "DB_HOST")
DB_PORT = int(_load_config("DATABASE", "DB_PORT"))
DB_NAME = _load_config("DATABASE", "DB_NAME")
DB_COLLECTION_NAME = _load_config("DATABASE", "DB_COLLECTION_NAME")

# RSS
with open(_load_config("RSS", "FEEDS_YAML_FILENAME"), "r") as feeds_yml:
    RSS_FEEDS = safe_load(feeds_yml)
