# ─────────────────────────────────────────────────────────────────────────────
# repository/meal_plan_repository.py
# Author: JOHN VESLIN
# Layer: Repository (Database Access)
# Use Cases: UC-05 (Generate Meal Plan) · UC-06 (Modify Meal Plan)
#
# Only this file talks to the database for meal plan data.
# Called by: services/meal_plan_service.py
# ─────────────────────────────────────────────────────────────────────────────

from repository.database import get_db


def fetch_week(week: str) -> dict:
    """
    Return the full meal plan for a given week offset as a nested dict:
      { day: { meal_type: { name, cals, emoji } } }
    """
    conn = get_db()
    rows = conn.execute(
        "SELECT day, meal_type, name, cals, emoji FROM meal_plan WHERE week = ?",
        (week,)
    ).fetchall()
    conn.close()

    plan: dict = {}
    for row in rows:
        day   = row["day"]
        meal  = row["meal_type"]
        plan.setdefault(day, {})[meal] = {
            "name":  row["name"],
            "cals":  row["cals"],
            "emoji": row["emoji"],
        }
    return plan


def upsert_meal(week: str, day: str, meal_type: str, name: str, cals: int, emoji: str) -> dict:
    """
    Insert or replace a single meal slot, then return the updated week plan.
    """
    conn = get_db()
    conn.execute("""
        INSERT INTO meal_plan (week, day, meal_type, name, cals, emoji)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(week, day, meal_type) DO UPDATE SET
            name  = excluded.name,
            cals  = excluded.cals,
            emoji = excluded.emoji
    """, (week, day, meal_type, name, cals, emoji))
    conn.commit()
    conn.close()
    return fetch_week(week)


def delete_meal(week: str, day: str, meal_type: str) -> dict:
    """
    Remove a single meal slot.
    Raises ValueError if the slot does not exist.
    """
    conn = get_db()
    row  = conn.execute(
        "SELECT id FROM meal_plan WHERE week = ? AND day = ? AND meal_type = ?",
        (week, day, meal_type)
    ).fetchone()

    if not row:
        conn.close()
        raise ValueError(f"Meal slot not found: week={week} day={day} meal={meal_type}")

    conn.execute(
        "DELETE FROM meal_plan WHERE week = ? AND day = ? AND meal_type = ?",
        (week, day, meal_type)
    )
    conn.commit()
    conn.close()
    return fetch_week(week)


def clear_week(week: str) -> None:
    """Delete every meal slot for a given week offset."""
    conn = get_db()
    conn.execute("DELETE FROM meal_plan WHERE week = ?", (week,))
    conn.commit()
    conn.close()
