# ─────────────────────────────────────────────────────────────────────────────
# services/user_service.py
# Author: KEERTHAN SANJAY
# Layer: Service (Business Logic)
# Use Cases: UC-03 (User Profile) · UC-04 (Dashboard)
#
# Contains all business rules for user profile management.
# Called by: routes/user_routes.py
# Calls:     repository/user_repository.py
# ─────────────────────────────────────────────────────────────────────────────

from repository import user_repository


def get_profile(user_id: int = 1) -> dict:
    """
    UC-03: Retrieve the user's current profile.
    Raises ValueError if the user is not found.
    """
    profile = user_repository.fetch_user(user_id)
    if not profile:
        raise ValueError(f"User id {user_id} not found")
    return profile


def update_profile(user_id: int, fields: dict) -> dict:
    """
    UC-03: Apply business validation rules before saving.

    Test Case 1 — Successful update  : valid fields → saved and returned.
    Test Case 2 — Empty weight        : blank/missing weight → ValueError raised.
    """
    weight = fields.get("weight", "").strip()
    if not weight:
        raise ValueError("Weight cannot be empty!")

    return user_repository.update_user(user_id, fields)
