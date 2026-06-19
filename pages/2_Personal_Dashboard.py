from __future__ import annotations

import streamlit as st

from src.auth import render_auth_sidebar, require_login
from src.charts import goal_comparison_chart, line_chart
from src.database import fetch_user_entries
from src.metrics import prepare_entries, weekly_summary, workout_streak


st.set_page_config(page_title="Personal Dashboard", layout="wide")
render_auth_sidebar()
user = require_login()

st.title("Personal Dashboard")

raw_entries = fetch_user_entries(user.id)
if raw_entries.empty:
    st.info("No entries yet. Add your first daily entry to see trends.")
    st.stop()

entries = prepare_entries(raw_entries)
latest = entries.sort_values("entry_date").iloc[-1]

metric_cols = st.columns(4)
metric_cols[0].metric("Latest weight", f"{latest['body_weight_kg']:.1f} kg")
metric_cols[1].metric("7-day avg calories", f"{latest['7_day_avg_calories']:.0f}")
metric_cols[2].metric("7-day avg steps", f"{latest['7_day_avg_steps']:.0f}")
metric_cols[3].metric("Workout streak", workout_streak(entries))

left, right = st.columns(2)
with left:
    st.plotly_chart(
        line_chart(entries, "body_weight_kg", "Weight Trend", y_label="kg"),
        use_container_width=True,
    )
    st.plotly_chart(
        goal_comparison_chart(
            entries,
            "protein_g",
            "protein_goal_g",
            "Protein Intake vs Goal",
            "Protein",
            "Goal",
        ),
        use_container_width=True,
    )

with right:
    st.plotly_chart(
        goal_comparison_chart(
            entries,
            "calories_eaten",
            "calorie_goal",
            "Calories vs Goal",
            "Calories",
            "Goal",
        ),
        use_container_width=True,
    )
    st.plotly_chart(
        line_chart(entries, "steps", "Steps Trend"),
        use_container_width=True,
    )

st.subheader("Weekly Averages")
weekly = weekly_summary(raw_entries)
st.dataframe(weekly, use_container_width=True, hide_index=True)
