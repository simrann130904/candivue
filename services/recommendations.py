from typing import List, Dict, Any, Optional
from database.db import DatabaseManager, get_db


class RecommendationEngine:
    """Generates explainable, targeted interview preparation recommendations based on student performance data."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or get_db()

    def generate_recommendations(self, user_id: int) -> List[Dict[str, Any]]:
        """Generate a prioritized list of explainable study recommendations."""
        answers = self.db.get_user_answers(user_id)

        # Cold start: when user has not completed enough questions
        if len(answers) < 3:
            return [
                {
                    "type": "General",
                    "title": "Establish Your Baseline",
                    "description": "Complete your first 5-question mock interview in any core subject (Python, SQL, or OOP) to discover your knowledge strengths and technical gaps.",
                    "action_subject": "Python Programming",
                    "action_difficulty": "Beginner",
                    "priority": "High",
                    "tag": "Getting Started"
                },
                {
                    "type": "Curriculum",
                    "title": "Master Fundamental Principles",
                    "description": "Campus interviewers frequently evaluate OOP Pillars (Encapsulation, Polymorphism) and SQL JOIN mechanics before moving to system architecture.",
                    "action_subject": "Object-Oriented Programming",
                    "action_difficulty": "Beginner",
                    "priority": "Medium",
                    "tag": "Core High-Yield"
                },
                {
                    "type": "Strategy",
                    "title": "Structure Your Responses",
                    "description": "When answering technical questions, state the definition first, explain the underlying memory/runtime mechanism, and conclude with real-world trade-offs.",
                    "action_subject": "SQL",
                    "action_difficulty": "Beginner",
                    "priority": "Low",
                    "tag": "Interview Technique"
                }
            ]

        # Aggregate performance by topic and subject
        topic_stats: Dict[str, Dict[str, Any]] = {}
        missing_concepts_freq: Dict[str, int] = {}

        for a in answers:
            topic = a.get("topic", "General")
            subject = a.get("subject", "General")
            score = a.get("score", 0.0)

            if topic not in topic_stats:
                topic_stats[topic] = {
                    "subject": subject,
                    "scores": [],
                    "attempts": 0,
                    "latest_score": score
                }
            topic_stats[topic]["scores"].append(score)
            topic_stats[topic]["attempts"] += 1
            topic_stats[topic]["latest_score"] = score

            # Collect missing concepts
            for c in a.get("concepts_missing", []):
                missing_concepts_freq[c] = missing_concepts_freq.get(c, 0) + 1

        recommendations: List[Dict[str, Any]] = []

        # 1. Identify consistently weak topics (avg < 6.0 across >= 2 attempts, or < 5.0 on single attempt)
        weak_topics = []
        for topic, data in topic_stats.items():
            avg_score = sum(data["scores"]) / len(data["scores"])
            if avg_score < 6.5:
                weak_topics.append((topic, avg_score, data))

        # Sort weakest first
        weak_topics.sort(key=lambda x: x[1])

        for topic, avg_score, data in weak_topics[:3]:
            attempts = data["attempts"]
            subject = data["subject"]
            recommendations.append({
                "type": "Targeted Practice",
                "title": f"Revise {topic} ({subject})",
                "description": f"Your average score in **{topic}** is **{avg_score:.1f}/10** across {attempts} question(s). Revisit the underlying theory, run hands-on code examples, and re-test yourself.",
                "action_subject": subject,
                "action_difficulty": "Intermediate" if avg_score >= 5.0 else "Beginner",
                "priority": "High" if avg_score < 5.0 else "Medium",
                "tag": f"Score: {avg_score:.1f}/10"
            })

        # 2. Prioritize frequently missing concepts
        if missing_concepts_freq:
            sorted_concepts = sorted(missing_concepts_freq.items(), key=lambda x: x[1], reverse=True)
            top_missing = [c for c, _ in sorted_concepts[:3]]
            recommendations.append({
                "type": "Concept Focus",
                "title": "Deep-Dive Frequently Omitted Concepts",
                "description": f"You frequently missed keywords or mechanics regarding: `{', '.join(top_missing)}`. Explicitly mentioning these during interviews signals deep technical mastery.",
                "action_subject": recommendations[0]["action_subject"] if recommendations else "Database Management Systems",
                "action_difficulty": "Intermediate",
                "priority": "Medium",
                "tag": "Concept Gap"
            })

        # 3. Advancement recommendation if user is scoring high
        strong_topics = [
            (t, sum(d["scores"]) / len(d["scores"]), d["subject"])
            for t, d in topic_stats.items()
            if (sum(d["scores"]) / len(d["scores"])) >= 8.0 and d["attempts"] >= 2
        ]
        if strong_topics:
            best_topic = strong_topics[0]
            recommendations.append({
                "type": "Advancement",
                "title": f"Level Up in {best_topic[0]}",
                "description": f"You have achieved high proficiency in **{best_topic[0]}** ({best_topic[1]:.1f}/10). Challenge yourself with Advanced questions to master architectural trade-offs.",
                "action_subject": best_topic[2],
                "action_difficulty": "Advanced",
                "priority": "Low",
                "tag": "Strength Area"
            })

        return recommendations
