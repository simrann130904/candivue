import os
import gc
import tempfile
import pytest
from database.db import DatabaseManager
from services.recommendations import RecommendationEngine


@pytest.fixture
def test_setup():
    """Setup isolated DB and recommendation engine."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = DatabaseManager(db_path=path)
    engine = RecommendationEngine(db=db)
    yield db, engine
    del engine
    del db
    gc.collect()
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def test_cold_start_recommendations(test_setup):
    """Verify general onboarding recommendations when user has no/few answers."""
    db, engine = test_setup
    user_id = db.create_user("newuser@univ.edu", "New User", "hash")

    recs = engine.generate_recommendations(user_id)
    assert len(recs) >= 2
    assert any(r["tag"] == "Getting Started" for r in recs)


def test_targeted_weak_topic_recommendation(test_setup):
    """Verify that a topic with low scores triggers a targeted practice recommendation."""
    db, engine = test_setup
    user_id = db.create_user("learner@univ.edu", "Learner", "hash")
    session_id = db.create_session(user_id, "SQL", "Intermediate", 3)

    # Add 3 low-scoring answers in SQL Joins
    for i in range(3):
        db.save_answer(
            session_id=session_id,
            user_id=user_id,
            question_id=f"SQL-0{i}",
            question_text="Join question",
            subject="SQL",
            topic="Joins",
            difficulty="Beginner",
            user_answer="Inner join connects tables.",
            score=4.0,
            concepts_covered=["INNER JOIN"],
            concepts_missing=["LEFT JOIN", "NULL values", "FULL OUTER JOIN"],
            feedback="Omitted outer join mechanics.",
            reference_answer="Ref",
            evaluation_mode="rule_based"
        )

    recs = engine.generate_recommendations(user_id)
    assert len(recs) > 0

    # There should be a targeted practice recommendation for Joins
    join_rec = next((r for r in recs if "Joins" in r["title"]), None)
    assert join_rec is not None
    assert join_rec["type"] == "Targeted Practice"
    assert "4.0/10" in join_rec["tag"]
