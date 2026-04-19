# ─────────────────────────────────────────────────────────────────────────────
# services/meal_plan_service.py
# Author: JOHN VESLIN
# Layer: Service (Business Logic)
# Use Cases: UC-05 (Generate Meal Plan) · UC-06 (Modify Meal Plan)
#
# Contains all business rules for weekly meal planning.
# Called by: routes/meal_plan_routes.py
# Calls:     repository/meal_plan_repository.py
# ─────────────────────────────────────────────────────────────────────────────

from repository import meal_plan_repository

VALID_MEAL_TYPES = {"Breakfast", "Lunch", "Dinner", "Snack"}
VALID_DAYS       = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}


def get_week_plan(week: str) -> dict:
    """
    UC-05: Return the full meal plan for a given week offset.
    Week "0" = current week; "1" = next week; "-1" = last week.
    """
    return meal_plan_repository.fetch_week(str(week))


def save_meal(week: str, day: str, meal_type: str, entry: dict) -> dict:
    """
    UC-06: Validate inputs then save (insert or update) a meal slot.
    Business rules:
      - day must be a valid weekday name
      - meal_type must be Breakfast / Lunch / Dinner / Snack
      - entry must include name, cals, and emoji
    """
    if day not in VALID_DAYS:
        raise ValueError(f"Invalid day: '{day}'. Must be a full weekday name (e.g. Monday).")
    if meal_type not in VALID_MEAL_TYPES:
        raise ValueError(f"Invalid meal type: '{meal_type}'. Must be one of {VALID_MEAL_TYPES}.")
    if not entry.get("name"):
        raise ValueError("Meal entry must include a 'name'.")

    updated_plan = meal_plan_repository.upsert_meal(
        week     = str(week),
        day      = day,
        meal_type= meal_type,
        name     = entry["name"],
        cals     = int(entry.get("cals", 0)),
        emoji    = entry.get("emoji", "🍽️"),
    )
    return {"message": "Meal saved", "plan": updated_plan}


def delete_meal(week: str, day: str, meal_type: str) -> dict:
    """
    UC-06: Remove a single meal slot.
    Raises ValueError if the slot doesn't exist (propagated from repo).
    """
    updated_plan = meal_plan_repository.delete_meal(str(week), day, meal_type)
    return {"message": "Meal removed", "plan": updated_plan}


def clear_week(week: str) -> dict:
    """UC-06: Delete all meal slots for a given week."""
    meal_plan_repository.clear_week(str(week))
    return {"message": f"Week {week} plan cleared"}
