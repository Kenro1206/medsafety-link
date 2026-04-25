from flask import has_request_context, session
from core.config_manager import load_settings


def get_current_institution_id():
    if has_request_context():
        institution_id = session.get("institution_id")
        if institution_id:
            return institution_id

    s = load_settings()
    return s.get("default_institution_id")


def get_current_institution():
    s = load_settings()
    institution_id = get_current_institution_id()
    return s.get("institutions", {}).get(institution_id)


def require_institution():
    return get_current_institution() is not None


def get_all_institutions():
    s = load_settings()
    return s.get("institutions", {})
