from enum import IntEnum, verify, UNIQUE, NAMED_FLAGS

@verify(UNIQUE, NAMED_FLAGS)
class InteractionType(IntEnum):
    PING = 1
    APPLICATION_COMMAND = 2
    MESSAGE_COMPONENT = 3


@verify(UNIQUE, NAMED_FLAGS)
class InteractionCallbackType(IntEnum):
    PONG = 1
    CHANNEL_MESSAGE_WITH_SOURCE = 4


@verify(UNIQUE, NAMED_FLAGS)
class MessageComponentType(IntEnum):
    ACTION_ROW = 1
    BUTTON = 2
