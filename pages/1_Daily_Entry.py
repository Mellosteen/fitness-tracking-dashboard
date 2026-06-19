from __future__ import annotations

from datetime import date

import streamlit as st

from src.auth import render_auth_sidebar, require_login
from src.database import fetch_entry_for_date, upsert_daily_entry


st.set_page_config(page_title="Daily Entry", layout="wide")
render_auth_sidebar()
user = require_login()

st.title("Daily Entry")

selected_date = st.date_input("Date", value=date.today())
existing = fetch_entry_for_date(user.id, selected_date) or {}

with st.form("daily_entry_form"):
    col_weight, col_activity = st.columns(2)
    with col_weight:
        body_weight_kg = st.number_input(
            "Body weight in kg",
            min_value=0.0,
            max_value=500.0,
            value=float(existing.get("body_weight_kg") or 0.0),
            step=0.1,
        )
        calories_eaten = st.number_input(
            "Calories eaten",
            min_value=0,
            value=int(existing.get("calories_eaten") or 0),
        )
        calorie_goal = st.number_input(
            "Calorie goal",
            min_value=0,
            value=int(existing.get("calorie_goal") or 0),
        )
        protein_g = st.number_input(
            "Protein intake in grams",
            min_value=0,
            value=int(existing.get("protein_g") or 0),
        )
        protein_goal_g = st.number_input(
            "Protein goal in grams",
            min_value=0,
            value=int(existing.get("protein_goal_g") or 0),
        )
        carbs_g = st.number_input(
            "Carbohydrate intake in grams",
            min_value=0,
            value=int(existing.get("carbs_g") or 0),
        )
        carbs_goal_g = st.number_input(
            "Carbohydrate goal in grams",
            min_value=0,
            value=int(existing.get("carbs_goal_g") or 0),
        )
        fat_g = st.number_input(
            "Fat intake in grams",
            min_value=0,
            value=int(existing.get("fat_g") or 0),
        )
        fat_goal_g = st.number_input(
            "Fat goal in grams",
            min_value=0,
            value=int(existing.get("fat_goal_g") or 0),
        )

    with col_activity:
        steps = st.number_input(
            "Steps",
            min_value=0,
            value=int(existing.get("steps") or 0),
        )
        activity_calories = st.number_input(
            "Activity calories",
            min_value=0,
            value=int(existing.get("activity_calories") or 0),
        )
        activity_type = st.text_input(
            "Activity type",
            value=str(existing.get("activity_type") or ""),
        )
        workout_done = st.checkbox(
            "Workout completed",
            value=bool(existing.get("workout_done") or False),
        )
        sleep_hours = st.number_input(
            "Sleep hours",
            min_value=0.0,
            max_value=24.0,
            value=float(existing.get("sleep_hours") or 0.0),
            step=0.5,
        )
        energy_level = st.slider(
            "Energy level",
            min_value=1,
            max_value=10,
            value=int(existing.get("energy_level") or 5),
        )
        hunger_level = st.slider(
            "Hunger level",
            min_value=1,
            max_value=10,
            value=int(existing.get("hunger_level") or 5),
        )
        notes = st.text_area("Notes", value=str(existing.get("notes") or ""))

    submitted = st.form_submit_button("Save entry", use_container_width=True)

if submitted:
    values = {
        "user_id": user.id,
        "display_name": user.display_name,
        "entry_date": selected_date.isoformat(),
        "body_weight_kg": body_weight_kg or None,
        "calories_eaten": calories_eaten,
        "calorie_goal": calorie_goal,
        "protein_g": protein_g,
        "protein_goal_g": protein_goal_g,
        "carbs_g": carbs_g,
        "carbs_goal_g": carbs_goal_g,
        "fat_g": fat_g,
        "fat_goal_g": fat_goal_g,
        "steps": steps,
        "activity_calories": activity_calories,
        "activity_type": activity_type,
        "workout_done": workout_done,
        "sleep_hours": sleep_hours or None,
        "energy_level": energy_level,
        "hunger_level": hunger_level,
        "notes": notes,
    }
    try:
        upsert_daily_entry(values)
        st.success("Entry saved.")
    except Exception as exc:
        st.error(f"Could not save entry: {exc}")
