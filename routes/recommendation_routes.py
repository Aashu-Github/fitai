# ─────────────────────────────────────────────────────────────────────────────
# routes/recommendation_routes.py
# Author: SAI
# Layer: Routes (HTTP Interface)
# Use Cases: UC-07 (Meal Recommendations) · UC-08 (Recipe Nutrition Details)
#
# Thin Flask Blueprint — only parses HTTP input and formats HTTP output.
# All logic lives in: services/recommendation_service.py
# ─────────────────────────────────────────────────────────────────────────────

from flask import Blueprint, request, jsonify
from services import recommendation_service

recommendation_routes = Blueprint("recommendation_routes", __name__)


# ── UC-08: Full recipe details (nutrition + steps + tips) ─────────────────────
@recommendation_routes.route("/api/recipes/<int:recipe_id>/details", methods=["GET"])
def get_recipe_details(recipe_id):
    try:
        result = recommendation_service.get_recipe_details(recipe_id)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


# ── UC-07: Goal-based recipe recommendations ──────────────────────────────────
@recommendation_routes.route("/api/recommendations", methods=["GET"])
def get_recommendations():
    goal_override = request.args.get("goal", "").strip()
    tag_param     = request.args.get("tags", "").strip()
    limit         = int(request.args.get("limit", 5))
    result = recommendation_service.get_recommendations(goal_override, tag_param, limit)
    return jsonify(result)
