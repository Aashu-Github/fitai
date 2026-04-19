# ─────────────────────────────────────────────────────────────────────────────
# routes/meal_plan_routes.py
# Author: JOHN VESLIN
# Layer: Routes (HTTP Interface)
# Use Cases: UC-05 (Generate Meal Plan) · UC-06 (Modify Meal Plan)
#
# Thin Flask Blueprint — only parses HTTP input and formats HTTP output.
# All logic lives in: services/meal_plan_service.py
# ─────────────────────────────────────────────────────────────────────────────

from flask import Blueprint, render_template, request, jsonify
from services import meal_plan_service

meal_plan_routes = Blueprint("meal_plan_routes", __name__)


# ── UC-05: Meal planner page ──────────────────────────────────────────────────
@meal_plan_routes.route("/meal-plan")
def meal_plan_page():
    return render_template("meal_planner.html")


# ── UC-05: Get a week's meal plan ─────────────────────────────────────────────
@meal_plan_routes.route("/api/meal-plan", methods=["GET"])
def get_meal_plan():
    week = request.args.get("week", "0")
    return jsonify(meal_plan_service.get_week_plan(week))


# ── UC-06: Add or update a single meal slot ───────────────────────────────────
@meal_plan_routes.route("/api/meal-plan", methods=["POST"])
def set_meal():
    data = request.get_json(force=True)
    try:
        result = meal_plan_service.save_meal(
            week      = str(data.get("week", "0")),
            day       = data.get("day", ""),
            meal_type = data.get("meal", ""),
            entry     = data.get("entry", {}),
        )
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


# ── UC-06: Remove a single meal slot ─────────────────────────────────────────
@meal_plan_routes.route("/api/meal-plan", methods=["DELETE"])
def delete_meal():
    data = request.get_json(force=True)
    try:
        result = meal_plan_service.delete_meal(
            week      = str(data.get("week", "0")),
            day       = data.get("day", ""),
            meal_type = data.get("meal", ""),
        )
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


# ── UC-06: Clear an entire week ───────────────────────────────────────────────
@meal_plan_routes.route("/api/meal-plan/clear", methods=["POST"])
def clear_week():
    data = request.get_json(force=True)
    result = meal_plan_service.clear_week(str(data.get("week", "0")))
    return jsonify(result)
