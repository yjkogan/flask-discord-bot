from enum import IntEnum, verify, UNIQUE, NAMED_FLAGS
from flask import (current_app)

from .request import discord_request

@verify(UNIQUE, NAMED_FLAGS)
class ApplicationCommandType(IntEnum):
    CHAT_INPUT = 1
    USER = 2
    MESSAGE = 3

@verify(UNIQUE, NAMED_FLAGS)
class ApplicationCommandOptionType(IntEnum):
    SUB_COMMAND = 1
    SUB_COMMAND_GROUP = 2
    STRING = 3
    INTEGER = 4
    BOOLEAN = 5
    USER = 6
    CHANNEL = 7
    ROLE = 8
    MENTIONABLE = 9
    NUMBER = 10
    ATTACHMENT = 11


def install_global_commands(appId, commands):
  # API endpoint to overwrite global commands
  endpoint = f'applications/{appId}/commands'
  current_app.logger.info(f'endpoint: {endpoint}')

  try:
    #This is calling the bulk overwrite endpoint: https://discord.com/developers/docs/interactions/application-commands#bulk-overwrite-global-application-commands
    discord_request(endpoint, { 'method': 'PUT', 'data': commands })
  except Exception as e:
    current_app.logger.error(e)
