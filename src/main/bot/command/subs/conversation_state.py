"""
States used by "subscriptions" command conversation handler.
"""

from enum import Enum, auto


class ConversationState(Enum):
    LIST_NAMES = auto()
    LIST_TYPES = auto()
    SHOW_DETAILS = auto()
    CONFIRM_REMOVAL = auto()
