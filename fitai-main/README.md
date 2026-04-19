# FitAI — Setup, Run & GitHub Guide

## Architecture: Routes → Services → Repository → Database (SQLite)

```
fitai/
├── app.py                                    ← Run this to start the server
├── recipe_search.html                        ← Open this in your browser
├── requirements.txt
├── fitai.db                                  ← Auto-created on first run (never commit)
│
├── routes/                                   ← Layer 1: HTTP only (Flask)
│   ├── recipe_routes.py          (Garnet)    UC-01 filter · UC-02 reorder
│   ├── user_routes.py            (Keerthan)  UC-03 profile · UC-04 dashboard
│   ├── favorites_routes.py       (Roshini)   UC-09 favourites · UC-10 nutrition
│   ├── meal_plan_routes.py       (John)      UC-05 generate · UC-06 modify
│   └── recommendation_routes.py  (Sai)       UC-07 recs · UC-08 details
│
├── services/                                 ← Layer 2: Business logic (no Flask, no DB)
│   ├── recipe_service.py         (Garnet)
│   ├── user_service.py           (Keerthan)
│   ├── favorites_service.py      (Roshini)
│   ├── meal_plan_service.py      (John)
│   └── recommendation_service.py (Sai)
│
└── repository/                               ← Layer 3: Database access only
    ├── database.py               (shared)    Creates all tables + seeds data
    ├── recipe_repository.py      (Garnet)
    ├── user_repository.py        (Keerthan)
    ├── favorites_repository.py   (Roshini)
    ├── meal_plan_repository.py   (John)
    └── recipe_details_repository.py (Sai)
```

---

## Running the project

### 1 — Install dependencies
```bash
pip install -r requirements.txt
```

### 2 — Start the backend
```bash
python app.py
```
The first run auto-creates fitai.db and seeds all 12 recipes. You will see:
  FitAI Backend — http://localhost:5000

### 3 — Open the frontend
Open recipe_search.html in your browser (double-click it or drag into Chrome).
It connects to http://localhost:5000 automatically.

---

## GitHub Setup (one-time)

### A — Create the repo (one person)
1. Go to https://github.com/new
2. Name it: fitai
3. Set Private, click Create repository (no README)

### B — Push initial code (one person)
```bash
cd fitai
git init
git add .
git commit -m "Initial project: 4-layer architecture"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/fitai.git
git push -u origin main
```

### C — Add .gitignore (commit this immediately)
Create .gitignore with:
  fitai.db
  __pycache__/
  *.pyc
  .DS_Store

```bash
git add .gitignore
git commit -m "Add gitignore"
git push
```

### D — Everyone else clones
```bash
git clone https://github.com/YOUR_USERNAME/fitai.git
cd fitai
pip install -r requirements.txt
python app.py
```

---

## Daily Workflow (each person)

```bash
# 1. Pull latest main before starting
git checkout main
git pull origin main

# 2. Switch to your branch (create it once with -b)
git checkout -b garnet/recipe-layer   # first time only
git checkout garnet/recipe-layer      # after that

# 3. Merge in any updates from teammates
git merge main

# 4. Edit ONLY your files (see table below), then commit
git add routes/recipe_routes.py services/recipe_service.py repository/recipe_repository.py
git commit -m "UC-01: tag filtering with pagination"
git push origin garnet/recipe-layer

# 5. Open a Pull Request on GitHub → get a teammate to review → Merge

# 6. After merge, update local main
git checkout main
git pull origin main
```

## Branch + File Ownership

| Person   | Branch                    | Files                                                                                     |
|----------|---------------------------|-------------------------------------------------------------------------------------------|
| Garnet   | garnet/recipe-layer       | routes/recipe_routes.py, services/recipe_service.py, repository/recipe_repository.py     |
| Keerthan | keerthan/user-layer       | routes/user_routes.py, services/user_service.py, repository/user_repository.py           |
| Roshini  | roshini/favorites-layer   | routes/favorites_routes.py, services/favorites_service.py, repository/favorites_repository.py |
| John     | john/meal-plan-layer      | routes/meal_plan_routes.py, services/meal_plan_service.py, repository/meal_plan_repository.py |
| Sai      | sai/recommendation-layer  | routes/recommendation_routes.py, services/recommendation_service.py, repository/recipe_details_repository.py |

---

## Troubleshooting

ModuleNotFoundError: No module named flask
  pip install -r requirements.txt

Address already in use (port 5000)
  Mac:     lsof -ti:5000 | xargs kill -9
  Windows: netstat -ano | findstr :5000  →  taskkill /PID <number> /F

Database looks wrong or missing data
  rm fitai.db   (or delete fitai.db on Windows)
  python app.py

Frontend says backend offline
  Make sure python app.py is running in a separate terminal.
  The UI still works offline using local fallback data.
