import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from database.db import DatabaseManager, get_db

PROJECT_CATEGORIES = [
    "Machine Learning",
    "Web Development",
    "Data Analytics",
    "UI/UX Design",
    "Mobile Development",
    "Academic",
    "Research",
    "Other",
]

PROJECT_STATUSES = [
    "Not Started",
    "In Progress",
    "On Hold",
    "Completed",
]

PROJECT_PRIORITIES = [
    "Low",
    "Medium",
    "High",
]

TASK_STATUSES = [
    "To Do",
    "In Progress",
    "Completed",
]


class ProjectService:
    """Service for validating, processing, and managing student personal projects and tasks."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or get_db()

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL structure if provided."""
        if not url or not url.strip():
            return True
        u = url.strip()
        # Accept http, https, or common domain patterns like github.com/...
        pattern = r"^(https?:\/\/)?([\w\d\-]+\.)+[\w\d\-]+(\/.*)?$"
        return bool(re.match(pattern, u, re.IGNORECASE))

    @staticmethod
    def normalize_url(url: str) -> str:
        """Ensure URL has https:// prefix if non-empty and missing scheme."""
        if not url or not url.strip():
            return ""
        u = url.strip()
        if not u.startswith("http://") and not u.startswith("https://"):
            return f"https://{u}"
        return u

    def validate_project_data(
        self,
        name: str,
        category: str,
        start_date: str = "",
        target_deadline: str = "",
        github_url: str = "",
        demo_url: str = "",
    ) -> Tuple[bool, str]:
        """Validate project fields before saving."""
        if not name or len(name.strip()) < 2:
            return False, "Project name must be at least 2 characters long."

        if category not in PROJECT_CATEGORIES:
            return False, f"Please select a valid category from: {', '.join(PROJECT_CATEGORIES)}"

        # Validate dates if both provided
        if start_date and target_deadline:
            try:
                s_dt = datetime.strptime(start_date, "%Y-%m-%d")
                d_dt = datetime.strptime(target_deadline, "%Y-%m-%d")
                if s_dt > d_dt:
                    return False, "Target deadline cannot be earlier than the project start date."
            except ValueError:
                return False, "Invalid date format. Expected YYYY-MM-DD."

        if github_url and not self.validate_url(github_url):
            return False, "Invalid GitHub URL format."

        if demo_url and not self.validate_url(demo_url):
            return False, "Invalid live demo URL format."

        return True, ""

    def create_project(
        self,
        user_id: int,
        name: str,
        description: str = "",
        category: str = "Web Development",
        tech_stack: str = "",
        start_date: str = "",
        target_deadline: str = "",
        priority: str = "Medium",
        status: str = "Not Started",
        github_url: str = "",
        demo_url: str = "",
        notes: str = "",
    ) -> Tuple[bool, str, Optional[int]]:
        """Validate and create a project."""
        is_valid, err = self.validate_project_data(
            name=name,
            category=category,
            start_date=start_date,
            target_deadline=target_deadline,
            github_url=github_url,
            demo_url=demo_url,
        )
        if not is_valid:
            return False, err, None

        norm_github = self.normalize_url(github_url)
        norm_demo = self.normalize_url(demo_url)

        try:
            pid = self.db.create_project(
                user_id=user_id,
                name=name,
                description=description,
                category=category,
                tech_stack=tech_stack,
                start_date=start_date,
                target_deadline=target_deadline,
                priority=priority if priority in PROJECT_PRIORITIES else "Medium",
                status=status if status in PROJECT_STATUSES else "Not Started",
                github_url=norm_github,
                demo_url=norm_demo,
                notes=notes,
            )
            return True, "Project created successfully!", pid
        except Exception as e:
            return False, f"Database error: {str(e)}", None

    def update_project(
        self,
        project_id: int,
        user_id: int,
        name: str,
        description: str,
        category: str,
        tech_stack: str,
        start_date: str,
        target_deadline: str,
        priority: str,
        status: str,
        github_url: str = "",
        demo_url: str = "",
        notes: str = "",
    ) -> Tuple[bool, str]:
        """Validate and update an existing project."""
        is_valid, err = self.validate_project_data(
            name=name,
            category=category,
            start_date=start_date,
            target_deadline=target_deadline,
            github_url=github_url,
            demo_url=demo_url,
        )
        if not is_valid:
            return False, err

        norm_github = self.normalize_url(github_url)
        norm_demo = self.normalize_url(demo_url)

        updated = self.db.update_project(
            project_id=project_id,
            user_id=user_id,
            name=name,
            description=description,
            category=category,
            tech_stack=tech_stack,
            start_date=start_date,
            target_deadline=target_deadline,
            priority=priority,
            status=status,
            github_url=norm_github,
            demo_url=norm_demo,
            notes=notes,
        )
        if updated:
            return True, "Project updated successfully!"
        return False, "Project not found or unauthorized."

    def delete_project(self, project_id: int, user_id: int) -> bool:
        """Delete project and associated tasks."""
        return self.db.delete_project(project_id, user_id)

    def get_project_with_details(self, project_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Fetch project details along with calculated task progress."""
        proj = self.db.get_project(project_id, user_id)
        if not proj:
            return None

        total, completed, progress = self.db.get_project_task_counts(project_id, user_id)
        today = datetime.now().strftime("%Y-%m-%d")
        is_overdue = bool(
            proj["target_deadline"]
            and proj["target_deadline"] < today
            and proj["status"] != "Completed"
        )

        proj["total_tasks"] = total
        proj["completed_tasks"] = completed
        proj["progress"] = progress
        proj["is_overdue"] = is_overdue
        return proj

    def get_user_projects_enriched(
        self,
        user_id: int,
        status: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "updated_desc",
    ) -> List[Dict[str, Any]]:
        """Fetch list of user projects enriched with progress and overdue indicators."""
        projects = self.db.get_user_projects(
            user_id=user_id,
            status=status,
            category=category,
            priority=priority,
            search=search,
            sort_by=sort_by,
        )

        today = datetime.now().strftime("%Y-%m-%d")
        enriched = []
        for p in projects:
            total, completed, progress = self.db.get_project_task_counts(p["id"], user_id)
            p["total_tasks"] = total
            p["completed_tasks"] = completed
            p["progress"] = progress
            p["is_overdue"] = bool(
                p["target_deadline"]
                and p["target_deadline"] < today
                and p["status"] != "Completed"
            )
            enriched.append(p)

        # Handle progress sorting in Python if requested
        if sort_by == "progress_desc":
            enriched.sort(key=lambda x: x["progress"], reverse=True)
        elif sort_by == "progress_asc":
            enriched.sort(key=lambda x: x["progress"])

        return enriched

    # Tasks
    def add_task(
        self,
        project_id: int,
        user_id: int,
        title: str,
        description: str = "",
        due_date: str = "",
        priority: str = "Medium",
        status: str = "To Do",
    ) -> Tuple[bool, str, Optional[int]]:
        """Validate and create a task under project."""
        if not title or len(title.strip()) < 2:
            return False, "Task title must be at least 2 characters long.", None

        if status not in TASK_STATUSES:
            status = "To Do"
        if priority not in PROJECT_PRIORITIES:
            priority = "Medium"

        try:
            tid = self.db.create_project_task(
                project_id=project_id,
                user_id=user_id,
                title=title,
                description=description,
                due_date=due_date,
                priority=priority,
                status=status,
            )
            return True, "Task added!", tid
        except PermissionError:
            return False, "Unauthorized project access.", None
        except Exception as e:
            return False, f"Database error: {str(e)}", None

    def toggle_task_status(self, task_id: int, user_id: int) -> bool:
        """Toggle task status between Completed and To Do."""
        task = self.db.get_task(task_id, user_id)
        if not task:
            return False
        new_status = "To Do" if task["status"] == "Completed" else "Completed"
        return self.db.update_project_task(task_id, user_id, status=new_status)

    def update_task(
        self,
        task_id: int,
        user_id: int,
        title: str,
        description: str = "",
        due_date: str = "",
        priority: str = "Medium",
        status: str = "To Do",
    ) -> Tuple[bool, str]:
        """Update an existing task."""
        if not title or len(title.strip()) < 2:
            return False, "Task title must be at least 2 characters long."

        ok = self.db.update_project_task(
            task_id=task_id,
            user_id=user_id,
            title=title,
            description=description,
            due_date=due_date,
            priority=priority,
            status=status,
        )
        if ok:
            return True, "Task updated successfully!"
        return False, "Task not found or unauthorized."

    def delete_task(self, task_id: int, user_id: int) -> bool:
        """Delete task."""
        return self.db.delete_project_task(task_id, user_id)

    def get_project_tasks_enriched(self, project_id: int, user_id: int) -> List[Dict[str, Any]]:
        """Fetch tasks enriched with overdue flag."""
        tasks = self.db.get_project_tasks(project_id, user_id)
        today = datetime.now().strftime("%Y-%m-%d")
        for t in tasks:
            t["is_overdue"] = bool(
                t["due_date"]
                and t["due_date"] < today
                and t["status"] != "Completed"
            )
        return tasks
