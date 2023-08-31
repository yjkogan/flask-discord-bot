import re

from flask import current_app, jsonify

from flaskr.commands import BotCommandNames
from ..discord import InteractionCallbackType, MessageComponentType
from ..models.user import User
from ..models.artist import Artist, ArtistExistsException
from ..ratings import Comparison

from flaskr.db import get_db

MAX_COMPARISONS = 100000


class DiscordInteractionHandler:
    def handle_application_command(discord_user, interaction_data):
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
        artist_name = interaction_data["options"][0]["value"]
        user = User.get_or_create_for_discord_user(discord_user)
        artists_for_user = user.get_artists()

        artist = Artist.get_or_create_artist(user=user, artist_name=artist_name)
        rating_calculator = artist.begin_rating(artists_for_user=artists_for_user)
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
            rating_calculator.item_being_rated.name,
            next_comparison.name,
            next_comparison.index,
        )

    def handle_message_interaction(discord_user, interaction_data):
        # TODO: extract into "parse" function
        matches = re.search(
            "n_([a-zA-Z0-9 -]*)_c_([a-zA-Z0-9 -]*)_cidx_([0-9]*)_pc_(no|yes)",
            interaction_data["custom_id"],
        )
        match_groups = matches.groups()
        artist_name = match_groups[0]
        compared_to_artist = match_groups[1]
        compared_artist_index = int(match_groups[2])
        is_preferred_to_new_artist = match_groups[3] == "yes"
        user = User.get_by_username(discord_user["username"])
        artist = Artist.get_by_name_for_user(user=user, artist_name=artist_name)
        rating_calculator = artist.continue_rating(
            Comparison(
                name=compared_to_artist,
                index=compared_artist_index,
                is_preferred=is_preferred_to_new_artist,
            )
        )
        if rating_calculator is None:
            return jsonify(
                {
                    "type": InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
                    "data": {
                        "content": f"Cannot find an ongoing attempt to rate {artist_name} form {discord_user}"
                    },
                }
            )

        next_comparison = rating_calculator.get_next_comparison()
        is_enough_comparisons = len(rating_calculator.comparisons) >= MAX_COMPARISONS
        if next_comparison is None or is_enough_comparisons:
            new_rateables = rating_calculator.get_overall_ratings()
            Artist.update_all_with_new_ratings(user=user, new_rateables=new_rateables)
            rating_calculator.complete()
            ratings_message = get_ratings_message(new_rateables)
            return jsonify(
                {
                    "type": InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
                    "data": {
                        "content": f"Got it! Your new ratings are\n {ratings_message}"
                    },
                }
            )

        return send_comparison(
            rating_calculator.item_being_rated.name,
            next_comparison.name,
            next_comparison.index,
        )


def get_ratings_message(rateables):
    lines = []
    for r in rateables:
        lines.append(f"{r.name}: {r.rating}")
    lines.reverse()
    return "\n".join(lines)


# Could maybe become a function on a Rating
def send_comparison(artist_name, artist_to_compare, artist_to_compare_idx):
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
                                "label": f"{artist_name}",
                                "style": 1,
                                "custom_id": f"n_{artist_name}_c_{artist_to_compare}_cidx_{artist_to_compare_idx}_pc_no",
                            },
                            {
                                "type": MessageComponentType.BUTTON,
                                "label": f"{artist_to_compare}",
                                "style": 1,
                                "custom_id": f"n_{artist_name}_c_{artist_to_compare}_cidx_{artist_to_compare_idx}_pc_yes",
                            },
                        ],
                    }
                ],
            },
        }
    )
