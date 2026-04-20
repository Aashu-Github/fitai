# ─────────────────────────────────────────────────────────────────────────────
# routes.py  —  HTTP Routes Layer (all Flask endpoints in one file)
# Architecture:  routes.py → services.py → repository.py → fitai.db (SQLite)
# ─────────────────────────────────────────────────────────────────────────────
 
import os, json
import urllib.request, urllib.error
from flask import Blueprint, request, jsonify, session
import services
 
all_routes = Blueprint("all_routes", __name__)
 
# ─────────────────────────────────────────────────────────────────────────────
# PASTE YOUR GROQ API KEY BELOW (between the quotes)  ← FREE, no credit card
# Get one at: https://console.groq.com  → API Keys → Create API Key
# ─────────────────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")
 
 
def current_user_id():
    """Return the logged-in user id from the session, or 1 as guest fallback."""
    return session.get("user_id", 1)
 
 
# ══════════════════════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════════════════════
 
@all_routes.route("/api/signup", methods=["POST"])
def signup():
    d = request.get_json(force=True)
    try:
        user = services.signup(d.get("display_name",""), d.get("username",""),
                               d.get("email",""), d.get("password",""), d.get("confirm_password",""))
        session["user_id"] = user["id"]
        return jsonify({"message": "Account created!", "user": user})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
 
 
@all_routes.route("/api/login", methods=["POST"])
def login():
    d = request.get_json(force=True)
    try:
        user = services.login(d.get("username",""), d.get("password",""))
        session["user_id"] = user["id"]
        return jsonify({"message": "Logged in!", "user": user})
    except ValueError as e:
        return jsonify({"error": str(e)}), 401
 
 
@all_routes.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})
 
 
@all_routes.route("/api/me", methods=["GET"])
def me():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"error": "Not logged in"}), 401
    try:
        return jsonify(services.get_profile(uid))
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
 
 
# ══════════════════════════════════════════════════════════════════════════════
# USER PROFILE  (Keerthan UC-03/04)
# ══════════════════════════════════════════════════════════════════════════════
 
@all_routes.route("/api/profile", methods=["GET"])
def get_profile():
    try:
        return jsonify(services.get_profile(current_user_id()))
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
 
 
@all_routes.route("/api/profile", methods=["POST"])
def update_profile():
    try:
        updated = services.update_profile(current_user_id(), request.get_json(force=True))
        return jsonify({"message": "Profile updated!", "user": updated})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
 
 
# ══════════════════════════════════════════════════════════════════════════════
# RECIPES  (Garnet UC-01/02)
# ══════════════════════════════════════════════════════════════════════════════
 
@all_routes.route("/api/recipes", methods=["GET"])
def get_recipes():
    return jsonify(services.get_recipes(
        request.args.get("tags",""),
        int(request.args.get("page",1)),
        int(request.args.get("per_page",12))
    ))
 
 
@all_routes.route("/api/tags", methods=["GET"])
def get_tags():
    return jsonify({"tags": services.get_tags()})
 
 
@all_routes.route("/api/recipes/<int:recipe_id>/move", methods=["POST"])
def move_recipe(recipe_id):
    try:
        return jsonify(services.reorder(recipe_id, request.get_json(force=True).get("direction","")))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
 
 
@all_routes.route("/api/recipes/<int:recipe_id>/details", methods=["GET"])
def get_details(recipe_id):
    try:
        return jsonify(services.get_details(recipe_id))
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
 
 
@all_routes.route("/api/recommendations", methods=["GET"])
def get_recommendations():
    return jsonify(services.get_recommendations(
        request.args.get("goal",""),
        request.args.get("tags",""),
        int(request.args.get("limit",5)),
        current_user_id()
    ))
 
 
# ══════════════════════════════════════════════════════════════════════════════
# FAVORITES  (Roshini UC-09)
# ══════════════════════════════════════════════════════════════════════════════
 
@all_routes.route("/api/favorites", methods=["GET"])
def get_favorites():
    return jsonify({"favorites": services.list_favorites(current_user_id())})
 
 
@all_routes.route("/api/favorites/<int:recipe_id>", methods=["POST"])
def add_favorite(recipe_id):
    try:
        return jsonify(services.add_favorite(current_user_id(), recipe_id))
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
 
 
@all_routes.route("/api/favorites/<int:recipe_id>", methods=["DELETE"])
def remove_favorite(recipe_id):
    return jsonify(services.remove_favorite(current_user_id(), recipe_id))
 
 
# ══════════════════════════════════════════════════════════════════════════════
# NUTRITION LOG  (Roshini UC-10)
# ══════════════════════════════════════════════════════════════════════════════
 
@all_routes.route("/api/nutrition/log", methods=["POST"])
def log_meal():
    d = request.get_json(force=True)
    try:
        entries = services.log_meal(
            current_user_id(), d.get("log_date",""), d.get("meal_type","Lunch"),
            d.get("name",""), int(d.get("calories",0)), int(d.get("protein",0)),
            int(d.get("carbs",0)), int(d.get("fat",0)), int(d.get("ts",0))
        )
        return jsonify({"message": "Meal logged", "entries": entries})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
 
 
@all_routes.route("/api/nutrition/day", methods=["GET"])
def get_day():
    date = request.args.get("date","")
    return jsonify({"entries": services.get_day_log(current_user_id(), date)})
 
 
@all_routes.route("/api/nutrition/log/<int:entry_id>", methods=["DELETE"])
def delete_log(entry_id):
    services.delete_log(entry_id, current_user_id())
    return jsonify({"message": "Deleted"})
 
 
@all_routes.route("/api/nutrition/week", methods=["GET"])
def get_week():
    dates = request.args.get("dates","").split(",")
    return jsonify({"week": services.get_week_nutrition(current_user_id(), [d for d in dates if d])})
 
 
# ══════════════════════════════════════════════════════════════════════════════
# GOALS
# ══════════════════════════════════════════════════════════════════════════════
 
@all_routes.route("/api/goals", methods=["GET"])
def get_goals():
    return jsonify(services.get_goals(current_user_id()))
 
 
@all_routes.route("/api/goals", methods=["POST"])
def set_goals():
    d = request.get_json(force=True)
    return jsonify(services.set_goals(
        current_user_id(),
        int(d.get("cal",2000)), int(d.get("protein",150)),
        int(d.get("carbs",200)), int(d.get("fat",65))
    ))
 
 
# ══════════════════════════════════════════════════════════════════════════════
# MEAL PLAN  (John UC-05/06)
# ══════════════════════════════════════════════════════════════════════════════
 
@all_routes.route("/api/meal-plan", methods=["GET"])
def get_meal_plan():
    return jsonify(services.get_meal_plan(current_user_id(), request.args.get("week","0")))
 
 
@all_routes.route("/api/meal-plan", methods=["POST"])
def save_meal():
    d = request.get_json(force=True)
    try:
        return jsonify(services.save_meal(
            current_user_id(), d.get("week","0"),
            d.get("day",""), d.get("meal",""), d.get("entry",{})
        ))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
 
 
@all_routes.route("/api/meal-plan", methods=["DELETE"])
def delete_meal():
    d = request.get_json(force=True)
    return jsonify(services.delete_meal(
        current_user_id(), d.get("week","0"), d.get("day",""), d.get("meal","")
    ))
 
 
# ══════════════════════════════════════════════════════════════════════════════
# AI PROXY  — server-side Groq call (free tier, no credit card needed)
# ══════════════════════════════════════════════════════════════════════════════
 
@all_routes.route("/api/ai/recommend", methods=["POST"])
def ai_recommend():
    """
    Receives prompt from frontend, calls Groq API server-side (free tier).
    Requires GROQ_API_KEY — get one free at https://console.groq.com
    """
    if not GROQ_API_KEY or GROQ_API_KEY == "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":
        return jsonify({"error": "Groq API key not set. Open routes.py and paste your key into GROQ_API_KEY."}), 500
 
    d            = request.get_json(force=True)
    ingredients  = d.get("ingredients", "").strip()
    preferences  = d.get("preferences", "").strip()
    recipe_names = d.get("recipe_names", [])
 
    if not ingredients:
        return jsonify({"error": "No ingredients provided"}), 400
 
    prompt = f"""You are a recipe assistant. User has ingredients: "{ingredients}".
{f'Their preferences: "{preferences}".' if preferences else ''}
 
From this list of available recipes, recommend the 3 best matches:
{', '.join(recipe_names)}
 
You may also suggest 1-2 new creative recipes using these ingredients.
 
Respond ONLY with valid JSON (no markdown, no backticks, no preamble):
{{"recommendations":[{{"name":"Recipe Name","emoji":"🍳","inLibrary":true,"reason":"One sentence why this fits."}}]}}"""
 
    payload = json.dumps({
        "model": "llama3-8b-8192",
        "max_tokens": 800,
        "messages": [{"role": "user", "content": prompt}]
    }).encode("utf-8")
 
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_API_KEY}"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        raw    = result["choices"][0]["message"]["content"]
        parsed = json.loads(raw.strip().replace("```json", "").replace("```", "").strip())
        return jsonify(parsed)
    except urllib.error.HTTPError as e:
        return jsonify({"error": f"Groq API error {e.code}: {e.read().decode()}"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500
 
 
# ══════════════════════════════════════════════════════════════════════════════
# FREE RECIPE API — TheMealDB (completely free, no key needed)
# ══════════════════════════════════════════════════════════════════════════════
 
@all_routes.route("/api/search-meals", methods=["GET"])
def search_meals():
    """
    Proxy to TheMealDB free API. No API key required, never expires.
    Query params:  q (search term)  or  i (ingredient)  or  c (category)
    """
    q   = request.args.get("q","")
    ing = request.args.get("i","")
    cat = request.args.get("c","")
 
    if ing:
        url = f"https://www.themealdb.com/api/json/v1/1/filter.php?i={urllib.parse.quote(ing)}"
    elif cat:
        url = f"https://www.themealdb.com/api/json/v1/1/filter.php?c={urllib.parse.quote(cat)}"
    else:
        url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={urllib.parse.quote(q)}"
 
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
 
 
@all_routes.route("/api/meal-detail", methods=["GET"])
def meal_detail():
    """Get full recipe detail from TheMealDB by meal id."""
    meal_id = request.args.get("id","")
    try:
        url = f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={meal_id}"
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
 
 
import urllib.parse  # make sure this is available
 
