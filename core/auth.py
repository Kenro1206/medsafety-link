from flask import session, redirect
from core.config_manager import load_settings


def get_admin_password():
    s = load_settings()
    return s.get("auth", {}).get("admin_password", "admin")


def is_logged_in():
    return session.get("logged_in", False)


def require_login():
    if not is_logged_in():
        return redirect("/login")
    return None
