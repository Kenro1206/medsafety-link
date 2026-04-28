from flask import session, redirect
from core.config_manager import load_settings


def is_logged_in():
    return session.get("logged_in", False) and session.get("institution_id")


def require_login():
    if not is_logged_in():
        return redirect("/login")
    return None


def get_system_admin_institution_ids():
    s = load_settings()
    ids = s.get("system_admins", {}).get("institution_ids", [])
    if ids:
        return ids
    if "kumamoto_chuo" in s.get("institutions", {}):
        return ["kumamoto_chuo"]
    default_id = s.get("default_institution_id")
    return [default_id] if default_id else []


def can_manage_institutions():
    institution_id = session.get("institution_id")
    return bool(institution_id and institution_id in get_system_admin_institution_ids())


def require_system_admin():
    auth = require_login()
    if auth:
        return auth
    if not can_manage_institutions():
        return redirect("/admin/dashboard")
    return None
