# ─────────────────────────────────────────────────────────────────────────────
# routes/favorites_routes.py
# Author: ROSHINI
# Layer: Routes (HTTP Interface)
# Use Cases: UC-09 (Favourite Recipes) · UC-10 (Nutrition Logging)
#
# Thin Flask Blueprint — only parses HTTP input and formats HTTP output.
# All logic lives in: services/favorites_service.py
# ─────────────────────────────────────────────────────────────────────────────

from flask import Blueprint, render_template, request, jsonify
from services import favorites_service

favorites_routes = Blueprint("favorites_routes", __name__)


# ── UC-09: Favourites page ────────────────────────────────────────────────────
@favorites_routes.route("/favorites")
def favorites_page():
    return render_template("favorite_recipes.html")


# ── UC-09: List all favourites ────────────────────────────────────────────────
@favorites_routes.route("/api/favorites", methods=["GET"])
def get_favorites():
    return jsonify({"favorites": favorites_service.list_favorites()})


# ── UC-09: Add a recipe to favourites ────────────────────────────────────────
@favorites_routes.route("/api/favorites/<int:recipe_id>", methods=["POST"])
def add_favorite(recipe_id):
    try:
        result = favorites_service.add_to_favorites(recipe_id)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


# ── UC-09: Remove a recipe from favourites ────────────────────────────────────
@favorites_routes.route("/api/favorites/<int:recipe_id>", methods=["DELETE"])
def remove_favorite(recipe_id):
    try:
        result = favorites_service.remove_from_favorites(recipe_id)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


# ── UC-10: Get nutrition totals ───────────────────────────────────────────────
@favorites_routes.route("/api/nutrition", methods=["GET"])
def get_nutrition():
    return jsonify(favorites_service.get_nutrition())


# ── UC-10: Log a meal ─────────────────────────────────────────────────────────
@favorites_routes.route("/api/log_meal", methods=["POST"])
def log_meal():
    data = request.get_json(force=True)
    try:
        result = favorites_service.log_meal(
            calories = int(data.get("calories", 0)),
            protein  = int(data.get("protein",  0)),
            carbs    = int(data.get("carbs",    0)),
        )
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


# ── UC-10: Reset nutrition totals ─────────────────────────────────────────────
@favorites_routes.route("/api/nutrition/reset", methods=["POST"])
def reset_nutrition():
    return jsonify(favorites_service.reset_nutrition())
