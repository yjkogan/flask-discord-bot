from flask import Blueprint, request, current_app, jsonify

from ..interaction_cache import InteractionCache
from ..discord.auth import DiscordAuth
from ..discord import (InteractionType, InteractionCallbackType)
from .handler import DiscordInteractionHandler

bp = Blueprint("interactions", __name__, url_prefix="/interactions")

@bp.route("/", methods=("GET", "POST"))
def interactions():
    content = request.json
    interaction_type = int(content["type"])
    current_app.logger.info("Starting interaction")

    if interaction_type == InteractionType.PING:
        return jsonify({"type": InteractionCallbackType.PONG})
    elif interaction_type == InteractionType.APPLICATION_COMMAND:
        return DiscordInteractionHandler.handle_application_command(
            discord_user=content["member"]["user"], interaction_data=content["data"]
        )
    elif interaction_type == InteractionType.MESSAGE_COMPONENT:
        return DiscordInteractionHandler.handle_message_interaction(
            discord_user=content["member"]["user"],
            interaction_data=content["data"]
        )
    else:
        current_app.logger.warn(f"Unknown interaction type: {interaction_type}")
        return jsonify({"type": InteractionCallbackType.PONG})
    
@bp.before_app_request
def verify_bot_key():
    DiscordAuth.verify_discord_request(request=request)
