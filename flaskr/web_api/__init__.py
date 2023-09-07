from flask import Blueprint, request, current_app, jsonify, Response

from ..models.rating import Rating
from ..ratings.rating_calculator import RatingCalculator, CompletedComparison
from ..models.user import User

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/ratings", methods=["GET"])
def get_ratings() -> Response:
    username = request.args.get("username")
    rating_type = request.args.get("rating_type")
    current_app.logger.info(f"Getting ratings of type {rating_type} for {username}")
    # Begin shareable part
    user = User.get_by_username(username=username)
    if user is None:
        return (jsonify({"error": f"User {username} not found"}), 404)
    ratings = user.get_ratings(rating_type=rating_type)
    # End shareable part
    ratings.reverse()
    return jsonify({"ratings": [r.to_json() for r in ratings]})


@bp.route("/ratings", methods=["POST"])
def create_rating() -> Response:
    content = request.json
    username = content["username"]
    rating_type = content["rating_type"]
    rating_name = content["rating_name"]
    current_app.logger.info(f"Getting ratings of type {rating_type} for {username}")

    # Begin shareable part
    user = User.get_by_username(username=username)
    if user is None:
        return (jsonify({"error": f"User {username} not found"}), 404)
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
        return jsonify({"rating": new_rating.to_json()})
    # End shareable part
    return jsonify({"rating": new_rating.to_json(), "next_comparison": next_comparison.to_json()})

@bp.route("/ratings/compare", methods=["PUT"])
def create_comparison() -> Response:
    content = request.json
    username = content["username"]
    rating_id = content["rating_id"]
    comparison_id = content["comparison"]["id"]
    comparison_index = content["comparison"]["index"]
    is_comparison_preferred = content["is_comparison_preferred"]

    comparison = CompletedComparison(
                id=comparison_id,
                index=comparison_index,
                is_preferred=is_comparison_preferred,
            )

    # Begin shareable part
    user = User.get_by_username(username)
    rating = Rating.get_by_id_for_user(user=user, rating_id=rating_id)
    if rating is None:
        return (jsonify({"error": f"Rating with id {rating_id} not found"}), 404)

    rating_calculator = RatingCalculator.continue_rating(
        item_being_rated=rating,
        comparison=comparison,
    )
    next_comparison = rating_calculator.get_next_comparison()
    if next_comparison:
        return jsonify({"next_comparison": next_comparison.to_json()})

    new_ratings = rating_calculator.get_overall_ratings()
    Rating.update_all_with_new_ratings(user=user, new_ratings=new_ratings)
    rating_calculator.complete()
    # End shareable part
    return jsonify({"new_ratings": [r.to_json() for r in new_ratings]})

@bp.route("/ratings", methods=["DELETE"])
def delete_rating() -> Response:
    content = request.json
    username = content["username"]
    rating_type = content["rating_type"]
    rating_name = content["rating_name"]
    current_app.logger.info(
        f"Deleting rating {rating_name} of type {rating_type} for {username}"
    )

    # Begin shareable part
    user = User.get_by_username(username=username)
    if user is None:
        return (jsonify({"error": f"User {username} not found"}), 404)
    rating = Rating.get_by_name_for_user(
        user=user, rating_name=rating_name, rating_type=rating_type
    )
    # End shareable part
    if rating is None:
        return (
            jsonify({"error": f"Rating {rating_name} of type {rating_type} not found"}),
            404,
        )
    Rating.remove_rating_for_user(user, rating)
    return jsonify({"rating_id": rating.id})


@bp.route("/rating_types", methods=["GET"])
def ratings_types() -> Response:
    username = request.args.get("username")
    current_app.logger.info(f"Getting rating types for {username}")
    user = User.get_by_username(username=username)
    if user is None:
        return (jsonify({"error": f"User {username} not found"}), 404)
    rating_types = user.get_rating_types()
    return jsonify({"rating_types": rating_types})
