from werkzeug.security import check_password_hash, generate_password_hash


HASH_PREFIXES = ("pbkdf2:", "scrypt:")


def is_password_hash(value):
    return isinstance(value, str) and value.startswith(HASH_PREFIXES)


def set_institution_password(institution, password):
    institution["password_hash"] = generate_password_hash(password)
    institution["password"] = ""


def verify_institution_password(institution, password):
    password_hash = institution.get("password_hash", "")
    if password_hash:
        try:
            return check_password_hash(password_hash, password)
        except ValueError:
            return False

    legacy_password = institution.get("password", "")
    return bool(legacy_password) and password == legacy_password


def upgrade_institution_password_if_needed(institution, password):
    if institution.get("password_hash"):
        if institution.get("password"):
            institution["password"] = ""
            return True
        return False

    if institution.get("password") and password == institution.get("password"):
        set_institution_password(institution, password)
        return True

    return False


def migrate_plaintext_passwords(settings):
    for institution in settings.get("institutions", {}).values():
        password_hash = institution.get("password_hash", "")
        password = institution.get("password", "")
        if password_hash:
            institution["password"] = ""
        elif password:
            set_institution_password(institution, password)
    return settings
