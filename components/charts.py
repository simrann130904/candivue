import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any, Optional
import streamlit as st
from components.styles import get_current_theme


def get_chart_layout_theme() -> Dict[str, Any]:
    """Return common Plotly layout formatting that matches current theme."""
    theme = get_current_theme()
    is_dark = st.session_state.get("theme", "dark") == "dark"

    return {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {
            "family": "Plus Jakarta Sans, sans-serif",
            "color": theme["text_primary"],
            "size": 12,
        },
        "margin": dict(l=30, r=20, t=40, b=40),
        "xaxis": {
            "gridcolor": "rgba(255,255,255,0.06)" if is_dark else "rgba(0,0,0,0.06)",
            "zerolinecolor": "rgba(255,255,255,0.08)" if is_dark else "rgba(0,0,0,0.08)",
            "color": theme["text_secondary"],
        },
        "yaxis": {
            "gridcolor": "rgba(255,255,255,0.06)" if is_dark else "rgba(0,0,0,0.06)",
            "zerolinecolor": "rgba(255,255,255,0.08)" if is_dark else "rgba(0,0,0,0.08)",
            "color": theme["text_secondary"],
        },
    }


def create_subject_bar_chart(df: pd.DataFrame) -> go.Figure:
    """Create a polished subject-wise average score bar chart."""
    theme = get_current_theme()
    layout = get_chart_layout_theme()

    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No interview attempts recorded yet.<br>Complete a practice session to view your subject scores.",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(color=theme["text_secondary"], size=13)
        )
        fig.update_layout(layout)
        return fig

    # Bar chart with rounded corners and gradient aesthetic
    fig = go.Figure(data=[
        go.Bar(
            x=df["Subject"],
            y=df["Average Score"],
            text=df["Average Score"].apply(lambda v: f"{v}/10"),
            textposition="auto",
            marker=dict(
                color=df["Average Score"],
                colorscale=[
                    [0.0, theme["accent_yellow"]],
                    [0.5, theme["accent_pink"]],
                    [1.0, theme["accent_lavender"]],
                ],
                cmin=0,
                cmax=10,
                line=dict(color=theme["border_color"], width=1.5),
            ),
            hoverinfo="x+y+text",
        )
    ])

    fig.update_layout(layout)
    fig.update_layout(
        title=dict(text="<b>Subject-Wise Average Score</b>", font=dict(size=14, color=theme["text_primary"])),
        yaxis=dict(range=[0, 10.5], title="Average Score (out of 10)"),
        xaxis=dict(title=""),
        height=320,
    )
    return fig


def create_performance_timeline_chart(df: pd.DataFrame) -> go.Figure:
    """Create a score progression timeline chart."""
    theme = get_current_theme()
    layout = get_chart_layout_theme()

    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No timeline data available.<br>Start answering interview questions to track your trajectory.",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(color=theme["text_secondary"], size=13)
        )
        fig.update_layout(layout)
        return fig

    fig = go.Figure()

    # Individual question scores
    fig.add_trace(go.Scatter(
        x=df["Attempt"],
        y=df["Score"],
        mode="markers+lines",
        name="Question Score",
        line=dict(color=theme["accent_pink"], width=2, dash="dot"),
        marker=dict(size=7, color=theme["accent_pink"]),
        hovertext=[f"{s} ({t})" for s, t in zip(df["Subject"], df.get("Topic", [""] * len(df)))],
    ))

    # Rolling average trend
    if "Rolling Average" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["Attempt"],
            y=df["Rolling Average"],
            mode="lines",
            name="Rolling Average Trend",
            line=dict(color=theme["accent_lavender"], width=3.5),
        ))

    fig.update_layout(layout)
    fig.update_layout(
        title=dict(text="<b>Score Progression Over Time</b>", font=dict(size=14, color=theme["text_primary"])),
        yaxis=dict(range=[0, 10.5], title="Score (out of 10)"),
        xaxis=dict(title="Question Sequence Number"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=320,
    )
    return fig


def create_topic_mastery_chart(df: pd.DataFrame) -> go.Figure:
    """Create a horizontal bar chart displaying topic-level scores."""
    theme = get_current_theme()
    layout = get_chart_layout_theme()

    if df.empty:
        fig = go.Figure()
        fig.update_layout(layout)
        return fig

    # Top 8 topics
    df_sub = df.head(8)

    colors = []
    for score in df_sub["Average Score"]:
        if score >= 7.5:
            colors.append(theme["accent_mint"])
        elif score >= 5.5:
            colors.append(theme["accent_yellow"])
        else:
            colors.append(theme["accent_pink"])

    fig = go.Figure(data=[
        go.Bar(
            y=df_sub["Topic"],
            x=df_sub["Average Score"],
            orientation="h",
            text=df_sub["Average Score"].apply(lambda s: f"{s:.1f}/10"),
            textposition="auto",
            marker=dict(color=colors),
        )
    ])

    fig.update_layout(layout)
    fig.update_layout(
        title=dict(text="<b>Topic Proficiency Breakdown</b>", font=dict(size=14, color=theme["text_primary"])),
        xaxis=dict(range=[0, 10.5], title="Average Score"),
        yaxis=dict(autorange="reversed"),
        height=300,
    )
    return fig
