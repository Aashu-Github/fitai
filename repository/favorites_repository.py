# ─────────────────────────────────────────────────────────────────────────────
# repository/favorites_repository.py
# Author: ROSHINI
# Layer: Repository (Database Access)
# Use Cases: UC-09 (Favourite Recipes) · UC-10 (Nutrition Logging)
#
# Only this file talks to the database for favourites and nutrition data.
# Called by: services/favorites_service.py
# ─────────────────────────────────────────────────────────────────────────────

from repository.database import get_db


# ── UC-09: Favourites ─────────────────────────────────────────────────────────

def fetch_all_favorites() -> list[dict]:
    """Return all favourited recipes (joined with the recipes table)."""
    conn = get_db()
    rows = conn.execute("""
        SELECT r.id, r.name, r.emoji, r.tags
        FROM   favorites f
        JOIN   recipes   r ON f.recipe_id = r.id
        ORDER  BY f.id ASC
    """).fetchall()
    conn.close()
    result = []
    for row in rows:
        d = dict(row)
        d["tags"] = [t.strip() for t in d.get("tags", "").split(",") if t.strip()]
        result.append(d)
    return result


def add_favorite(recipe_id: int) -> list[dict]:
    """
    Add a recipe to favourites (idempotent — ignores duplicates).
    Returns the updated favourites list.
    Raises ValueError if the recipe does not exist in the recipes table.
    """
    conn = get_db()
    exists = conn.execute("SELECT id FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
    if not exists:
        conn.close()
        raise ValueError(f"Recipe id {recipe_id} not found")

    conn.execute(
        "INSERT OR IGNORE INTO favorites (recipe_id) VALUES (?)", (recipe_id,)
    )
    conn.commit()
    conn.close()
    return fetch_all_favorites()


def remove_favorite(recipe_id: int) -> list[dict]:
    """
    Remove a recipe from favourites.
    Raises ValueError if it wasn't favourited.
    """
    conn = get_db()
    row  = conn.execute("SELECT id FROM favorites WHERE recipe_id = ?", (recipe_id,)).fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Recipe id {recipe_id} is not in favourites")
    conn.execute("DELETE FROM favorites WHERE recipe_id = ?", (recipe_id,))
    conn.commit()
    conn.close()
    return fetch_all_favorites()


# ── UC-10: Nutrition Log ──────────────────────────────────────────────────────

def fetch_nutrition(log_id: int = 1) -> dict:
    """Return the current nutrition totals."""
    conn = get_db()
    row  = conn.execute("SELECT * FROM nutrition_log WHERE id = ?", (log_id,)).fetchone()
    conn.close()
    return dict(row) if row else {"calories": 0, "protein": 0, "carbs": 0}


def add_nutrition(calories: int, protein: int, carbs: int, log_id: int = 1) -> dict:
    """Increment the running nutrition totals and return the updated row."""
    conn = get_db()
    conn.execute("""
        UPDATE nutrition_log
        SET calories = calories + ?,
            protein  = protein  + ?,
            carbs    = carbs    + ?
        WHERE id = ?
    """, (calories, protein, carbs, log_id))
    conn.commit()
    row = conn.execute("SELECT * FROM nutrition_log WHERE id = ?", (log_id,)).fetchone()
    conn.close()
    return dict(row)


def reset_nutrition(log_id: int = 1) -> dict:
    """Reset all nutrition totals to zero."""
    conn = get_db()
    conn.execute(
        "UPDATE nutrition_log SET calories = 0, protein = 0, carbs = 0 WHERE id = ?",
        (log_id,)
    )
    conn.commit()
    conn.close()
    return {"id": log_id, "calories": 0, "protein": 0, "carbs": 0}
