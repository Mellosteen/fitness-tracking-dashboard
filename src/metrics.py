from __future__ import annotations

import pandas as pd


NUMERIC_COLUMNS = [
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
    "sleep_hours",
    "energy_level",
    "hunger_level",
]


def prepare_entries(entries: pd.DataFrame) -> pd.DataFrame:
    if entries.empty:
        return entries

    df = entries.copy()
    df["entry_date"] = pd.to_datetime(df["entry_date"])
    df = df.sort_values(["display_name", "entry_date"])

    for column in NUMERIC_COLUMNS:
        if column in df:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    df["workout_done"] = df.get("workout_done", False).fillna(False).astype(bool)
    df["calorie_difference"] = df["calories_eaten"] - df["calorie_goal"]
    df["protein_difference"] = df["protein_g"] - df["protein_goal_g"]
    df["carbs_difference"] = df["carbs_g"] - df["carbs_goal_g"]
    df["fat_difference"] = df["fat_g"] - df["fat_goal_g"]

    grouped = df.groupby("user_id", group_keys=False)
    df["7_day_avg_weight"] = grouped["body_weight_kg"].transform(
        lambda s: s.rolling(7, min_periods=1).mean()
    )
    df["7_day_avg_calories"] = grouped["calories_eaten"].transform(
        lambda s: s.rolling(7, min_periods=1).mean()
    )
    df["7_day_avg_protein"] = grouped["protein_g"].transform(
        lambda s: s.rolling(7, min_periods=1).mean()
    )
    df["7_day_avg_steps"] = grouped["steps"].transform(
        lambda s: s.rolling(7, min_periods=1).mean()
    )
    df["7_day_avg_activity_calories"] = grouped["activity_calories"].transform(
        lambda s: s.rolling(7, min_periods=1).mean()
    )

    df["days_since_start"] = grouped["entry_date"].transform(
        lambda s: (s - s.min()).dt.days
    )
    df["week_start"] = df["entry_date"].dt.to_period("W-SUN").dt.start_time
    df["adherence_score"] = (
        df["calorie_difference"].abs().le(100).astype(int)
        + df["protein_difference"].ge(0).astype(int)
        + df["steps"].ge(8000).astype(int)
        + df["workout_done"].astype(int)
    )
    return df


def weekly_summary(entries: pd.DataFrame) -> pd.DataFrame:
    if entries.empty:
        return entries
    df = prepare_entries(entries)
    summary = (
        df.groupby(["display_name", "week_start"], as_index=False)
        .agg(
            weekly_avg_body_weight=("body_weight_kg", "mean"),
            weekly_avg_calorie_difference=("calorie_difference", "mean"),
            weekly_workout_count=("workout_done", "sum"),
            weekly_adherence_score=("adherence_score", "mean"),
            entries=("id", "count"),
        )
        .sort_values(["week_start", "display_name"])
    )
    return summary


def workout_streak(entries: pd.DataFrame) -> int:
    if entries.empty or "workout_done" not in entries:
        return 0
    df = prepare_entries(entries).sort_values("entry_date", ascending=False)
    streak = 0
    for completed in df["workout_done"].fillna(False):
        if completed:
            streak += 1
        else:
            break
    return streak
