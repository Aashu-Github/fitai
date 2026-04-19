# ─────────────────────────────────────────────────────────────────────────────
# services/recommendation_service.py
# Author: SAI
# Layer: Service (Business Logic)
# Use Cases: UC-07 (Meal Recommendations) · UC-08 (Recipe Nutrition Details)
#
# Contains all scoring logic and business rules for recommendations.
# Called by: routes/recommendation_routes.py
# Calls:     repository/recipe_details_repository.py
#            repository/user_repository.py
# ─────────────────────────────────────────────────────────────────────────────

from repository import recipe_details_repository, user_repository


def get_recipe_details(recipe_id: int) -> dict:
    """
    UC-08: Return full nutritional info + preparation steps + tips.
    Raises ValueError if recipe or details not found.
    Mirrors the sequence: RecipeGUI → RecipeController.requestRecipeDetails(id)
                          → DBMgr.getRecipeDetails(id) → <<RecipeDetails>>
    """
    details = recipe_details_repository.fetch_details_by_id(recipe_id)
    if not details:
        raise ValueError(f"Recipe id {recipe_id} not found or has no details")
    return details


def get_recommendations(goal_override: str, tag_param: str, limit: int) -> dict:
    """
    UC-07: Score every recipe against the user's fitness goal and return the
    top `limit` results with their nutrition details attached.

    Precondition : User is logged in and has a goal set in their profile.
    TUCBW        : User clicks the recommendation / search button.
    TUCEW        : System returns top N scored recipes filtered by preferences.

    Scoring rules:
      "lose" / "cut" / "fat"     → favour lower calories + lower fat
      "muscle" / "gain" / "bulk" → favour higher protein
      default (maintain)         → favour calories closest to 300 kcal
    """
    # Resolve the goal (caller can override; fallback to stored profile)
    profile = user_repository.fetch_user(1) or {}
    goal    = (goal_override or profile.get("goal", "")).lower()

    active_tags = [t.strip() for t in tag_param.split(",") if t.strip()] if tag_param else []

    # Fetch every recipe that has details
    all_recipes = recipe_details_repository.fetch_all_with_details()

    # Filter by dietary tags
    if active_tags:
        all_recipes = [r for r in all_recipes if all(t in r["tags"] for t in active_tags)]

    # Score each recipe
    def _score(recipe: dict) -> float:
        cals    = recipe.get("calories", 0)
        protein = _parse_int(recipe.get("protein", "0"))
        fat     = _parse_int(recipe.get("fat",     "0"))

        if any(k in goal for k in ("lose", "cut", "fat")):
            return -(cals + fat * 2)
        elif any(k in goal for k in ("muscle", "gain", "bulk")):
            return float(protein)
        else:
            return -abs(cals - 300)

    top = sorted(all_recipes, key=_score, reverse=True)[:limit]

    return {
        "goal":            profile.get("goal", ""),
        "active_tags":     active_tags,
        "recommendations": top,
        "count":           len(top),
    }


def _parse_int(value: str | int) -> int:
    """Safely parse a value like '14g' or 14 into an integer."""
    try:
        return int(str(value).replace("g", "").strip())
    except (ValueError, TypeError):
        return 0
