"""
Tasklyn — Auth / Profile Service
====================================
Handles first-launch detection, profile creation, profile updates,
and password recovery with a recovery key.
"""
from __future__ import annotations
import hashlib
import secrets
from typing import Optional
from database.repositories import UserRepository, SettingsRepository
from models import User
from utils.logger import get_logger
from utils.validation import validate_name, validate_password

log = get_logger(__name__)
_user_repo = UserRepository()
_settings_repo = SettingsRepository()

# Cached active user in-process
_active_user: Optional[User] = None


def is_first_launch() -> bool:
    """Return True if no user profile exists yet."""
    return _user_repo.get_first() is None


def get_active_user() -> Optional[User]:
    """Return the active (first) user; None if not set up yet."""
    global _active_user
    if _active_user is None:
        _active_user = _user_repo.get_first()
    return _active_user


def create_profile(name: str, avatar_id: str, gender: str, password: Optional[str] = None) -> tuple[bool, str, Optional[User]]:
    """
    Create the user profile.

    Returns
    -------
    (success, error_message, user)
    """
    global _active_user
    ok, err = validate_name(name, "Name")
    if not ok:
        return False, err, None
    try:
        user = _user_repo.create(name=name.strip(), avatar_id=avatar_id, gender=gender, password=password)
        _active_user = user
        log.info("Profile created: %s (id=%d)", user.name, user.id)
        return True, "", user
    except Exception as exc:
        log.error("Failed to create profile: %s", exc, exc_info=True)
        return False, "Failed to save profile. Please try again.", None


def update_profile(name: str, avatar_id: str, gender: str) -> tuple[bool, str]:
    user = get_active_user()
    if not user:
        return False, "No profile found."
    ok, err = validate_name(name, "Name")
    if not ok:
        return False, err
    try:
        _user_repo.update_profile(user.id, name.strip(), avatar_id, gender)
        user.name = name.strip()
        user.avatar_id = avatar_id
        user.gender = gender
        log.info("Profile updated: %s", user.name)
        return True, ""
    except Exception as exc:
        log.error("Failed to update profile: %s", exc, exc_info=True)
        return False, "Failed to update profile."


def refresh_active_user() -> Optional[User]:
    global _active_user
    _active_user = _user_repo.get_first()
    return _active_user


def authenticate(name: str, password: str) -> tuple[bool, str, Optional[User]]:
    """Authenticate a user by name and password."""
    global _active_user
    user = _user_repo.get_first()
    if not user:
        return False, "No profile exists yet.", None

    if user.name.lower() != name.lower().strip():
        return False, "User not found.", None

    if user.password != password:
        return False, "Incorrect password.", None

    _active_user = user
    return True, "", user


# ── Password recovery ─────────────────────────────────────────────────────

def _hash_key(key: str) -> str:
    """Hash a recovery key (ignores dashes, spaces and letter case)."""
    cleaned = key.replace("-", "").replace(" ", "").strip().upper()
    return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()


def has_recovery_key(user: Optional[User]) -> bool:
    """Return True if this user already has a recovery key saved."""
    return bool(user and getattr(user, "recovery_key_hash", None))


def generate_recovery_key(user_id: int) -> str:
    """Create a new recovery key, store only its hash, and return the key."""
    raw = secrets.token_hex(8).upper()  # 16 characters
    key = "-".join(raw[i:i + 4] for i in range(0, 16, 4))
    _user_repo.set_recovery_key_hash(user_id, _hash_key(key))

    user = get_active_user()
    if user and user.id == user_id:
        user.recovery_key_hash = _hash_key(key)
    log.info("Recovery key generated for user id=%d", user_id)
    return key


def reset_password(name: str, recovery_key: str, new_password: str) -> tuple[bool, str]:
    """Reset the password using the recovery key. Returns (success, error_message)."""
    user = _user_repo.get_first()
    if not user:
        return False, "No profile exists yet."

    if user.name.lower() != name.lower().strip():
        return False, "User not found."

    if not getattr(user, "recovery_key_hash", None):
        return False, "No recovery key was set up for this account."

    if _hash_key(recovery_key) != user.recovery_key_hash:
        return False, "Incorrect recovery key."

    ok, err = validate_password(new_password)
    if not ok:
        return False, err

    try:
        _user_repo.set_password(user.id, new_password)
        user.password = new_password
        log.info("Password reset for user id=%d", user.id)
        return True, ""
    except Exception as exc:
        log.error("Failed to reset password: %s", exc, exc_info=True)
        return False, "Failed to reset password. Please try again."