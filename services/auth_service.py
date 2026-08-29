"""Authentication and account-management rules."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import User

_HASH_ITERATIONS = 210_000


class AuthService:
    """Manages library user accounts without storing plain-text passwords."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def ensure_admin(self) -> None:
        """Create the documented initial administrator only for an empty account store."""
        if self.session.scalar(select(User.id).limit(1)) is None:
            self.session.add(User(username="admin", display_name="Administrator", password_hash=self._hash_password("admin123"), is_admin=True, role="Administrator"))
            self.session.commit()

    def authenticate(self, username: str, password: str) -> User | None:
        """Return the matching account when its password is valid."""
        user = self.find_user(username)
        if user and self._password_matches(password, user.password_hash):
            return user
        return None

    def list_users(self) -> list[User]:
        """Return accounts ordered for management display."""
        return list(self.session.scalars(select(User).order_by(User.username)))

    def find_user(self, username: str) -> User | None:
        """Find an account by a normalized username."""
        return self.session.scalar(select(User).where(User.username == username.strip()))

    def create_user(self, username: str, display_name: str, password: str, role: str) -> None:
        """Create an account with the selected role."""
        normalized_username = self._validate_credentials(username, password)
        normalized_display_name = display_name.strip() or normalized_username
        if role not in {"Administrator", "User", "Guest"}:
            raise ValueError("Select a valid role.")
        try:
            self.session.add(User(username=normalized_username, display_name=normalized_display_name, password_hash=self._hash_password(password), is_admin=role == "Administrator", role=role))
            self.session.commit()
        except IntegrityError as error:
            self.session.rollback()
            raise ValueError("That username is already in use.") from error

    def reset_password(self, username: str, password: str) -> None:
        """Set a new password for an existing account."""
        normalized_username = self._validate_credentials(username, password)
        user = self.find_user(normalized_username)
        if user is None:
            raise ValueError("User not found.")
        user.password_hash = self._hash_password(password)
        self.session.commit()

    def update_user(self, username: str, new_username: str, display_name: str, role: str) -> None:
        """Update an account name and its permissions role."""
        user = self.find_user(username)
        if user is None:
            raise ValueError("User not found.")
        normalized_username = new_username.strip()
        if not normalized_username:
            raise ValueError("Username is required.")
        if role not in {"Administrator", "User", "Guest"}:
            raise ValueError("Select a valid role.")
        if user.username == "admin":
            normalized_username = "admin"
            role = "Administrator"
        existing_user = self.find_user(normalized_username)
        if existing_user is not None and existing_user.id != user.id:
            raise ValueError("That username is already in use.")
        user.username = normalized_username
        user.display_name = display_name.strip() or normalized_username
        user.role = role
        user.is_admin = role == "Administrator"
        self.session.commit()

    def delete_user(self, username: str) -> None:
        """Delete a standard account; the administrator account is protected."""
        user = self.find_user(username)
        if user is None:
            raise ValueError("User not found.")
        if user.is_admin:
            raise ValueError("The administrator account cannot be deleted.")
        self.session.delete(user)
        self.session.commit()

    @staticmethod
    def _validate_credentials(username: str, password: str) -> str:
        normalized_username = username.strip()
        if not normalized_username:
            raise ValueError("Username is required.")
        if len(password) < 6:
            raise ValueError("Password must contain at least 6 characters.")
        return normalized_username

    @staticmethod
    def _hash_password(password: str) -> str:
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _HASH_ITERATIONS)
        return "$".join((str(_HASH_ITERATIONS), base64.b64encode(salt).decode(), base64.b64encode(digest).decode()))

    @staticmethod
    def _password_matches(password: str, stored_hash: str) -> bool:
        try:
            iterations, salt_text, digest_text = stored_hash.split("$", maxsplit=2)
            expected = base64.b64decode(digest_text)
            actual = hashlib.pbkdf2_hmac(
                "sha256", password.encode(), base64.b64decode(salt_text), int(iterations)
            )
            return hmac.compare_digest(actual, expected)
        except (TypeError, ValueError):
            return False