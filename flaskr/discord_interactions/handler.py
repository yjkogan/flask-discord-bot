import re
from collections import namedtuple

from flask import current_app, jsonify

from flaskr.commands import BotCommandNames
from ..discord import InteractionCallbackType, MessageComponentType
from ..discord.request import discord_request
from ..models.user import User
from ..models.artist import Artist
from ..ratings import Comparison, RatingCalculator

Interaction = namedtuple("Interaction", ["id", "token"])


class DiscordInteractionHandler:
    def handle_application_command(json_data):
        discord_user = json_data["member"]["user"]
        interaction_data = json_data["data"]
        command_name = interaction_data["name"]
        if command_name == BotCommandNames.echo.name:
            return DiscordInteractionHandler._handle_echo(interaction_data)
        elif command_name == BotCommandNames.rate_artist.name:
            return DiscordInteractionHandler._handle_rate_artist(
                discord_user, interaction_data
            )
        else:
            current_app.logger.warn(f"Unknown command name: {command_name}")
            return jsonify({"type": InteractionCallbackType.PONG})

    def _handle_echo(interaction_data):
        to_echo = interaction_data["options"][0]["value"]
        return jsonify(
            {
                "type": InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
                "data": {"content": to_echo},
            }
        )

    def _handle_rate_artist(discord_user, interaction_data):
        artist_name = interaction_data["options"][0]["value"].strip()
        user = User.get_or_create_for_discord_user(discord_user)

        artists_for_user = user.get_artists()
        artist = Artist.get_or_create_artist(user=user, artist_name=artist_name)
        other_items = [a for a in artists_for_user if a.id != artist.id]
        rating_calculator = RatingCalculator.begin_rating(
            item_being_rated=artist,
            other_items=other_items,
        )
        next_comparison = rating_calculator.get_next_comparison()
        if next_comparison is None:
            rating_calculator.complete()
            return jsonify(
                {
                    "type": InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
                    "data": {
                        "content": "Thanks for adding your first artist! Rate another artist to create a relative ranking."
                    },
                }
            )

        return send_comparison(
            rating_calculator.item_being_rated,
            next_comparison,
            next_comparison.index,
        )

    def handle_message_interaction(json_data):
        discord_user = json_data["member"]["user"]
        interaction_data = json_data["data"]
        (artist_id, comparison) = DiscordInteractionHandler._parse_custom_id(
            interaction_data["custom_id"]
        )

        user = User.get_by_username(discord_user["username"])
        artist = Artist.get_by_id_for_user(user=user, artist_id=artist_id)
        rating_calculator = RatingCalculator.continue_rating(
            item_being_rated=artist,
            comparison=comparison,
        )
        if rating_calculator is None:
            return jsonify(
                {
                    "type": InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
                    "data": {
                        "content": f"Cannot find an ongoing attempt to rate {artist.name} form {discord_user}"
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

        new_rateables = rating_calculator.get_overall_ratings()
        Artist.update_all_with_new_ratings(user=user, new_rateables=new_rateables)
        rating_calculator.complete()
        ratings_message = get_ratings_message(new_rateables)
        return jsonify(
            {
                "type": InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
                "data": {
                    "content": f"Got it! Your new ratings are:\n\n{ratings_message}"
                },
            }
        )

    def _parse_custom_id(custom_id):
        matches = re.search(
            "a_([0-9]*)_c_([0-9]*)_cidx_([0-9]*)_pc_(no|yes)",
            custom_id,
        )
        match_groups = matches.groups()
        artist_id = match_groups[0]
        compared_to_artist_id = match_groups[1]
        compared_artist_index = int(match_groups[2])
        is_preferred = match_groups[3] == "yes"
        return (
            artist_id,
            Comparison(
                id=compared_to_artist_id,
                name=None,  # Irrelevant in this case because we don't need to read the ID, but this feels bad / wrong
                index=compared_artist_index,
                is_preferred=is_preferred,
            ),
        )


def get_ratings_message(rateables):
    lines = []
    for r in rateables:
        lines.append(f"{r.name}: {r.rating}")
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
#                                     "custom_id": f"a_{artist.id}_c_{artist_to_compare.id}_cidx_{artist_to_compare_idx}_pc_no",
#                                 },
#                                 {
#                                     "type": MessageComponentType.BUTTON,
#                                     "label": f"{artist_to_compare.name}",
#                                     "style": 1,
#                                     "custom_id": f"a_{artist.id}_c_{artist_to_compare.id}_cidx_{artist_to_compare_idx}_pc_yes",
#                                 },
#                             ],
#                         }
#                     ],
#                 },
#             },
#         },
#     )


# Could maybe become a function on a Rating
def send_comparison(artist, artist_to_compare, artist_to_compare_idx):
    return jsonify(
        {
            "type": InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
            "data": {
                "content": f"Which of these artists do you prefer?",
                "components": [
                    {
                        "type": MessageComponentType.ACTION_ROW,
                        "components": [
                            {
                                "type": MessageComponentType.BUTTON,
                                "label": f"{artist.name}",
                                "style": 1,
                                "custom_id": f"a_{artist.id}_c_{artist_to_compare.id}_cidx_{artist_to_compare_idx}_pc_no",
                            },
                            {
                                "type": MessageComponentType.BUTTON,
                                "label": f"{artist_to_compare.name}",
                                "style": 1,
                                "custom_id": f"a_{artist.id}_c_{artist_to_compare.id}_cidx_{artist_to_compare_idx}_pc_yes",
                            },
                        ],
                    }
                ],
            },
        }
    )
