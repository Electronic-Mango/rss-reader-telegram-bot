from telegram.ext.filters import User

from settings import ALLOWED_USERNAMES

USER_FILTER = User(username=ALLOWED_USERNAMES, allow_empty=True)
