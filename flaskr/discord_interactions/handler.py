from flask import current_app, jsonify, Response

from flaskr.commands import BotCommandNames, RateSubCommandNames
from ..discord import InteractionCallbackType
from ..ratings.rating_handler import RatingHandler

class DiscordInteractionHandler:

    @staticmethod
    def handle_application_command(json_data: dict) -> Response:
        discord_user: dict = json_data["member"]["user"]
        interaction_data: dict = json_data["data"]
        command_name: str = interaction_data["name"]
        if command_name == BotCommandNames.echo.name:
            return DiscordInteractionHandler._handle_echo(interaction_data)
        elif command_name == BotCommandNames.rate.name:
            sub_command = interaction_data["options"][0]
            sub_command_name = sub_command["name"]

            if sub_command_name == RateSubCommandNames.list_ratings.name:
                return RatingHandler.handle_list_ratings(discord_user=discord_user, interaction_data=sub_command)
            elif sub_command_name == RateSubCommandNames.list_types.name:
                return RatingHandler.handle_list_types(discord_user=discord_user)
            elif sub_command_name == RateSubCommandNames.remove_rating.name:
                return RatingHandler.handle_remove_rating(discord_user=discord_user, interaction_data=sub_command)
            elif sub_command_name == RateSubCommandNames.add_rating.name:
                return RatingHandler.handle_add_rating(
                    discord_user=discord_user,
                    interaction_data=sub_command,
                )
            else:
                current_app.logger.warn(f"Unknown sub command name: {sub_command_name}")
                return jsonify({"type": InteractionCallbackType.PONG})
        else:
            current_app.logger.warn(f"Unknown command name: {command_name}")
            return jsonify({"type": InteractionCallbackType.PONG})

    @staticmethod
    def _handle_echo(interaction_data: dict):
        to_echo: str = interaction_data["options"][0]["value"]
        return jsonify(
            {
                "type": InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
                "data": {"content": to_echo},
            }
        )

    @staticmethod
    def handle_message_interaction(json_data: dict):
        discord_user: dict = json_data["member"]["user"]
        interaction_data: dict = json_data["data"]
        return RatingHandler.handle_responded_to_comparison(discord_user=discord_user, interaction_data=interaction_data)

