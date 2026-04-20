# ─────────────────────────────────────────────────────────────────────────────
# app.py  —  FitAI Master Entry Point
# Architecture:  routes.py → services.py → repository.py → fitai.db (SQLite)
# ─────────────────────────────────────────────────────────────────────────────
# Team file map:
#   routes.py      — ALL HTTP endpoints (Garnet, Keerthan, Roshini, John, Sai)
#   services.py    — ALL business logic
#   repository.py  — ALL database access
# ─────────────────────────────────────────────────────────────────────────────

import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from repository import init_db
from routes import all_routes

app = Flask(__name__, static_folder="static")
app.secret_key = os.environ.get("SECRET_KEY", "fitai-dev-secret-change-in-production")
CORS(app, supports_credentials=True)

init_db()
app.register_blueprint(all_routes)

# Serve HTML files directly
@app.route("/")
def index():
    return send_from_directory("static", "login.html")
@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory("static", filename)

if __name__ == "__main__":
    print("=" * 55)
    print("  FitAI Backend  —  http://localhost:5000")
    print("  Open: http://localhost:5000/login.html")
    print("  Architecture: routes → services → repository → SQLite")
    print("=" * 55)
    app.run(debug=True, port=5000)
