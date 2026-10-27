import os
import json
import random
import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Optional

# Core Candivue services & components
from database.db import get_db, DatabaseManager
from services.auth import AuthService
from services.evaluator import AnswerEvaluator, EvaluationResult
from services.analytics import AnalyticsService
from services.recommendations import RecommendationEngine
from services.projects import (
    ProjectService,
    PROJECT_CATEGORIES,
    PROJECT_STATUSES,
    PROJECT_PRIORITIES,
    TASK_STATUSES,
)
import importlib

try:
    from components.styles import (
        inject_custom_css,
        render_metric_card,
        render_hero_banner,
        render_quote_card,
        get_current_theme,
        get_status_badge_html,
        get_priority_badge_html,
    )
except ImportError:
    import components.styles
    importlib.reload(components.styles)
    try:
        from components.styles import (
            inject_custom_css,
            render_metric_card,
            render_hero_banner,
            render_quote_card,
            get_current_theme,
            get_status_badge_html,
            get_priority_badge_html,
        )
    except ImportError:
        from components.styles import (
            inject_custom_css,
            render_metric_card,
            render_hero_banner,
            render_quote_card,
            get_current_theme,
        )
        def get_status_badge_html(status: str) -> str:
            status_map = {
                "Completed": "pill-mint",
                "In Progress": "pill-lavender",
                "On Hold": "pill-yellow",
                "Not Started": "pill-neutral",
            }
            pill_class = status_map.get(status, "pill-neutral")
            return f'<span class="pill-badge {pill_class}">{status}</span>'

        def get_priority_badge_html(priority: str) -> str:
            priority_map = {
                "High": "pill-pink",
                "Medium": "pill-yellow",
                "Low": "pill-neutral",
            }
            pill_class = priority_map.get(priority, "pill-neutral")
            return f'<span class="pill-badge {pill_class}">{priority}</span>'
from components.charts import (
    create_subject_bar_chart,
    create_performance_timeline_chart,
    create_topic_mastery_chart,
)

# Page configuration
st.set_page_state = getattr(st, "set_page_config", None)
st.set_page_config(
    page_title="Candivue | AI Adaptive Technical Interview System",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Global instances
db = get_db()
auth_service = AuthService(db)
analytics_service = AnalyticsService(db)
rec_engine = RecommendationEngine(db)
project_service = ProjectService(db)


@st.cache_data
def load_question_bank() -> List[Dict[str, Any]]:
    """Load questions from data/questions.json."""
    q_path = os.path.join(os.path.dirname(__file__), "data", "questions.json")
    if os.path.exists(q_path):
        with open(q_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


# Initialize Session State
def init_session_state():
    defaults = {
        "user": None,
        "theme": "dark",
        "current_page": "Dashboard",
        "interview_state": None,
        "selected_history_session": None,
        "practice_question_id": None,
        "projects_view": "list",
        "selected_project_id": None,
        "confirm_delete_project_id": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


init_session_state()
inject_custom_css()
theme = get_current_theme()


# ==========================================
# AUTHENTICATION VIEW
# ==========================================
def render_auth_page():
    """Render the login and registration page."""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            f"""
            <div style="text-align: center; margin-top: 40px; margin-bottom: 25px;">
                <div style="display: inline-block; background: {theme['accent_gradient_card']}; padding: 12px 24px; border-radius: 40px; border: 1px solid {theme['border_color']}; margin-bottom: 15px;">
                    <span style="font-size: 1.2rem; font-weight: 800; letter-spacing: -0.02em; color: {theme['accent_pink']};">CANDIVUE</span>
                </div>
                <h1 style="font-size: 2.4rem; margin-bottom: 8px;">Technical Interview Preparation</h1>
                <p style="font-size: 1.1rem; color: {theme['text_secondary']};">
                    Know your gaps. Master your interviews.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        auth_tab_login, auth_tab_register = st.tabs(["🔐 Log In", "📝 Create Account"])

        with auth_tab_login:
            st.markdown('<div class="candivue-card">', unsafe_allow_html=True)
            with st.form("login_form", clear_on_submit=False):
                st.subheader("Welcome Back")
                login_email = st.text_input("College / University Email", placeholder="student@university.edu")
                login_password = st.text_input("Password", type="password", placeholder="••••••••")
                login_submitted = st.form_submit_button("Sign In to Candivue", use_container_width=True)

                if login_submitted:
                    success, message, user_data = auth_service.login_user(login_email, login_password)
                    if success and user_data:
                        st.session_state.user = user_data
                        # Load user theme preference
                        user_prefs = db.get_user_preferences(user_data["id"])
                        st.session_state.theme = user_prefs.get("theme", "dark")
                        st.toast("Welcome back! Login successful.", icon="🎉")
                        st.rerun()
                    else:
                        st.error(message)

            st.markdown(
                f"""
                <div style="margin-top: 15px; padding: 12px; border-radius: 10px; background: rgba(216, 180, 248, 0.1); border: 1px dashed {theme['accent_lavender']}; font-size: 0.85rem;">
                    <b>💡 Quick Demo Login:</b><br>
                    Email: <code>demo@candivue.edu</code> | Password: <code>candivue2026</code>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("⚡ Sign in with Demo Account (Adam William)", key="quick_demo_btn", use_container_width=True):
                success, _, user_data = auth_service.login_user("demo@candivue.edu", "candivue2026")
                if success and user_data:
                    st.session_state.user = user_data
                    st.session_state.theme = "dark"
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with auth_tab_register:
            st.markdown('<div class="candivue-card">', unsafe_allow_html=True)
            with st.form("register_form", clear_on_submit=False):
                st.subheader("Join Candivue")
                st.caption("Free access for students. No external API key required to practice.")
                reg_name = st.text_input("Full Name", placeholder="e.g. Alex Morgan")
                reg_email = st.text_input("Email Address", placeholder="alex@campus.edu")
                reg_pass = st.text_input("Create Password (min. 6 characters)", type="password", placeholder="••••••••")
                reg_confirm = st.text_input("Confirm Password", type="password", placeholder="••••••••")
                reg_submitted = st.form_submit_button("Create Student Account", use_container_width=True)

                if reg_submitted:
                    success, message, new_user = auth_service.register_user(
                        reg_email, reg_name, reg_pass, reg_confirm
                    )
                    if success and new_user:
                        st.session_state.user = new_user
                        st.toast("Account created successfully! Logging you in...", icon="🚀")
                        st.rerun()
                    else:
                        st.error(message)
            st.markdown('</div>', unsafe_allow_html=True)


def get_user_initials(name: Optional[str]) -> str:
    """Generate 1-2 character uppercase initials from a user's full name."""
    if not name:
        return "U"
    parts = name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    elif len(parts) == 1 and len(parts[0]) > 0:
        return parts[0][:2].upper() if len(parts[0]) >= 2 else parts[0][0].upper()
    return "U"


# ==========================================
# SIDEBAR
# ==========================================
def render_sidebar():
    """Render the refined, editorial SaaS navigation sidebar."""
    user = st.session_state.user
    curr_theme = st.session_state.get("theme", "dark")
    is_dark = curr_theme == "dark"

    with st.sidebar:
        # 1. Compact Brand Header with geometric Candivue logo mark
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 10px; padding: 2px 6px 14px 6px; border-bottom: 1px solid {theme['border_color']}; margin-bottom: 8px;">
                <div style="width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="{theme['accent_lavender']}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 2L2 7L12 12L22 7L12 2Z"/>
                        <path d="M2 17L12 22L22 17"/>
                        <path d="M2 12L12 17L22 12"/>
                    </svg>
                </div>
                <div style="line-height: 1.15;">
                    <div style="font-family: 'Outfit', sans-serif; font-size: 1.05rem; font-weight: 700; letter-spacing: -0.025em; color: {theme['text_primary']};">candivue</div>
                    <div style="font-size: 0.68rem; color: {theme['text_secondary']}; letter-spacing: 0.02em; font-weight: 500;">Interview preparation</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 2. Main Navigation Group
        st.markdown('<span class="sidebar-section-header">MAIN</span>', unsafe_allow_html=True)

        main_nav_items = [
            ("Dashboard", "Dashboard", ":material/dashboard:"),
            ("Mock Interviews", "Start Interview", ":material/track_changes:"),
            ("Practice Questions", "Practice Questions", ":material/menu_book:"),
            ("Performance Analytics", "Performance Analytics", ":material/bar_chart:"),
            ("Interview History", "Interview History", ":material/history:"),
        ]

        curr_page = st.session_state.current_page
        for label, target_page, icon in main_nav_items:
            is_active = (
                curr_page == target_page or
                (target_page == "Start Interview" and curr_page in ("Start Interview", "Mock Interviews"))
            )
            if st.button(
                label,
                key=f"nav_{target_page}",
                type="primary" if is_active else "secondary",
                icon=icon,
                use_container_width=True,
            ):
                st.session_state.current_page = target_page
                st.rerun()

        # 3. Preferences Navigation Group
        st.markdown('<span class="sidebar-section-header">PREFERENCES</span>', unsafe_allow_html=True)

        pref_nav_items = [
            ("My Projects", "My Projects", ":material/folder:"),
            ("Settings", "Settings", ":material/settings:"),
        ]

        for label, target_page, icon in pref_nav_items:
            is_active = (
                curr_page == target_page or
                (target_page == "My Projects" and curr_page in ("My Projects", "Project Development Status", "Project Status"))
            )
            if st.button(
                label,
                key=f"nav_{target_page}",
                type="primary" if is_active else "secondary",
                icon=icon,
                use_container_width=True,
            ):
                st.session_state.current_page = target_page
                st.rerun()

        # 4. Compact Account Section
        if user:
            user_name = user.get("full_name") or "User"
            user_email = user.get("email") or ""
            initials = get_user_initials(user_name)

            st.markdown(
                f"""
                <div class="sidebar-account-row">
                    <div class="sidebar-avatar">{initials}</div>
                    <div style="overflow: hidden; flex: 1; min-width: 0;">
                        <div style="font-weight: 600; font-size: 0.82rem; color: {theme['text_primary']}; white-space: nowrap; text-overflow: ellipsis; overflow: hidden; line-height: 1.2;">
                            {user_name}
                        </div>
                        {f'<div style="font-size: 0.7rem; color: {theme["text_secondary"]}; white-space: nowrap; text-overflow: ellipsis; overflow: hidden; line-height: 1.2; margin-top: 2px;">{user_email}</div>' if user_email else ''}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # 5. Footer divider & actions (Theme & Logout)
        st.markdown(f'<div style="border-top: 1px solid {theme["border_color"]}; margin: 10px 4px 8px 4px;"></div>', unsafe_allow_html=True)

        # Theme Toggle
        theme_label = "Light mode" if is_dark else "Dark mode"
        theme_icon = ":material/light_mode:" if is_dark else ":material/dark_mode:"

        if st.button(theme_label, key="nav_theme_toggle", type="secondary", icon=theme_icon, use_container_width=True):
            new_theme = "light" if is_dark else "dark"
            st.session_state.theme = new_theme
            if user:
                db.update_user_preferences(user["id"], theme=new_theme)
            st.rerun()

        # Logout Action
        if st.button("Log out", key="nav_logout", type="secondary", icon=":material/logout:", use_container_width=True):
            st.session_state.user = None
            st.session_state.interview_state = None
            st.session_state.current_page = "Dashboard"
            st.toast("Logged out successfully.")
            st.rerun()


# ==========================================
# PAGE: DASHBOARD
# ==========================================
def render_dashboard_page():
    """Render student dashboard."""
    user = st.session_state.user
    first_name = user["full_name"].split()[0] if user.get("full_name") else "Student"

    # Hero Banner
    render_hero_banner(first_name)

    # Prominent Mock Interview pastel CTA card
    col_cta1, col_cta2 = st.columns([3, 1])
    with col_cta1:
        st.markdown(
            f"""
            <div style="background: {theme['accent_gradient_card']}; border: 1px solid {theme['border_color']}; border-radius: 18px; padding: 18px 24px; margin-bottom: 24px;">
                <div style="font-weight: 700; font-size: 1.15rem; color: {theme['accent_pink']}; margin-bottom: 4px;">Ready for your next round?</div>
                <div style="font-size: 0.92rem; color: {theme['text_secondary']};">
                    Take an adaptive 5, 10, or 15-question technical mock interview with instant concept coverage feedback.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_cta2:
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        if st.button("🚀 Start a Mock Interview", key="dash_start_mock_btn", use_container_width=True):
            st.session_state.current_page = "Start Interview"
            st.rerun()

    # Calculate actual metrics from SQLite
    summary = analytics_service.get_dashboard_summary(user["id"])

    # 4 Metric Cards
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_metric_card("Questions Attempted", summary["questions_attempted"], "Total submissions", "pink")
    with m2:
        score_val = f"{summary['average_score']}/10" if summary["has_data"] else "0.0/10"
        render_metric_card("Average Score", score_val, "Across all subjects", "lavender")
    with m3:
        render_metric_card("Interviews Completed", summary["interviews_completed"], "Full sessions finished", "yellow")
    with m4:
        render_metric_card("Focus Areas", summary["focus_areas_count"], "Topics needing revision", "mint")

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # Empty State for brand new users
    if not summary["has_data"]:
        st.markdown(
            f"""
            <div class="candivue-card" style="text-align: center; padding: 45px 30px;">
                <div style="font-size: 3rem; margin-bottom: 12px;">🌱</div>
                <h3 style="margin-bottom: 8px;">Your Performance Canvas is Fresh</h3>
                <p style="color: {theme['text_secondary']}; max-width: 500px; margin: 0 auto 20px auto;">
                    You have not answered any technical interview questions yet. Start your first session to unlock real-time analytics, concept coverage heatmaps, and personalized placement recommendations.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        # Motivational quote
        render_quote_card()
        return

    # Charts Row
    c_left, c_right = st.columns(2)
    with c_left:
        st.markdown('<div class="candivue-card">', unsafe_allow_html=True)
        df_subj = analytics_service.get_subject_performance_data(user["id"])
        fig_subj = create_subject_bar_chart(df_subj)
        st.plotly_chart(fig_subj, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c_right:
        st.markdown('<div class="candivue-card">', unsafe_allow_html=True)
        df_time = analytics_service.get_performance_over_time(user["id"])
        fig_time = create_performance_timeline_chart(df_time)
        st.plotly_chart(fig_time, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Strongest / Weakest Topics & Recommendations
    row2_left, row2_right = st.columns([1, 1])

    with row2_left:
        st.markdown('<div class="candivue-card">', unsafe_allow_html=True)
        st.subheader("Strengths & Gaps Analysis")
        st.caption("Derived from your recent technical submissions")

        strongest = summary["strongest_topic"]
        weakest = summary["weakest_topic"]

        if strongest:
            st.markdown(
                f"""
                <div style="background: rgba(168, 230, 207, 0.12); border-left: 4px solid {theme['accent_mint']}; padding: 12px 16px; border-radius: 8px; margin-bottom: 14px;">
                    <div style="font-size: 0.8rem; font-weight: 600; color: {theme['accent_mint']}; text-transform: uppercase;">Top Strength</div>
                    <div style="font-weight: 700; font-size: 1.05rem;">{strongest[0]}</div>
                    <div style="font-size: 0.85rem; color: {theme['text_secondary']};">Average score: <b>{strongest[1]:.1f}/10</b></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if weakest:
            st.markdown(
                f"""
                <div style="background: rgba(249, 184, 208, 0.12); border-left: 4px solid {theme['accent_pink']}; padding: 12px 16px; border-radius: 8px;">
                    <div style="font-size: 0.8rem; font-weight: 600; color: {theme['accent_pink']}; text-transform: uppercase;">Primary Focus Area</div>
                    <div style="font-weight: 700; font-size: 1.05rem;">{weakest[0]}</div>
                    <div style="font-size: 0.85rem; color: {theme['text_secondary']};">Average score: <b>{weakest[1]:.1f}/10</b> (Target: 7.5+)</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)

    with row2_right:
        st.markdown('<div class="candivue-card">', unsafe_allow_html=True)
        st.subheader("Personalized Recommendations")
        st.caption("Targeted next steps to boost campus placement readiness")

        recs = rec_engine.generate_recommendations(user["id"])
        for r in recs[:2]:
            st.markdown(
                f"""
                <div style="border-bottom: 1px solid {theme['border_color']}; padding-bottom: 12px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <span style="font-weight: 700; font-size: 0.95rem;">{r['title']}</span>
                        <span class="pill-badge pill-lavender">{r['tag']}</span>
                    </div>
                    <div style="font-size: 0.85rem; color: {theme['text_secondary']}; line-height: 1.4;">
                        {r['description']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)

    # Recent attempts & quote
    recent_col, quote_col = st.columns([2, 1])
    with recent_col:
        st.markdown('<div class="candivue-card">', unsafe_allow_html=True)
        st.subheader("Recent Interview Sessions")
        recent_sessions = db.get_user_sessions(user["id"], limit=4)
        if recent_sessions:
            for s in recent_sessions:
                dt_str = s["created_at"][:16] if s.get("created_at") else "Recent"
                status_color = theme["accent_mint"] if s["status"] == "completed" else theme["accent_yellow"]
                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid {theme['border_color']};">
                        <div>
                            <div style="font-weight: 600;">{s['subject']} <span class="pill-badge pill-lavender">{s['difficulty']}</span></div>
                            <div style="font-size: 0.8rem; color: {theme['text_secondary']};">{dt_str} • {s['question_count']} questions</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-weight: 800; font-size: 1.1rem; color: {status_color};">{s['average_score']:.1f}/10</div>
                            <div style="font-size: 0.75rem; text-transform: uppercase; color: {theme['text_secondary']};">{s['status']}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No sessions recorded yet.")
        st.markdown('</div>', unsafe_allow_html=True)

    with quote_col:
        render_quote_card()


# ==========================================
# PAGE: START INTERVIEW & WORKFLOW
# ==========================================
def render_start_interview_page():
    """Render the mock interview configuration and execution flow."""
    user = st.session_state.user
    q_bank = load_question_bank()

    # If interview is currently active, render the interview loop
    if st.session_state.interview_state is not None:
        render_active_interview(q_bank)
        return

    # Interview Setup Form
    st.markdown(
        f"""
        <div style="margin-bottom: 24px;">
            <h2>Start a Mock Technical Interview</h2>
            <p style="color: {theme['text_secondary']};">
                Configure your mock session parameters. Candivue will select questions matching your criteria and score your answers using technical concept verification.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="candivue-card">', unsafe_allow_html=True)
    with st.form("interview_setup_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            subject = st.selectbox(
                "Select Subject",
                [
                    "Python Programming",
                    "SQL",
                    "Object-Oriented Programming",
                    "Database Management Systems",
                    "Computer Networks",
                ],
            )

        with col2:
            difficulty = st.selectbox("Difficulty Level", ["Beginner", "Intermediate", "Advanced"])

        with col3:
            num_questions = st.selectbox("Number of Questions", [5, 10, 15], index=0)

        st.markdown(
            f"""
            <div style="margin: 16px 0; padding: 14px 18px; border-radius: 12px; background: rgba(216, 180, 248, 0.08); border: 1px solid {theme['border_color']}; font-size: 0.88rem; color: {theme['text_secondary']};">
                💡 <b>Interview Tip:</b> For each question, explain definitions, underlying mechanisms, and operational trade-offs. The evaluation engine automatically checks for core technical concepts.
            </div>
            """,
            unsafe_allow_html=True,
        )

        start_btn = st.form_submit_button("Begin Technical Interview 🚀", use_container_width=True)

        if start_btn:
            # Filter question bank
            matching_qs = [
                q for q in q_bank
                if q["subject"] == subject and q["difficulty"] == difficulty
            ]

            # If not enough exact difficulty matches, complement with same subject
            if len(matching_qs) < num_questions:
                complement = [
                    q for q in q_bank
                    if q["subject"] == subject and q["difficulty"] != difficulty
                ]
                matching_qs.extend(complement)

            if not matching_qs:
                st.error("No questions found for the selected subject. Please pick another subject.")
                return

            random.shuffle(matching_qs)
            selected_qs = matching_qs[:num_questions]

            # Create persistent session in SQLite
            session_id = db.create_session(
                user_id=user["id"],
                subject=subject,
                difficulty=difficulty,
                question_count=len(selected_qs),
            )

            # Store in session state
            st.session_state.interview_state = {
                "session_id": session_id,
                "subject": subject,
                "difficulty": difficulty,
                "questions": selected_qs,
                "current_index": 0,
                "answers": [],
                "current_evaluation": None,
                "is_completed": False,
            }
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def render_active_interview(q_bank: List[Dict[str, Any]]):
    """Render the active question-and-answer cycle."""
    user = st.session_state.user
    state = st.session_state.interview_state

    # Check if final report is reached
    if state["is_completed"]:
        render_final_report()
        return

    questions = state["questions"]
    curr_idx = state["current_index"]
    total_q = len(questions)
    curr_q = questions[curr_idx]

    # Progress Bar
    progress_val = curr_idx / total_q
    st.progress(progress_val)

    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <div>
                <span class="pill-badge pill-lavender">{state['subject']}</span>
                <span class="pill-badge pill-yellow">{curr_q['difficulty']}</span>
                <span class="pill-badge pill-pink">{curr_q['topic']}</span>
            </div>
            <div style="font-weight: 700; font-size: 1.1rem; color: {theme['text_secondary']};">
                Question {curr_idx + 1} of {total_q}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Question Prompt Card
    st.markdown(
        f"""
        <div class="candivue-card" style="border-left: 5px solid {theme['accent_pink']}; margin-bottom: 24px;">
            <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: {theme['text_secondary']}; margin-bottom: 6px;">Technical Prompt</div>
            <h3 style="margin-top: 0; line-height: 1.4;">{curr_q['question']}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Check if an evaluation was already performed for the current question
    eval_result: Optional[EvaluationResult] = state["current_evaluation"]

    if eval_result is None:
        # Candidate text input
        user_answer = st.text_area(
            "Your Technical Answer:",
            height=200,
            placeholder="Type your explanation here. Include key mechanisms, terminology, and trade-offs...",
            key=f"ans_input_{curr_idx}",
        )

        col_sub, col_abandon = st.columns([3, 1])
        with col_sub:
            if st.button("Submit Answer for Evaluation 🎯", key=f"submit_q_{curr_idx}", use_container_width=True):
                if not user_answer or len(user_answer.strip()) < 5:
                    st.warning("Please enter a substantive answer before submitting.")
                else:
                    # Retrieve API key if stored in preferences or env
                    user_prefs = db.get_user_preferences(user["id"])
                    api_key = user_prefs.get("api_key") or os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY")

                    evaluator = AnswerEvaluator(api_key=api_key)
                    with st.spinner("Analyzing answer concepts and technical depth..."):
                        res = evaluator.evaluate(curr_q, user_answer)

                    # Save answer in SQLite database
                    db.save_answer(
                        session_id=state["session_id"],
                        user_id=user["id"],
                        question_id=curr_q["id"],
                        question_text=curr_q["question"],
                        subject=curr_q["subject"],
                        topic=curr_q["topic"],
                        difficulty=curr_q["difficulty"],
                        user_answer=user_answer,
                        score=res.score,
                        concepts_covered=res.concepts_covered,
                        concepts_missing=res.concepts_missing,
                        feedback=res.feedback,
                        reference_answer=res.reference_answer,
                        evaluation_mode=res.evaluation_mode,
                    )

                    state["answers"].append({
                        "question": curr_q,
                        "user_answer": user_answer,
                        "evaluation": res,
                    })
                    state["current_evaluation"] = res
                    st.rerun()

        with col_abandon:
            if st.button("Abandon Session", key="abandon_interview_btn", use_container_width=True):
                st.session_state.interview_state = None
                st.session_state.current_page = "Dashboard"
                st.rerun()

    else:
        # Display Evaluation Feedback Card
        score = eval_result.score
        score_color = theme["accent_mint"] if score >= 7.0 else (theme["accent_yellow"] if score >= 4.5 else theme["accent_pink"])

        st.markdown(
            f"""
            <div class="candivue-card" style="border-top: 4px solid {score_color};">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap;">
                    <div>
                        <span style="font-size: 0.85rem; font-weight: 600; color: {theme['text_secondary']};">EVALUATION RESULT</span>
                        <div style="font-size: 2.2rem; font-weight: 800; color: {score_color}; font-family: 'Outfit', sans-serif;">
                            {score:.1f} <span style="font-size: 1.1rem; color: {theme['text_secondary']}; font-weight: 500;">/ 10</span>
                        </div>
                    </div>
                    <div>
                        <span class="pill-badge pill-lavender">Mode: {eval_result.evaluation_mode}</span>
                        <span class="pill-badge pill-yellow">Depth: {eval_result.technical_depth}</span>
                    </div>
                </div>
            """,
            unsafe_allow_html=True,
        )

        # Concepts Covered Pills
        if eval_result.concepts_covered:
            covered_pills = "".join([f'<span class="pill-badge pill-mint">✓ {c}</span>' for c in eval_result.concepts_covered])
            st.markdown(f"<div style='margin-bottom: 10px;'><b>Concepts Covered:</b><br>{covered_pills}</div>", unsafe_allow_html=True)

        # Concepts Missing Pills
        if eval_result.concepts_missing:
            missing_pills = "".join([f'<span class="pill-badge pill-missing">✗ {c}</span>' for c in eval_result.concepts_missing])
            st.markdown(f"<div style='margin-bottom: 14px;'><b>Omitted or Incomplete Concepts:</b><br>{missing_pills}</div>", unsafe_allow_html=True)

        # Constructive Feedback Text
        st.markdown(f"<div style='background: rgba(0,0,0,0.1); padding: 14px; border-radius: 12px; margin-bottom: 14px;'>{eval_result.feedback}</div>", unsafe_allow_html=True)

        # Optional follow up probe
        if eval_result.follow_up_question:
            st.markdown(
                f"""
                <div style="padding: 10px 14px; border-radius: 10px; background: rgba(253, 226, 147, 0.1); border: 1px solid rgba(253, 226, 147, 0.25); font-size: 0.9rem; margin-bottom: 14px;">
                    🤔 <b>Interviewer Follow-up Probe:</b> {eval_result.follow_up_question}
                </div>
                """,
                unsafe_allow_html=True,
            )

        with st.expander("📖 View Model Reference Answer"):
            st.markdown(eval_result.reference_answer)

        st.markdown('</div>', unsafe_allow_html=True)

        # Navigation to next question or final report
        is_last_q = (curr_idx + 1) >= total_q
        btn_label = "Complete Interview & View Final Report 🏆" if is_last_q else f"Continue to Question {curr_idx + 2} ➔"

        if st.button(btn_label, key=f"next_btn_{curr_idx}", use_container_width=True):
            if is_last_q:
                # Calculate average score and save completion
                all_scores = [a["evaluation"].score for a in state["answers"]]
                avg_score = sum(all_scores) / len(all_scores) if all_scores else 0.0
                db.complete_session(state["session_id"], user["id"], avg_score)
                state["is_completed"] = True
            else:
                state["current_index"] += 1
                state["current_evaluation"] = None
            st.rerun()


def render_final_report():
    """Render the comprehensive interview conclusion report."""
    user = st.session_state.user
    state = st.session_state.interview_state
    answers = state["answers"]

    scores = [a["evaluation"].score for a in answers]
    avg_score = sum(scores) / len(scores) if scores else 0.0

    st.markdown(
        f"""
        <div class="candivue-card-hero" style="text-align: center;">
            <span class="pill-badge pill-mint">SESSION COMPLETED</span>
            <h1 style="margin: 12px 0 6px 0;">Technical Interview Evaluation Report</h1>
            <p style="color: {theme['text_secondary']}; max-width: 650px; margin: 0 auto 20px auto;">
                Here is your comprehensive evaluation breakdown across {len(answers)} technical interview questions in <b>{state['subject']}</b> ({state['difficulty']}).
            </p>
            <div style="display: inline-block; background: {theme['bg_card']}; border: 1px solid {theme['border_color']}; padding: 14px 30px; border-radius: 18px;">
                <div style="font-size: 0.85rem; color: {theme['text_secondary']}; text-transform: uppercase;">Overall Average Score</div>
                <div style="font-size: 2.6rem; font-weight: 800; color: {theme['accent_pink']}; font-family: 'Outfit', sans-serif;">{avg_score:.1f} / 10</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Detailed Question Breakdown Accordion
    st.subheader("Question-by-Question Detailed Review")
    for i, a in enumerate(answers, start=1):
        q = a["question"]
        res: EvaluationResult = a["evaluation"]
        with st.expander(f"Q{i}: {q['question']} — Score: {res.score:.1f}/10"):
            st.markdown(f"**Topic:** `{q['topic']}` | **Difficulty:** `{q['difficulty']}`")
            st.markdown(f"**Your Answer:**\n> {a['user_answer']}")
            
            if res.concepts_covered:
                st.markdown(f"**Concepts Explained:** `{'`, `'.join(res.concepts_covered)}`")
            if res.concepts_missing:
                st.markdown(f"**Concepts Missing:** `{'`, `'.join(res.concepts_missing)}`")

            st.markdown(f"**Feedback:**\n{res.feedback}")
            st.markdown(f"**Reference Answer:**\n{res.reference_answer}")

    col_ret1, col_ret2 = st.columns(2)
    with col_ret1:
        if st.button("Return to Dashboard 📊", key="return_dash_btn", use_container_width=True):
            st.session_state.interview_state = None
            st.session_state.current_page = "Dashboard"
            st.rerun()

    with col_ret2:
        if st.button("Practice Another Interview 🚀", key="retake_interview_btn", use_container_width=True):
            st.session_state.interview_state = None
            st.session_state.current_page = "Start Interview"
            st.rerun()


# ==========================================
# PAGE: PRACTICE QUESTIONS
# ==========================================
def render_practice_questions_page():
    """Browse the question bank and practice individual questions on demand."""
    q_bank = load_question_bank()
    st.markdown(
        f"""
        <div style="margin-bottom: 20px;">
            <h2>Curated Technical Question Bank</h2>
            <p style="color: {theme['text_secondary']};">
                Explore campus interview questions by subject and difficulty. Practice individual questions on demand with instant technical concept scoring.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        sel_subj = st.selectbox(
            "Filter by Subject",
            ["All Subjects", "Python Programming", "SQL", "Object-Oriented Programming", "Database Management Systems", "Computer Networks"],
        )
    with f_col2:
        sel_diff = st.selectbox("Filter by Difficulty", ["All Difficulties", "Beginner", "Intermediate", "Advanced"])
    with f_col3:
        search_query = st.text_input("Search Questions or Concepts", placeholder="e.g. JOIN, GIL, Polymorphism...")

    # Filtering
    filtered = q_bank
    if sel_subj != "All Subjects":
        filtered = [q for q in filtered if q["subject"] == sel_subj]
    if sel_diff != "All Difficulties":
        filtered = [q for q in filtered if q["difficulty"] == sel_diff]
    if search_query.strip():
        sq = search_query.strip().lower()
        filtered = [
            q for q in filtered
            if sq in q["question"].lower() or sq in q["topic"].lower() or any(sq in c.lower() for c in q["expected_concepts"])
        ]

    st.markdown(f"<div style='font-size: 0.9rem; color: {theme['text_secondary']}; margin-bottom: 14px;'>Displaying <b>{len(filtered)}</b> technical interview questions</div>", unsafe_allow_html=True)

    for q in filtered:
        with st.expander(f"[{q['id']}] {q['subject']} • {q['topic']} ({q['difficulty']}) — {q['question']}"):
            st.markdown(f"**Question:** {q['question']}")
            st.markdown(f"**Expected Concepts:** `{'`, `'.join(q['expected_concepts'])}`")
            st.markdown(f"**Evaluation Criteria:** {q['evaluation_criteria']}")
            st.markdown(f"**Reference Answer:**\n{q['reference_answer']}")


# ==========================================
# PAGE: PERFORMANCE ANALYTICS
# ==========================================
def render_analytics_page():
    """Render comprehensive performance analytics and charts."""
    user = st.session_state.user
    st.markdown(
        f"""
        <div style="margin-bottom: 24px;">
            <h2>Performance Analytics</h2>
            <p style="color: {theme['text_secondary']};">
                Examine your progress across subjects, score trajectories, and topic-level concept mastery.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    summary = analytics_service.get_dashboard_summary(user["id"])

    if not summary["has_data"]:
        st.info("No analytics data available yet. Please complete a mock interview or practice question first.")
        return

    # Top Metric Summary Cards
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_metric_card("Questions Answered", summary["questions_attempted"], "Total submissions", "pink")
    with m2:
        render_metric_card("Overall Average", f"{summary['average_score']}/10", "Across all tests", "lavender")
    with m3:
        st_subj = summary["strongest_subject"] or "None"
        render_metric_card("Strongest Subject", st_subj, "Highest average score", "mint")
    with m4:
        render_metric_card("Interviews Completed", summary["interviews_completed"], "Sessions finished", "yellow")

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # Charts
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="candivue-card">', unsafe_allow_html=True)
        df_subj = analytics_service.get_subject_performance_data(user["id"])
        st.plotly_chart(create_subject_bar_chart(df_subj), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="candivue-card">', unsafe_allow_html=True)
        df_time = analytics_service.get_performance_over_time(user["id"])
        st.plotly_chart(create_performance_timeline_chart(df_time), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Topic Breakdown
    st.markdown('<div class="candivue-card">', unsafe_allow_html=True)
    st.subheader("Topic Mastery Matrix")
    df_topics = analytics_service.get_topic_breakdown(user["id"])
    if not df_topics.empty:
        col_t1, col_t2 = st.columns([1, 1])
        with col_t1:
            st.plotly_chart(create_topic_mastery_chart(df_topics), use_container_width=True)
        with col_t2:
            st.dataframe(df_topics, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ==========================================
# PAGE: INTERVIEW HISTORY
# ==========================================
def render_history_page():
    """Render historical interview sessions with drill-down review."""
    user = st.session_state.user
    st.markdown(
        f"""
        <div style="margin-bottom: 24px;">
            <h2>Interview History</h2>
            <p style="color: {theme['text_secondary']};">
                Review all your previous interview attempts, scores, and detailed answer evaluations. All data is securely stored in SQLite.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    sessions = db.get_user_sessions(user["id"], limit=100)

    if not sessions:
        st.markdown(
            f"""
            <div class="candivue-card" style="text-align: center; padding: 40px;">
                <div style="font-size: 2.5rem; margin-bottom: 10px;">📜</div>
                <h3>No Previous Sessions Found</h3>
                <p style="color: {theme['text_secondary']};">Complete an interview session to build your placement history archive.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Table view of past sessions
    for s in sessions:
        dt = s["created_at"][:16] if s.get("created_at") else "N/A"
        status_color = theme["accent_mint"] if s["status"] == "completed" else theme["accent_yellow"]

        with st.expander(f"{s['subject']} ({s['difficulty']}) — {dt} — Average: {s['average_score']:.1f}/10 [{s['status'].upper()}]"):
            st.markdown(f"**Session ID:** `{s['id']}` | **Subject:** `{s['subject']}` | **Difficulty:** `{s['difficulty']}`")
            st.markdown(f"**Questions Configured:** `{s['question_count']}` | **Status:** `<span style='color:{status_color}; font-weight:700;'>{s['status'].upper()}</span>`", unsafe_allow_html=True)
            st.markdown(f"**Overall Score:** `{s['average_score']:.1f}/10`")

            # Load answers for this specific session
            answers = db.get_session_answers(s["id"], user["id"])
            if answers:
                st.markdown("#### Question Evaluations in this Session:")
                for idx, ans in enumerate(answers, start=1):
                    ans_score_color = theme["accent_mint"] if ans["score"] >= 7.0 else (theme["accent_yellow"] if ans["score"] >= 4.5 else theme["accent_pink"])
                    st.markdown(
                        f"""
                        <div style="border: 1px solid {theme['border_color']}; border-radius: 12px; padding: 14px; margin-bottom: 12px; background: rgba(0,0,0,0.05);">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <b>Q{idx}: {ans['question_text']}</b>
                                <span style="font-weight: 800; color: {ans_score_color};">{ans['score']:.1f}/10</span>
                            </div>
                            <div style="margin-top: 6px; font-size: 0.88rem; color: {theme['text_secondary']};">
                                <b>Student Submission:</b> {ans['user_answer']}
                            </div>
                            <div style="margin-top: 6px; font-size: 0.85rem;">
                                <b>Feedback:</b> {ans['feedback']}
                            </div>
                            <div style="margin-top: 6px; font-size: 0.85rem;">
                                <b>Reference Answer:</b> {ans['reference_answer']}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("No answers recorded for this session.")


# ==========================================
# PAGE: MY PROJECTS (Personal Project Management)
# ==========================================
def render_my_projects_page():
    """Render the personal project management and progress tracking module."""
    user = st.session_state.user
    user_id = user["id"]

    view = st.session_state.get("projects_view", "list")
    selected_id = st.session_state.get("selected_project_id")

    # ----------------------------------------------------
    # VIEW: CREATE NEW PROJECT
    # ----------------------------------------------------
    if view == "new":
        st.markdown(
            f"""
            <div style="margin-bottom: 20px;">
                <span class="pill-badge pill-lavender">NEW PROJECT</span>
                <h2 style="margin: 6px 0 4px 0;">Add Personal Project</h2>
                <p style="color: {theme['text_secondary']}; margin: 0;">
                    Define your project scope, target tech stack, and milestone deadlines.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("← Back to Projects", key="btn_cancel_new_proj", type="secondary"):
            st.session_state.projects_view = "list"
            st.rerun()

        st.markdown('<div class="candivue-card">', unsafe_allow_html=True)
        with st.form("form_create_project", clear_on_submit=False):
            col_n1, col_n2 = st.columns([2, 1])
            with col_n1:
                p_name = st.text_input("Project Name *", placeholder="e.g. Distributed Key-Value Store")
            with col_n2:
                p_cat = st.selectbox("Category *", PROJECT_CATEGORIES, index=0)

            p_desc = st.text_area("Short Description", placeholder="Brief summary of what you are building and why...", height=85)
            p_tech = st.text_input("Technology Stack (comma-separated)", placeholder="e.g. Python, FastAPI, Docker, Redis, Pytest")

            col_d1, col_d2 = st.columns(2)
            with col_d1:
                p_start = st.date_input("Start Date", value=datetime.today().date())
            with col_d2:
                p_deadline = st.date_input("Target Deadline", value=datetime.today().date())

            col_p1, col_p2 = st.columns(2)
            with col_p1:
                p_priority = st.selectbox("Priority", PROJECT_PRIORITIES, index=1)
            with col_p2:
                p_status = st.selectbox("Current Status", PROJECT_STATUSES, index=0)

            col_u1, col_u2 = st.columns(2)
            with col_u1:
                p_github = st.text_input("GitHub Repository URL (Optional)", placeholder="https://github.com/username/project")
            with col_u2:
                p_demo = st.text_input("Live Demo URL (Optional)", placeholder="https://myproject.app")

            p_notes = st.text_area("Technical Notes & Goals (Optional)", placeholder="Key architectural goals, placement showcase points...", height=90)

            submitted = st.form_submit_button("Create Project 🚀", use_container_width=True)

            if submitted:
                start_str = p_start.isoformat() if p_start else ""
                dead_str = p_deadline.isoformat() if p_deadline else ""
                ok, msg, new_pid = project_service.create_project(
                    user_id=user_id,
                    name=p_name,
                    description=p_desc,
                    category=p_cat,
                    tech_stack=p_tech,
                    start_date=start_str,
                    target_deadline=dead_str,
                    priority=p_priority,
                    status=p_status,
                    github_url=p_github,
                    demo_url=p_demo,
                    notes=p_notes,
                )
                if ok and new_pid:
                    st.session_state.selected_project_id = new_pid
                    st.session_state.projects_view = "detail"
                    st.toast("Project created successfully!", icon="🎉")
                    st.rerun()
                else:
                    st.error(msg)
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # ----------------------------------------------------
    # VIEW: EDIT PROJECT
    # ----------------------------------------------------
    if view == "edit" and selected_id:
        proj = project_service.get_project_with_details(selected_id, user_id)
        if not proj:
            st.error("Project not found.")
            st.session_state.projects_view = "list"
            st.rerun()

        st.markdown(
            f"""
            <div style="margin-bottom: 20px;">
                <span class="pill-badge pill-yellow">EDITING</span>
                <h2 style="margin: 6px 0 4px 0;">Edit: {proj['name']}</h2>
                <p style="color: {theme['text_secondary']}; margin: 0;">Update project metadata, links, or deadlines.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("← Cancel & Back to Details", key="btn_cancel_edit_proj", type="secondary"):
            st.session_state.projects_view = "detail"
            st.rerun()

        # Parse existing dates
        def parse_date(d_str: str):
            try:
                return datetime.strptime(d_str, "%Y-%m-%d").date() if d_str else datetime.today().date()
            except Exception:
                return datetime.today().date()

        st.markdown('<div class="candivue-card">', unsafe_allow_html=True)
        with st.form("form_edit_project", clear_on_submit=False):
            col_n1, col_n2 = st.columns([2, 1])
            with col_n1:
                edit_name = st.text_input("Project Name *", value=proj["name"])
            with col_n2:
                cat_idx = PROJECT_CATEGORIES.index(proj["category"]) if proj["category"] in PROJECT_CATEGORIES else 0
                edit_cat = st.selectbox("Category *", PROJECT_CATEGORIES, index=cat_idx)

            edit_desc = st.text_area("Short Description", value=proj.get("description", ""), height=85)
            edit_tech = st.text_input("Technology Stack (comma-separated)", value=proj.get("tech_stack", ""))

            col_d1, col_d2 = st.columns(2)
            with col_d1:
                edit_start = st.date_input("Start Date", value=parse_date(proj.get("start_date", "")))
            with col_d2:
                edit_deadline = st.date_input("Target Deadline", value=parse_date(proj.get("target_deadline", "")))

            col_p1, col_p2 = st.columns(2)
            with col_p1:
                pri_idx = PROJECT_PRIORITIES.index(proj["priority"]) if proj["priority"] in PROJECT_PRIORITIES else 1
                edit_priority = st.selectbox("Priority", PROJECT_PRIORITIES, index=pri_idx)
            with col_p2:
                stat_idx = PROJECT_STATUSES.index(proj["status"]) if proj["status"] in PROJECT_STATUSES else 0
                edit_status = st.selectbox("Current Status", PROJECT_STATUSES, index=stat_idx)

            col_u1, col_u2 = st.columns(2)
            with col_u1:
                edit_github = st.text_input("GitHub Repository URL (Optional)", value=proj.get("github_url", ""))
            with col_u2:
                edit_demo = st.text_input("Live Demo URL (Optional)", value=proj.get("demo_url", ""))

            edit_notes = st.text_area("Technical Notes & Goals (Optional)", value=proj.get("notes", ""), height=90)

            save_submitted = st.form_submit_button("Save Changes 💾", use_container_width=True)

            if save_submitted:
                ok, msg = project_service.update_project(
                    project_id=selected_id,
                    user_id=user_id,
                    name=edit_name,
                    description=edit_desc,
                    category=edit_cat,
                    tech_stack=edit_tech,
                    start_date=edit_start.isoformat() if edit_start else "",
                    target_deadline=edit_deadline.isoformat() if edit_deadline else "",
                    priority=edit_priority,
                    status=edit_status,
                    github_url=edit_github,
                    demo_url=edit_demo,
                    notes=edit_notes,
                )
                if ok:
                    st.session_state.projects_view = "detail"
                    st.toast("Project updated successfully!", icon="✅")
                    st.rerun()
                else:
                    st.error(msg)
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # ----------------------------------------------------
    # VIEW: PROJECT DETAIL & TASK MANAGEMENT
    # ----------------------------------------------------
    if view == "detail" and selected_id:
        proj = project_service.get_project_with_details(selected_id, user_id)
        if not proj:
            st.error("Project not found.")
            st.session_state.projects_view = "list"
            st.rerun()

        # Navigation & Actions Bar
        col_nav_back, col_actions = st.columns([2, 1])
        with col_nav_back:
            if st.button("← Back to All Projects", key="btn_back_to_list", type="secondary"):
                st.session_state.projects_view = "list"
                st.rerun()
        with col_actions:
            c_edit, c_del = st.columns(2)
            with c_edit:
                if st.button("✏️ Edit", key="btn_detail_edit", use_container_width=True):
                    st.session_state.projects_view = "edit"
                    st.rerun()
            with c_del:
                if st.button("🗑️ Delete", key="btn_detail_del_prompt", use_container_width=True):
                    st.session_state.confirm_delete_project_id = selected_id
                    st.rerun()

        # Delete confirmation card
        if st.session_state.get("confirm_delete_project_id") == selected_id:
            st.markdown(
                f"""
                <div style="background: rgba(255, 99, 132, 0.12); border: 1px solid rgba(255, 99, 132, 0.4); border-radius: 12px; padding: 16px; margin-bottom: 20px;">
                    <div style="font-weight: 700; color: #FF859A; margin-bottom: 4px;">Delete Project Confirmation</div>
                    <div style="font-size: 0.9rem; margin-bottom: 12px;">
                        Are you sure you want to permanently delete <b>{proj['name']}</b> and all its associated tasks? This action cannot be undone.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            col_cd1, col_cd2 = st.columns([1, 1])
            with col_cd1:
                if st.button("⚠️ Yes, Permanently Delete", key="btn_confirm_delete_exec", use_container_width=True):
                    project_service.delete_project(selected_id, user_id)
                    st.session_state.confirm_delete_project_id = None
                    st.session_state.selected_project_id = None
                    st.session_state.projects_view = "list"
                    st.toast("Project deleted.", icon="🗑️")
                    st.rerun()
            with col_cd2:
                if st.button("Cancel", key="btn_cancel_delete_exec", use_container_width=True):
                    st.session_state.confirm_delete_project_id = None
                    st.rerun()

        # Project Overview Card
        st.markdown('<div class="candivue-card">', unsafe_allow_html=True)
        # Header badges
        status_html = get_status_badge_html(proj["status"])
        priority_html = get_priority_badge_html(proj["priority"])
        overdue_pill = '<span class="pill-badge pill-missing">⚠️ Overdue</span>' if proj["is_overdue"] else ''

        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px; margin-bottom: 12px;">
                <div>
                    <h2 style="margin: 0 0 6px 0;">{proj['name']}</h2>
                    <div>
                        <span class="pill-badge pill-neutral">{proj['category']}</span>
                        {status_html}
                        {priority_html}
                        {overdue_pill}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if proj.get("description"):
            st.markdown(f"<p style='color: {theme['text_secondary']}; font-size: 0.95rem; margin-bottom: 14px;'>{proj['description']}</p>", unsafe_allow_html=True)

        # Tech stack pills
        if proj.get("tech_stack"):
            tech_tags = "".join([f'<span class="tech-tag">{t.strip()}</span>' for t in proj["tech_stack"].split(",") if t.strip()])
            st.markdown(f"<div style='margin-bottom: 14px;'><b>Tech Stack:</b> {tech_tags}</div>", unsafe_allow_html=True)

        # Key details in clean metadata grid
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.markdown(f"**Start Date:** {proj.get('start_date') or 'Not set'}")
        with col_m2:
            st.markdown(f"**Target Deadline:** {proj.get('target_deadline') or 'Not set'}")
        with col_m3:
            st.markdown(f"**Last Updated:** {proj.get('updated_at', '')[:16]}")

        # Links (GitHub & Demo)
        links_html = []
        if proj.get("github_url"):
            links_html.append(f'<a href="{proj["github_url"]}" target="_blank" style="color: {theme["accent_lavender"]}; text-decoration: none; font-weight: 600; margin-right: 18px;">🔗 GitHub Repository ↗</a>')
        if proj.get("demo_url"):
            links_html.append(f'<a href="{proj["demo_url"]}" target="_blank" style="color: {theme["accent_pink"]}; text-decoration: none; font-weight: 600;">🚀 Live Demo ↗</a>')
        if links_html:
            st.markdown(f"<div style='margin-top: 10px; padding-top: 10px; border-top: 1px solid {theme['border_color']};'>{' '.join(links_html)}</div>", unsafe_allow_html=True)

        if proj.get("notes"):
            with st.expander("📝 Project Notes & Technical Objectives"):
                st.markdown(proj["notes"])

        st.markdown('</div>', unsafe_allow_html=True)

        # Progress Summary Card
        st.markdown('<div class="candivue-card">', unsafe_allow_html=True)
        st.subheader("Progress & Completion")
        prog_val = min(1.0, max(0.0, proj["progress"] / 100))
        st.progress(prog_val)

        p_col1, p_col2 = st.columns([2, 1])
        with p_col1:
            st.markdown(f"<span style='font-size: 1.15rem; font-weight: 700; color: {theme['accent_pink']};'>{proj['progress']:.0f}% Completed</span> • {proj['completed_tasks']} of {proj['total_tasks']} tasks marked done", unsafe_allow_html=True)
        with p_col2:
            if proj["total_tasks"] > 0 and proj["completed_tasks"] == proj["total_tasks"] and proj["status"] != "Completed":
                if st.button("🎉 Mark Project as Completed", key="btn_complete_project_prompt", use_container_width=True):
                    project_service.update_project(
                        project_id=selected_id,
                        user_id=user_id,
                        name=proj["name"],
                        description=proj.get("description", ""),
                        category=proj["category"],
                        tech_stack=proj.get("tech_stack", ""),
                        start_date=proj.get("start_date", ""),
                        target_deadline=proj.get("target_deadline", ""),
                        priority=proj["priority"],
                        status="Completed",
                        github_url=proj.get("github_url", ""),
                        demo_url=proj.get("demo_url", ""),
                        notes=proj.get("notes", ""),
                    )
                    st.toast("Project marked as Completed! Great job!", icon="🏆")
                    st.rerun()

        if proj["total_tasks"] == 0:
            st.caption("No tasks created yet. Add milestones below to track development progress.")
        st.markdown('</div>', unsafe_allow_html=True)

        # Tasks & Milestones Section
        st.markdown('<div class="candivue-card">', unsafe_allow_html=True)
        st.subheader("Tasks & Milestones")

        # Expandable Add Task Form
        with st.expander("➕ Add New Milestone / Task"):
            with st.form(f"form_add_task_{selected_id}", clear_on_submit=True):
                t_title = st.text_input("Task Title *", placeholder="e.g. Implement JWT authentication module")
                col_tk1, col_tk2, col_tk3 = st.columns(3)
                with col_tk1:
                    t_due = st.date_input("Due Date", value=datetime.today().date())
                with col_tk2:
                    t_priority = st.selectbox("Priority", PROJECT_PRIORITIES, index=1)
                with col_tk3:
                    t_status = st.selectbox("Initial Status", TASK_STATUSES, index=0)
                t_desc = st.text_input("Task Details / Notes (Optional)", placeholder="Notes, acceptance criteria, or PR link...")
                t_submit = st.form_submit_button("Add Task")

                if t_submit:
                    due_str = t_due.isoformat() if t_due else ""
                    t_ok, t_msg, _ = project_service.add_task(
                        project_id=selected_id,
                        user_id=user_id,
                        title=t_title,
                        description=t_desc,
                        due_date=due_str,
                        priority=t_priority,
                        status=t_status,
                    )
                    if t_ok:
                        st.toast("Task added!", icon="✅")
                        st.rerun()
                    else:
                        st.error(t_msg)

        # Task Filter Tabs
        all_tasks = project_service.get_project_tasks_enriched(selected_id, user_id)
        task_filter = st.radio(
            "Filter Tasks",
            ["All Tasks", "To Do", "In Progress", "Completed"],
            horizontal=True,
            label_visibility="collapsed",
            key="task_filter_radio"
        )

        filtered_tasks = all_tasks
        if task_filter != "All Tasks":
            filtered_tasks = [t for t in all_tasks if t["status"] == task_filter]

        if not filtered_tasks:
            st.markdown(
                f"<div style='text-align: center; padding: 25px 0; color: {theme['text_secondary']};'>No tasks found for <b>{task_filter}</b>.</div>",
                unsafe_allow_html=True,
            )
        else:
            for t in filtered_tasks:
                is_done = t["status"] == "Completed"
                overdue_tag = '<span style="color: #FF859A; font-weight: 600; font-size: 0.75rem; margin-left: 8px;">⚠️ Overdue</span>' if t["is_overdue"] else ''
                due_text = f"Due: {t['due_date']}" if t.get("due_date") else "No due date"

                st.markdown(
                    f"""
                    <div style="border: 1px solid {theme['border_color']}; border-radius: 8px; padding: 10px 14px; margin-bottom: 8px; background: rgba(0,0,0,0.03);">
                        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                            <div style="flex: 1; min-width: 200px;">
                                <div style="font-weight: 600; font-size: 0.92rem; {'text-decoration: line-through; opacity: 0.65;' if is_done else ''}">
                                    {t['title']} {overdue_tag}
                                </div>
                                <div style="font-size: 0.75rem; color: {theme['text_secondary']}; margin-top: 2px;">
                                    {due_text} • Priority: <b>{t['priority']}</b> • Status: <b>{t['status']}</b>
                                </div>
                                {f'<div style="font-size: 0.8rem; color: {theme["text_secondary"]}; margin-top: 4px;">{t["description"]}</div>' if t.get("description") else ''}
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Quick action buttons row for task
                col_t_act1, col_t_act2 = st.columns([4, 1])
                with col_t_act1:
                    toggle_label = "↩ Reopen Task" if is_done else "✓ Mark Done"
                    if st.button(toggle_label, key=f"t_toggle_{t['id']}"):
                        project_service.toggle_task_status(t["id"], user_id)
                        st.rerun()
                with col_t_act2:
                    if st.button("Delete", key=f"t_del_{t['id']}"):
                        project_service.delete_task(t["id"], user_id)
                        st.toast("Task removed.")
                        st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
        return

    # ----------------------------------------------------
    # VIEW: PROJECT DASHBOARD / LIST (DEFAULT)
    # ----------------------------------------------------
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; flex-wrap: wrap; gap: 12px;">
            <div>
                <h2 style="margin: 0 0 4px 0;">My Projects</h2>
                <p style="color: {theme['text_secondary']}; margin: 0; font-size: 0.95rem;">
                    Plan your work. Track your progress. Finish what you start.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Top Add Project Action Button
    col_cta, col_empty = st.columns([1, 4])
    with col_cta:
        if st.button("➕ Add Project", key="btn_add_project_top", type="primary", use_container_width=True):
            st.session_state.projects_view = "new"
            st.rerun()

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Summary Metrics Cards
    summary = db.get_projects_summary(user_id)
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_metric_card("Total Projects", summary["total"], "All personal projects", "lavender")
    with m2:
        render_metric_card("In Progress", summary["in_progress"], "Active development", "yellow")
    with m3:
        render_metric_card("Completed", summary["completed"], "Finished projects", "mint")
    with m4:
        ov_color = "pink" if summary["overdue"] > 0 else "neutral"
        render_metric_card("Overdue", summary["overdue"], "Past target deadline", ov_color)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Filter & Sort Controls
    st.markdown('<div class="candivue-card" style="padding: 16px 20px; margin-bottom: 20px;">', unsafe_allow_html=True)
    f_col1, f_col2, f_col3, f_col4, f_col5 = st.columns([2, 1, 1, 1, 1])

    with f_col1:
        search_txt = st.text_input("Search Projects", placeholder="Search by name, tech...", key="proj_search_input", label_visibility="collapsed")
    with f_col2:
        filter_status = st.selectbox("Status", ["All Statuses"] + PROJECT_STATUSES, key="proj_status_filter", label_visibility="collapsed")
    with f_col3:
        filter_cat = st.selectbox("Category", ["All Categories"] + PROJECT_CATEGORIES, key="proj_cat_filter", label_visibility="collapsed")
    with f_col4:
        filter_priority = st.selectbox("Priority", ["All Priorities"] + PROJECT_PRIORITIES, key="proj_priority_filter", label_visibility="collapsed")
    with f_col5:
        sort_choice = st.selectbox(
            "Sort",
            ["Recently Updated", "Deadline (Earliest)", "Deadline (Latest)", "Progress (Highest)", "Progress (Lowest)", "Name (A-Z)"],
            key="proj_sort_filter",
            label_visibility="collapsed"
        )

    # Map sort choice
    sort_map = {
        "Recently Updated": "updated_desc",
        "Deadline (Earliest)": "deadline_asc",
        "Deadline (Latest)": "deadline_desc",
        "Progress (Highest)": "progress_desc",
        "Progress (Lowest)": "progress_asc",
        "Name (A-Z)": "name_asc",
    }
    sort_key = sort_map.get(sort_choice, "updated_desc")

    projects = project_service.get_user_projects_enriched(
        user_id=user_id,
        status=filter_status,
        category=filter_cat,
        priority=filter_priority,
        search=search_txt,
        sort_by=sort_key,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # Empty States
    if summary["total"] == 0:
        st.markdown(
            f"""
            <div class="candivue-card" style="text-align: center; padding: 45px 30px;">
                <div style="font-size: 2.8rem; margin-bottom: 12px;">🌱</div>
                <h3 style="margin-bottom: 6px;">No projects yet</h3>
                <p style="color: {theme['text_secondary']}; max-width: 500px; margin: 0 auto 20px auto; font-size: 0.95rem;">
                    Plan your work, track milestones, and showcase your development journey. Create your first project to organize your campus portfolio.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col_c1, col_c2, col_c3 = st.columns([1, 1, 1])
        with col_c2:
            if st.button("➕ Add Your First Project", key="btn_first_proj", type="primary", use_container_width=True):
                st.session_state.projects_view = "new"
                st.rerun()
        return

    if not projects:
        st.markdown(
            f"""
            <div class="candivue-card" style="text-align: center; padding: 35px 20px;">
                <h4 style="margin-bottom: 6px;">No projects match your active filters</h4>
                <p style="color: {theme['text_secondary']}; font-size: 0.9rem;">
                    Try clearing your search query or selecting "All" across the filter dropdowns.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Render Project Cards
    for p in projects:
        status_html = get_status_badge_html(p["status"])
        priority_html = get_priority_badge_html(p["priority"])
        overdue_badge = '<span class="pill-badge pill-missing">⚠️ Overdue</span>' if p["is_overdue"] else ''
        tech_tags = "".join([f'<span class="tech-tag">{t.strip()}</span>' for t in p.get("tech_stack", "").split(",") if t.strip()])

        dead_str = f"Deadline: <b>{p['target_deadline']}</b>" if p.get("target_deadline") else "No deadline"

        st.markdown(
            f"""
            <div class="candivue-card" style="margin-bottom: 16px;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px; margin-bottom: 8px;">
                    <div>
                        <div style="font-weight: 700; font-size: 1.15rem; color: {theme['text_primary']};">{p['name']}</div>
                        <div style="font-size: 0.8rem; color: {theme['text_secondary']}; margin-top: 2px;">
                            <span class="pill-badge pill-neutral">{p['category']}</span>
                            {status_html}
                            {priority_html}
                            {overdue_badge}
                        </div>
                    </div>
                    <div style="text-align: right; font-size: 0.82rem; color: {theme['text_secondary']};">
                        {dead_str}
                    </div>
                </div>
                {f'<p style="color: {theme["text_secondary"]}; font-size: 0.88rem; margin: 8px 0 10px 0;">{p["description"]}</p>' if p.get("description") else ''}
                {f'<div style="margin-bottom: 10px;">{tech_tags}</div>' if tech_tags else ''}
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Progress bar & card action button
        col_pb, col_act = st.columns([3, 1])
        with col_pb:
            p_val = min(1.0, max(0.0, p["progress"] / 100))
            st.progress(p_val)
            task_label = f"{p['completed_tasks']} of {p['total_tasks']} tasks completed" if p["total_tasks"] > 0 else "No tasks added yet"
            st.markdown(f"<div style='font-size: 0.8rem; color: {theme['text_secondary']};'><b>{p['progress']:.0f}% Complete</b> • {task_label}</div>", unsafe_allow_html=True)
        with col_act:
            if st.button("Open Project ➔", key=f"open_proj_{p['id']}", use_container_width=True):
                st.session_state.selected_project_id = p["id"]
                st.session_state.projects_view = "detail"
                st.rerun()

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)



# ==========================================
# PAGE: SETTINGS
# ==========================================
def render_settings_page():
    """Render user settings and optional API key configuration."""
    user = st.session_state.user
    st.markdown(
        f"""
        <div style="margin-bottom: 24px;">
            <h2>Account & Evaluation Settings</h2>
            <p style="color: {theme['text_secondary']};">
                Configure your display preferences and optional AI evaluation keys.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    prefs = db.get_user_preferences(user["id"])

    st.markdown('<div class="candivue-card">', unsafe_allow_html=True)
    st.subheader("Profile Information")
    st.markdown(f"**Full Name:** {user['full_name']}")
    st.markdown(f"**Email Address:** {user['email']}")
    st.markdown(f"**Account Created:** {user.get('created_at', 'Active')}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="candivue-card">', unsafe_allow_html=True)
    with st.form("settings_form"):
        st.subheader("Preferences & Optional AI Integration")

        col1, col2 = st.columns(2)
        with col1:
            theme_choice = st.selectbox(
                "Interface Theme",
                ["dark", "light"],
                index=0 if prefs.get("theme", "dark") == "dark" else 1,
            )
        with col2:
            diff_choice = st.selectbox(
                "Default Preferred Difficulty",
                ["Beginner", "Intermediate", "Advanced"],
                index=["Beginner", "Intermediate", "Advanced"].index(prefs.get("preferred_difficulty", "Intermediate")),
            )

        st.markdown("<hr style='opacity: 0.15; margin: 15px 0;'>", unsafe_allow_html=True)
        st.markdown("#### Optional AI Evaluation Engine (Gemini / OpenAI)")
        st.caption(
            "Candivue features a 100% offline rule-based evaluation engine that scores technical answers and identifies missing concepts without an API key. "
            "If you have a Gemini or OpenAI API key and wish to enable LLM-powered feedback, enter it below:"
        )

        current_key = prefs.get("api_key", "")
        # Mask key display
        masked_display = (current_key[:4] + "••••••••" + current_key[-4:]) if len(current_key) > 8 else current_key
        api_key_input = st.text_input(
            "AI API Key (Optional)",
            value=current_key,
            type="password",
            placeholder="AIzaSy... or sk-...",
        )

        save_btn = st.form_submit_button("Save Preferences", use_container_width=True)

        if save_btn:
            db.update_user_preferences(
                user_id=user["id"],
                theme=theme_choice,
                api_key=api_key_input.strip(),
                preferred_difficulty=diff_choice,
            )
            st.session_state.theme = theme_choice
            st.toast("Settings updated successfully!", icon="✅")
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# ==========================================
# MAIN APPLICATION CONTROLLER
# ==========================================
def main():
    if not st.session_state.user:
        render_auth_page()
    else:
        render_sidebar()
        page = st.session_state.current_page

        if page == "Dashboard":
            render_dashboard_page()
        elif page in ("Start Interview", "Mock Interviews"):
            render_start_interview_page()
        elif page == "Practice Questions":
            render_practice_questions_page()
        elif page == "Performance Analytics":
            render_analytics_page()
        elif page == "Interview History":
            render_history_page()
        elif page in ("My Projects", "Project Development Status", "Project Status"):
            render_my_projects_page()
        elif page == "Settings":
            render_settings_page()
        else:
            render_dashboard_page()


if __name__ == "__main__":
    main()
