import os
import gc
import tempfile
import pytest
from database.db import DatabaseManager
from services.auth import AuthService


@pytest.fixture
def auth_service():
    """Create AuthService instance with an isolated database."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = DatabaseManager(db_path=path)
    service = AuthService(db=db)
    yield service
    del service
    del db
    gc.collect()
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def test_password_hashing_and_verification(auth_service):
    """Verify that password hashing produces non-trivial hashes and verifies correctly."""
    raw_pwd = "SecretPassword123!"
    hashed = auth_service.hash_password(raw_pwd)

    assert hashed != raw_pwd
    assert len(hashed) > 20
    assert auth_service.verify_password(raw_pwd, hashed) is True
    assert auth_service.verify_password("WrongPassword", hashed) is False
    assert auth_service.verify_password("", hashed) is False


def test_registration_success(auth_service):
    """Test successful user registration and subsequent login."""
    success, msg, user = auth_service.register_user(
        email="student@campus.ac.in",
        full_name="Priya Sharma",
        password="MySecurePassword#1",
        confirm_password="MySecurePassword#1"
    )
    assert success is True
    assert user is not None
    assert user["email"] == "student@campus.ac.in"
    assert user["full_name"] == "Priya Sharma"

    # Test login
    login_ok, login_msg, logged_user = auth_service.login_user(
        "student@campus.ac.in", "MySecurePassword#1"
    )
    assert login_ok is True
    assert logged_user["id"] == user["id"]


def test_registration_validation_errors(auth_service):
    """Test invalid registration inputs."""
    # Mismatched passwords
    ok, msg, _ = auth_service.register_user("test@ex.com", "Test", "password123", "password456")
    assert ok is False
    assert "Passwords do not match" in msg

    # Short password
    ok, msg, _ = auth_service.register_user("test@ex.com", "Test", "123", "123")
    assert ok is False
    assert "at least 6 characters" in msg

    # Invalid email
    ok, msg, _ = auth_service.register_user("not-an-email", "Test", "secret123", "secret123")
    assert ok is False
    assert "valid email" in msg


def test_duplicate_registration_rejection(auth_service):
    """Ensure duplicate email registration is properly blocked with helpful message."""
    ok1, _, _ = auth_service.register_user(
        "duplicate@univ.edu", "First User", "password123", "password123"
    )
    assert ok1 is True

    ok2, msg, user2 = auth_service.register_user(
        "duplicate@univ.edu", "Second User", "password456", "password456"
    )
    assert ok2 is False
    assert user2 is None
    assert "already exists" in msg


def test_login_invalid_credentials(auth_service):
    """Verify rejection of wrong email or wrong password."""
    auth_service.register_user("valid@univ.edu", "Valid User", "correct_pwd", "correct_pwd")

    # Non-existent email
    ok, msg, _ = auth_service.login_user("wrong@univ.edu", "correct_pwd")
    assert ok is False
    assert "Invalid email or password" in msg

    # Wrong password
    ok, msg, _ = auth_service.login_user("valid@univ.edu", "wrong_pwd")
    assert ok is False
    assert "Invalid email or password" in msg
