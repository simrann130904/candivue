import os
import gc
import tempfile
import pytest
from database.db import DatabaseManager
from services.auth import AuthService
from services.evaluator import AnswerEvaluator
from services.analytics import AnalyticsService
from services.recommendations import RecommendationEngine


def test_complete_interview_lifecycle():
    """End-to-end test simulating a complete student journey from registration to analytics."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = DatabaseManager(db_path=path)
    auth = AuthService(db)
    evaluator = AnswerEvaluator()
    analytics = AnalyticsService(db)
    recs = RecommendationEngine(db)

    # 1. Student Registration
    ok, msg, user = auth.register_user(
        email="rahul.verma@college.edu",
        full_name="Rahul Verma",
        password="CollegePassword123!",
        confirm_password="CollegePassword123!"
    )
    assert ok is True
    assert user["id"] is not None
    user_id = user["id"]

    # 2. Check Empty State Analytics
    summary_initial = analytics.get_dashboard_summary(user_id)
    assert summary_initial["has_data"] is False
    assert summary_initial["questions_attempted"] == 0

    # Cold start recommendations
    initial_recs = recs.generate_recommendations(user_id)
    assert len(initial_recs) >= 2

    # 3. Start Mock Interview (Computer Networks)
    session_id = db.create_session(
        user_id=user_id,
        subject="Computer Networks",
        difficulty="Beginner",
        question_count=2
    )
    assert session_id is not None

    # 4. Answer Question 1 (TCP vs UDP)
    q1 = {
        "id": "CN-BEG-02",
        "subject": "Computer Networks",
        "topic": "Transport Protocols",
        "difficulty": "Beginner",
        "question": "What are the primary differences between TCP and UDP?",
        "expected_concepts": [
            "Connection-oriented vs connectionless",
            "Reliability acknowledgments retransmissions",
            "Three-way handshake SYN SYN-ACK ACK",
            "Ordering sequencing flow control",
            "Low latency lightweight header streaming gaming DNS"
        ],
        "reference_answer": "TCP is connection-oriented and reliable using 3-way handshake SYN SYN-ACK ACK. UDP is connectionless with low latency.",
        "evaluation_criteria": "Must cover connection-oriented vs connectionless, reliability, and use cases.",
    }
    user_ans_1 = "TCP is connection-oriented and reliable, establishing connections with a three-way handshake SYN SYN-ACK ACK. It provides sequencing and flow control. UDP is connectionless, faster, with lightweight headers for streaming and gaming."
    res1 = evaluator.evaluate_rule_based(q1, user_ans_1)
    assert res1.score >= 7.0

    db.save_answer(
        session_id=session_id,
        user_id=user_id,
        question_id=q1["id"],
        question_text=q1["question"],
        subject=q1["subject"],
        topic=q1["topic"],
        difficulty=q1["difficulty"],
        user_answer=user_ans_1,
        score=res1.score,
        concepts_covered=res1.concepts_covered,
        concepts_missing=res1.concepts_missing,
        feedback=res1.feedback,
        reference_answer=res1.reference_answer,
        evaluation_mode=res1.evaluation_mode
    )

    # 5. Answer Question 2 (Partial answer)
    user_ans_2 = "The OSI model has 7 layers including Physical, Data Link, Network, and Transport. The TCP/IP model has 4 layers which combine these."
    q2 = {
        "id": "CN-BEG-01",
        "subject": "Computer Networks",
        "topic": "Network Models",
        "difficulty": "Beginner",
        "question": "Compare the 7 layers of OSI with the 4 layers of TCP/IP.",
        "expected_concepts": [
            "Physical Data Link Network Transport Session Presentation Application",
            "TCP/IP Network Interface Internet Transport Application",
            "Encapsulation headers payloads",
            "Packets frames segments bits"
        ],
        "reference_answer": "OSI 7 layers vs TCP/IP 4 layers.",
        "evaluation_criteria": "Details required.",
    }
    res2 = evaluator.evaluate_rule_based(q2, user_ans_2)
    assert 3.0 <= res2.score <= 7.0

    db.save_answer(
        session_id=session_id,
        user_id=user_id,
        question_id=q2["id"],
        question_text=q2["question"],
        subject=q2["subject"],
        topic=q2["topic"],
        difficulty=q2["difficulty"],
        user_answer=user_ans_2,
        score=res2.score,
        concepts_covered=res2.concepts_covered,
        concepts_missing=res2.concepts_missing,
        feedback=res2.feedback,
        reference_answer=res2.reference_answer,
        evaluation_mode=res2.evaluation_mode
    )

    # 6. Complete Session
    avg_score = (res1.score + res2.score) / 2
    completed = db.complete_session(session_id, user_id, avg_score)
    assert completed is True

    # 7. Verify Dashboard Analytics reflect new data
    summary_after = analytics.get_dashboard_summary(user_id)
    assert summary_after["has_data"] is True
    assert summary_after["questions_attempted"] == 2
    assert summary_after["interviews_completed"] == 1
    assert summary_after["average_score"] == round(avg_score, 1)

    # 8. Verify History Retrieval
    sessions = db.get_user_sessions(user_id)
    assert len(sessions) == 1
    assert sessions[0]["status"] == "completed"

    session_answers = db.get_session_answers(session_id, user_id)
    assert len(session_answers) == 2

    # Cleanup
    del db
    del auth
    del evaluator
    del analytics
    del recs
    gc.collect()
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
