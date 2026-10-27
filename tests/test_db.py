import os
import gc
import tempfile
import pytest
from database.db import DatabaseManager


@pytest.fixture
def temp_db():
    """Create a clean isolated SQLite database for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = DatabaseManager(db_path=path)
    yield db
    del db
    gc.collect()
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def test_db_initialization(temp_db):
    """Verify that tables and indexes are initialized correctly."""
    with temp_db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row["name"] for row in cursor.fetchall()]
        assert "users" in tables
        assert "user_preferences" in tables
        assert "interview_sessions" in tables
        assert "interview_answers" in tables


def test_create_and_get_user(temp_db):
    """Test user creation and lookup by email and ID."""
    user_id = temp_db.create_user("alice@college.edu", "Alice Johnson", "hashed_password_123")
    assert user_id is not None

    user = temp_db.get_user_by_email("alice@college.edu")
    assert user is not None
    assert user["full_name"] == "Alice Johnson"
    assert user["email"] == "alice@college.edu"

    user_by_id = temp_db.get_user_by_id(user_id)
    assert user_by_id["email"] == "alice@college.edu"


def test_duplicate_email_prevention(temp_db):
    """Ensure duplicate emails cannot be registered."""
    id1 = temp_db.create_user("student@univ.edu", "Student One", "hash1")
    assert id1 is not None

    id2 = temp_db.create_user("student@univ.edu", "Student Two", "hash2")
    assert id2 is None


def test_user_preferences(temp_db):
    """Verify user preferences update and default values."""
    user_id = temp_db.create_user("bob@univ.edu", "Bob", "hash")
    prefs = temp_db.get_user_preferences(user_id)
    assert prefs["theme"] == "dark"

    temp_db.update_user_preferences(user_id, theme="light", preferred_difficulty="Advanced")
    updated = temp_db.get_user_preferences(user_id)
    assert updated["theme"] == "light"
    assert updated["preferred_difficulty"] == "Advanced"


def test_interview_session_and_answers(temp_db):
    """Test session lifecycle and saving answer records with user isolation."""
    user1_id = temp_db.create_user("user1@test.com", "User One", "hash1")
    user2_id = temp_db.create_user("user2@test.com", "User Two", "hash2")

    session_id = temp_db.create_session(user1_id, "Python Programming", "Beginner", 5)
    assert session_id is not None

    # Save an answer
    ans_id = temp_db.save_answer(
        session_id=session_id,
        user_id=user1_id,
        question_id="PY-BEG-01",
        question_text="What is a list vs tuple?",
        subject="Python Programming",
        topic="Data Structures",
        difficulty="Beginner",
        user_answer="Lists are mutable while tuples are immutable.",
        score=8.5,
        concepts_covered=["mutable", "immutable"],
        concepts_missing=["hashable", "dictionary key"],
        feedback="Great answer!",
        reference_answer="Full reference answer.",
        evaluation_mode="rule_based"
    )
    assert ans_id is not None

    # Complete session
    completed = temp_db.complete_session(session_id, user1_id, 8.5)
    assert completed is True

    # User 1 should see session and answer
    user1_sessions = temp_db.get_user_sessions(user1_id)
    assert len(user1_sessions) == 1
    assert user1_sessions[0]["status"] == "completed"
    assert user1_sessions[0]["average_score"] == 8.5

    user1_answers = temp_db.get_session_answers(session_id, user1_id)
    assert len(user1_answers) == 1
    assert user1_answers[0]["concepts_covered"] == ["mutable", "immutable"]

    # User 2 should NOT see User 1's session or answers (User Isolation)
    user2_sessions = temp_db.get_user_sessions(user2_id)
    assert len(user2_sessions) == 0

    user2_answers = temp_db.get_session_answers(session_id, user2_id)
    assert len(user2_answers) == 0
