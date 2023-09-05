import httpx
import json

from flask import current_app


def discord_request(endpoint, input_options=None):
    current_app.logger.info("In discord request")
    options = input_options or {}
    url = str(f"https://discord.com/api/v10/{endpoint}")
    request = {
        "headers": {
            "Authorization": f"Bot {current_app.config['DISCORD_TOKEN']}",
            "Content-Type": "application/json; charset=UTF-8",
            "User-Agent": "DiscordBot (https://github.com/discord/discord-example-app, 1.0.0)",
        }
        | options.get("headers", {}),
    } | options
    current_app.logger.info(endpoint)
    current_app.logger.info(request)
    response = None
    try:
        response = httpx.request(
            url=url,
            method=request["method"],
            headers=request["headers"],
            json=request["data"],
        )
    except Exception as e:
        current_app.logger.error(e)
    current_app.logger.info("Request is done")

    current_app.logger.info(response)

    if not is_response_okay(response):
        data = response.json()
        current_app.logger.error(response.status_code)
        raise RuntimeError(json.dumps(data))

    return response

def is_response_okay(response):
    return response.status_code == httpx.codes.OK or response.status_code == httpx.codes.NO_CONTENT
