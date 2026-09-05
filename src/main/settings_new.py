"""
Module holding all configuration parameters for the project based on "settings.yml" file.
Additional parameters, overwriting the default ones can be loaded from a file defined in
"CUSTOM_SETTINGS_PATH" environment variable.
This overwriting file doesn't have to contain everything, only values to overwrite.
"""

from functools import reduce
from os import getenv
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from mergedeep import merge
from yaml import safe_load


class Settings:
    # Names of environment variables
    _DEFAULT_SETTINGS_PATH_VARIABLE_NAME = "DEFAULT_SETTINGS_PATH"
    _CUSTOM_SETTINGS_PATH_VARIABLE_NAME = "CUSTOM_SETTINGS_PATH"

    # Internal settings storage and optional fields
    _SETTINGS = None
    _OPTIONAL_FIELDS = {"DEFAULT_IMAGE_PATH", "ALLOWED_USERNAMES"}

    # Telegram
    TOKEN: str = None
    ALLOWED_USERNAMES: list[str] = None
    PERSISTENCE_FILE: str = None

    # Telegram updates
    LOOKUP_INTERVAL: int = None
    LOOKUP_INTERVAL_RANDOMNESS: int = None
    LOOKUP_INITIAL_DELAY: int = None
    LOOKUP_FEED_DELAY: int = None
    LOOKUP_FEED_DELAY_RANDOMNESS: int = None
    QUIET_HOURS: list[int] = None
    SHUFFLE_UPDATES: bool = None

    # Telegram messages
    MAX_MESSAGE_SIZE: int = None
    MAX_MEDIA_ITEMS_PER_MESSAGE: int = None
    PIN_VIDEOS: bool = None
    DEFAULT_IMAGE_PATH: str = None
    SEND_MEDIA_TIMEOUT: int = None
    UPDATES_AS_REPLIES: bool = None

    # Logging
    LOG_PATH: str = None
    MAX_BYTES: int = None
    BACKUP_COUNT: int = None

    # Database
    DB_HOST: str = None
    DB_PORT: int = None
    DB_NAME: str = None
    DB_FEEDS_NAME: str = None

    # RSS
    RSS_FEEDS: dict[str, dict[str, Any]] = None

    @classmethod
    def init(cls, default_settings: Path | None = None, custom_settings: list[Path] | None = None):
        cls._prepare_settings(default_settings, custom_settings)

        cls.TOKEN = cls._load_str("telegram", "token")
        cls.ALLOWED_USERNAMES = cls._load_str_list("telegram", "allowed_usernames", default=[])
        cls.PERSISTENCE_FILE = cls._load_str("telegram", "persistence_file", default="persistence")

        # telegram updates
        cls.LOOKUP_INTERVAL = cls._load_int("telegram", "updates", "lookup_interval", default=3600)
        cls.LOOKUP_INTERVAL_RANDOMNESS = cls._load_int(
            "telegram", "updates", "lookup_interval_randomness", default=0
        )
        cls.LOOKUP_INITIAL_DELAY = cls._load_int(
            "telegram", "updates", "lookup_initial_delay", default=30
        )
        cls.LOOKUP_FEED_DELAY = cls._load_int(
            "telegram", "updates", "lookup_feed_delay", default=10
        )
        cls.LOOKUP_FEED_DELAY_RANDOMNESS = cls._load_int(
            "telegram", "updates", "lookup_feed_delay_randomness", default=0
        )
        cls.QUIET_HOURS = cls._load_int_list("telegram", "updates", "quiet_hours", default=[])
        cls.SHUFFLE_UPDATES = cls._load_bool(
            "telegram", "updates", "shuffle_updates", default=False
        )

        # telegram messages
        cls.MAX_MESSAGE_SIZE = cls._load_int(
            "telegram", "messages", "max_message_size", default=1024
        )
        cls.MAX_MEDIA_ITEMS_PER_MESSAGE = cls._load_int(
            "telegram", "messages", "max_media_items_per_message", default=10
        )
        cls.PIN_VIDEOS = cls._load_bool("telegram", "messages", "pin_videos", default=True)
        cls.DEFAULT_IMAGE_PATH = cls._load_str(
            "telegram", "messages", "default_image_path", default=None
        )
        cls.SEND_MEDIA_TIMEOUT = cls._load_int(
            "telegram", "messages", "send_media_timeout", default=180
        )
        cls.UPDATES_AS_REPLIES = cls._load_bool(
            "telegram", "messages", "updates_as_replies", default=True
        )

        # logging
        cls.LOG_PATH = cls._load_str("logging", "log_path", default="bot.log")
        cls.MAX_BYTES = cls._load_int("logging", "max_bytes", default=1000000)
        cls.BACKUP_COUNT = cls._load_int("logging", "backup_count", default=10)

        # database
        cls.DB_HOST = cls._load_str("database", "host", default="localhost")
        cls.DB_PORT = cls._load_int("database", "port", default=27017)
        cls.DB_NAME = cls._load_str("database", "name", default="rss_reader")
        cls.DB_FEEDS_NAME = cls._load_str("database", "feeds_name", default="feed_data")

        # rss
        if feeds_filename := cls._load_str("rss", "feeds_yaml_filename", default="feed_links.yml"):
            with open(feeds_filename, "r") as feeds_path:
                feeds = safe_load(feeds_path) or {}
                cls.RSS_FEEDS = {name: data for name, data in feeds.items() if "url" in data}

        cls._validate()

    @classmethod
    def _prepare_settings(cls, default_settings: Path | None, custom_settings: list[Path] | None):
        load_dotenv()
        default_settings = default_settings or (
            Path(default_settings_env)
            if (default_settings_env := getenv(cls._DEFAULT_SETTINGS_PATH_VARIABLE_NAME))
            else Path("settings.yml")
        )
        custom_settings = custom_settings or (
            [Path(p) for p in custom_settings_env.split(",")]
            if (custom_settings_env := getenv(cls._CUSTOM_SETTINGS_PATH_VARIABLE_NAME))
            else []
        )
        cls._SETTINGS = merge(
            cls._load_settings(default_settings),
            *[cls._load_settings(custom) for custom in custom_settings],
        )

    @classmethod
    def _load_settings(cls, settings_path: Path) -> dict[str, Any]:
        if not settings_path.exists():
            return {}
        with open(settings_path) as settings_yaml:
            return safe_load(settings_yaml) or {}

    @classmethod
    def _load_str(cls, *keys: str, default: str | None = None) -> str | None:
        if (val := cls._load(*keys)) is None:
            return default
        return str(val)

    @classmethod
    def _load_int(cls, *keys: str, default: int | None = None) -> int | None:
        if (val := cls._load(*keys)) is None:
            return default
        return int(val)

    @classmethod
    def _load_bool(cls, *keys: str, default: bool | None = None) -> bool | None:
        if (val := cls._load(*keys)) is None:
            return default
        if isinstance(val, bool):
            return val
        return str(val).lower() in ("1", "true", "yes")

    @classmethod
    def _load_str_list(cls, *keys: str, default: list[str] | None = None) -> list[str] | None:
        if (val := cls._load(*keys)) is None:
            return default
        if isinstance(val, list):
            return [str(x) for x in val]
        return [item.strip() for item in str(val).split(",") if item.strip()]

    @classmethod
    def _load_int_list(cls, *keys: str, default: list[int] | None = None) -> list[int] | None:
        if (val := cls._load(*keys)) is None:
            return default
        if isinstance(val, list):
            return [int(x) for x in val]
        return [int(item.strip()) for item in str(val).split(",") if item.strip()]

    @classmethod
    def _load(cls, *keys: str) -> Any:
        if (env_val := getenv("_".join(keys).upper())) is not None:
            return env_val
        return reduce(
            lambda table, key: table.get(key) if isinstance(table, dict) else None,
            keys,
            cls._SETTINGS,
        )

    @classmethod
    def _validate(cls) -> None:
        missing = [
            field
            for field in cls.__annotations__
            if not field.startswith("_")
            and field not in cls._OPTIONAL_FIELDS
            and getattr(cls, field) is None
        ]
        if missing:
            raise ValueError(f"Required configuration settings are missing: {', '.join(missing)}")
