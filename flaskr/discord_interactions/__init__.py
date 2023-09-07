from typing import Any
from flask import Blueprint, request, current_app, jsonify, Response

from ..discord.auth import DiscordAuth
from ..discord import InteractionType, InteractionCallbackType
from .handler import DiscordInteractionHandler

bp = Blueprint("interactions", __name__, url_prefix="/interactions")


@bp.route("/", methods=("GET", "POST"))
def discord_interactions() -> Response:
    content: Any = request.json
    interaction_type: int = int(content["type"])
    current_app.logger.info("Starting interaction")

    if interaction_type == InteractionType.PING:
        return jsonify({"type": InteractionCallbackType.PONG})
    elif interaction_type == InteractionType.APPLICATION_COMMAND:
        return DiscordInteractionHandler.handle_application_command(json_data=content)
    elif interaction_type == InteractionType.MESSAGE_COMPONENT:
        return DiscordInteractionHandler.handle_message_interaction(json_data=content)
    else:
        current_app.logger.warn(f"Unknown interaction type: {interaction_type}")
        return jsonify({"type": InteractionCallbackType.PONG})


@bp.before_request
def verify_bot_key():
    DiscordAuth.verify_discord_request(request=request)
