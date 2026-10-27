import os
import gc
import tempfile
import pytest
from database.db import DatabaseManager
from services.projects import ProjectService


@pytest.fixture
def test_setup():
    """Setup isolated DB and ProjectService."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = DatabaseManager(db_path=path)
    service = ProjectService(db=db)

    # Create two test users
    user_a = db.create_user("student_a@campus.edu", "Alice Student", "hash123")
    user_b = db.create_user("student_b@campus.edu", "Bob Student", "hash456")

    yield db, service, user_a, user_b

    del service
    del db
    gc.collect()
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def test_create_and_get_project(test_setup):
    """Test creating a project with valid data and retrieving it."""
    db, service, user_a, _ = test_setup

    ok, msg, pid = service.create_project(
        user_id=user_a,
        name="Campus Placement Tracker",
        description="A dashboard for tracking company application cycles.",
        category="Web Development",
        tech_stack="Python, Streamlit, SQLite",
        start_date="2026-01-01",
        target_deadline="2026-06-30",
        priority="High",
        status="In Progress",
        github_url="https://github.com/alice/tracker",
        demo_url="https://tracker.demo.app",
        notes="Targeting top tier product companies."
    )

    assert ok is True
    assert pid is not None

    proj = service.get_project_with_details(pid, user_a)
    assert proj is not None
    assert proj["name"] == "Campus Placement Tracker"
    assert proj["priority"] == "High"
    assert proj["status"] == "In Progress"
    assert proj["total_tasks"] == 0
    assert proj["progress"] == 0.0


def test_project_validation_errors(test_setup):
    """Test validation errors for empty name, inverted dates, and invalid URLs."""
    db, service, user_a, _ = test_setup

    # Empty name
    ok, msg, _ = service.create_project(user_a, name=" ")
    assert ok is False
    assert "at least 2 characters" in msg

    # Inverted dates (deadline before start)
    ok, msg, _ = service.create_project(
        user_a,
        name="Valid Name",
        start_date="2026-05-01",
        target_deadline="2026-02-01"
    )
    assert ok is False
    assert "Target deadline cannot be earlier" in msg

    # Invalid URL
    ok, msg, _ = service.create_project(
        user_a,
        name="Valid Name",
        github_url="not_a_valid_url_@@@"
    )
    assert ok is False
    assert "Invalid GitHub URL" in msg


def test_task_management_and_progress_calculation(test_setup):
    """Test adding tasks, toggling completion, and verifying automatic progress calculation."""
    db, service, user_a, _ = test_setup

    ok, _, pid = service.create_project(user_a, name="ML Fraud Detection", category="Machine Learning")
    assert ok is True

    # Initial progress should be 0.0%
    proj = service.get_project_with_details(pid, user_a)
    assert proj["progress"] == 0.0
    assert proj["total_tasks"] == 0

    # Add 4 tasks
    t1_ok, _, t1 = service.add_task(pid, user_a, title="Data Cleaning & EDA", priority="High")
    t2_ok, _, t2 = service.add_task(pid, user_a, title="Feature Engineering", priority="Medium")
    t3_ok, _, t3 = service.add_task(pid, user_a, title="Model Training XGBoost", priority="High")
    t4_ok, _, t4 = service.add_task(pid, user_a, title="Streamlit Dashboard", priority="Low")

    assert t1_ok and t2_ok and t3_ok and t4_ok

    # Check 0 of 4 completed -> 0%
    proj = service.get_project_with_details(pid, user_a)
    assert proj["total_tasks"] == 4
    assert proj["completed_tasks"] == 0
    assert proj["progress"] == 0.0

    # Mark 2 tasks completed
    service.toggle_task_status(t1, user_a)
    service.toggle_task_status(t2, user_a)

    # 2 of 4 completed -> 50%
    proj = service.get_project_with_details(pid, user_a)
    assert proj["completed_tasks"] == 2
    assert proj["progress"] == 50.0

    # Mark 3rd task completed -> 75%
    service.toggle_task_status(t3, user_a)
    proj = service.get_project_with_details(pid, user_a)
    assert proj["completed_tasks"] == 3
    assert proj["progress"] == 75.0

    # Reopen 1st task -> back to 50%
    service.toggle_task_status(t1, user_a)
    proj = service.get_project_with_details(pid, user_a)
    assert proj["completed_tasks"] == 2
    assert proj["progress"] == 50.0


def test_user_data_isolation(test_setup):
    """Verify that User B cannot see, modify, or delete User A's projects or tasks."""
    db, service, user_a, user_b = test_setup

    ok, _, pid = service.create_project(user_a, name="User A Secret Project")
    assert ok is True
    _, _, tid = service.add_task(pid, user_a, title="Confidential Task")

    # User B tries to view User A's project
    b_proj = service.get_project_with_details(pid, user_b)
    assert b_proj is None

    # User B tries to get list of projects
    b_list = service.get_user_projects_enriched(user_b)
    assert len(b_list) == 0

    # User B tries to update User A's project
    up_ok, _ = service.update_project(pid, user_b, name="Hacked Name", description="", category="Other", tech_stack="", start_date="", target_deadline="", priority="Low", status="Completed")
    assert up_ok is False
    assert service.get_project_with_details(pid, user_a)["name"] == "User A Secret Project"

    # User B tries to delete User A's project
    del_ok = service.delete_project(pid, user_b)
    assert del_ok is False
    assert service.get_project_with_details(pid, user_a) is not None

    # User B tries to add task to User A's project
    add_t_ok, _, _ = service.add_task(pid, user_b, title="Unauthorized Task")
    assert add_t_ok is False

    # User B tries to toggle User A's task
    tog_ok = service.toggle_task_status(tid, user_b)
    assert tog_ok is False


def test_delete_project_cascades_tasks(test_setup):
    """Verify deleting a project removes its tasks."""
    db, service, user_a, _ = test_setup

    _, _, pid = service.create_project(user_a, name="Temporary Project")
    _, _, tid = service.add_task(pid, user_a, title="Temporary Task")

    assert service.get_project_with_details(pid, user_a) is not None
    assert db.get_task(tid, user_a) is not None

    deleted = service.delete_project(pid, user_a)
    assert deleted is True

    assert service.get_project_with_details(pid, user_a) is None
    assert db.get_task(tid, user_a) is None
