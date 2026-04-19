# ─────────────────────────────────────────────────────────────────────────────
# services.py  —  Business Logic Layer (all service logic in one file)
# Architecture:  routes.py → services.py → repository.py → fitai.db (SQLite)
# ─────────────────────────────────────────────────────────────────────────────

import repository as repo

ALL_TAGS = ["vegetarian","vegan","pescatarian","dairy-free","gluten-free",
            "no-fish","no-shellfish","no-sesame-oil","no-soybeans","no-wheat","no-eggs","no-nuts"]

VALID_MEAL_TYPES = {"Breakfast","Lunch","Dinner","Snack"}
VALID_DAYS       = {"Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"}


# ══════════════════════════════════════════════════════════════════════════════
# AUTH  (Garnet UC-01 / Keerthan UC-03/04)
# ══════════════════════════════════════════════════════════════════════════════

def signup(display_name, username, email, password, confirm_password) -> dict:
    if not all([display_name, username, email, password]):
        raise ValueError("All fields are required.")
    if password != confirm_password:
        raise ValueError("Passwords do not match.")
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters.")
    try:
        user = repo.create_user(display_name, username, email, password)
        return _safe_user(user)
    except ValueError as e:
        msg = str(e)
        if "UNIQUE" in msg and "username" in msg:
            raise ValueError("Username already taken.")
        if "UNIQUE" in msg and "email" in msg:
            raise ValueError("Email already in use.")
        raise

def login(username_or_email, password) -> dict:
    user = repo.login_user(username_or_email, password)
    if not user:
        raise ValueError("Incorrect username or password.")
    return _safe_user(user)

def get_profile(user_id) -> dict:
    user = repo.fetch_user(user_id)
    if not user: raise ValueError("User not found.")
    return _safe_user(user)

def update_profile(user_id, fields) -> dict:
    # FTC3.1 — weight is required; empty or missing → error
    weight = str(fields.get("weight", "")).strip()
    if not weight:
        raise ValueError("Weight is required. Please enter your weight.")

    # FTC3.2 — height is required; empty or missing → error
    height = str(fields.get("height", "")).strip()
    if not height:
        raise ValueError("Height is required. Please enter your height.")

    # FTC3.4 — weight must be a positive number
    try:
        weight_val = float(weight)
        if weight_val <= 0:
            raise ValueError()
    except ValueError:
        raise ValueError("Invalid weight format. Please enter a positive number (e.g. 150).")

    # FTC3.5 — height must follow ft'in\" or numeric format
    import re
    if not re.match(r"^\d+(['′]\d{1,2}[\"″]?)?$|^\d+(\.\d+)?$", height):
        raise ValueError("Invalid height format. Please enter a valid height (e.g. 6'0\" or 72).")

    # FTC3.3 — conflicting dietary preferences warning
    # (Vegan conflicts with High Protein animal-based; saved but warned)
    prefs = fields.get("dietary_prefs", [])
    if isinstance(prefs, str):
        import json as _json
        try:
            prefs = _json.loads(prefs)
        except Exception:
            prefs = []
    conflict_warning = None
    if "Vegan" in prefs and "High Protein" in prefs:
        conflict_warning = "Warning: Vegan and High Protein may conflict — limited recipe matches."

    # FTC3.5 (no goal) — default to Maintain Weight instead of error
    if not str(fields.get("goal", "")).strip():
        fields["goal"] = "Maintain Weight"

    # FTC3.6 — no dietary prefs is valid; profile saves normally
    # FTC3.7 — cancel is handled on the frontend; reaching here means save was confirmed

    updated = repo.update_user(user_id, fields)
    result = _safe_user(updated)
    if conflict_warning:
        result["warning"] = conflict_warning
    return result

def change_password(user_id, new_password):
    if len(new_password) < 6:
        raise ValueError("Password must be at least 6 characters.")
    repo.update_password(user_id, new_password)

def _safe_user(user: dict) -> dict:
    """Strip password hash before returning to client."""
    return {k: v for k, v in user.items() if k != "password_hash"}


# ══════════════════════════════════════════════════════════════════════════════
# RECIPES  (Garnet UC-01/02)
# ══════════════════════════════════════════════════════════════════════════════

def get_recipes(tag_param, page, per_page) -> dict:
    tags = [t.strip() for t in tag_param.split(",") if t.strip()] if tag_param else []
    return repo.fetch_recipes(tags, page, per_page)

def get_tags() -> list:
    return ALL_TAGS

def reorder(recipe_id, direction) -> dict:
    if direction not in ("up", "down"):
        raise ValueError("direction must be 'up' or 'down'")
    recipes = repo.swap_positions(recipe_id, direction)
    return {"message": f"Moved recipe {recipe_id} {direction}", "recipes": recipes}


# ══════════════════════════════════════════════════════════════════════════════
# RECIPE DETAILS  (Sai UC-07/08)
# ══════════════════════════════════════════════════════════════════════════════

def get_details(recipe_id) -> dict:
    d = repo.fetch_details(recipe_id)
    if not d: raise ValueError(f"Recipe {recipe_id} not found.")
    return d

def get_recommendations(goal_override, tag_param, limit, user_id=1) -> dict:
    user = repo.fetch_user(user_id) or {}
    goal = (goal_override or user.get("goal", "")).lower()
    tags = [t.strip() for t in tag_param.split(",") if t.strip()] if tag_param else []
    all_r = repo.fetch_all_with_details()
    if tags:
        all_r = [r for r in all_r if all(t in r["tags"] for t in tags)]
    def score(r):
        cal = r.get("calories", 0)
        pro = _int(r.get("protein","0"))
        fat = _int(r.get("fat","0"))
        if any(k in goal for k in ("lose","cut","fat")): return -(cal + fat*2)
        if any(k in goal for k in ("muscle","gain","bulk")): return float(pro)
        return -abs(cal-300)
    top = sorted(all_r, key=score, reverse=True)[:limit]
    return {"goal": user.get("goal",""), "recommendations": top, "count": len(top)}

def _int(v): 
    try: return int(str(v).replace("g","").strip())
    except: return 0


# ══════════════════════════════════════════════════════════════════════════════
# FAVORITES  (Roshini UC-09)
# ══════════════════════════════════════════════════════════════════════════════

def list_favorites(user_id) -> list:
    return repo.fetch_favorites(user_id)

def add_favorite(user_id, recipe_id) -> dict:
    favs = repo.add_favorite(user_id, recipe_id)
    return {"message": "Added to favourites", "favorites": favs}

def remove_favorite(user_id, recipe_id) -> dict:
    favs = repo.remove_favorite(user_id, recipe_id)
    return {"message": "Removed from favourites", "favorites": favs}


# ══════════════════════════════════════════════════════════════════════════════
# NUTRITION LOG  (Roshini UC-10)
# ══════════════════════════════════════════════════════════════════════════════

def log_meal(user_id, log_date, meal_type, name, calories, protein, carbs, fat, ts) -> list:
    if any(v < 0 for v in [calories, protein, carbs, fat]):
        raise ValueError("Nutrition values cannot be negative.")
    return repo.log_meal_entry(user_id, log_date, meal_type, name, calories, protein, carbs, fat, ts)

def get_day_log(user_id, log_date) -> list:
    return repo.fetch_day_log(user_id, log_date)

def delete_log(entry_id, user_id) -> bool:
    return repo.delete_log_entry(entry_id, user_id)

def get_week_nutrition(user_id, dates) -> list:
    return repo.fetch_week_nutrition(user_id, dates)


# ══════════════════════════════════════════════════════════════════════════════
# GOALS
# ══════════════════════════════════════════════════════════════════════════════

def get_goals(user_id) -> dict:
    return repo.fetch_goals(user_id)

def set_goals(user_id, cal, protein, carbs, fat) -> dict:
    return repo.save_goals(user_id, cal, protein, carbs, fat)


# ══════════════════════════════════════════════════════════════════════════════
# MEAL PLAN  (John UC-05/06)
# ══════════════════════════════════════════════════════════════════════════════

def get_meal_plan(user_id, week) -> dict:
    return repo.fetch_week_plan(user_id, str(week))

def save_meal(user_id, week, day, meal_type, entry) -> dict:
    if day not in VALID_DAYS: raise ValueError(f"Invalid day: {day}")
    if meal_type not in VALID_MEAL_TYPES: raise ValueError(f"Invalid meal type: {meal_type}")
    if not entry.get("name"): raise ValueError("Meal entry must include a name.")
    plan = repo.upsert_meal(user_id, str(week), day, meal_type,
                            entry["name"], int(entry.get("cals",0)), entry.get("emoji","🍽️"))
    return {"message": "Meal saved", "plan": plan}

def delete_meal(user_id, week, day, meal_type) -> dict:
    plan = repo.delete_meal_slot(user_id, str(week), day, meal_type)
    return {"message": "Meal removed", "plan": plan}