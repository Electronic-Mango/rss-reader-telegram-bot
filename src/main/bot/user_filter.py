from functools import lru_cache

from telegram.ext.filters import User

from settings import Settings


@lru_cache(maxsize=1)
def user_filter() -> User:
    return User(username=Settings.ALLOWED_USERNAMES, allow_empty=True)
