# ─────────────────────────────────────────────────────────────────────────────
# repository.py  —  Database Layer (all DB access in one file)
# Architecture:  routes.py → services.py → repository.py → fitai.db (SQLite)
# ─────────────────────────────────────────────────────────────────────────────

import sqlite3, json, os, hashlib, secrets

DB_PATH = os.path.join(os.path.dirname(__file__), "fitai.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables and seed data on first run."""
    conn = get_db()
    c = conn.cursor()

    # ── users ─────────────────────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        display_name  TEXT    NOT NULL DEFAULT '',
        username      TEXT    NOT NULL UNIQUE,
        email         TEXT    NOT NULL UNIQUE,
        password_hash TEXT    NOT NULL,
        weight        TEXT    NOT NULL DEFAULT '',
        height        TEXT    NOT NULL DEFAULT '',
        goal          TEXT    NOT NULL DEFAULT 'Maintain Weight',
        dietary_prefs TEXT    NOT NULL DEFAULT '[]'
    )""")

    # ── recipes ───────────────────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS recipes (
        id       INTEGER PRIMARY KEY,
        name     TEXT    NOT NULL,
        emoji    TEXT    NOT NULL DEFAULT '🍽️',
        tags     TEXT    NOT NULL DEFAULT '',
        position INTEGER NOT NULL DEFAULT 0
    )""")

    # ── recipe_details ────────────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS recipe_details (
        recipe_id INTEGER PRIMARY KEY REFERENCES recipes(id),
        calories  INTEGER NOT NULL DEFAULT 0,
        protein   TEXT    NOT NULL DEFAULT '0g',
        carbs     TEXT    NOT NULL DEFAULT '0g',
        fat       TEXT    NOT NULL DEFAULT '0g',
        steps     TEXT    NOT NULL DEFAULT '[]',
        tips      TEXT    NOT NULL DEFAULT '[]',
        ingredients TEXT  NOT NULL DEFAULT '[]'
    )""")

    # ── favorites ─────────────────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS favorites (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id   INTEGER NOT NULL DEFAULT 1,
        recipe_id INTEGER NOT NULL REFERENCES recipes(id),
        UNIQUE(user_id, recipe_id)
    )""")

    # ── nutrition_log ─────────────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS nutrition_log (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id  INTEGER NOT NULL DEFAULT 1,
        log_date TEXT    NOT NULL,
        meal_type TEXT   NOT NULL DEFAULT 'Lunch',
        name     TEXT    NOT NULL DEFAULT '',
        calories INTEGER NOT NULL DEFAULT 0,
        protein  INTEGER NOT NULL DEFAULT 0,
        carbs    INTEGER NOT NULL DEFAULT 0,
        fat      INTEGER NOT NULL DEFAULT 0,
        ts       INTEGER NOT NULL DEFAULT 0
    )""")

    # ── meal_plan ─────────────────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS meal_plan (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id   INTEGER NOT NULL DEFAULT 1,
        week      TEXT    NOT NULL DEFAULT '0',
        day       TEXT    NOT NULL,
        meal_type TEXT    NOT NULL,
        name      TEXT    NOT NULL,
        cals      INTEGER NOT NULL DEFAULT 0,
        emoji     TEXT    NOT NULL DEFAULT '🍽️',
        UNIQUE(user_id, week, day, meal_type)
    )""")

    # ── goals ─────────────────────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS goals (
        user_id  INTEGER PRIMARY KEY DEFAULT 1,
        cal      INTEGER NOT NULL DEFAULT 2000,
        protein  INTEGER NOT NULL DEFAULT 150,
        carbs    INTEGER NOT NULL DEFAULT 200,
        fat      INTEGER NOT NULL DEFAULT 65
    )""")

    conn.commit()
    _seed(conn)
    conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# AUTH  (Garnet — UC-01 / Keerthan — UC-03/04)
# ══════════════════════════════════════════════════════════════════════════════

def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(display_name, username, email, password) -> dict:
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (display_name,username,email,password_hash) VALUES (?,?,?,?)",
            (display_name, username, email, _hash(password))
        )
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        # seed goals for new user
        conn.execute("INSERT OR IGNORE INTO goals (user_id) VALUES (?)", (row["id"],))
        conn.commit()
        return dict(row)
    except sqlite3.IntegrityError as e:
        raise ValueError(str(e))
    finally:
        conn.close()

def login_user(username, password):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM users WHERE (username=? OR email=?) AND password_hash=?",
        (username, username, _hash(password))
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def fetch_user(user_id=1): 
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def update_user(user_id, fields: dict) -> dict:
    allowed = {"display_name","username","email","weight","height","goal","dietary_prefs"}
    updates = {k:v for k,v in fields.items() if k in allowed}
    if not updates: raise ValueError("No valid fields")
    conn = get_db()
    set_clause = ", ".join(f"{k}=?" for k in updates)
    conn.execute(f"UPDATE users SET {set_clause} WHERE id=?", [*updates.values(), user_id])
    conn.commit()
    row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return dict(row)

def update_password(user_id, new_password):
    conn = get_db()
    conn.execute("UPDATE users SET password_hash=? WHERE id=?", (_hash(new_password), user_id))
    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# RECIPES  (Garnet — UC-01/02)
# ══════════════════════════════════════════════════════════════════════════════

def fetch_recipes(active_tags, page, per_page) -> dict:
    conn = get_db()
    rows = conn.execute("SELECT * FROM recipes ORDER BY position ASC").fetchall()
    conn.close()
    recipes = [_recipe_dict(r) for r in rows]
    if active_tags:
        recipes = [r for r in recipes if all(t in r["tags"] for t in active_tags)]
    total = len(recipes)
    total_pages = max(1, -(-total // per_page))
    page = max(1, min(page, total_pages))
    return {"recipes": recipes[(page-1)*per_page : page*per_page], "total": total,
            "page": page, "per_page": per_page, "total_pages": total_pages}

def fetch_recipe_by_id(recipe_id): 
    conn = get_db()
    row = conn.execute("SELECT * FROM recipes WHERE id=?", (recipe_id,)).fetchone()
    conn.close()
    return _recipe_dict(row) if row else None

def swap_positions(recipe_id, direction) -> list:
    conn = get_db()
    c = conn.cursor()
    row = c.execute("SELECT id,position FROM recipes WHERE id=?", (recipe_id,)).fetchone()
    if not row: conn.close(); raise ValueError("Not found")
    pos = row["position"]
    neighbor = c.execute(
        f"SELECT id,position FROM recipes WHERE position {'<' if direction=='up' else '>'} ? ORDER BY position {'DESC' if direction=='up' else 'ASC'} LIMIT 1",
        (pos,)
    ).fetchone()
    if not neighbor: conn.close(); raise ValueError("Already at boundary")
    c.execute("UPDATE recipes SET position=? WHERE id=?", (neighbor["position"], recipe_id))
    c.execute("UPDATE recipes SET position=? WHERE id=?", (pos, neighbor["id"]))
    conn.commit()
    rows = conn.execute("SELECT * FROM recipes ORDER BY position").fetchall()
    conn.close()
    return [_recipe_dict(r) for r in rows]

def _recipe_dict(row) -> dict:
    d = dict(row)
    d["tags"] = [t.strip() for t in d.get("tags","").split(",") if t.strip()]
    return d


# ══════════════════════════════════════════════════════════════════════════════
# RECIPE DETAILS  (Sai — UC-07/08)
# ══════════════════════════════════════════════════════════════════════════════

def fetch_details(recipe_id): 
    conn = get_db()
    row = conn.execute("""
        SELECT rd.*, r.name, r.emoji, r.tags
        FROM recipe_details rd JOIN recipes r ON rd.recipe_id=r.id
        WHERE rd.recipe_id=?""", (recipe_id,)).fetchone()
    conn.close()
    if not row: return None
    d = dict(row)
    d["tags"]        = [t.strip() for t in d.get("tags","").split(",") if t.strip()]
    d["steps"]       = json.loads(d.get("steps","[]"))
    d["tips"]        = json.loads(d.get("tips","[]"))
    d["ingredients"] = json.loads(d.get("ingredients","[]"))
    return d

def fetch_all_with_details() -> list:
    conn = get_db()
    rows = conn.execute("""
        SELECT r.id,r.name,r.emoji,r.tags,r.position,
               rd.calories,rd.protein,rd.carbs,rd.fat,rd.steps,rd.tips,rd.ingredients
        FROM recipes r JOIN recipe_details rd ON r.id=rd.recipe_id
        ORDER BY r.position""").fetchall()
    conn.close()
    result = []
    for row in rows:
        d = dict(row)
        d["tags"]        = [t.strip() for t in d.get("tags","").split(",") if t.strip()]
        d["steps"]       = json.loads(d.get("steps","[]"))
        d["tips"]        = json.loads(d.get("tips","[]"))
        d["ingredients"] = json.loads(d.get("ingredients","[]"))
        result.append(d)
    return result


# ══════════════════════════════════════════════════════════════════════════════
# FAVORITES  (Roshini — UC-09 Favorites Management)
# ══════════════════════════════════════════════════════════════════════════════

def fetch_favorites(user_id=1) -> list:
    conn = get_db()
    rows = conn.execute("""
        SELECT r.id,r.name,r.emoji,r.tags FROM favorites f
        JOIN recipes r ON f.recipe_id=r.id WHERE f.user_id=? ORDER BY f.id""", (user_id,)).fetchall()
    conn.close()
    return [_recipe_dict(r) for r in rows]

def add_favorite(user_id, recipe_id) -> list:
    conn = get_db()
    if not conn.execute("SELECT id FROM recipes WHERE id=?", (recipe_id,)).fetchone():
        conn.close(); raise ValueError("Recipe not found")
    conn.execute("INSERT OR IGNORE INTO favorites (user_id,recipe_id) VALUES (?,?)", (user_id, recipe_id))
    conn.commit(); conn.close()
    return fetch_favorites(user_id)

def remove_favorite(user_id, recipe_id) -> list:
    conn = get_db()
    conn.execute("DELETE FROM favorites WHERE user_id=? AND recipe_id=?", (user_id, recipe_id))
    conn.commit(); conn.close()
    return fetch_favorites(user_id)


# ══════════════════════════════════════════════════════════════════════════════
# NUTRITION LOG  (Roshini — UC-10 Nutrition Tracking)
# ══════════════════════════════════════════════════════════════════════════════

def log_meal_entry(user_id, log_date, meal_type, name, calories, protein, carbs, fat, ts) -> list:
    conn = get_db()
    conn.execute(
        "INSERT INTO nutrition_log (user_id,log_date,meal_type,name,calories,protein,carbs,fat,ts) VALUES (?,?,?,?,?,?,?,?,?)",
        (user_id, log_date, meal_type, name, calories, protein, carbs, fat, ts)
    )
    conn.commit(); conn.close()
    return fetch_day_log(user_id, log_date)

def fetch_day_log(user_id, log_date) -> list:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM nutrition_log WHERE user_id=? AND log_date=? ORDER BY ts",
        (user_id, log_date)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_log_entry(entry_id, user_id) -> bool:
    conn = get_db()
    conn.execute("DELETE FROM nutrition_log WHERE id=? AND user_id=?", (entry_id, user_id))
    conn.commit(); conn.close()
    return True

def fetch_week_nutrition(user_id, dates: list) -> list:
    conn = get_db()
    result = []
    for d in dates:
        rows = conn.execute(
            "SELECT SUM(calories) cal, SUM(protein) pro, SUM(carbs) carb, SUM(fat) fat FROM nutrition_log WHERE user_id=? AND log_date=?",
            (user_id, d)
        ).fetchone()
        result.append({"date": d, "cal": rows["cal"] or 0, "pro": rows["pro"] or 0,
                        "carb": rows["carb"] or 0, "fat": rows["fat"] or 0})
    conn.close()
    return result


# ══════════════════════════════════════════════════════════════════════════════
# GOALS  (shared)
# ══════════════════════════════════════════════════════════════════════════════

def fetch_goals(user_id=1) -> dict:
    conn = get_db()
    row = conn.execute("SELECT * FROM goals WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    if row: return dict(row)
    return {"user_id": user_id, "cal": 2000, "protein": 150, "carbs": 200, "fat": 65}

def save_goals(user_id, cal, protein, carbs, fat) -> dict:
    conn = get_db()
    conn.execute("""INSERT INTO goals (user_id,cal,protein,carbs,fat) VALUES (?,?,?,?,?)
        ON CONFLICT(user_id) DO UPDATE SET cal=excluded.cal, protein=excluded.protein,
        carbs=excluded.carbs, fat=excluded.fat""", (user_id, cal, protein, carbs, fat))
    conn.commit(); conn.close()
    return fetch_goals(user_id)


# ══════════════════════════════════════════════════════════════════════════════
# MEAL PLAN  (John — UC-05/06)
# ══════════════════════════════════════════════════════════════════════════════

def fetch_week_plan(user_id, week) -> dict:
    conn = get_db()
    rows = conn.execute(
        "SELECT day,meal_type,name,cals,emoji FROM meal_plan WHERE user_id=? AND week=?",
        (user_id, str(week))
    ).fetchall()
    conn.close()
    plan = {}
    for row in rows:
        plan.setdefault(row["day"], {})[row["meal_type"]] = {
            "name": row["name"], "cals": row["cals"], "emoji": row["emoji"]
        }
    return plan

def upsert_meal(user_id, week, day, meal_type, name, cals, emoji) -> dict:
    conn = get_db()
    conn.execute("""INSERT INTO meal_plan (user_id,week,day,meal_type,name,cals,emoji) VALUES (?,?,?,?,?,?,?)
        ON CONFLICT(user_id,week,day,meal_type) DO UPDATE SET name=excluded.name,cals=excluded.cals,emoji=excluded.emoji""",
        (user_id, str(week), day, meal_type, name, cals, emoji))
    conn.commit(); conn.close()
    return fetch_week_plan(user_id, week)

def delete_meal_slot(user_id, week, day, meal_type) -> dict:
    conn = get_db()
    conn.execute("DELETE FROM meal_plan WHERE user_id=? AND week=? AND day=? AND meal_type=?",
                 (user_id, str(week), day, meal_type))
    conn.commit(); conn.close()
    return fetch_week_plan(user_id, week)


# ══════════════════════════════════════════════════════════════════════════════
# SEED DATA
# ══════════════════════════════════════════════════════════════════════════════

SEED_RECIPES = [
    (1,"Chipotle Maple Brussels Sprouts","🥦","vegetarian,vegan,dairy-free,gluten-free,no-fish,no-shellfish,no-sesame-oil,no-soybeans,no-wheat,no-eggs,no-nuts"),
    (2,"Beef Tacos","🌮","dairy-free,gluten-free,no-fish,no-shellfish,no-sesame-oil,no-soybeans,no-wheat,no-eggs,no-nuts"),
    (3,"Steak","🥩","gluten-free,no-fish,no-shellfish,no-sesame-oil,no-soybeans,no-eggs,no-nuts"),
    (4,"Sheet Pan Potatoes O'Brien","🥔","vegetarian,vegan,dairy-free,gluten-free,no-fish,no-shellfish,no-sesame-oil,no-soybeans,no-wheat,no-eggs,no-nuts"),
    (5,"Sheet Pan Veggie Buddha Bowl","🥗","vegetarian,vegan,dairy-free,gluten-free,no-fish,no-shellfish,no-sesame-oil,no-soybeans,no-wheat,no-eggs,no-nuts"),
    (6,"Lemon Garlic Pasta Primavera","🍜","vegetarian,no-fish,no-shellfish,no-sesame-oil,no-soybeans,no-eggs,no-nuts"),
    (7,"Chickpea Sweet Potato Curry","🍛","vegetarian,vegan,dairy-free,gluten-free,no-fish,no-shellfish,no-sesame-oil,no-soybeans,no-wheat,no-eggs,no-nuts"),
    (8,"Zucchini Noodle Stir Fry","🥒","vegetarian,vegan,dairy-free,gluten-free,no-fish,no-shellfish,no-wheat,no-eggs,no-nuts"),
    (9,"Spinach & Feta Stuffed Peppers","🍅","vegetarian,gluten-free,no-fish,no-shellfish,no-sesame-oil,no-soybeans,no-wheat,no-eggs,no-nuts"),
    (10,"Sweet Potato Black Bean Bowls","🫑","vegetarian,vegan,dairy-free,gluten-free,no-fish,no-shellfish,no-sesame-oil,no-soybeans,no-wheat,no-eggs,no-nuts"),
    (11,"Lentil Vegetable Soup","🧄","vegetarian,vegan,dairy-free,gluten-free,no-fish,no-shellfish,no-sesame-oil,no-soybeans,no-wheat,no-eggs,no-nuts"),
    (12,"Avocado Toast Platter","🥑","vegetarian,vegan,dairy-free,no-fish,no-shellfish,no-sesame-oil,no-soybeans,no-eggs,no-nuts"),
]

SEED_DETAILS = [
    (1,120,"4g","18g","5g",json.dumps(["Preheat oven to 220°C.","Halve Brussels sprouts and toss with olive oil, maple syrup, chipotle powder, salt & pepper.","Spread cut-side down on a sheet pan.","Roast 20–25 min until caramelised and crispy."]),json.dumps(["Don't crowd the pan.","Add lime juice at the end."]),json.dumps(["Brussels sprouts","Olive oil","Maple syrup","Chipotle powder","Garlic powder"])),
    (2,310,"22g","24g","13g",json.dumps(["Season beef with cumin, chili powder, garlic powder.","Cook in skillet 8 min until browned.","Warm corn tortillas.","Fill with beef, lettuce, tomato, salsa.","Top with lime and cilantro."]),json.dumps(["Use 80/20 ground beef.","Corn tortillas keep it gluten-free."]),json.dumps(["Ground beef","Corn tortillas","Lettuce","Tomato","Salsa","Lime","Cilantro"])),
    (3,280,"34g","0g","16g",json.dumps(["Bring steak to room temp 30 min before cooking.","Season with salt and pepper.","Heat cast-iron pan until smoking hot.","Sear 3–4 min per side for medium-rare.","Rest 5–10 min before slicing."]),json.dumps(["Dry-brine overnight.","57°C = medium-rare."]),json.dumps(["Steak","Salt","Pepper","High-smoke-point oil","Butter","Garlic","Thyme"])),
    (4,180,"3g","32g","5g",json.dumps(["Dice potatoes, bell peppers, and onion.","Toss with olive oil, smoked paprika, garlic powder.","Spread on sheet pan.","Roast at 220°C for 30–35 min, flipping halfway.","Garnish with parsley."]),json.dumps(["Parboil 5 min for extra crispiness."]),json.dumps(["Potatoes","Red bell pepper","Green bell pepper","Onion","Olive oil","Smoked paprika"])),
    (5,350,"12g","48g","14g",json.dumps(["Chop broccoli, chickpeas, zucchini, cherry tomatoes.","Toss with olive oil, salt, spice.","Roast at 200°C for 25 min.","Serve over cooked quinoa or brown rice.","Drizzle with tahini-lemon dressing."]),json.dumps(["Roast chickpeas separately so they stay crispy."]),json.dumps(["Broccoli","Chickpeas","Zucchini","Cherry tomatoes","Quinoa","Tahini","Lemon"])),
    (6,420,"14g","62g","13g",json.dumps(["Cook pasta until al dente; reserve 1 cup pasta water.","Sauté garlic in olive oil.","Add seasonal vegetables and cook 5 min.","Toss with lemon zest, juice, and parmesan.","Finish with fresh basil."]),json.dumps(["Use pasta water to build a silky sauce."]),json.dumps(["Pasta","Garlic","Olive oil","Seasonal vegetables","Lemon","Parmesan","Basil"])),
    (7,390,"13g","58g","12g",json.dumps(["Dice sweet potatoes and drain chickpeas.","Sauté onion then add garlic and ginger.","Stir in curry powder and cook 1 min.","Add sweet potatoes, chickpeas, and coconut milk. Simmer 20 min.","Serve with rice or naan."]),json.dumps(["Stir in spinach at the end."]),json.dumps(["Sweet potatoes","Chickpeas","Onion","Garlic","Ginger","Curry powder","Coconut milk"])),
    (8,200,"8g","16g","12g",json.dumps(["Spiralise 3 medium zucchinis.","Stir-fry garlic, ginger, and veggies in sesame oil 3 min.","Add zucchini noodles and toss 2 min.","Add soy sauce, rice vinegar, chilli flakes.","Top with sesame seeds and green onions."]),json.dumps(["Salt zucchini and let sit 10 min, then pat dry."]),json.dumps(["Zucchini","Sesame oil","Garlic","Ginger","Soy sauce","Rice vinegar","Sesame seeds"])),
    (9,260,"11g","22g","14g",json.dumps(["Preheat oven to 190°C. Halve and deseed 4 bell peppers.","Sauté spinach with garlic until wilted.","Mix with crumbled feta, cooked rice, salt & pepper.","Fill peppers and bake covered 30 min.","Uncover for last 10 min."]),json.dumps(["Swap rice for quinoa for more protein."]),json.dumps(["Bell peppers","Spinach","Feta cheese","Rice","Garlic","Olive oil"])),
    (10,370,"14g","56g","10g",json.dumps(["Cube sweet potatoes and roast with oil, cumin, smoked paprika 25 min.","Warm black beans with garlic, cumin, chilli.","Cook rice or quinoa.","Assemble: grain, sweet potato, beans, avocado, salsa.","Finish with lime and cilantro."]),json.dumps(["Meal-prep for 4 days."]),json.dumps(["Sweet potatoes","Black beans","Rice","Avocado","Salsa","Lime","Cilantro"])),
    (11,290,"16g","44g","5g",json.dumps(["Dice onion, carrots, celery. Sauté in olive oil 5 min.","Add garlic, cumin, coriander, cook 1 min.","Add red lentils, diced tomatoes, and vegetable broth.","Simmer 25–30 min until lentils are soft.","Season with salt, pepper, and lemon juice."]),json.dumps(["Blend half for a creamy-chunky texture."]),json.dumps(["Red lentils","Onion","Carrots","Celery","Garlic","Cumin","Vegetable broth","Diced tomatoes"])),
    (12,310,"8g","28g","20g",json.dumps(["Toast thick slices of sourdough.","Mash avocados with lemon juice, salt, pepper, chilli flakes.","Spread generously over toast.","Top with cherry tomatoes, microgreens, everything bagel seasoning.","Serve immediately."]),json.dumps(["Don't skip the lemon juice."]),json.dumps(["Sourdough bread","Avocados","Lemon","Cherry tomatoes","Microgreens","Everything bagel seasoning"])),
]

def _seed(conn):
    c = conn.cursor()
    if c.execute("SELECT COUNT(*) FROM recipes").fetchone()[0] == 0:
        c.executemany("INSERT INTO recipes (id,name,emoji,tags,position) VALUES (?,?,?,?,?)",
                      [(r[0],r[1],r[2],r[3],i) for i,r in enumerate(SEED_RECIPES)])
    if c.execute("SELECT COUNT(*) FROM recipe_details").fetchone()[0] == 0:
        c.executemany("INSERT INTO recipe_details (recipe_id,calories,protein,carbs,fat,steps,tips,ingredients) VALUES (?,?,?,?,?,?,?,?)",
                      SEED_DETAILS)
    if c.execute("SELECT COUNT(*) FROM goals").fetchone()[0] == 0:
        c.execute("INSERT INTO goals (user_id,cal,protein,carbs,fat) VALUES (1,2000,150,200,65)")
    conn.commit()
