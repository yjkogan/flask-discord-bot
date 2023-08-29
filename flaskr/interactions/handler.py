import re
import sqlite3

from flask import current_app, jsonify

from ..interaction_cache import InteractionCache
from ..discord import (InteractionCallbackType, MessageComponentType)

from flaskr.db import get_db

MAX_COMPARISONS = 100000

class DiscordInteractionHandler:
    def handle_application_command(discord_user, interaction_data):
        command_name = interaction_data["name"]
        if command_name == "test":
            return jsonify(
                {
                    "type": InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
                    "data": {"content": "hello world"},
                }
            )
        elif command_name == "rate_artist":
            # current_app.logger.info(interaction_data)
            artist_name = interaction_data["options"][0]["value"]
            user = get_or_create_user(discord_user)
            artists_for_user = get_artists_for_user(user)
            db = get_db()
            try:
                db.execute(
                    "INSERT INTO artist (user_id, name) VALUES (?, ?)",
                    (user["id"], artist_name),
                )
                db.commit()
                if not artists_for_user:
                    return jsonify({
                        "type": InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
                        "data": {"content": "Thanks for adding your first artist! Rate another artist to create a relative ranking."},
                    })
                interaction = InteractionCache.store_interaction(
                    user_id=user["id"],
                    artist_name=artist_name,
                    artists_for_user=artists_for_user,
                )
                (artist_to_compare_idx, artist_to_compare_obj) = InteractionCache.get_artist_to_compare(interaction)
                return run_comparison(artist_name=artist_name, artist_to_compare=artist_to_compare_obj['name'], artist_to_compare_idx=artist_to_compare_idx)
            except sqlite3.IntegrityError as e:
                return jsonify(
                    {
                        "type": InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
                        "data": "You've already rated that artist",
                    }
                )
        else:
            return jsonify({"type": InteractionCallbackType.PONG})


    def handle_message_interaction(discord_user, interaction_data, original_message):
        # Get all the data we need in the custom_id so it is more parsable
        matches = re.search(
            "n_([a-zA-Z0-9 -]*)_c_([a-zA-Z0-9 -]*)_cidx_([0-9]*)_pc_(no|yes)",
            interaction_data["custom_id"],
        )
        # current_app.logger.info(f"interaction_data: {interaction_data}")
        # current_app.logger.info(f'interaction_data["custom_id"]: {interaction_data["custom_id"]}')
        # current_app.logger.info(f'matches: {matches}')
        # current_app.logger.info(f"matches: {matches.groups()}")
        match_groups = matches.groups()
        artist_name = match_groups[0]
        compared_to_artist = match_groups[1]
        compared_artist_index = int(match_groups[2])
        is_preferred_to_new_artist = match_groups[3] == "yes"
        user = get_user(discord_user["username"])
        interaction = InteractionCache.get_interaction(
            user_id=user["id"], artist_name=artist_name
        )
        if interaction is None:
            return jsonify(
                {
                    "type": InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
                    "data": {
                        "content": f"Cannot find an ongoing attempt to rate {artist_name} form {discord_user}"
                    },
                }
            )
        # current_app.logger.info(
        #     f"artist_name: {artist_name}, compared_to_artist: {compared_to_artist}, is_preferred_to_new_artist: {is_preferred_to_new_artist}"
        # )
        interaction = InteractionCache.add_comparison(
            interaction=interaction,
            compared_to_artist=compared_to_artist,
            index_of_compared_artist=compared_artist_index,
            is_preferred_to_new_artist=is_preferred_to_new_artist,
        )
        comparisons = interaction["comparisons"]
        # current_app.logger.info(f'comparisons are {comparisons}')
        (artist_to_compare_idx, artist_to_compare_obj) = InteractionCache.get_artist_to_compare(interaction)
        if len(comparisons) >= MAX_COMPARISONS or artist_to_compare_obj is None:
            new_artist_rankings = save_rating(interaction, user["id"])
            rankings_message = get_rankings_message(new_artist_rankings)
            return jsonify(
                {
                    "type": InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
                    "data": {
                        "content": f"Got it!\n{rankings_message}",
                    },
                }
            )

        # current_app.logger.info("Running comparison")
        return run_comparison(artist_name=artist_name, artist_to_compare=artist_to_compare_obj['name'], artist_to_compare_idx=artist_to_compare_idx)



def get_rankings_message(rankings):
    lines = []
    for (rating, name) in rankings:
        lines.append(f'{name}: {rating}')
    lines.reverse()
    return '\n'.join(lines)

def save_rating(interaction, user_id):
    artist_name = interaction['artist_name']
    artist_names = [artist['name'] for artist in interaction["artists_for_user"]]
    # current_app.logger.info(f'Artists for user {interaction["artists_for_user"]}')
    current_ratings = [(a['rating'], a['name']) for a in interaction["artists_for_user"]]
    # current_app.logger.info(f'Current ratings {current_ratings}')

    last_comparison = interaction["comparisons"][-1]
    last_comparison_idx = last_comparison['index_of_compared_artist']
    index_for_artist = last_comparison_idx if last_comparison['is_preferred_to_new_artist'] else last_comparison_idx + 1
    artist_names.insert(index_for_artist, artist_name)
    # current_app.logger.info(f'New artist names list {artist_names}')
    denominator = len(artist_names) - 1
    ratings = [(round((idx / denominator) * 100, 2), name) for (idx, name) in enumerate(artist_names)]
    
    current_app.logger.info('executing query')
    db = get_db()
    for (rating, name) in ratings:
        # current_app.logger.info(f'rating: {rating}, name: {name}, user_id: {user_id}')
        db.execute(
            'UPDATE artist'
            ' SET rating = ?'
            ' WHERE name = ? AND user_id = ?',
            (rating, name, user_id)
        )
    db.commit()
    
    return ratings


def run_comparison(artist_name, artist_to_compare, artist_to_compare_idx):
    # current_app.logger.info(f"artist to compare: {artist_to_compare}")
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
                                "type": 2,
                                "label": f"{artist_name}",
                                "style": 1,
                                "custom_id": f"n_{artist_name}_c_{artist_to_compare}_cidx_{artist_to_compare_idx}_pc_no",
                            },
                            {
                                "type": 2,
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


def get_artists_for_user(user):
    artists = (
        get_db()
        .execute(
            "SELECT * FROM artist WHERE user_id = ?" " ORDER BY rating ASC",
            (user["id"],),
        )
        .fetchall()
    )
    # current_app.logger.info(f'Got artists {", ".join([a["name"] for a in artists])}')
    # current_app.logger.info(f'With ratings {", ".join([str(a["rating"]) for a in artists])}')
    return artists


def get_or_create_user(discord_user):
    username = discord_user["username"]
    user = get_user(username)

    if user is None:
        db = get_db()
        db.execute(
            "INSERT INTO user (username, discord_id)" " VALUES (?, ?)",
            (username, discord_user["id"]),
        )
        db.commit()

    return get_user(username)


def get_user(username):
    db = get_db()
    return db.execute(
        "SELECT u.id, u.username" " FROM user u" " WHERE u.username = ?", (username,)
    ).fetchone()
