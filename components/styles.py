import streamlit as st
from typing import Dict, Any, List

__all__ = [
    "THEMES",
    "MOTIVATIONAL_QUOTES",
    "get_current_theme",
    "inject_custom_css",
    "render_metric_card",
    "render_hero_banner",
    "render_quote_card",
    "get_status_badge_html",
    "get_priority_badge_html",
]

THEMES = {
    "dark": {
        "bg_main": "#120D1D",
        "bg_card": "#1D162E",
        "bg_card_secondary": "#251C3B",
        "bg_sidebar": "#150F23",
        "text_primary": "#F7F5FA",
        "text_secondary": "#9E95B0",
        "border_color": "rgba(235, 225, 255, 0.07)",
        "accent_pink": "#F9B8D0",
        "accent_lavender": "#D8B4F8",
        "accent_yellow": "#FDE293",
        "accent_mint": "#A8E6CF",
        "nav_active_bg": "rgba(216, 180, 248, 0.08)",
        "nav_hover_bg": "rgba(255, 255, 255, 0.035)",
        "nav_active_border": "#D8B4F8",
        "avatar_bg": "rgba(216, 180, 248, 0.12)",
        "avatar_text": "#D8B4F8",
        "accent_gradient_hero": "linear-gradient(135deg, #2D1B4E 0%, #1D1530 100%)",
        "accent_gradient_card": "linear-gradient(135deg, rgba(216, 180, 248, 0.15) 0%, rgba(249, 184, 208, 0.08) 100%)",
        "shadow": "0 8px 30px rgba(7, 4, 15, 0.4)",
        "input_bg": "#181226",
        "input_border": "rgba(216, 180, 248, 0.2)"
    },
    "light": {
        "bg_main": "#FAF7F5",
        "bg_card": "#FFFFFF",
        "bg_card_secondary": "#F4EFEA",
        "bg_sidebar": "#F6F2EC",
        "text_primary": "#1E162B",
        "text_secondary": "#706780",
        "border_color": "rgba(40, 25, 60, 0.08)",
        "accent_pink": "#E06A94",
        "accent_lavender": "#965BD6",
        "accent_yellow": "#D99B16",
        "accent_mint": "#3E9E7D",
        "nav_active_bg": "rgba(150, 91, 214, 0.08)",
        "nav_hover_bg": "rgba(30, 22, 43, 0.035)",
        "nav_active_border": "#965BD6",
        "avatar_bg": "rgba(150, 91, 214, 0.12)",
        "avatar_text": "#965BD6",
        "accent_gradient_hero": "linear-gradient(135deg, #FDE8F1 0%, #EFE8FA 100%)",
        "accent_gradient_card": "linear-gradient(135deg, rgba(249, 184, 208, 0.3) 0%, rgba(216, 180, 248, 0.2) 100%)",
        "shadow": "0 6px 24px rgba(45, 30, 60, 0.06)",
        "input_bg": "#FFFFFF",
        "input_border": "rgba(169, 112, 230, 0.25)"
    }
}

MOTIVATIONAL_QUOTES = [
    {"quote": "Every master was once a beginner. Keep refining your fundamentals.", "author": "Robin Sharma"},
    {"quote": "Confidence in an interview comes from clarity of concepts, not memorization.", "author": "Candivue Placement Insights"},
    {"quote": "Small steps today. Stronger interviews tomorrow.", "author": "Candivue"},
    {"quote": "It is not about having all the answers immediately; it is about demonstrating how systematically you think.", "author": "Senior Tech Interviewer"},
    {"quote": "The gap between where you are and where you want to be is bridged by deliberate practice.", "author": "James Clear"}
]


def get_current_theme() -> Dict[str, str]:
    """Retrieve theme tokens based on session state."""
    theme_name = st.session_state.get("theme", "dark")
    return THEMES.get(theme_name, THEMES["dark"])


def inject_custom_css():
    """Inject polished custom CSS adhering to the deep plum/charcoal & pastel aesthetic."""
    theme = get_current_theme()
    is_dark = st.session_state.get("theme", "dark") == "dark"

    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700&display=swap');

    /* Global Base */
    html, body, [data-testid="stAppViewContainer"] {{
        background-color: {theme['bg_main']} !important;
        color: {theme['text_primary']} !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    [data-testid="stHeader"] {{
        background-color: transparent !important;
    }}

    /* Sidebar Layout - Clean, fixed width approx 250px on desktop */
    [data-testid="stSidebar"] {{
        min-width: 250px !important;
        max-width: 260px !important;
        width: 256px !important;
        background-color: {theme['bg_sidebar']} !important;
        border-right: 1px solid {theme['border_color']} !important;
    }}

    [data-testid="stSidebar"] > div:first-child {{
        min-width: 250px !important;
        max-width: 260px !important;
        width: 256px !important;
        padding-top: 1.1rem !important;
        padding-bottom: 1.1rem !important;
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
    }}

    [data-testid="stSidebarUserContent"] {{
        padding-top: 0 !important;
    }}

    /* Sidebar Section Headers */
    .sidebar-section-header {{
        font-size: 0.68rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.08em !important;
        color: {theme['text_secondary']} !important;
        text-transform: uppercase !important;
        padding: 12px 10px 4px 10px !important;
        margin: 0 !important;
        display: block !important;
        opacity: 0.75;
    }}

    /* Sidebar Navigation Button Container */
    [data-testid="stSidebar"] div.stButton {{
        margin: 1px 0 !important;
    }}

    /* Sidebar Navigation Button Rows - Compact, left-aligned, full width */
    [data-testid="stSidebar"] div.stButton > button {{
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        justify-content: flex-start !important;
        text-align: left !important;
        width: 100% !important;
        height: 36px !important;
        min-height: 36px !important;
        max-height: 36px !important;
        padding: 0 10px !important;
        border-radius: 6px !important;
        font-size: 0.84rem !important;
        font-weight: 500 !important;
        letter-spacing: -0.01em !important;
        background: transparent !important;
        border: 1px solid transparent !important;
        border-left: 2px solid transparent !important;
        box-shadow: none !important;
        color: {theme['text_secondary']} !important;
        cursor: pointer !important;
        transition: background-color 0.15s ease, color 0.15s ease, border-color 0.15s ease !important;
    }}

    /* Sidebar Button Hover */
    [data-testid="stSidebar"] div.stButton > button:hover {{
        background-color: {theme['nav_hover_bg']} !important;
        color: {theme['text_primary']} !important;
        border-left: 2px solid transparent !important;
        transform: none !important;
        box-shadow: none !important;
    }}

    /* Sidebar Button Active State (kind="primary" on Streamlit button) */
    [data-testid="stSidebar"] div.stButton > button[kind="primary"],
    [data-testid="stSidebar"] div.stButton > button[data-testid="stBaseButton-primary"] {{
        background-color: {theme['nav_active_bg']} !important;
        color: {theme['text_primary']} !important;
        border-left: 2px solid {theme['nav_active_border']} !important;
        font-weight: 600 !important;
    }}

    /* Material Outline Icons inside sidebar buttons - 18px monochrome */
    [data-testid="stSidebar"] div.stButton > button span[data-testid="stIconMaterial"] {{
        font-size: 18px !important;
        width: 18px !important;
        height: 18px !important;
        min-width: 18px !important;
        margin-right: 10px !important;
        margin-left: 0 !important;
        color: inherit !important;
        font-variation-settings: 'FILL' 0, 'wght' 350, 'GRAD' 0, 'opsz' 20 !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        opacity: 0.88 !important;
    }}

    /* Text inside sidebar buttons */
    [data-testid="stSidebar"] div.stButton > button p {{
        font-size: 0.84rem !important;
        font-weight: inherit !important;
        color: inherit !important;
        margin: 0 !important;
        line-height: 1 !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }}

    /* Compact account row */
    .sidebar-account-row {{
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 10px;
        border-radius: 6px;
        margin-top: 12px;
        margin-bottom: 4px;
        background: transparent;
    }}

    .sidebar-avatar {{
        width: 28px;
        height: 28px;
        min-width: 28px;
        border-radius: 50%;
        background-color: {theme['avatar_bg']};
        color: {theme['avatar_text']};
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        border: 1px solid {theme['border_color']};
    }}

    /* Typography */
    h1, h2, h3, h4, h5, h6 {{
        font-family: 'Outfit', 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 700 !important;
        color: {theme['text_primary']} !important;
        letter-spacing: -0.02em;
    }}

    p, span, label, div {{
        color: {theme['text_primary']};
    }}

    /* Cards */
    .candivue-card {{
        background-color: {theme['bg_card']};
        border: 1px solid {theme['border_color']};
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: {theme['shadow']};
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}

    .candivue-card-hero {{
        background: {theme['accent_gradient_hero']};
        border: 1px solid {theme['border_color']};
        border-radius: 24px;
        padding: 32px;
        margin-bottom: 28px;
        box-shadow: {theme['shadow']};
        position: relative;
        overflow: hidden;
    }}

    /* Metric Card */
    .metric-box {{
        background-color: {theme['bg_card']};
        border: 1px solid {theme['border_color']};
        border-radius: 18px;
        padding: 20px 22px;
        box-shadow: {theme['shadow']};
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 100%;
    }}

    .metric-value {{
        font-size: 2.2rem;
        font-weight: 800;
        font-family: 'Outfit', sans-serif;
        color: {theme['accent_pink'] if is_dark else theme['accent_lavender']};
        margin: 6px 0;
        line-height: 1.1;
    }}

    .metric-label {{
        font-size: 0.88rem;
        color: {theme['text_secondary']};
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}

    /* Badges & Pills */
    .pill-badge {{
        display: inline-block;
        padding: 4px 12px;
        border-radius: 30px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.02em;
        margin-right: 6px;
        margin-bottom: 6px;
    }}

    .pill-pink {{
        background: rgba(249, 184, 208, 0.2);
        color: {theme['accent_pink']};
        border: 1px solid rgba(249, 184, 208, 0.4);
    }}

    .pill-lavender {{
        background: rgba(216, 180, 248, 0.2);
        color: {theme['accent_lavender']};
        border: 1px solid rgba(216, 180, 248, 0.4);
    }}

    .pill-yellow {{
        background: rgba(253, 226, 147, 0.2);
        color: {theme['accent_yellow']};
        border: 1px solid rgba(253, 226, 147, 0.4);
    }}

    .pill-mint {{
        background: rgba(168, 230, 207, 0.2);
        color: {theme['accent_mint']};
        border: 1px solid rgba(168, 230, 207, 0.4);
    }}

    .pill-missing {{
        background: rgba(255, 99, 132, 0.15);
        color: #FF859A;
        border: 1px solid rgba(255, 99, 132, 0.3);
    }}

    .pill-neutral {{
        background: rgba(160, 150, 180, 0.15);
        color: {theme['text_secondary']};
        border: 1px solid rgba(160, 150, 180, 0.25);
    }}

    /* Project Tech Tags */
    .tech-tag {{
        display: inline-block;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.74rem;
        font-weight: 500;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid {theme['border_color']};
        color: {theme['text_secondary']};
        margin-right: 4px;
        margin-bottom: 4px;
    }}

    /* Task Item Card */
    .task-card {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 14px;
        border-radius: 10px;
        background-color: {theme['bg_card']};
        border: 1px solid {theme['border_color']};
        margin-bottom: 8px;
        transition: border-color 0.15s ease;
    }}

    .task-card:hover {{
        border-color: {theme['accent_lavender']};
    }}

    /* Input & Forms */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>div {{
        background-color: {theme['input_bg']} !important;
        color: {theme['text_primary']} !important;
        border-radius: 12px !important;
        border: 1px solid {theme['input_border']} !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }}

    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {{
        border-color: {theme['accent_pink']} !important;
        box-shadow: 0 0 0 2px rgba(249, 184, 208, 0.25) !important;
    }}

    /* Primary Action Buttons (Main Content) */
    section.main div.stButton > button,
    [data-testid="stMainBlockContainer"] div.stButton > button {{
        background: linear-gradient(135deg, {theme['accent_lavender']} 0%, {theme['accent_pink']} 100%) !important;
        color: #1A1227 !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        border: none !important;
        padding: 9px 22px !important;
        font-size: 0.92rem !important;
        box-shadow: 0 4px 14px rgba(216, 180, 248, 0.25) !important;
        transition: all 0.2s ease !important;
    }}

    section.main div.stButton > button:hover,
    [data-testid="stMainBlockContainer"] div.stButton > button:hover {{
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 18px rgba(249, 184, 208, 0.4) !important;
    }}

    /* Streamlit tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: {theme['bg_card']};
        padding: 6px;
        border-radius: 16px;
        border: 1px solid {theme['border_color']};
    }}

    .stTabs [data-baseweb="tab"] {{
        border-radius: 12px;
        color: {theme['text_secondary']};
        font-weight: 600;
        padding: 8px 16px;
    }}

    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, rgba(216, 180, 248, 0.25) 0%, rgba(249, 184, 208, 0.2) 100%) !important;
        color: {theme['text_primary']} !important;
    }}

    /* Progress bar */
    .stProgress > div > div > div > div {{
        background: linear-gradient(90deg, {theme['accent_lavender']} 0%, {theme['accent_pink']} 100%) !important;
        border-radius: 10px !important;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_metric_card(label: str, value: Any, subtext: str = "", pill_color: str = "pink"):
    """Render a modern pastel-styled metric card."""
    theme = get_current_theme()
    pill_css = f"pill-{pill_color}"
    html = f"""
    <div class="metric-box">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {f'<div style="font-size: 0.8rem; color: {theme["text_secondary"]};">{subtext}</div>' if subtext else ''}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_hero_banner(first_name: str):
    """Render the dashboard hero card inspired by the reference design."""
    theme = get_current_theme()
    html = f"""
    <div class="candivue-card-hero">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <div style="max-width: 650px;">
                <span class="pill-badge pill-lavender">ADAPTIVE INTERVIEW PREPARATION</span>
                <h1 style="margin: 12px 0 6px 0; font-size: 2.3rem;">Welcome back, {first_name} 👋</h1>
                <p style="font-size: 1.05rem; color: {theme['text_secondary']}; margin-bottom: 0;">
                    Small steps today. Stronger interviews tomorrow. Identify technical knowledge gaps and master campus placements with structured evaluations.
                </p>
            </div>
            <div style="background: rgba(255, 255, 255, 0.05); padding: 14px 20px; border-radius: 18px; border: 1px solid {theme['border_color']}; text-align: center; margin-top: 10px;">
                <div style="font-size: 0.8rem; color: {theme['text_secondary']}; font-weight: 600;">TARGET GOAL</div>
                <div style="font-size: 1.3rem; font-weight: 700; color: {theme['accent_yellow']};">Campus Placement</div>
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_quote_card():
    """Render a motivational quote card."""
    import random
    theme = get_current_theme()
    quote_obj = random.choice(MOTIVATIONAL_QUOTES)
    html = f"""
    <div class="candivue-card" style="border-left: 4px solid {theme['accent_lavender']}; background: {theme['accent_gradient_card']};">
        <div style="font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; color: {theme['text_secondary']}; font-weight: 600; margin-bottom: 6px;">Daily Motivation</div>
        <div style="font-style: italic; font-size: 1.05rem; color: {theme['text_primary']}; line-height: 1.5; margin-bottom: 8px;">
            "{quote_obj['quote']}"
        </div>
        <div style="font-size: 0.82rem; color: {theme['text_secondary']}; text-align: right; font-weight: 500;">
            — {quote_obj['author']}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def get_status_badge_html(status: str) -> str:
    """Return HTML markup for project status pill badge."""
    status_map = {
        "Completed": "pill-mint",
        "In Progress": "pill-lavender",
        "On Hold": "pill-yellow",
        "Not Started": "pill-neutral",
    }
    pill_class = status_map.get(status, "pill-neutral")
    return f'<span class="pill-badge {pill_class}">{status}</span>'


def get_priority_badge_html(priority: str) -> str:
    """Return HTML markup for priority pill badge."""
    priority_map = {
        "High": "pill-pink",
        "Medium": "pill-yellow",
        "Low": "pill-neutral",
    }
    pill_class = priority_map.get(priority, "pill-neutral")
    return f'<span class="pill-badge {pill_class}">{priority}</span>'

