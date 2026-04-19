# ─────────────────────────────────────────────────────────────────────────────
# repository/database.py
# SHARED — Database Layer
#
# Sets up the SQLite database and exposes a get_db() helper used by every
# repository module. This replaces the old in-memory lists with a real DB.
#
# Tables created here:
#   recipes          — master recipe list (Garnet)
#   recipe_details   — nutrition + steps + tips (Sai)
#   users            — user profile (Keerthan)
#   favorites        — bookmarked recipes per user (Roshini)
#   nutrition_log    — daily macro totals (Roshini)
#   meal_plan        — weekly meal slots (John)
# ─────────────────────────────────────────────────────────────────────────────

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "fitai.db")


def get_db() -> sqlite3.Connection:
    """Open and return a SQLite connection with row_factory set to Row."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables and seed initial data if the DB is empty."""
    conn = get_db()
    c = conn.cursor()

    # ── recipes ──────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            id       INTEGER PRIMARY KEY,
            name     TEXT    NOT NULL,
            emoji    TEXT    NOT NULL DEFAULT '🍽️',
            color    TEXT    NOT NULL DEFAULT 'r1',
            tags     TEXT    NOT NULL DEFAULT '',   -- comma-separated
            position INTEGER NOT NULL DEFAULT 0     -- for UC-02 ordering
        )
    """)

    # ── recipe_details ────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS recipe_details (
            recipe_id INTEGER PRIMARY KEY REFERENCES recipes(id),
            calories  INTEGER NOT NULL DEFAULT 0,
            protein   TEXT    NOT NULL DEFAULT '0g',
            carbs     TEXT    NOT NULL DEFAULT '0g',
            fat       TEXT    NOT NULL DEFAULT '0g',
            steps     TEXT    NOT NULL DEFAULT '[]',  -- JSON array
            tips      TEXT    NOT NULL DEFAULT '[]'   -- JSON array
        )
    """)

    # ── users ─────────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id     INTEGER PRIMARY KEY DEFAULT 1,
            weight TEXT NOT NULL DEFAULT '185 lbs',
            height TEXT NOT NULL DEFAULT '6''0"',
            goal   TEXT NOT NULL DEFAULT 'Maintain Muscle & Lose Body Fat'
        )
    """)

    # ── favorites ─────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER NOT NULL REFERENCES recipes(id),
            UNIQUE(recipe_id)
        )
    """)

    # ── nutrition_log ─────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS nutrition_log (
            id       INTEGER PRIMARY KEY DEFAULT 1,
            calories INTEGER NOT NULL DEFAULT 0,
            protein  INTEGER NOT NULL DEFAULT 0,
            carbs    INTEGER NOT NULL DEFAULT 0
        )
    """)

    # ── meal_plan ─────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS meal_plan (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            week      TEXT    NOT NULL DEFAULT '0',
            day       TEXT    NOT NULL,
            meal_type TEXT    NOT NULL,
            name      TEXT    NOT NULL,
            cals      INTEGER NOT NULL DEFAULT 0,
            emoji     TEXT    NOT NULL DEFAULT '🍽️',
            UNIQUE(week, day, meal_type)
        )
    """)

    conn.commit()
    _seed(conn)
    conn.close()


# ─── Seed data ────────────────────────────────────────────────────────────────
import json

SEED_RECIPES = [
    (1,  "Chipotle Maple Brussels Sprouts", "🥦", "r1", "vegetarian,vegan,dairy-free,gluten-free,no-fish,no-shellfish,no-sesame-oil,no-soybeans,no-wheat,no-eggs,no-nuts"),
    (2,  "Beef Tacos",                      "🌮", "r3", "dairy-free,gluten-free,no-fish,no-shellfish,no-sesame-oil,no-soybeans,no-wheat,no-eggs,no-nuts"),
    (3,  "Steak",                           "🥩", "r1", "no-fish,no-shellfish,no-sesame-oil,no-soybeans,no-eggs,no-nuts"),
    (4,  "Sheet Pan Potatoes O'Brien",      "🥔", "r2", "vegetarian,vegan,dairy-free,gluten-free,no-fish,no-shellfish,no-sesame-oil,no-soybeans,no-wheat,no-eggs,no-nuts"),
    (5,  "Sheet Pan Veggie Buddha Bowl",    "🥗", "r3", "vegetarian,vegan,dairy-free,gluten-free,no-fish,no-shellfish,no-sesame-oil,no-soybeans,no-wheat,no-eggs,no-nuts"),
    (6,  "Lemon Garlic Pasta Primavera",    "🍜", "r1", "vegetarian,no-fish,no-shellfish,no-sesame-oil,no-soybeans,no-eggs,no-nuts"),
    (7,  "Chickpea Sweet Potato Curry",     "🍛", "r2", "vegetarian,vegan,dairy-free,gluten-free,no-fish,no-shellfish,no-sesame-oil,no-soybeans,no-wheat,no-eggs,no-nuts"),
    (8,  "Zucchini Noodle Stir Fry",        "🥒", "r2", "vegetarian,vegan,dairy-free,gluten-free,no-fish,no-shellfish,no-wheat,no-eggs,no-nuts"),
    (9,  "Spinach & Feta Stuffed Peppers",  "🍅", "r3", "vegetarian,gluten-free,no-fish,no-shellfish,no-sesame-oil,no-soybeans,no-wheat,no-eggs,no-nuts"),
    (10, "Sweet Potato Black Bean Bowls",   "🫑", "r1", "vegetarian,vegan,dairy-free,gluten-free,no-fish,no-shellfish,no-sesame-oil,no-soybeans,no-wheat,no-eggs,no-nuts"),
    (11, "Lentil Vegetable Soup",           "🧄", "r2", "vegetarian,vegan,dairy-free,gluten-free,no-fish,no-shellfish,no-sesame-oil,no-soybeans,no-wheat,no-eggs,no-nuts"),
    (12, "Avocado Toast Platter",           "🥑", "r3", "vegetarian,vegan,dairy-free,no-fish,no-shellfish,no-sesame-oil,no-soybeans,no-eggs,no-nuts"),
]

SEED_DETAILS = [
    (1,  120, "4g",  "18g", "5g",
     json.dumps(["Preheat oven to 220°C (425°F).", "Halve 450g Brussels sprouts and toss with olive oil, maple syrup, chipotle powder, garlic powder, salt & pepper.", "Spread cut-side down on a sheet pan.", "Roast 20–25 min until caramelised and crispy.", "Drizzle with a touch more maple syrup before serving."]),
     json.dumps(["Don't crowd the pan — use two sheet pans for max crispiness.", "Add a squeeze of lime juice at the end for brightness.", "Swap chipotle powder for smoked paprika for a milder version."])),
    (2,  310, "22g", "24g", "13g",
     json.dumps(["Season 400g ground beef with cumin, chili powder, garlic powder, salt & pepper.", "Cook in a skillet over medium-high heat until browned, about 8 min.", "Warm corn tortillas in a dry pan.", "Fill with beef, lettuce, diced tomato, and salsa.", "Top with lime juice and fresh cilantro."]),
     json.dumps(["Use 80/20 ground beef for the best flavour.", "Double the batch and freeze the meat.", "Corn tortillas keep it gluten-free."])),
    (3,  280, "34g", "0g",  "16g",
     json.dumps(["Bring steak to room temperature 30 min before cooking.", "Season generously with salt and pepper on both sides.", "Heat a cast-iron pan until smoking hot. Add a high-smoke-point oil.", "Sear 3–4 min per side for medium-rare.", "Rest on a cutting board for 5–10 min before slicing against the grain."]),
     json.dumps(["Dry-brine overnight in the fridge for deeper flavour.", "Baste with butter, garlic, and thyme during the last minute.", "Use a thermometer: 57°C (135°F) = medium-rare."])),
    (4,  180, "3g",  "32g", "5g",
     json.dumps(["Dice 600g potatoes, ½ red bell pepper, ½ green bell pepper, and ½ onion.", "Toss with olive oil, smoked paprika, garlic powder, salt & pepper.", "Spread on a sheet pan in a single layer.", "Roast at 220°C for 30–35 min, flipping halfway.", "Garnish with fresh parsley."]),
     json.dumps(["Parboil potatoes for 5 min before roasting for extra crispiness.", "Add a pinch of cayenne for heat.", "Leftovers make a great breakfast hash with a fried egg on top."])),
    (5,  350, "12g", "48g", "14g",
     json.dumps(["Chop broccoli, chickpeas, zucchini, and cherry tomatoes.", "Toss each with olive oil, salt, and your choice of spice.", "Roast at 200°C for 25 min.", "Serve over cooked quinoa or brown rice.", "Drizzle with tahini-lemon dressing."]),
     json.dumps(["Roast chickpeas separately so they stay crispy.", "Batch cook the grains ahead of time.", "Tahini dressing: 2 tbsp tahini, 1 tbsp lemon juice, 1 tsp maple syrup, water to thin."])),
    (6,  420, "14g", "62g", "13g",
     json.dumps(["Cook 300g pasta until al dente; reserve 1 cup pasta water.", "Sauté 4 cloves minced garlic in olive oil for 1 min.", "Add seasonal vegetables and cook 5 min.", "Add pasta, lemon zest, lemon juice, and parmesan; toss with pasta water.", "Finish with fresh basil."]),
     json.dumps(["Use the pasta water to build a silky sauce.", "Add chilli flakes for heat.", "Any short pasta works: penne, farfalle, rigatoni."])),
    (7,  390, "13g", "58g", "12g",
     json.dumps(["Dice 2 medium sweet potatoes and drain 1 can chickpeas.", "Sauté 1 diced onion in oil until soft, then add garlic and ginger.", "Stir in 2 tbsp curry powder and cook 1 min.", "Add sweet potatoes, chickpeas, and 1 can coconut milk. Simmer 20 min.", "Season with salt and serve with rice or naan."]),
     json.dumps(["Stir in a handful of spinach at the end for extra nutrients.", "Make it spicier with cayenne or fresh chilli.", "Leftovers taste even better the next day."])),
    (8,  200, "8g",  "16g", "12g",
     json.dumps(["Spiralise 3 medium zucchinis into noodles.", "Stir-fry garlic, ginger, and veggies in sesame oil for 3 min.", "Add zucchini noodles and toss for 2 min.", "Add soy sauce, rice vinegar, and chilli flakes.", "Top with sesame seeds and green onions."]),
     json.dumps(["Salt zucchini and let sit 10 min, then pat dry.", "Add tofu or shrimp for extra protein.", "Work quickly over high heat to keep the noodles from going soggy."])),
    (9,  260, "11g", "22g", "14g",
     json.dumps(["Preheat oven to 190°C. Halve and deseed 4 bell peppers.", "Sauté 2 cups spinach with garlic until wilted.", "Mix spinach with crumbled feta, cooked rice, salt & pepper.", "Fill pepper halves and bake covered for 30 min.", "Uncover for last 10 min to brown the tops."]),
     json.dumps(["Pre-roast the pepper shells for 10 min for a softer texture.", "Add sun-dried tomatoes for extra depth.", "Swap rice for quinoa for more protein."])),
    (10, 370, "14g", "56g", "10g",
     json.dumps(["Cube 2 sweet potatoes and roast with oil, cumin, and smoked paprika for 25 min.", "Warm 1 can black beans with garlic, cumin, and a pinch of chilli.", "Cook rice or quinoa.", "Assemble bowls: grain, sweet potato, black beans, avocado, salsa.", "Finish with lime juice and cilantro."]),
     json.dumps(["Meal-prep for 4 days — store components separately.", "Add a poached egg for extra protein.", "Chipotle sauce or Greek yogurt works great as a creamy topping."])),
    (11, 290, "16g", "44g", "5g",
     json.dumps(["Dice 1 onion, 3 carrots, and 3 celery stalks. Sauté in olive oil 5 min.", "Add minced garlic, cumin, coriander, and cook 1 min.", "Add 1 cup red lentils, 1 can diced tomatoes, and 1.2L vegetable broth.", "Simmer 25–30 min until lentils are completely soft.", "Season with salt, pepper, and a squeeze of lemon juice."]),
     json.dumps(["Red lentils break down and thicken the soup.", "Blend half the soup for a creamy-chunky mix.", "Freezes beautifully for up to 3 months."])),
    (12, 310, "8g",  "28g", "20g",
     json.dumps(["Toast thick slices of sourdough or whole grain bread until golden.", "Mash 2 ripe avocados with lemon juice, salt, pepper, and chilli flakes.", "Spread generously over toast slices.", "Top with cherry tomatoes, microgreens, and everything bagel seasoning.", "Serve immediately."]),
     json.dumps(["Ripe avocados should give slightly when pressed.", "Add a soft-boiled egg or smoked salmon for protein.", "Fan out toppings for a beautiful platter presentation."])),
]


def _seed(conn: sqlite3.Connection):
    c = conn.cursor()

    # Only seed if tables are empty
    if c.execute("SELECT COUNT(*) FROM recipes").fetchone()[0] == 0:
        c.executemany(
            "INSERT INTO recipes (id, name, emoji, color, tags, position) VALUES (?,?,?,?,?,?)",
            [(r[0], r[1], r[2], r[3], r[4], i) for i, r in enumerate(SEED_RECIPES)]
        )

    if c.execute("SELECT COUNT(*) FROM recipe_details").fetchone()[0] == 0:
        c.executemany(
            "INSERT INTO recipe_details (recipe_id, calories, protein, carbs, fat, steps, tips) VALUES (?,?,?,?,?,?,?)",
            SEED_DETAILS
        )

    if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        c.execute("INSERT INTO users (id, weight, height, goal) VALUES (1, '185 lbs', '6''0\"', 'Maintain Muscle & Lose Body Fat')")

    if c.execute("SELECT COUNT(*) FROM nutrition_log").fetchone()[0] == 0:
        c.execute("INSERT INTO nutrition_log (id, calories, protein, carbs) VALUES (1, 0, 0, 0)")

    conn.commit()
