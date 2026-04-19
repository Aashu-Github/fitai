# ─────────────────────────────────────────────────────────────────────────────
# app.py  —  FitAI Master Entry Point
# ─────────────────────────────────────────────────────────────────────────────
#
# Architecture:  Routes → Controllers → Services → Repository (Database)
#
# File map (by layer):
#
#  ROUTES  (HTTP interface — Flask only)
#    routes/recipe_routes.py          Garnet   UC-01 UC-02
#    routes/user_routes.py            Keerthan UC-03 UC-04
#    routes/favorites_routes.py       Roshini  UC-09 UC-10
#    routes/meal_plan_routes.py       John     UC-05 UC-06
#    routes/recommendation_routes.py  Sai      UC-07 UC-08
#
#  SERVICES  (Business logic — no Flask, no DB)
#    services/recipe_service.py
#    services/user_service.py
#    services/favorites_service.py
#    services/meal_plan_service.py
#    services/recommendation_service.py
#
#  REPOSITORY  (Database access — SQLite only)
#    repository/database.py                 ← shared DB setup + init
#    repository/recipe_repository.py        Garnet
#    repository/user_repository.py          Keerthan
#    repository/favorites_repository.py     Roshini
#    repository/meal_plan_repository.py     John
#    repository/recipe_details_repository.py Sai
# ─────────────────────────────────────────────────────────────────────────────

from flask import Flask
from flask_cors import CORS

from repository.database import init_db

from routes.recipe_routes         import recipe_routes
from routes.user_routes           import user_routes
from routes.favorites_routes      import favorites_routes
from routes.meal_plan_routes      import meal_plan_routes
from routes.recommendation_routes import recommendation_routes

app = Flask(__name__)
CORS(app)  # Allows the HTML frontend to call the API from any origin

# ── Initialise DB (creates tables + seeds data on first run) ──────────────────
init_db()

# ── Register every Blueprint ──────────────────────────────────────────────────
app.register_blueprint(recipe_routes)          # Garnet
app.register_blueprint(user_routes)            # Keerthan
app.register_blueprint(favorites_routes)       # Roshini
app.register_blueprint(meal_plan_routes)       # John
app.register_blueprint(recommendation_routes)  # Sai

# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  FitAI Backend  —  http://localhost:5000")
    print("  Architecture: Routes → Services → Repository → SQLite")
    print("=" * 60)
    app.run(debug=True, port=5000)
