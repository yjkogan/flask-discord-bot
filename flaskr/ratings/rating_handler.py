import re

from flask import jsonify

from ..discord import InteractionCallbackType, MessageComponentType
from ..models.user import User
from ..models.rating import Rating
from ..ratings.rating_calculator import (
    RatingCalculator,
    CompletedComparison,
    ComparisonToSend,
)


class RatingHandler:
    @staticmethod
    def handle_add_rating(discord_user: dict, interaction_data: dict):
        rating_type: str = RatingHandler._parse_rating_type(
            interaction_data["options"][0]["value"]
        )
        rating_name: str = RatingHandler._parse_rating_name(
            interaction_data["options"][1]["value"]
        )
        user = User.get_or_create_for_discord_user(discord_user)

        ratings_for_user = user.get_ratings(rating_type=rating_type)
        new_rating = Rating.get_or_create_rating(
            user=user, rating_name=rating_name, rating_type=rating_type
        )
        other_items = [r for r in ratings_for_user if r.id != new_rating.id]
        rating_calculator = RatingCalculator.begin_rating(
            item_being_rated=new_rating,
            other_items=other_items,
        )
        next_comparison = rating_calculator.get_next_comparison()
        if next_comparison is None:
            rating_calculator.complete()
            return jsonify(RatingJsonResponder.get_first_rating_json(rating_type))

        return jsonify(
            RatingJsonResponder.get_comparison_json(
                rating_calculator.item_being_rated,
                next_comparison,
                next_comparison.index,
            )
        )

    @staticmethod
    def handle_remove_rating(discord_user: dict, interaction_data: dict):
        rating_type: str = RatingHandler._parse_rating_type(
            interaction_data["options"][0]["value"]
        )
        rating_name: str = RatingHandler._parse_rating_name(
            interaction_data["options"][1]["value"]
        )
        user = User.get_or_create_for_discord_user(discord_user)

        rating = Rating.get_by_name_for_user(
            user=user, rating_name=rating_name, rating_type=rating_type
        )
        if rating is None:
            return jsonify(
                RatingJsonResponder.get_not_found_json(
                    f"**{rating_name}** of type **{rating_type}**",
                    discord_user["username"],
                )
            )

        Rating.remove_rating_for_user(user=user, rating=rating)
        return jsonify(RatingJsonResponder.get_removed_success_json(rating))

    @staticmethod
    def handle_list_ratings(discord_user: dict, interaction_data: dict):
        rating_type: str = RatingHandler._parse_rating_type(
            interaction_data["options"][0]["value"]
        )
        user = User.get_or_create_for_discord_user(discord_user)

        ratings_for_user = user.get_ratings(rating_type=rating_type)
        return jsonify(
            RatingJsonResponder.get_ratings_list_json(
                rating_type=rating_type, ratings=ratings_for_user
            )
        )

    @staticmethod
    def handle_list_types(discord_user: dict):
        user = User.get_or_create_for_discord_user(discord_user)

        rating_types = user.get_rating_types()
        return jsonify(RatingJsonResponder.get_types_list_json(rating_types))

    @staticmethod
    def handle_responded_to_comparison(discord_user: dict, interaction_data: dict):
        (rating_id, comparison) = RatingHandler._parse_custom_id(
            interaction_data["custom_id"]
        )

        user = User.get_by_username(discord_user["username"])
        rating = Rating.get_by_id_for_user(user=user, rating_id=rating_id)
        if rating is None:
            return jsonify(
                RatingJsonResponder.get_not_found_json(
                    f"id:{rating_id}", discord_user["username"]
                )
            )

        rating_calculator = RatingCalculator.continue_rating(
            item_being_rated=rating,
            comparison=comparison,
        )
        if rating_calculator is None:
            return jsonify(
                RatingJsonResponder.get_not_found_json(
                    f"name:{rating.name}", discord_user["username"]
                )
            )

        next_comparison = rating_calculator.get_next_comparison()
        if next_comparison:
            return jsonify(
                RatingJsonResponder.get_comparison_json(
                    rating_calculator.item_being_rated,
                    next_comparison,
                    next_comparison.index,
                )
            )

        new_ratings = rating_calculator.get_overall_ratings()
        Rating.update_all_with_new_ratings(user=user, new_ratings=new_ratings)
        rating_calculator.complete()
        return jsonify(RatingJsonResponder.get_ratings_list_json(rating.type, new_ratings))

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

    @staticmethod
    def _parse_rating_type(rating_type: str) -> str:
        return rating_type.strip().lower()

    @staticmethod
    def _parse_rating_name(rating_name: str) -> str:
        return rating_name.strip()


class RatingJsonResponder:
    @staticmethod
    def get_comparison_json(
        rating: Rating, rating_to_compare: ComparisonToSend, rating_to_compare_idx: int
    ) -> dict:
        return {
            "type": InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
            "data": {
                "content": f"Which of these **{rating.type}s** do you prefer?",
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

    @staticmethod
    def get_ratings_list_json(rating_type: str, ratings: list[Rating]):
        if len(ratings) == 0:
            return {
                "type": InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
                "data": {"content": f"You have no ratings of **{rating_type}s**"},
            }
        lines = []
        for r in ratings:
            lines.append(f"{r.name}: {r.value}")
        lines.reverse()
        ratings_message = "\n".join(lines)
        return {
            "type": InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
            "data": {
                "content": f"Your new ratings for **{rating_type}s** are:\n\n{ratings_message}"
            },
        }

    @staticmethod
    def get_types_list_json(rating_types: list[str]):
        if len(rating_types) == 0:
            return {
                "type": InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
                "data": {"content": "You haven't rated anything yet!"},
            }

        types_message = "\n".join(rating_types)
        return {
            "type": InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
            "data": {
                "content": f"You have ratings of the following types:\n\n{types_message}"
            },
        }

    @staticmethod
    def get_first_rating_json(rating_type: str):
        return {
            "type": InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
            "data": {
                "content": f"Thanks for adding your first **{rating_type}**! Rate another **{rating_type}** to create a relative ranking."
            },
        }

    @staticmethod
    def get_removed_success_json(rating: Rating):
        return {
            "type": InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
            "data": {
                "content": f"Removed **{rating.name}** from your **{rating.type}s** ratings"
            },
        }

    @staticmethod
    def get_not_found_json(identifier: str, username: str):
        return {
            "type": InteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
            "data": {"content": f"Cannot find rating {identifier} for user {username}"},
        }
