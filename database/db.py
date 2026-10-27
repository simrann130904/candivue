import os
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple


class DatabaseManager:
    """Manages SQLite database connections and operations for Candivue."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            self.db_path = os.environ.get("CANDIVUE_DB_PATH", "candivue.db")
        else:
            self.db_path = db_path
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Create and return a configured SQLite connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def close(self) -> None:
        """Explicitly clear database resources if needed."""
        pass

    def init_db(self) -> None:
        """Create tables and indexes if they do not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL COLLATE NOCASE,
                    full_name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # User Preferences
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id INTEGER PRIMARY KEY,
                    theme TEXT DEFAULT 'dark',
                    api_key TEXT DEFAULT '',
                    preferred_difficulty TEXT DEFAULT 'Intermediate',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
            """)

            # Interview Sessions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS interview_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    subject TEXT NOT NULL,
                    difficulty TEXT NOT NULL,
                    question_count INTEGER NOT NULL,
                    status TEXT DEFAULT 'in_progress',
                    average_score REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
            """)

            # Interview Answers
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS interview_answers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    question_id TEXT NOT NULL,
                    question_text TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    difficulty TEXT NOT NULL,
                    user_answer TEXT NOT NULL,
                    score REAL NOT NULL,
                    concepts_covered TEXT,
                    concepts_missing TEXT,
                    feedback TEXT,
                    reference_answer TEXT,
                    evaluation_mode TEXT DEFAULT 'rule_based',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES interview_sessions(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
            """)

            # Indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON interview_sessions(user_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_status ON interview_sessions(status);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_answers_session_id ON interview_answers(session_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_answers_user_id ON interview_answers(user_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_answers_subject ON interview_answers(subject);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_answers_topic ON interview_answers(topic);")

            # Personal Projects
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    category TEXT NOT NULL,
                    tech_stack TEXT DEFAULT '',
                    start_date TEXT DEFAULT '',
                    target_deadline TEXT DEFAULT '',
                    priority TEXT DEFAULT 'Medium',
                    status TEXT DEFAULT 'Not Started',
                    github_url TEXT DEFAULT '',
                    demo_url TEXT DEFAULT '',
                    notes TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
            """)

            # Project Tasks & Milestones
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    due_date TEXT DEFAULT '',
                    priority TEXT DEFAULT 'Medium',
                    status TEXT DEFAULT 'To Do',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_category ON projects(category);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON project_tasks(project_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON project_tasks(user_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON project_tasks(status);")

            conn.commit()

    # User CRUD
    def create_user(self, email: str, full_name: str, password_hash: str) -> Optional[int]:
        """Insert a new user. Returns user_id if successful, None if email already exists."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (email, full_name, password_hash) VALUES (?, ?, ?)",
                    (email.strip().lower(), full_name.strip(), password_hash),
                )
                user_id = cursor.lastrowid
                cursor.execute(
                    "INSERT INTO user_preferences (user_id, theme, preferred_difficulty) VALUES (?, 'dark', 'Intermediate')",
                    (user_id,),
                )
                conn.commit()
                return user_id
        except sqlite3.IntegrityError:
            return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Retrieve user record by email."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, email, full_name, password_hash, created_at FROM users WHERE email = ?",
                (email.strip().lower(),),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve user record by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, email, full_name, password_hash, created_at FROM users WHERE id = ?",
                (user_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    # User Preferences
    def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Fetch preferences for a given user."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT theme, api_key, preferred_difficulty FROM user_preferences WHERE user_id = ?",
                (user_id,),
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return {"theme": "dark", "api_key": "", "preferred_difficulty": "Intermediate"}

    def update_user_preferences(self, user_id: int, theme: Optional[str] = None, api_key: Optional[str] = None, preferred_difficulty: Optional[str] = None) -> bool:
        """Update user preferences."""
        current = self.get_user_preferences(user_id)
        new_theme = theme if theme is not None else current.get("theme", "dark")
        new_api_key = api_key if api_key is not None else current.get("api_key", "")
        new_diff = preferred_difficulty if preferred_difficulty is not None else current.get("preferred_difficulty", "Intermediate")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_preferences (user_id, theme, api_key, preferred_difficulty, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    theme = excluded.theme,
                    api_key = excluded.api_key,
                    preferred_difficulty = excluded.preferred_difficulty,
                    updated_at = CURRENT_TIMESTAMP
            """, (user_id, new_theme, new_api_key, new_diff))
            conn.commit()
            return True

    # Interview Sessions
    def create_session(self, user_id: int, subject: str, difficulty: str, question_count: int) -> int:
        """Create a new in-progress interview session."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO interview_sessions (user_id, subject, difficulty, question_count, status)
                   VALUES (?, ?, ?, ?, 'in_progress')""",
                (user_id, subject, difficulty, question_count),
            )
            conn.commit()
            return cursor.lastrowid

    def get_session(self, session_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a specific session ensuring user isolation."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM interview_sessions WHERE id = ? AND user_id = ?",
                (session_id, user_id),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_user_sessions(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get sessions for a specific user ordered by creation time descending."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM interview_sessions 
                   WHERE user_id = ? 
                   ORDER BY created_at DESC LIMIT ?""",
                (user_id, limit),
            )
            return [dict(r) for r in cursor.fetchall()]

    def complete_session(self, session_id: int, user_id: int, average_score: float) -> bool:
        """Mark an interview session as completed and record average score."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE interview_sessions
                   SET status = 'completed',
                       average_score = ?,
                       completed_at = CURRENT_TIMESTAMP
                   WHERE id = ? AND user_id = ?""",
                (round(average_score, 2), session_id, user_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    # Interview Answers
    def save_answer(
        self,
        session_id: int,
        user_id: int,
        question_id: str,
        question_text: str,
        subject: str,
        topic: str,
        difficulty: str,
        user_answer: str,
        score: float,
        concepts_covered: List[str],
        concepts_missing: List[str],
        feedback: str,
        reference_answer: str,
        evaluation_mode: str = "rule_based",
    ) -> int:
        """Record an evaluated answer to the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO interview_answers 
                   (session_id, user_id, question_id, question_text, subject, topic, difficulty, 
                    user_answer, score, concepts_covered, concepts_missing, feedback, reference_answer, evaluation_mode)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    session_id,
                    user_id,
                    question_id,
                    question_text,
                    subject,
                    topic,
                    difficulty,
                    user_answer,
                    round(score, 1),
                    json.dumps(concepts_covered),
                    json.dumps(concepts_missing),
                    feedback,
                    reference_answer,
                    evaluation_mode,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def get_session_answers(self, session_id: int, user_id: int) -> List[Dict[str, Any]]:
        """Get all answers for a specific session ensuring user isolation."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM interview_answers 
                   WHERE session_id = ? AND user_id = ? 
                   ORDER BY id ASC""",
                (session_id, user_id),
            )
            results = []
            for row in cursor.fetchall():
                data = dict(row)
                data["concepts_covered"] = json.loads(data["concepts_covered"]) if data["concepts_covered"] else []
                data["concepts_missing"] = json.loads(data["concepts_missing"]) if data["concepts_missing"] else []
                results.append(data)
            return results

    def get_user_answers(self, user_id: int, limit: int = 500) -> List[Dict[str, Any]]:
        """Fetch all answers submitted by a user for analytics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM interview_answers 
                   WHERE user_id = ? 
                   ORDER BY created_at DESC LIMIT ?""",
                (user_id, limit),
            )
            results = []
            for row in cursor.fetchall():
                data = dict(row)
                data["concepts_covered"] = json.loads(data["concepts_covered"]) if data["concepts_covered"] else []
                data["concepts_missing"] = json.loads(data["concepts_missing"]) if data["concepts_missing"] else []
                results.append(data)
            return results

    # ==========================================
    # Personal Projects CRUD
    # ==========================================
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
    ) -> int:
        """Create a new personal project belonging strictly to user_id."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO projects 
                   (user_id, name, description, category, tech_stack, start_date, target_deadline, 
                    priority, status, github_url, demo_url, notes, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
                (
                    user_id,
                    name.strip(),
                    description.strip(),
                    category.strip(),
                    tech_stack.strip(),
                    start_date.strip(),
                    target_deadline.strip(),
                    priority.strip(),
                    status.strip(),
                    github_url.strip(),
                    demo_url.strip(),
                    notes.strip(),
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def get_project(self, project_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a specific project with user isolation."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM projects WHERE id = ? AND user_id = ?",
                (project_id, user_id),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_user_projects(
        self,
        user_id: int,
        status: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "updated_desc",
    ) -> List[Dict[str, Any]]:
        """Retrieve user projects with optional filtering and sorting."""
        query = "SELECT * FROM projects WHERE user_id = ?"
        params: List[Any] = [user_id]

        if status and status != "All Statuses" and status != "All":
            query += " AND status = ?"
            params.append(status)

        if category and category != "All Categories" and category != "All":
            query += " AND category = ?"
            params.append(category)

        if priority and priority != "All Priorities" and priority != "All":
            query += " AND priority = ?"
            params.append(priority)

        if search and search.strip():
            s = f"%{search.strip().lower()}%"
            query += " AND (LOWER(name) LIKE ? OR LOWER(description) LIKE ? OR LOWER(tech_stack) LIKE ?)"
            params.extend([s, s, s])

        if sort_by == "deadline_asc":
            query += " ORDER BY CASE WHEN target_deadline IS NULL OR target_deadline = '' THEN 1 ELSE 0 END, target_deadline ASC"
        elif sort_by == "deadline_desc":
            query += " ORDER BY target_deadline DESC"
        elif sort_by == "name_asc":
            query += " ORDER BY name ASC COLLATE NOCASE"
        else:
            query += " ORDER BY updated_at DESC, id DESC"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            return [dict(r) for r in cursor.fetchall()]

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
    ) -> bool:
        """Update an existing project owned by user_id."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE projects SET
                   name = ?,
                   description = ?,
                   category = ?,
                   tech_stack = ?,
                   start_date = ?,
                   target_deadline = ?,
                   priority = ?,
                   status = ?,
                   github_url = ?,
                   demo_url = ?,
                   notes = ?,
                   updated_at = CURRENT_TIMESTAMP
                   WHERE id = ? AND user_id = ?""",
                (
                    name.strip(),
                    description.strip(),
                    category.strip(),
                    tech_stack.strip(),
                    start_date.strip(),
                    target_deadline.strip(),
                    priority.strip(),
                    status.strip(),
                    github_url.strip(),
                    demo_url.strip(),
                    notes.strip(),
                    project_id,
                    user_id,
                ),
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_project(self, project_id: int, user_id: int) -> bool:
        """Delete a project and all associated tasks with user isolation."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM project_tasks WHERE project_id = ? AND user_id = ?",
                (project_id, user_id),
            )
            cursor.execute(
                "DELETE FROM projects WHERE id = ? AND user_id = ?",
                (project_id, user_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    # ==========================================
    # Project Tasks & Milestones CRUD
    # ==========================================
    def create_project_task(
        self,
        project_id: int,
        user_id: int,
        title: str,
        description: str = "",
        due_date: str = "",
        priority: str = "Medium",
        status: str = "To Do",
    ) -> int:
        """Add a task to a project ensuring user ownership."""
        # Verify project belongs to user
        proj = self.get_project(project_id, user_id)
        if not proj:
            raise PermissionError("Project does not exist or belong to the authenticated user.")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO project_tasks
                   (project_id, user_id, title, description, due_date, priority, status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
                (
                    project_id,
                    user_id,
                    title.strip(),
                    description.strip(),
                    due_date.strip(),
                    priority.strip(),
                    status.strip(),
                ),
            )
            # Touch project updated_at
            cursor.execute(
                "UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
                (project_id, user_id),
            )
            conn.commit()
            return cursor.lastrowid

    def get_project_tasks(self, project_id: int, user_id: int) -> List[Dict[str, Any]]:
        """Fetch all tasks for a project strictly scoped to user_id."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM project_tasks 
                   WHERE project_id = ? AND user_id = ? 
                   ORDER BY 
                     CASE status WHEN 'To Do' THEN 1 WHEN 'In Progress' THEN 2 ELSE 3 END,
                     CASE WHEN due_date IS NULL OR due_date = '' THEN 1 ELSE 0 END,
                     due_date ASC, id ASC""",
                (project_id, user_id),
            )
            return [dict(r) for r in cursor.fetchall()]

    def get_task(self, task_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a specific task ensuring user isolation."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM project_tasks WHERE id = ? AND user_id = ?",
                (task_id, user_id),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_project_task(
        self,
        task_id: int,
        user_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        due_date: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
    ) -> bool:
        """Update task fields and touch project updated_at."""
        current = self.get_task(task_id, user_id)
        if not current:
            return False

        new_title = title.strip() if title is not None else current["title"]
        new_desc = description.strip() if description is not None else current["description"]
        new_due = due_date.strip() if due_date is not None else current["due_date"]
        new_priority = priority.strip() if priority is not None else current["priority"]
        new_status = status.strip() if status is not None else current["status"]

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE project_tasks SET
                   title = ?,
                   description = ?,
                   due_date = ?,
                   priority = ?,
                   status = ?,
                   updated_at = CURRENT_TIMESTAMP
                   WHERE id = ? AND user_id = ?""",
                (new_title, new_desc, new_due, new_priority, new_status, task_id, user_id),
            )
            # Touch project updated_at
            cursor.execute(
                "UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
                (current["project_id"], user_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_project_task(self, task_id: int, user_id: int) -> bool:
        """Delete a task owned by user_id."""
        task = self.get_task(task_id, user_id)
        if not task:
            return False

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM project_tasks WHERE id = ? AND user_id = ?",
                (task_id, user_id),
            )
            cursor.execute(
                "UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
                (task["project_id"], user_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_project_task_counts(self, project_id: int, user_id: int) -> Tuple[int, int, float]:
        """Return (total_tasks, completed_tasks, progress_percentage)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT 
                     COUNT(*) as total,
                     SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed
                   FROM project_tasks 
                   WHERE project_id = ? AND user_id = ?""",
                (project_id, user_id),
            )
            row = cursor.fetchone()
            total = row["total"] if row and row["total"] else 0
            completed = row["completed"] if row and row["completed"] else 0
            progress = round((completed / total) * 100, 1) if total > 0 else 0.0
            return total, completed, progress

    def get_projects_summary(self, user_id: int) -> Dict[str, int]:
        """Compute metrics: total, in_progress, completed, and overdue projects."""
        today = datetime.now().strftime("%Y-%m-%d")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT status, target_deadline FROM projects WHERE user_id = ?",
                (user_id,),
            )
            rows = cursor.fetchall()
            total = len(rows)
            in_progress = sum(1 for r in rows if r["status"] == "In Progress")
            completed = sum(1 for r in rows if r["status"] == "Completed")
            overdue = sum(
                1 for r in rows
                if r["status"] != "Completed" and r["target_deadline"] and r["target_deadline"] < today
            )
            return {
                "total": total,
                "in_progress": in_progress,
                "completed": completed,
                "overdue": overdue,
            }


_db_instance: Optional[DatabaseManager] = None

def get_db(db_path: Optional[str] = None) -> DatabaseManager:
    """Singleton getter for DatabaseManager."""
    global _db_instance
    if _db_instance is None or (db_path and _db_instance.db_path != db_path):
        _db_instance = DatabaseManager(db_path=db_path)
    return _db_instance
