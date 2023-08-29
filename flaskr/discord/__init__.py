import httpx
import json

from flask import (abort, current_app)

from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

def verify_discord_request(request):
    verify_key = VerifyKey(bytes.fromhex(current_app.config['PUBLIC_KEY']))
    signature = request.headers["X-Signature-Ed25519"]
    timestamp = request.headers["X-Signature-Timestamp"]
    body = request.data.decode("utf-8")

    try:
        verify_key.verify(f'{timestamp}{body}'.encode(), bytes.fromhex(signature))
    except BadSignatureError:
        abort(401, 'invalid request signature')

def discord_request(endpoint, input_options = None):
  current_app.logger.info('In discord request')
  options = input_options or {}
  url = str(f'https://discord.com/api/v10/{endpoint}')
  request = {
      'headers': {
          'Authorization': f"Bot {current_app.config['DISCORD_TOKEN']}",
          'Content-Type': 'application/json; charset=UTF-8',
          'User-Agent': 'DiscordBot (https://github.com/discord/discord-example-app, 1.0.0)',
      } | options.get('headers', {}),
      
  } | options
  current_app.logger.info(request)
  response = None
  try:
      response = httpx.request(url = url, method = request['method'], headers = request['headers'], json = request['data'])
  except Exception as e:
      current_app.logger.error(e)
  current_app.logger.info('Request is done')

  current_app.logger.info(response)

  if (response.status_code != httpx.codes.OK):
    data = response.json()
    current_app.logger.error(response.status_code)
    raise RuntimeError(json.dumps(data))

  return response

def install_global_commands(appId, commands):
  # API endpoint to overwrite global commands
  endpoint = f'applications/{appId}/commands'
  current_app.logger.info(f'endpoint: {endpoint}')

  try:
    #This is calling the bulk overwrite endpoint: https://discord.com/developers/docs/interactions/application-commands#bulk-overwrite-global-application-commands
    discord_request(endpoint, { 'method': 'PUT', 'data': commands })
  except Exception as e:
    current_app.logger.error(e)
