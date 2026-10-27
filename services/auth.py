import re
import os
import hashlib
import hmac
from typing import Optional, Dict, Any, Tuple
from database.db import DatabaseManager, get_db

try:
    import bcrypt
    _HAS_BCRYPT = True
except ImportError:
    _HAS_BCRYPT = False


class AuthService:
    """Authentication and session credential validation service."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or get_db()

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password securely using bcrypt or PBKDF2-HMAC-SHA256."""
        if _HAS_BCRYPT:
            salt = bcrypt.gensalt(rounds=12)
            hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
            return hashed.decode("utf-8")
        else:
            # PBKDF2 fallback with 100,000 rounds and random salt
            salt = os.urandom(16)
            dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
            return f"pbkdf2${salt.hex()}${dk.hex()}"

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify candidate password against stored hash."""
        if not hashed or not password:
            return False

        if hashed.startswith("$2b$") or hashed.startswith("$2a$") or hashed.startswith("$2y$"):
            try:
                return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
            except Exception:
                return False
        elif hashed.startswith("pbkdf2$"):
            try:
                parts = hashed.split("$")
                if len(parts) != 3:
                    return False
                salt = bytes.fromhex(parts[1])
                expected_dk = bytes.fromhex(parts[2])
                actual_dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
                return hmac.compare_digest(actual_dk, expected_dk)
            except Exception:
                return False
        return False

    @staticmethod
    def validate_registration_inputs(
        email: str, full_name: str, password: str, confirm_password: str
    ) -> Tuple[bool, str]:
        """Validate registration fields."""
        if not full_name or len(full_name.strip()) < 2:
            return False, "Full name must be at least 2 characters long."

        email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not email or not re.match(email_pattern, email.strip()):
            return False, "Please enter a valid email address."

        if not password or len(password) < 6:
            return False, "Password must be at least 6 characters long."

        if password != confirm_password:
            return False, "Passwords do not match."

        return True, ""

    def register_user(
        self, email: str, full_name: str, password: str, confirm_password: str
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Register a new student user."""
        is_valid, err = self.validate_registration_inputs(email, full_name, password, confirm_password)
        if not is_valid:
            return False, err, None

        normalized_email = email.strip().lower()
        existing = self.db.get_user_by_email(normalized_email)
        if existing:
            return False, "An account with this email already exists. Please log in.", None

        pwd_hash = self.hash_password(password)
        user_id = self.db.create_user(normalized_email, full_name.strip(), pwd_hash)
        if not user_id:
            return False, "Failed to create user account. Please try again.", None

        user = self.db.get_user_by_id(user_id)
        return True, "Registration successful!", user

    def login_user(self, email: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Authenticate user credentials."""
        if not email or not password:
            return False, "Email and password are required.", None

        normalized_email = email.strip().lower()
        user = self.db.get_user_by_email(normalized_email)
        if not user:
            return False, "Invalid email or password.", None

        if not self.verify_password(password, user["password_hash"]):
            return False, "Invalid email or password.", None

        return True, "Login successful!", user
