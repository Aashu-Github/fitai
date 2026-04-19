# ─────────────────────────────────────────────────────────────────────────────
# services/favorites_service.py
# Author: ROSHINI
# Layer: Service (Business Logic)
# Use Cases: UC-09 (Favourite Recipes) · UC-10 (Nutrition Logging)
#
# Contains all business rules for favourites and nutrition logging.
# Called by: routes/favorites_routes.py
# Calls:     repository/favorites_repository.py
# ─────────────────────────────────────────────────────────────────────────────

from repository import favorites_repository


# ── UC-09: Favourites ─────────────────────────────────────────────────────────

def list_favorites() -> list[dict]:
    """Return all currently favourited recipes."""
    return favorites_repository.fetch_all_favorites()


def add_to_favorites(recipe_id: int) -> dict:
    """
    UC-09: Add a recipe to favourites.
    Business rule: recipe must exist (enforced at repo layer).
    Returns the updated list and a confirmation message.
    """
    favorites = favorites_repository.add_favorite(recipe_id)
    return {"message": f"Added recipe {recipe_id} to favourites", "favorites": favorites}


def remove_from_favorites(recipe_id: int) -> dict:
    """
    UC-09: Remove a recipe from favourites.
    Raises ValueError if the recipe wasn't favourited.
    """
    favorites = favorites_repository.remove_favorite(recipe_id)
    return {"message": f"Removed recipe {recipe_id} from favourites", "favorites": favorites}


# ── UC-10: Nutrition Logging ──────────────────────────────────────────────────

def get_nutrition() -> dict:
    """UC-10: Return the current running nutrition totals."""
    return favorites_repository.fetch_nutrition()


def log_meal(calories: int, protein: int, carbs: int) -> dict:
    """
    UC-10: Validate macro inputs then add to the running totals.
    Business rule: values must be non-negative integers.
    """
    if any(v < 0 for v in (calories, protein, carbs)):
        raise ValueError("Nutrition values cannot be negative.")
    updated = favorites_repository.add_nutrition(calories, protein, carbs)
    return {"message": "Meal logged successfully", "nutrition": updated}


def reset_nutrition() -> dict:
    """UC-10: Reset all daily nutrition totals to zero."""
    reset = favorites_repository.reset_nutrition()
    return {"message": "Nutrition totals reset", "nutrition": reset}
