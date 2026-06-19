from __future__ import annotations

import streamlit as st

from src.auth import render_auth_sidebar, require_login
from src.charts import comparison_bar, line_chart
from src.database import fetch_all_entries
from src.metrics import prepare_entries, weekly_summary


st.set_page_config(page_title="Friend Dashboard", layout="wide")
render_auth_sidebar()
require_login()

st.title("Friend Dashboard")

raw_entries = fetch_all_entries()
if raw_entries.empty:
    st.info("No shared entries yet.")
    st.stop()

entries = prepare_entries(raw_entries)
entries["workout_completed"] = entries["workout_done"].astype(int)

left, right = st.columns(2)
with left:
    st.plotly_chart(
        line_chart(
            entries,
            "body_weight_kg",
            "Body Weight Trend",
            color="display_name",
            y_label="kg",
        ),
        use_container_width=True,
    )
    st.plotly_chart(
        line_chart(
            entries,
            "protein_difference",
            "Protein Goal Adherence",
            color="display_name",
            y_label="grams vs goal",
        ),
        use_container_width=True,
    )
    st.plotly_chart(
        line_chart(entries, "steps", "Steps", color="display_name"),
        use_container_width=True,
    )

with right:
    st.plotly_chart(
        line_chart(
            entries,
            "calorie_difference",
            "Calorie Goal Adherence",
            color="display_name",
            y_label="calories vs goal",
        ),
        use_container_width=True,
    )
    st.plotly_chart(
        line_chart(
            entries,
            "activity_calories",
            "Activity Calories",
            color="display_name",
        ),
        use_container_width=True,
    )
    st.plotly_chart(
        comparison_bar(
            entries,
            x="entry_date",
            y="workout_completed",
            color="display_name",
            title="Workout Completion",
        ),
        use_container_width=True,
    )

st.subheader("Weekly Summaries")
weekly = weekly_summary(raw_entries)
st.dataframe(weekly, use_container_width=True, hide_index=True)

st.subheader("Shared Entries")
visible_columns = [
    "display_name",
    "entry_date",
    "body_weight_kg",
    "calories_eaten",
    "calorie_goal",
    "protein_g",
    "protein_goal_g",
    "carbs_g",
    "carbs_goal_g",
    "fat_g",
    "fat_goal_g",
    "steps",
    "activity_calories",
    "activity_type",
    "workout_done",
    "sleep_hours",
    "energy_level",
    "hunger_level",
    "notes",
]
st.dataframe(entries[visible_columns], use_container_width=True, hide_index=True)
