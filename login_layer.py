from __future__ import annotations

from typing import Any, Optional

import bcrypt

from application_layer import AppDatabase, upsert_premium


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _check_password(plain: str, stored: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), stored.encode("utf-8"))
    except ValueError:
        return False


def get_user_by_email(db: AppDatabase, email: str) -> Optional[dict[str, Any]]:
    rows = db.query(
        "SELECT `userID`, `name`, `password`, `email` FROM users WHERE `email` = %s",
        (email.strip(),),
    )
    return rows[0] if rows else None


def create_user(db: AppDatabase, name: str, email: str, plain_password: str) -> dict[str, Any]:
    email_clean = email.strip()
    if not name.strip() or not email_clean or not plain_password:
        return {"success": False, "message": "Name, email, and password are required.", "user_id": None}
    if get_user_by_email(db, email_clean):
        return {"success": False, "message": "An account with this email already exists.", "user_id": None}

    pw = _hash_password(plain_password)
    new_id = db.execute_write(
        "INSERT INTO users (`name`, `password`, `email`) VALUES (%s, %s, %s)",
        (name.strip(), pw, email_clean),
    )
    uid = int(new_id) if new_id else None
    if uid is not None:
        upsert_premium(db, uid, "N", "", None, "none", 0.0)
    return {"success": True, "message": "Account created.", "user_id": uid}


def verify_credentials(db: AppDatabase, email: str, plain_password: str) -> Optional[dict[str, Any]]:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not _check_password(plain_password, user["password"]):
        return None
    return {"userID": user["userID"], "name": user["name"], "email": user["email"]}


def login_response(email: str, password: str, db: AppDatabase) -> dict[str, Any]:
    user = verify_credentials(db, email, password)
    if not user:
        return {
            "success": False,
            "message": "Invalid email or password.",
            "user": None,
            "redirect": None,
        }
    return {
        "success": True,
        "message": f"Welcome, {user['name']}!",
        "user": user,
        "redirect": "dashboard.html",
    }
