# ─────────────────────────────────────────────────────────────────────────────
# routes/recipe_routes.py
# Author: GARNET TRAN
# Layer: Routes (HTTP Interface)
# Use Cases: UC-01 (Filter Recipes) · UC-02 (Reorder Recipes)
#
# Thin Flask Blueprint — only parses HTTP input and formats HTTP output.
# All logic lives in: services/recipe_service.py
# ─────────────────────────────────────────────────────────────────────────────

from flask import Blueprint, request, jsonify
from services import recipe_service

recipe_routes = Blueprint("recipe_routes", __name__)


# ── UC-01: List recipes (filter + paginate) ───────────────────────────────────
@recipe_routes.route("/api/recipes", methods=["GET"])
def get_recipes():
    tag_param = request.args.get("tags", "").strip()
    page      = int(request.args.get("page",     1))
    per_page  = int(request.args.get("per_page", 5))
    return jsonify(recipe_service.get_recipes(tag_param, page, per_page))


# ── UC-01: All available filter tags ─────────────────────────────────────────
@recipe_routes.route("/api/tags", methods=["GET"])
def get_tags():
    return jsonify({"tags": recipe_service.get_all_tags()})


# ── UC-02: Move a recipe up or down ──────────────────────────────────────────
@recipe_routes.route("/api/recipes/<int:recipe_id>/move", methods=["POST"])
def move_recipe(recipe_id):
    data      = request.get_json(force=True)
    direction = data.get("direction", "").lower()
    try:
        result = recipe_service.reorder_recipe(recipe_id, direction)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


# ── Remove a recipe ───────────────────────────────────────────────────────────
@recipe_routes.route("/api/recipes/<int:recipe_id>", methods=["DELETE"])
def delete_recipe(recipe_id):
    try:
        result = recipe_service.remove_recipe(recipe_id)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
