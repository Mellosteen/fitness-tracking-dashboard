from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.metrics import prepare_entries


MIN_REQUIRED_ENTRIES = 14

TARGET_COLUMN = "body_weight_kg"

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


@dataclass(frozen=True)
class PredictionDataset:
    frame: pd.DataFrame
    feature_columns: list[str]
    target_column: str
    missing_columns: list[str]
    ready: bool
    message: str


def build_prediction_dataset(entries: pd.DataFrame) -> PredictionDataset:
    """Prepare model-ready data without training a model yet.

    TODO(torch):
    - Import torch only when you start implementing the model.
    - Convert `frame[feature_columns]` into a float32 tensor.
    - Convert `frame[target_column]` into a float32 tensor with shape `(n, 1)`.
    - Normalize features before training; store means/stds for prediction.
    - Define a small `torch.nn.Module`, likely one linear layer first.
    - Train with MSE loss and an optimizer such as Adam or SGD.
    - Return predictions for 7, 14, and 30 days using the latest row as a base.
    """
    df = prepare_entries(entries)
    if df.empty:
        return _dataset(df, ready=False, message="No entries available yet.")

    model_frame = df.dropna(subset=[TARGET_COLUMN]).copy()
    if len(model_frame) < MIN_REQUIRED_ENTRIES:
        return _dataset(
            model_frame,
            ready=False,
            message=f"Add at least {MIN_REQUIRED_ENTRIES} entries with body weight.",
        )

    missing_columns = [
        column
        for column in [TARGET_COLUMN, *FEATURE_COLUMNS]
        if column not in model_frame.columns
    ]
    if missing_columns:
        return _dataset(
            model_frame,
            missing_columns=missing_columns,
            ready=False,
            message="Some required model columns are missing.",
        )

    model_frame["workout_done"] = model_frame["workout_done"].astype(int)
    for column in FEATURE_COLUMNS:
        model_frame[column] = pd.to_numeric(model_frame[column], errors="coerce")
    model_frame[TARGET_COLUMN] = pd.to_numeric(
        model_frame[TARGET_COLUMN],
        errors="coerce",
    )

    model_frame[FEATURE_COLUMNS] = model_frame[FEATURE_COLUMNS].fillna(
        model_frame[FEATURE_COLUMNS].median(numeric_only=True)
    )
    model_frame = model_frame.dropna(subset=[TARGET_COLUMN]).sort_values("entry_date")

    if len(model_frame) < MIN_REQUIRED_ENTRIES:
        return _dataset(
            model_frame,
            ready=False,
            message=f"Add at least {MIN_REQUIRED_ENTRIES} complete weight entries.",
        )

    return _dataset(
        model_frame,
        ready=True,
        message="Dataset is ready for your Torch implementation.",
    )


def _dataset(
    frame: pd.DataFrame,
    missing_columns: list[str] | None = None,
    ready: bool = False,
    message: str = "",
) -> PredictionDataset:
    return PredictionDataset(
        frame=frame,
        feature_columns=FEATURE_COLUMNS,
        target_column=TARGET_COLUMN,
        missing_columns=missing_columns or [],
        ready=ready,
        message=message,
    )
