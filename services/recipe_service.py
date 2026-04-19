# ─────────────────────────────────────────────────────────────────────────────
# services/recipe_service.py
# Author: GARNET TRAN
# Layer: Service (Business Logic)
# Use Cases: UC-01 (Filter Recipes) · UC-02 (Reorder Recipes)
#
# Contains all business rules for recipes.
# Called by: routes/recipe_routes.py
# Calls:     repository/recipe_repository.py
# ─────────────────────────────────────────────────────────────────────────────

from repository import recipe_repository

ALL_TAGS = [
    "vegetarian", "vegan", "pescatarian",
    "dairy-free", "gluten-free",
    "no-fish", "no-shellfish", "no-sesame-oil",
    "no-soybeans", "no-wheat", "no-eggs", "no-nuts",
]


def get_recipes(tag_param: str, page: int, per_page: int) -> dict:
    """
    UC-01: Parse the tag query string into a list, then delegate to the
    repository. Returns a paginated, filtered recipe payload.
    """
    active_tags = [t.strip() for t in tag_param.split(",") if t.strip()] if tag_param else []
    return recipe_repository.fetch_all_recipes(active_tags, page, per_page)


def get_all_tags() -> list[str]:
    """UC-01: Return the master list of supported dietary filter tags."""
    return ALL_TAGS


def reorder_recipe(recipe_id: int, direction: str) -> dict:
    """
    UC-02: Validate direction and delegate the swap to the repository.
    Returns the full updated recipe list.
    """
    if direction not in ("up", "down"):
        raise ValueError("direction must be 'up' or 'down'")
    recipes = recipe_repository.swap_recipe_positions(recipe_id, direction)
    return {"message": f"Moved recipe {recipe_id} {direction}", "recipes": recipes}


def remove_recipe(recipe_id: int) -> dict:
    """Remove a recipe and return a confirmation message."""
    name = recipe_repository.delete_recipe_by_id(recipe_id)
    return {"message": f"Removed '{name}' from list"}
