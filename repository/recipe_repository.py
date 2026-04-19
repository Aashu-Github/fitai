# ─────────────────────────────────────────────────────────────────────────────
# repository/recipe_repository.py
# Author: GARNET TRAN
# Layer: Repository (Database Access)
# Use Cases: UC-01 (Filter Recipes) · UC-02 (Reorder Recipes)
#
# Only this file talks to the database for recipes.
# Called by: services/recipe_service.py
# ─────────────────────────────────────────────────────────────────────────────

import json
from repository.database import get_db


def fetch_all_recipes(active_tags: list[str], page: int, per_page: int) -> dict:
    """
    UC-01: Fetch recipes from the DB, filtered by tags, paginated.
    Tags are stored as a comma-separated string; filtering is done in Python
    so every active tag must appear in the recipe's tag string.
    """
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM recipes ORDER BY position ASC"
    ).fetchall()
    conn.close()

    recipes = [_row_to_dict(r) for r in rows]

    # Filter: all active tags must be present
    if active_tags:
        recipes = [r for r in recipes if all(t in r["tags"] for t in active_tags)]

    total       = len(recipes)
    total_pages = max(1, -(-total // per_page))
    page        = max(1, min(page, total_pages))
    start       = (page - 1) * per_page
    paginated   = recipes[start : start + per_page]

    return {
        "recipes":     paginated,
        "total":       total,
        "page":        page,
        "per_page":    per_page,
        "total_pages": total_pages,
        "active_tags": active_tags,
    }


def fetch_recipe_by_id(recipe_id: int) -> dict | None:
    """Return a single recipe row as a dict, or None if not found."""
    conn = get_db()
    row  = conn.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
    conn.close()
    return _row_to_dict(row) if row else None


def swap_recipe_positions(recipe_id: int, direction: str) -> dict:
    """
    UC-02: Move a recipe up or down by swapping its position value with
    the adjacent recipe. Returns the updated full recipe list.
    """
    conn = get_db()
    c    = conn.cursor()

    row = c.execute(
        "SELECT id, position FROM recipes WHERE id = ?", (recipe_id,)
    ).fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Recipe id {recipe_id} not found")

    pos = row["position"]

    if direction == "up":
        neighbor = c.execute(
            "SELECT id, position FROM recipes WHERE position < ? ORDER BY position DESC LIMIT 1", (pos,)
        ).fetchone()
    else:
        neighbor = c.execute(
            "SELECT id, position FROM recipes WHERE position > ? ORDER BY position ASC LIMIT 1", (pos,)
        ).fetchone()

    if not neighbor:
        conn.close()
        raise ValueError(f"Cannot move {direction}: already at boundary")

    # Swap positions
    c.execute("UPDATE recipes SET position = ? WHERE id = ?", (neighbor["position"], recipe_id))
    c.execute("UPDATE recipes SET position = ? WHERE id = ?", (pos, neighbor["id"]))
    conn.commit()
    conn.close()

    return fetch_all_recipes([], 1, 100)["recipes"]


def delete_recipe_by_id(recipe_id: int) -> str:
    """Remove a recipe from the DB. Returns its name."""
    conn = get_db()
    row  = conn.execute("SELECT name FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Recipe id {recipe_id} not found")
    name = row["name"]
    conn.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
    conn.commit()
    conn.close()
    return name


# ── Helper ────────────────────────────────────────────────────────────────────
def _row_to_dict(row) -> dict:
    d = dict(row)
    # Convert comma-separated tags back to a list
    d["tags"] = [t.strip() for t in d.get("tags", "").split(",") if t.strip()]
    return d
