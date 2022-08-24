"""
States used by "list" command conversation handler.
"""

from enum import Enum, auto


class ConversationState(Enum):
    LIST_NAMES = auto()
    LIST_TYPES = auto()
