# ─────────────────────────────────────────────────────────────────────────────
# routes/user_routes.py
# Author: KEERTHAN SANJAY
# Layer: Routes (HTTP Interface)
# Use Cases: UC-03 (User Profile) · UC-04 (Dashboard)
#
# Thin Flask Blueprint — only parses HTTP input and formats HTTP output.
# All logic lives in: services/user_service.py
# ─────────────────────────────────────────────────────────────────────────────

from flask import Blueprint, render_template, request, jsonify
from services import user_service

user_routes = Blueprint("user_routes", __name__)


# ── UC-04: Dashboard page ─────────────────────────────────────────────────────
@user_routes.route("/")
def dashboard():
    return render_template("dashboard.html")


# ── UC-03: Profile page ───────────────────────────────────────────────────────
@user_routes.route("/profile")
def profile():
    try:
        data = user_service.get_profile()
        return render_template("profile.html", data=data)
    except ValueError as e:
        return str(e), 404


# ── UC-03: Get profile as JSON (used by the frontend) ─────────────────────────
@user_routes.route("/api/profile", methods=["GET"])
def get_profile():
    try:
        return jsonify(user_service.get_profile())
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


# ── UC-03: Update profile ─────────────────────────────────────────────────────
@user_routes.route("/api/update", methods=["POST"])
def update_profile():
    fields = request.get_json(force=True)
    try:
        updated = user_service.update_profile(user_id=1, fields=fields)
        return jsonify({"message": "Dietary profile updated successfully!", "profile": updated})
    except ValueError as e:
        return jsonify({"message": f"Error: {e}"}), 400
