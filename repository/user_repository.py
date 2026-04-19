# ─────────────────────────────────────────────────────────────────────────────
# repository/user_repository.py
# Author: KEERTHAN SANJAY
# Layer: Repository (Database Access)
# Use Cases: UC-03 (User Profile) · UC-04 (Dashboard)
#
# Only this file talks to the database for user profile data.
# Called by: services/user_service.py
# ─────────────────────────────────────────────────────────────────────────────

from repository.database import get_db


def fetch_user(user_id: int = 1) -> dict | None:
    """Return the user profile row as a dict, or None if not found."""
    conn = get_db()
    row  = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_user(user_id: int, fields: dict) -> dict:
    """
    Update allowed profile fields (weight, height, goal) for a given user.
    Returns the updated profile dict.
    Raises ValueError if the user does not exist.
    """
    allowed = {"weight", "height", "goal"}
    updates = {k: v for k, v in fields.items() if k in allowed}

    if not updates:
        raise ValueError("No valid fields provided to update.")

    conn = get_db()
    row  = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        conn.close()
        raise ValueError(f"User id {user_id} not found")

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values     = list(updates.values()) + [user_id]
    conn.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
    conn.commit()

    updated = dict(conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())
    conn.close()
    return updated
