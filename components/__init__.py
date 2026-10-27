"""UI components and visual styling package for Candivue."""
from components.styles import (
    THEMES,
    MOTIVATIONAL_QUOTES,
    get_current_theme,
    inject_custom_css,
    render_metric_card,
    render_hero_banner,
    render_quote_card,
    get_status_badge_html,
    get_priority_badge_html,
)

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
