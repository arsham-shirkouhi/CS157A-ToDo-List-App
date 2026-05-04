from __future__ import annotations

from typing import Any, Optional, Tuple

import bcrypt

from application_layer import AppDatabase


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


def create_user(db: AppDatabase, name: str, email: str, plain_password: str) -> Tuple[bool, str, Optional[int]]:
    """
    Register a new user. Fails if email is already used.
    Returns (success, message, user_id or none).
    """
    email_clean = email.strip()
    if not name.strip() or not email_clean or not plain_password:
        return False, "Name, email, and password are required.", None
    if get_user_by_email(db, email_clean):
        return False, "An account with this email already exists.", None

    pw = _hash_password(plain_password)
    new_id = db.execute_write(
        "INSERT INTO users (`name`, `password`, `email`) VALUES (%s, %s, %s)",
        (name.strip(), pw, email_clean),
    )
    return True, "Account created.", int(new_id) if new_id else None


def verify_credentials(db: AppDatabase, email: str, plain_password: str) -> Optional[dict[str, Any]]:
    """Return user row (without password) if email/password match, else None."""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not _check_password(plain_password, user["password"]):
        return None
    return {"userID": user["userID"], "name": user["name"], "email": user["email"]}


def authenticate_user(email: str, password: str, db: AppDatabase) -> Tuple[bool, Optional[dict[str, Any]]]:
    """Returns (is_authenticated, user_dict_without_password_or_none)."""
    user = verify_credentials(db, email, password)
    if user:
        return True, user
    return False, None


def signup_user(name: str, email: str, password: str, db: AppDatabase) -> dict[str, Any]:
    """
    High-level sign up response dict for a controller to use.
    """
    ok, message, uid = create_user(db, name, email, password)
    if not ok:
        return {"success": False, "message": message, "user_id": None}
    return {"success": True, "message": message, "user_id": uid}


def login_response(email: str, password: str, db: AppDatabase) -> dict[str, Any]:
    """
    High-level login response dict.
    """
    ok, user = authenticate_user(email, password, db)
    if not ok:
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
