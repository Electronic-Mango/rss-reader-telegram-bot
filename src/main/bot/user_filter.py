from telegram.ext.filters import Chat

from settings import ALLOWED_USERNAMES

USER_FILTER = Chat(username=ALLOWED_USERNAMES, allow_empty=True)
