import re
from collections import namedtuple
from typing import cast

from flask import current_app, jsonify

from flaskr.commands import BotCommandNames
from ..discord import InteractionCallbackType, MessageComponentType
from ..discord.request import discord_request
from ..models.user import User
from ..models.rating import Rating
from ..ratings import RatingCalculator, CompletedComparison

Interaction = namedtuple("Interaction", ["id", "token"])


class DiscordInteractionHandler:

    @staticmethod
    def handle_application_command(json_data: dict):
        discord_user: dict = json_data["member"]["user"]
        interaction_data: dict = json_data["data"]
        command_name: str = interaction_data["name"]
        if command_name == BotCommandNames.echo.name:
            return DiscordInteractionHandler._handle_echo(interaction_data)
        elif command_name == BotCommandNames.rate_artist.name:
            return DiscordInteractionHandler._handle_add_rating(
                discord_user, interaction_data
            )
        elif command_name == BotCommandNames.rate.name:
            raise NotImplementedError()
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
    def _handle_add_rating(discord_user: dict, interaction_data: dict):
        # rating_type: str = interaction_data["options"][0]["value"].strip()
        # rating_name: str = interaction_data["options"][1]["value"].strip()
        rating_type = 'artist'
        rating_name: str = interaction_data["options"][0]["value"].strip()
        user = User.get_or_create_for_discord_user(discord_user)

        ratings_for_user = user.get_ratings(rating_type=rating_type)
        new_rating = Rating.get_or_create_rating(user=user, rating_name=rating_name, rating_type=rating_type)
        other_items = [r for r in ratings_for_user if r.id != new_rating.id]
        rating_calculator = RatingCalculator.begin_rating(
            item_being_rated=new_rating,
            other_items=other_items,
        )
        next_comparison = rating_calculator.get_next_comparison()
        if next_comparison is None:
            rating_calculator.complete()
            return jsonify(
                {
                    "type": InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
                    "data": {
                        "content": f"Thanks for adding your first {rating_type}! Rate another {rating_type} to create a relative ranking."
                    },
                }
            )

        return send_comparison(
            rating_calculator.item_being_rated,
            next_comparison,
            next_comparison.index,
        )

    @staticmethod
    def handle_message_interaction(json_data: dict):
        discord_user: dict = json_data["member"]["user"]
        interaction_data: dict = json_data["data"]
        (rating_id, comparison) = DiscordInteractionHandler._parse_custom_id(
            interaction_data["custom_id"]
        )

        user = User.get_by_username(discord_user["username"])
        rating = Rating.get_by_id_for_user(user=user, rating_id=rating_id)
        if rating is None:
            # TODO: Refactor this out into a function
            return jsonify(
                {
                    "type": InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
                    "data": {
                        "content": f"Cannot find rating with ID {rating_id} for user {discord_user}"
                    },
                }
            )
        rating_calculator = RatingCalculator.continue_rating(
            item_being_rated=rating,
            comparison=comparison,
        )
        if rating_calculator is None:
            return jsonify(
                {
                    "type": InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
                    "data": {
                        "content": f"Cannot find an ongoing attempt to rate {rating.name} form {discord_user}"
                    },
                }
            )

        next_comparison = rating_calculator.get_next_comparison()
        if next_comparison:
            return send_comparison(
                rating_calculator.item_being_rated,
                next_comparison,
                next_comparison.index,
            )

        new_ratings = rating_calculator.get_overall_ratings()
        Rating.update_all_with_new_ratings(user=user, new_ratings=new_ratings)
        rating_calculator.complete()
        ratings_message = get_ratings_message(new_ratings)
        return jsonify(
            {
                "type": InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
                "data": {
                    "content": f"Got it! Your new ratings for {rating.type} are:\n\n{ratings_message}"
                },
            }
        )

    @staticmethod
    def _parse_custom_id(custom_id: str) -> tuple[int, CompletedComparison]:
        matches = re.search(
            "r_([0-9]*)_c_([0-9]*)_cidx_([0-9]*)_pc_(no|yes)",
            custom_id,
        )
        if matches is None:
            raise Exception(f"Could not parse custom ID: {custom_id}")

        match_groups = matches.groups()
        rating_id = int(match_groups[0])
        compared_to_rating_id = int(match_groups[1])
        compared_rating_index = int(match_groups[2])
        is_preferred = match_groups[3] == "yes"
        return (
            rating_id,
            CompletedComparison(
                id=compared_to_rating_id,
                index=compared_rating_index,
                is_preferred=is_preferred,
            ),
        )


def get_ratings_message(ratings: list[Rating]):
    lines = []
    for r in ratings:
        lines.append(f"{r.name}: {r.value}")
    lines.reverse()
    return "\n".join(lines)


# def send_comparison(
#     artist, artist_to_compare, artist_to_compare_idx, interaction
# ):
#     discord_request(
#         f"/interactions/{interaction.id}/{interaction.token}/callback",
#         {
#             "method": "POST",
#             "data": {
#                 "type": InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
#                 "data": {
#                     "content": f"Which of these artists do you prefer?",
#                     "components": [
#                         {
#                             "type": MessageComponentType.ACTION_ROW,
#                             "components": [
#                                 {
#                                     "type": MessageComponentType.BUTTON,
#                                     "label": f"{artist.name}",
#                                     "style": 1,
#                                     "custom_id": f"r_{artist.id}_c_{artist_to_compare.id}_cidx_{artist_to_compare_idx}_pc_no",
#                                 },
#                                 {
#                                     "type": MessageComponentType.BUTTON,
#                                     "label": f"{artist_to_compare.name}",
#                                     "style": 1,
#                                     "custom_id": f"r_{artist.id}_c_{artist_to_compare.id}_cidx_{artist_to_compare_idx}_pc_yes",
#                                 },
#                             ],
#                         }
#                     ],
#                 },
#             },
#         },
#     )


# Could maybe become a function on a Rating
def send_comparison(rating, rating_to_compare, rating_to_compare_idx):
    return jsonify(
        {
            "type": InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
            "data": {
                "content": f"Which of these {rating.type}s do you prefer?",
                "components": [
                    {
                        "type": MessageComponentType.ACTION_ROW,
                        "components": [
                            {
                                "type": MessageComponentType.BUTTON,
                                "label": f"{rating.name}",
                                "style": 1,
                                "custom_id": f"r_{rating.id}_c_{rating_to_compare.id}_cidx_{rating_to_compare_idx}_pc_no",
                            },
                            {
                                "type": MessageComponentType.BUTTON,
                                "label": f"{rating_to_compare.name}",
                                "style": 1,
                                "custom_id": f"r_{rating.id}_c_{rating_to_compare.id}_cidx_{rating_to_compare_idx}_pc_yes",
                            },
                        ],
                    }
                ],
            },
        }
    )
