# ─────────────────────────────────────────────────────────────────────────────
# repository/recipe_details_repository.py
# Author: SAI
# Layer: Repository (Database Access)
# Use Cases: UC-07 (Recommendations) · UC-08 (Recipe Nutrition Details)
#
# Only this file talks to the database for nutrition details.
# Called by: services/recommendation_service.py
# ─────────────────────────────────────────────────────────────────────────────

import json
from repository.database import get_db


def fetch_details_by_id(recipe_id: int) -> dict | None:
    """
    Return full nutrition + steps + tips for a single recipe.
    Returns None if the recipe or its details do not exist.
    """
    conn = get_db()
    row = conn.execute("""
        SELECT rd.*, r.name, r.emoji, r.tags
        FROM   recipe_details rd
        JOIN   recipes        r  ON rd.recipe_id = r.id
        WHERE  rd.recipe_id = ?
    """, (recipe_id,)).fetchone()
    conn.close()

    if not row:
        return None

    d = dict(row)
    d["tags"]  = [t.strip() for t in d.get("tags",  "").split(",") if t.strip()]
    d["steps"] = json.loads(d.get("steps", "[]"))
    d["tips"]  = json.loads(d.get("tips",  "[]"))
    return d


def fetch_all_with_details() -> list[dict]:
    """
    Return every recipe joined with its nutrition details.
    Used by the recommendation scorer to access calorie / protein / fat values.
    """
    conn = get_db()
    rows = conn.execute("""
        SELECT r.id, r.name, r.emoji, r.tags, r.position,
               rd.calories, rd.protein, rd.carbs, rd.fat, rd.steps, rd.tips
        FROM   recipes       r
        JOIN   recipe_details rd ON r.id = rd.recipe_id
        ORDER  BY r.position ASC
    """).fetchall()
    conn.close()

    result = []
    for row in rows:
        d = dict(row)
        d["tags"]  = [t.strip() for t in d.get("tags",  "").split(",") if t.strip()]
        d["steps"] = json.loads(d.get("steps", "[]"))
        d["tips"]  = json.loads(d.get("tips",  "[]"))
        result.append(d)
    return result
