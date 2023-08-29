from flask import (abort, current_app)

from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

SIGNATURE_HEADER = "X-Signature-Ed25519"
SIGNATURE_TIMESTAMP = "X-Signature-Timestamp"

class DiscordAuth:

  def verify_discord_request(request):
      verify_key = VerifyKey(bytes.fromhex(current_app.config['PUBLIC_KEY']))
      signature = request.headers[SIGNATURE_HEADER]
      timestamp = request.headers[SIGNATURE_TIMESTAMP]
      body = request.data.decode("utf-8")

      try:
          verify_key.verify(f'{timestamp}{body}'.encode(), bytes.fromhex(signature))
      except BadSignatureError:
          abort(401, 'invalid request signature')
