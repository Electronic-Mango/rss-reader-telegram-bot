from telegram.ext.filters import User

from settings_new import Settings

USER_FILTER = User(username=Settings.ALLOWED_USERNAMES, allow_empty=True)
