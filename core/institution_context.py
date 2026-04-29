from contextlib import contextmanager
from contextvars import ContextVar

from flask import has_request_context, session
from core.config_manager import load_settings

_institution_override = ContextVar("institution_override", default=None)


def get_current_institution_id():
    override = _institution_override.get()
    if override:
        return override

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


@contextmanager
def use_institution(institution_id):
    token = _institution_override.set(institution_id)
    try:
        yield
    finally:
        _institution_override.reset(token)
