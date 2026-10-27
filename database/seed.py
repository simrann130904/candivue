"""Optional database seeder providing a realistic demo student profile for demonstration purposes."""
import json
from database.db import get_db
from services.auth import AuthService


def seed_demo_data():
    db = get_db()
    auth = AuthService(db)

    demo_email = "demo@candivue.edu"
    existing = db.get_user_by_email(demo_email)
    if existing:
        user_id = existing["id"]
    else:
        # Register demo user
        pwd_hash = auth.hash_password("candivue2026")
        user_id = db.create_user(demo_email, "Adam William", pwd_hash)
        if not user_id:
            return None

    # Check if sessions already exist
    sessions = db.get_user_sessions(user_id)
    if not sessions:
        # Session 1: Python Programming (Intermediate) - Score 8.2
        s1_id = db.create_session(user_id, "Python Programming", "Intermediate", 2)
        db.save_answer(
            session_id=s1_id,
            user_id=user_id,
            question_id="PY-INT-01",
            question_text="Explain how Python generators work using the yield keyword and why they are memory efficient compared to returning lists.",
            subject="Python Programming",
            topic="Generators & Iteration",
            difficulty="Intermediate",
            user_answer="Generators use the yield keyword to produce values lazily on demand. Unlike functions that return a full list taking O(N) memory, generators maintain state and pause execution, giving O(1) memory efficiency.",
            score=8.5,
            concepts_covered=["yield", "generator function", "lazy evaluation", "memory efficiency", "state preservation"],
            concepts_missing=["iterator protocol"],
            feedback="🌟 Excellent explanation! You highlighted lazy evaluation and O(1) memory advantages cleanly.",
            reference_answer="A Python generator is an iterator created using yield. Execution pauses at yield preserving local state, enabling O(1) auxiliary memory.",
            evaluation_mode="Rule-Based Engine"
        )
        db.save_answer(
            session_id=s1_id,
            user_id=user_id,
            question_id="PY-INT-02",
            question_text="What is a decorator in Python, how does it work, and why should you use functools.wraps?",
            subject="Python Programming",
            topic="Decorators",
            difficulty="Intermediate",
            user_answer="A decorator is a function that wraps another function to add behavior using @ syntax. functools.wraps preserves metadata like __name__ and __doc__.",
            score=8.0,
            concepts_covered=["first-class functions", "wrapper function", "functools.wraps", "preserves metadata docstring name"],
            concepts_missing=["higher-order function"],
            feedback="👍 Strong answer. Clearly covered wrapping mechanics and metadata retention with functools.wraps.",
            reference_answer="A decorator is a higher-order function taking a function and returning a wrapper. functools.wraps copies name and docstrings.",
            evaluation_mode="Rule-Based Engine"
        )
        db.complete_session(s1_id, user_id, 8.25)

        # Session 2: SQL (Beginner) - Score 6.5
        s2_id = db.create_session(user_id, "SQL", "Beginner", 2)
        db.save_answer(
            session_id=s2_id,
            user_id=user_id,
            question_id="SQL-BEG-01",
            question_text="What is the difference between the WHERE clause and the HAVING clause in SQL?",
            subject="SQL",
            topic="Filtering & Aggregation",
            difficulty="Beginner",
            user_answer="WHERE filters rows before grouping, and HAVING filters after GROUP BY with aggregate functions.",
            score=7.5,
            concepts_covered=["WHERE filters individual rows", "HAVING filters aggregated groups", "aggregate functions in HAVING"],
            concepts_missing=["execution before vs after GROUP BY", "performance order of execution"],
            feedback="👍 Good grasp of row filtering vs group filtering.",
            reference_answer="WHERE filters individual rows prior to aggregation, while HAVING filters aggregated groups after GROUP BY.",
            evaluation_mode="Rule-Based Engine"
        )
        db.save_answer(
            session_id=s2_id,
            user_id=user_id,
            question_id="SQL-BEG-02",
            question_text="Explain the differences between INNER JOIN, LEFT JOIN, and FULL OUTER JOIN with examples.",
            subject="SQL",
            topic="Joins",
            difficulty="Beginner",
            user_answer="INNER JOIN gives matched rows. LEFT JOIN gives all left rows. I forget the exact full join syntax.",
            score=5.5,
            concepts_covered=["INNER JOIN matches both tables", "LEFT JOIN all left rows plus matching right"],
            concepts_missing=["NULL values for non-matches", "FULL OUTER JOIN all rows from both tables"],
            feedback="⚠️ Partially correct. Make sure to explain NULL padding on unmatched outer join rows.",
            reference_answer="INNER JOIN returns matching rows from both tables. LEFT JOIN returns all left rows plus matching right rows with NULL for non-matches. FULL OUTER JOIN returns all rows from both.",
            evaluation_mode="Rule-Based Engine"
        )
        db.complete_session(s2_id, user_id, 6.5)

    # Seed demo personal projects if none exist for user
    existing_projs = db.get_user_projects(user_id)
    if not existing_projs:
        p1 = db.create_project(
            user_id=user_id,
            name="Distributed Asynchronous Task Queue",
            description="A lightweight distributed job worker framework utilizing Redis streams, dead-letter queues, and round-robin worker dispatch.",
            category="Web Development",
            tech_stack="Python, Redis, Docker, Pytest",
            start_date="2026-01-10",
            target_deadline="2026-05-15",
            priority="High",
            status="In Progress",
            github_url="https://github.com/adam-william/py-task-queue",
            demo_url="",
            notes="Designed to showcase distributed systems concepts during placement interviews.",
        )
        db.create_project_task(p1, user_id, "Redis connection pool & stream consumer group", priority="High", status="Completed")
        db.create_project_task(p1, user_id, "Dead-letter retry queue exponential backoff", priority="High", status="Completed")
        db.create_project_task(p1, user_id, "Worker heartbeat and leader election monitoring", priority="Medium", status="To Do")

        p2 = db.create_project(
            user_id=user_id,
            name="Resume Skill Matcher & ATS Scorer",
            description="NLP-based parsing engine extracting candidate competencies and scoring alignment with job descriptions using TF-IDF and cosine similarity.",
            category="Machine Learning",
            tech_stack="Python, spaCy, FastAPI, Scikit-learn",
            start_date="2025-11-01",
            target_deadline="2026-02-28",
            priority="Medium",
            status="Completed",
            github_url="https://github.com/adam-william/resume-scorer",
            demo_url="https://ats-scorer.demo.app",
            notes="Completed pilot testing with 50 sample tech resumes.",
        )
        db.create_project_task(p2, user_id, "Regex & spaCy entity extraction pipeline", priority="Medium", status="Completed")
        db.create_project_task(p2, user_id, "Cosine similarity scoring algorithm", priority="High", status="Completed")
        db.create_project_task(p2, user_id, "FastAPI REST endpoint & documentation", priority="Low", status="Completed")

    return user_id


if __name__ == "__main__":
    uid = seed_demo_data()
    print(f"Seed completed. Demo user ID: {uid}")
