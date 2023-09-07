from flask import Blueprint, request, current_app, jsonify, Response

from ..models.rating import Rating
from ..models.user import User

bp = Blueprint("api", __name__, url_prefix="/api")

@bp.route("/ratings", methods=["GET"])
def ratings() -> Response:
    username = request.args.get("username")
    ratings_type = request.args.get("ratings_type")
    current_app.logger.info(f"Getting ratings of type {ratings_type} for {username}")
    user = User.get_by_username(username=username)
    if user is None:
        return (jsonify({"error": f"User {username} not found"}), 404)
    ratings = user.get_ratings(rating_type=ratings_type)
    ratings.reverse()
    return jsonify({"ratings": [r.to_json() for r in ratings]})

@bp.route("/ratings-types", methods=["GET"])
def ratings_types() -> Response:
    username = request.args.get("username")
    current_app.logger.info(f"Getting rating types for {username}")
    user = User.get_by_username(username=username)
    if user is None:
        return (jsonify({"error": f"User {username} not found"}), 404)
    rating_types = user.get_rating_types()
    return jsonify({"rating_types": rating_types})
