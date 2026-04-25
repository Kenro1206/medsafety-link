from flask import session, redirect


def is_logged_in():
    return session.get("logged_in", False) and session.get("institution_id")


def require_login():
    if not is_logged_in():
        return redirect("/login")
    return None
