from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def line_chart(
    df: pd.DataFrame,
    y: str,
    title: str,
    color: str | None = None,
    y_label: str | None = None,
) -> go.Figure:
    if df.empty:
        return go.Figure()
    fig = px.line(
        df,
        x="entry_date",
        y=y,
        color=color,
        markers=True,
        title=title,
        labels={"entry_date": "Date", y: y_label or y},
    )
    fig.update_layout(legend_title_text="", hovermode="x unified")
    return fig


def goal_comparison_chart(
    df: pd.DataFrame,
    actual: str,
    goal: str,
    title: str,
    actual_label: str,
    goal_label: str,
) -> go.Figure:
    fig = go.Figure()
    if df.empty:
        return fig
    fig.add_trace(
        go.Scatter(
            x=df["entry_date"],
            y=df[actual],
            mode="lines+markers",
            name=actual_label,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["entry_date"],
            y=df[goal],
            mode="lines",
            name=goal_label,
        )
    )
    fig.update_layout(title=title, xaxis_title="Date", hovermode="x unified")
    return fig


def comparison_bar(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str,
    title: str,
) -> go.Figure:
    if df.empty:
        return go.Figure()
    fig = px.bar(df, x=x, y=y, color=color, barmode="group", title=title)
    fig.update_layout(legend_title_text="")
    return fig


def prediction_chart(actual: pd.DataFrame, predictions: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if not actual.empty:
        fig.add_trace(
            go.Scatter(
                x=actual["entry_date"],
                y=actual["body_weight_kg"],
                mode="lines+markers",
                name="Actual weight",
            )
        )
    if not predictions.empty:
        fig.add_trace(
            go.Scatter(
                x=predictions["entry_date"],
                y=predictions["predicted_body_weight_kg"],
                mode="lines+markers",
                name="Predicted weight",
            )
        )
    fig.update_layout(
        title="Actual Weight vs Predicted Trajectory",
        xaxis_title="Date",
        yaxis_title="Body weight (kg)",
        hovermode="x unified",
    )
    return fig
