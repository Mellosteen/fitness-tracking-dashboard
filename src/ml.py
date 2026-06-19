from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

from src.metrics import prepare_entries


FEATURE_COLUMNS = [
    "days_since_start",
    "calorie_difference",
    "protein_g",
    "carbs_g",
    "fat_g",
    "steps",
    "activity_calories",
    "workout_done",
    "sleep_hours",
    "energy_level",
    "hunger_level",
    "7_day_avg_calories",
    "7_day_avg_steps",
    "7_day_avg_protein",
    "7_day_avg_activity_calories",
]


@dataclass
class PredictionResult:
    coefficients: pd.DataFrame
    r2_score: float
    predictions: pd.DataFrame


def train_weight_model(entries: pd.DataFrame) -> PredictionResult | None:
    df = prepare_entries(entries)
    if df.empty or len(df) < 14:
        return None

    model_frame = df.dropna(subset=["body_weight_kg"]).copy()
    if len(model_frame) < 14:
        return None

    model_frame["workout_done"] = model_frame["workout_done"].astype(int)
    for column in FEATURE_COLUMNS:
        model_frame[column] = pd.to_numeric(model_frame[column], errors="coerce")

    model_frame[FEATURE_COLUMNS] = model_frame[FEATURE_COLUMNS].fillna(
        model_frame[FEATURE_COLUMNS].median(numeric_only=True)
    )
    X = model_frame[FEATURE_COLUMNS]
    y = model_frame["body_weight_kg"]

    model = LinearRegression()
    model.fit(X, y)
    fitted = model.predict(X)
    score = float(r2_score(y, fitted)) if len(model_frame) > 1 else np.nan

    last = model_frame.sort_values("entry_date").iloc[-1].copy()
    start_date = model_frame["entry_date"].min()
    prediction_rows = []
    for days_ahead in (7, 14, 30):
        row = last.copy()
        row["entry_date"] = last["entry_date"] + timedelta(days=days_ahead)
        row["days_since_start"] = (row["entry_date"] - start_date).days
        predicted = model.predict(pd.DataFrame([row[FEATURE_COLUMNS]]))[0]
        prediction_rows.append(
            {
                "days_ahead": days_ahead,
                "entry_date": row["entry_date"],
                "predicted_body_weight_kg": float(predicted),
            }
        )

    coefficients = pd.DataFrame(
        {
            "feature": FEATURE_COLUMNS,
            "coefficient": model.coef_,
        }
    ).sort_values("coefficient", key=lambda s: s.abs(), ascending=False)

    return PredictionResult(
        coefficients=coefficients,
        r2_score=score,
        predictions=pd.DataFrame(prediction_rows),
    )
