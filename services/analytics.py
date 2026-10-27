import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from database.db import DatabaseManager, get_db


class AnalyticsService:
    """Computes student performance metrics and prepares chart datasets from real SQLite data."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or get_db()

    def get_dashboard_summary(self, user_id: int) -> Dict[str, Any]:
        """Calculate primary dashboard metrics for a user."""
        sessions = self.db.get_user_sessions(user_id)
        answers = self.db.get_user_answers(user_id)

        completed_sessions = [s for s in sessions if s.get("status") == "completed"]
        questions_attempted = len(answers)
        interviews_completed = len(completed_sessions)

        if answers:
            avg_score = round(sum(a["score"] for a in answers) / len(answers), 1)
        else:
            avg_score = 0.0

        # Topic aggregation to determine focus areas
        topic_scores: Dict[str, List[float]] = {}
        subject_scores: Dict[str, List[float]] = {}
        for a in answers:
            t = a.get("topic", "General")
            s = a.get("subject", "General")
            topic_scores.setdefault(t, []).append(a["score"])
            subject_scores.setdefault(s, []).append(a["score"])

        # Weakest topics (avg < 6.5)
        weak_topics = []
        for t, scores in topic_scores.items():
            if (sum(scores) / len(scores)) < 6.5:
                weak_topics.append(t)

        focus_areas_count = len(weak_topics)

        # Strongest and weakest topics
        topic_avg = {t: sum(sc) / len(sc) for t, sc in topic_scores.items()}
        sorted_topics = sorted(topic_avg.items(), key=lambda x: x[1])

        weakest_topic = sorted_topics[0] if sorted_topics else None
        strongest_topic = sorted_topics[-1] if sorted_topics else None

        # Subject averages
        subject_avg = {s: round(sum(sc) / len(sc), 1) for s, sc in subject_scores.items()}
        strongest_subject = max(subject_avg.items(), key=lambda x: x[1])[0] if subject_avg else None

        return {
            "questions_attempted": questions_attempted,
            "average_score": avg_score,
            "interviews_completed": interviews_completed,
            "focus_areas_count": focus_areas_count,
            "weak_topics": weak_topics,
            "strongest_topic": strongest_topic,
            "weakest_topic": weakest_topic,
            "strongest_subject": strongest_subject,
            "subject_avg": subject_avg,
            "has_data": questions_attempted > 0,
        }

    def get_subject_performance_data(self, user_id: int) -> pd.DataFrame:
        """Return DataFrame with subject-wise averages for plotting."""
        answers = self.db.get_user_answers(user_id)
        if not answers:
            return pd.DataFrame(columns=["Subject", "Average Score", "Attempts"])

        df = pd.DataFrame(answers)
        grouped = df.groupby("subject").agg(
            average_score=("score", "mean"),
            attempts=("id", "count")
        ).reset_index()

        grouped.rename(columns={
            "subject": "Subject",
            "average_score": "Average Score",
            "attempts": "Attempts"
        }, inplace=True)
        grouped["Average Score"] = grouped["Average Score"].round(1)
        return grouped

    def get_performance_over_time(self, user_id: int) -> pd.DataFrame:
        """Return chronological score progression DataFrame."""
        answers = self.db.get_user_answers(user_id)
        if not answers:
            return pd.DataFrame(columns=["Attempt", "Score", "Subject", "Date"])

        # Chronological order
        answers_sorted = sorted(answers, key=lambda x: x["created_at"])
        records = []
        for idx, a in enumerate(answers_sorted, start=1):
            records.append({
                "Attempt": idx,
                "Score": a["score"],
                "Subject": a["subject"],
                "Topic": a["topic"],
                "Date": a["created_at"][:16] if a.get("created_at") else f"Attempt {idx}"
            })

        df = pd.DataFrame(records)
        df["Rolling Average"] = df["Score"].rolling(window=min(3, len(df)), min_periods=1).mean().round(1)
        return df

    def get_topic_breakdown(self, user_id: int) -> pd.DataFrame:
        """Return breakdown by topic with average score, attempts, and mastery level."""
        answers = self.db.get_user_answers(user_id)
        if not answers:
            return pd.DataFrame(columns=["Topic", "Subject", "Attempts", "Average Score", "Mastery Level"])

        df = pd.DataFrame(answers)
        grouped = df.groupby(["topic", "subject"]).agg(
            attempts=("id", "count"),
            average_score=("score", "mean")
        ).reset_index()

        grouped.rename(columns={
            "topic": "Topic",
            "subject": "Subject",
            "attempts": "Attempts",
            "average_score": "Average Score"
        }, inplace=True)
        grouped["Average Score"] = grouped["Average Score"].round(1)

        def classify_mastery(score: float) -> str:
            if score >= 8.0:
                return "Mastered"
            elif score >= 6.0:
                return "Proficient"
            else:
                return "Needs Review"

        grouped["Mastery Level"] = grouped["Average Score"].apply(classify_mastery)
        return grouped.sort_values(by="Average Score", ascending=True)
