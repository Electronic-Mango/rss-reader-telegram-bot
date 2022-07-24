from telegram.ext.filters import Chat

from settings import ALLOWED_USERNAME

USER_FILTER = Chat(username=ALLOWED_USERNAME, allow_empty=True)
