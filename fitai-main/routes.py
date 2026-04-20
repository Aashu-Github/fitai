# ─────────────────────────────────────────────────────────────────────────────
# routes.py  —  HTTP Routes Layer (all Flask endpoints in one file)
# Architecture:  routes.py → services.py → repository.py → fitai.db (SQLite)
# ─────────────────────────────────────────────────────────────────────────────

import os, json
import urllib.request, urllib.error
from flask import Blueprint, request, jsonify, session
import services

all_routes = Blueprint("all_routes", __name__)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


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


@all_routes.route("/api/forgot-password", methods=["POST"])
def forgot_password():
    import smtplib, os
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    d = request.get_json(force=True)
    email = d.get("email", "").strip()
    if not email:
        return jsonify({"error": "Email is required."}), 400

    result = services.forgot_password(email)

    # Always return the same message to avoid revealing whether an email is registered
    generic_msg = "If that email is registered, a reset link has been sent."

    if not result["token"]:
        return jsonify({"message": generic_msg})

    reset_url = f"{request.host_url.rstrip('/')}login.html?reset_token={result['token']}"

    # ── SMTP config from environment variables ────────────────────────────────
    smtp_user = os.environ.get("FITAI_EMAIL_USER", "")       # e.g. yourapp@gmail.com
    smtp_pass = os.environ.get("FITAI_EMAIL_PASS", "")       # Gmail App Password
    smtp_host = os.environ.get("FITAI_EMAIL_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("FITAI_EMAIL_PORT", "587"))

    if smtp_user and smtp_pass:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "FitAI — Password Reset"
            msg["From"]    = smtp_user
            msg["To"]      = email

            text_body = f"Hi,\n\nClick the link below to reset your FitAI password (valid for 1 hour):\n\n{reset_url}\n\nIf you didn't request this, you can safely ignore this email.\n\n— The FitAI Team"
            html_body = f"""
<div style="font-family:Nunito,sans-serif;max-width:480px;margin:auto;padding:32px;background:#f0e8f8;border-radius:16px;">
  <h2 style="color:#3d1f7a;margin-bottom:8px;">🍎 FitAI Password Reset</h2>
  <p style="color:#1e0f40;">Click the button below to set a new password. This link expires in <strong>1 hour</strong>.</p>
  <a href="{reset_url}" style="display:inline-block;margin:20px 0;padding:14px 28px;background:#3d1f7a;color:#fff;border-radius:10px;text-decoration:none;font-weight:800;font-size:15px;">Reset My Password</a>
  <p style="font-size:12px;color:#8e7dbf;">If you didn't request this, you can safely ignore this email.</p>
  <p style="font-size:12px;color:#8e7dbf;">Or copy this link: {reset_url}</p>
</div>"""

            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, email, msg.as_string())

            return jsonify({"message": generic_msg})

        except Exception as e:
            # Log the error server-side but don't expose internals to the client
            print(f"[FitAI] Email send failed: {e}")
            return jsonify({"error": "Failed to send reset email. Check FITAI_EMAIL_USER / FITAI_EMAIL_PASS env vars."}), 500

    else:
        # No SMTP configured — return the reset URL directly so dev/local still works
        return jsonify({
            "message": generic_msg,
            "reset_url": reset_url,
            "warning": "FITAI_EMAIL_USER / FITAI_EMAIL_PASS not set — showing reset link directly (dev mode only)."
        })


@all_routes.route("/api/reset-password", methods=["POST"])
def reset_password():
    d = request.get_json(force=True)
    token    = d.get("token", "").strip()
    password = d.get("password", "")
    if not token:
        return jsonify({"error": "Reset token is missing."}), 400
    try:
        services.reset_password(token, password)
        return jsonify({"message": "Password updated! You can now log in."})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


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
# AI PROXY  — server-side Anthropic call (fixes browser CORS)
# ══════════════════════════════════════════════════════════════════════════════

@all_routes.route("/api/ai/recommend", methods=["POST"])
def ai_recommend():
    """
    Receives prompt from frontend, calls Anthropic API server-side,
    returns recommendations. Requires ANTHROPIC_API_KEY env variable.
    """
    if not ANTHROPIC_API_KEY:
        return jsonify({"error": "ANTHROPIC_API_KEY not set. See README for setup instructions."}), 500

    d            = request.get_json(force=True)
    ingredients  = d.get("ingredients","").strip()
    preferences  = d.get("preferences","").strip()
    recipe_names = d.get("recipe_names",[])

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
        "model": "claude-sonnet-4-20250514", "max_tokens": 800,
        "messages": [{"role":"user","content":prompt}]
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=payload,
        headers={"Content-Type":"application/json","x-api-key":ANTHROPIC_API_KEY,"anthropic-version":"2023-06-01"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        raw    = "".join(b.get("text","") for b in result.get("content",[]))
        parsed = json.loads(raw.strip().replace("```json","").replace("```","").strip())
        return jsonify(parsed)
    except urllib.error.HTTPError as e:
        return jsonify({"error": f"Anthropic API error {e.code}: {e.read().decode()}"}), 502
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