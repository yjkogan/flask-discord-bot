from flask import (current_app)

from .request import discord_request

def install_global_commands(appId, commands):
  # API endpoint to overwrite global commands
  endpoint = f'applications/{appId}/commands'
  current_app.logger.info(f'endpoint: {endpoint}')

  try:
    #This is calling the bulk overwrite endpoint: https://discord.com/developers/docs/interactions/application-commands#bulk-overwrite-global-application-commands
    discord_request(endpoint, { 'method': 'PUT', 'data': commands })
  except Exception as e:
    current_app.logger.error(e)
