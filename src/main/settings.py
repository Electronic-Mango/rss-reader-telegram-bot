"""
Module holding all configuration parameters for the project.

Parameters are loaded from YAML files. Default values are loaded from "settings.yml".
Additional parameters, overwriting the default ones can be loaded from a file defined in
"CUSTOM_SETTINGS_PATH" environment variable.
This overwriting file doesn't have to contain everything, only values to overwrite.
"""

from functools import reduce
from os import getenv
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from loguru import logger
from mergedeep import merge
from yaml import safe_load


class Settings:
    # Names of environment variables
    _DEFAULT_SETTINGS_PATH_VARIABLE_NAME = "DEFAULT_SETTINGS_PATH"
    _CUSTOM_SETTINGS_PATH_VARIABLE_NAME = "CUSTOM_SETTINGS_PATH"

    # Internal settings storage and optional fields
    _SETTINGS = None

    # Telegram
    TOKEN: str | None = None  # Bot will fail on startup for None
    ALLOWED_USERNAMES: list[str] = None
    PERSISTENCE_FILE: str | None = None

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
    DEFAULT_IMAGE_PATH: str | None = None
    SEND_MEDIA_TIMEOUT: int = None
    UPDATES_AS_REPLIES: bool = None

    # Logging
    LOG_PATH: str | None = None
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
    def init(
        cls,
        default_settings: Path | None = None,
        custom_settings: list[Path] | None = None,
    ) -> None:
        cls._prepare_settings(default_settings, custom_settings)

        cls.TOKEN = cls._load_str("telegram", "token")
        cls.ALLOWED_USERNAMES = cls._load_str_list(
            "telegram", "allowed_usernames", default=[]
        )
        cls.PERSISTENCE_FILE = cls._load_str("telegram", "persistence_file")

        cls.LOOKUP_INTERVAL = cls._load_int(
            "telegram", "updates", "lookup_interval", default=3600
        )
        cls.LOOKUP_INTERVAL_RANDOMNESS = cls._load_int(
            "telegram", "updates", "lookup_interval_randomness", default=0
        )
        cls.LOOKUP_INITIAL_DELAY = cls._load_int(
            "telegram", "updates", "lookup_initial_delay", default=0
        )
        cls.LOOKUP_FEED_DELAY = cls._load_int(
            "telegram", "updates", "lookup_feed_delay", default=0
        )
        cls.LOOKUP_FEED_DELAY_RANDOMNESS = cls._load_int(
            "telegram", "updates", "lookup_feed_delay_randomness", default=0
        )
        cls.QUIET_HOURS = cls._load_int_list(
            "telegram", "updates", "quiet_hours", default=[]
        )
        cls.SHUFFLE_UPDATES = cls._load_bool(
            "telegram", "updates", "shuffle_updates", default=False
        )

        cls.MAX_MESSAGE_SIZE = cls._load_int(
            "telegram", "messages", "max_message_size", default=1024
        )
        cls.MAX_MEDIA_ITEMS_PER_MESSAGE = cls._load_int(
            "telegram", "messages", "max_media_items_per_message", default=10
        )
        cls.PIN_VIDEOS = cls._load_bool(
            "telegram", "messages", "pin_videos", default=True
        )
        cls.DEFAULT_IMAGE_PATH = cls._load_str(
            "telegram", "messages", "default_image_path"
        )
        cls.SEND_MEDIA_TIMEOUT = cls._load_int(
            "telegram", "messages", "send_media_timeout", default=180
        )
        cls.UPDATES_AS_REPLIES = cls._load_bool(
            "telegram", "messages", "updates_as_replies", default=True
        )

        cls.LOG_PATH = cls._load_str("logging", "log_path")
        cls.MAX_BYTES = cls._load_int("logging", "max_bytes", default=0)
        cls.BACKUP_COUNT = cls._load_int("logging", "backup_count", default=0)

        cls.DB_HOST = cls._load_str("database", "host", default="localhost")
        cls.DB_PORT = cls._load_int("database", "port", default=27017)
        cls.DB_NAME = cls._load_str("database", "name", default="rss_reader")
        cls.DB_FEEDS_NAME = cls._load_str("database", "feeds_name", default="feed_data")

        feeds_filename = cls._load_str(
            "rss", "feeds_yaml_filename", default="feed_links.yml"
        )
        if feeds_filename:
            with Path(feeds_filename).open() as feeds_path:
                cls.RSS_FEEDS = {
                    name: data
                    for name, data in (safe_load(feeds_path) or {}).items()
                    if "url" in data
                }

    @classmethod
    def _prepare_settings(
        cls, default_settings: Path | None, custom_settings: list[Path] | None
    ) -> None:
        load_dotenv()
        default_settings = default_settings or (
            Path(default_env)
            if (default_env := getenv(cls._DEFAULT_SETTINGS_PATH_VARIABLE_NAME))
            else Path("settings.yml")
        )
        logger.info(f"Loading default settings from: []{default_settings}")
        custom_settings = custom_settings or (
            [Path(p) for p in custom_env.split(",")]
            if (custom_env := getenv(cls._CUSTOM_SETTINGS_PATH_VARIABLE_NAME))
            else []
        )
        logger.info(f"Loading custom settings from: [{custom_settings}]")
        cls._SETTINGS = merge(
            cls._load_settings(default_settings),
            *[cls._load_settings(custom) for custom in custom_settings],
        )

    @classmethod
    def _load_settings(cls, settings_path: Path) -> dict[str, Any]:
        if not settings_path.exists():
            logger.warning(f"Settings file not found: [{settings_path}]")
            return {}
        with Path(settings_path).open() as settings_yaml:
            return safe_load(settings_yaml) or {}

    @classmethod
    def _load_str(cls, *keys: str, default: str | None = None) -> str | None:
        return str(val) if (val := cls._load(*keys)) is not None else default

    @classmethod
    def _load_int(cls, *keys: str, default: int | None = None) -> int | None:
        return int(val) if (val := cls._load(*keys)) is not None else default

    @classmethod
    def _load_bool(cls, *keys: str, default: bool | None = None) -> bool | None:
        if (val := cls._load(*keys)) is None:
            return default
        if isinstance(val, bool):
            return val
        return str(val).lower() in ("1", "true", "yes")

    @classmethod
    def _load_str_list(
        cls, *keys: str, default: list[str] | None = None
    ) -> list[str] | None:
        if (val := cls._load(*keys)) is None:
            return default
        if isinstance(val, list):
            return [str(x) for x in val]
        return [item.strip() for item in str(val).split(",") if item.strip()]

    @classmethod
    def _load_int_list(
        cls, *keys: str, default: list[int] | None = None
    ) -> list[int] | None:
        if (val := cls._load(*keys)) is None:
            return default
        if isinstance(val, list):
            return [int(x) for x in val]
        return [int(item.strip()) for item in str(val).split(",") if item.strip()]

    @classmethod
    def _load(cls, *keys: str) -> Any:
        if (env_val := getenv("_".join(keys).upper())) is not None:
            key_name = ".".join(keys)
            logger.debug(f"Loading value for [{key_name}] from environment")
            return env_val or None
        return reduce(
            lambda table, key: table.get(key) if isinstance(table, dict) else None,
            keys,
            cls._SETTINGS,
        )
