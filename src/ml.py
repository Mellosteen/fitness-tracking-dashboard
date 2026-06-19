from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.metrics import prepare_entries


# ---------------------------------------------------------------------------
# 1. Learning objective
# ---------------------------------------------------------------------------
#
# This module intentionally prepares the data but does not train a model yet.
# Your next milestone is to implement a linear regression model in Torch:
#
#     y = X @ weights + bias
#
# where:
# - X is the feature matrix built from FEATURE_COLUMNS
# - y is body_weight_kg
# - weights and bias are learned during training
#
# Recommended path:
# 1. Inspect the prepared dataframe in the Streamlit Prediction page.
# 2. Convert X and y to torch.float32 tensors.
# 3. Normalize X.
# 4. Train one linear layer with MSE loss.
# 5. Add predictions for 7, 14, and 30 days.


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

LEARNING_TODOS = [
    "Create X from dataset.frame[dataset.feature_columns].",
    "Create y from dataset.frame[[dataset.target_column]].",
    "Convert X and y to torch.float32 tensors.",
    "Normalize X with training-set mean and standard deviation.",
    "Create a torch.nn.Linear(input_dim, 1) model.",
    "Train with torch.nn.MSELoss and an optimizer.",
    "Track loss values over epochs.",
    "Evaluate with MAE or R^2 after predictions work.",
    "Build 7, 14, and 30 day future rows from the latest entry.",
]


@dataclass(frozen=True)
class PredictionDataset:
    """Container for everything the Prediction page needs before modeling."""

    frame: pd.DataFrame
    feature_columns: list[str]
    target_column: str
    missing_columns: list[str]
    ready: bool
    message: str

    @property
    def feature_count(self) -> int:
        return len(self.feature_columns)

    @property
    def row_count(self) -> int:
        return len(self.frame)


# ---------------------------------------------------------------------------
# 2. Public helper used by the Streamlit page
# ---------------------------------------------------------------------------


def build_prediction_dataset(entries: pd.DataFrame) -> PredictionDataset:
    """Prepare clean tabular data for a future Torch linear regression model.

    This function should stay boring and dependable. It handles:
    - derived metrics from `prepare_entries`
    - missing-column checks
    - numeric conversion
    - simple missing-value filling for features
    - minimum-row checks

    The actual Torch work should happen in new functions below this preparation
    layer, so you can debug the data separately from the model.
    """
    prepared_entries = prepare_entries(entries)
    if prepared_entries.empty:
        return _dataset(
            prepared_entries,
            ready=False,
            message="No entries available yet.",
        )

    model_frame = _keep_rows_with_target(prepared_entries)
    if len(model_frame) < MIN_REQUIRED_ENTRIES:
        return _dataset(
            model_frame,
            ready=False,
            message=f"Add at least {MIN_REQUIRED_ENTRIES} entries with body weight.",
        )

    missing_columns = _missing_model_columns(model_frame)
    if missing_columns:
        return _dataset(
            model_frame,
            missing_columns=missing_columns,
            ready=False,
            message="Some required model columns are missing.",
        )

    model_frame = _coerce_model_columns_to_numeric(model_frame)
    model_frame = _fill_missing_feature_values(model_frame)
    model_frame = _keep_rows_with_target(model_frame)
    model_frame = model_frame.sort_values("entry_date")

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


# ---------------------------------------------------------------------------
# 3. Small data-preparation steps
# ---------------------------------------------------------------------------
#
# These are intentionally split up so you can inspect each stage while learning.


def _keep_rows_with_target(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.dropna(subset=[TARGET_COLUMN]).copy()


def _missing_model_columns(frame: pd.DataFrame) -> list[str]:
    return [
        column
        for column in [TARGET_COLUMN, *FEATURE_COLUMNS]
        if column not in frame.columns
    ]


def _coerce_model_columns_to_numeric(frame: pd.DataFrame) -> pd.DataFrame:
    numeric_frame = frame.copy()
    numeric_frame["workout_done"] = numeric_frame["workout_done"].astype(int)

    for column in FEATURE_COLUMNS:
        numeric_frame[column] = pd.to_numeric(numeric_frame[column], errors="coerce")

    numeric_frame[TARGET_COLUMN] = pd.to_numeric(
        numeric_frame[TARGET_COLUMN],
        errors="coerce",
    )
    return numeric_frame


def _fill_missing_feature_values(frame: pd.DataFrame) -> pd.DataFrame:
    filled_frame = frame.copy()
    feature_medians = filled_frame[FEATURE_COLUMNS].median(numeric_only=True)
    filled_frame[FEATURE_COLUMNS] = filled_frame[FEATURE_COLUMNS].fillna(
        feature_medians
    )
    return filled_frame


def get_feature_frame(dataset: PredictionDataset) -> pd.DataFrame:
    """Return X as a pandas dataframe.

    TODO(torch): once this is comfortable, convert this result with:

        torch.tensor(feature_frame.to_numpy(), dtype=torch.float32)
    """
    return dataset.frame[dataset.feature_columns].copy()


def get_target_frame(dataset: PredictionDataset) -> pd.DataFrame:
    """Return y as a single-column pandas dataframe.

    Keeping y two-dimensional makes it match a `torch.nn.Linear(..., 1)` output.
    """
    return dataset.frame[[dataset.target_column]].copy()


# ---------------------------------------------------------------------------
# 4. Torch implementation guide
# ---------------------------------------------------------------------------
#
# Leave these as TODOs until you are ready. A nice learner-friendly order is:
#
# A. Add torch to dependencies.
# B. Implement `to_torch_tensors`.
# C. Implement feature normalization.
# D. Implement `WeightLinearRegression`.
# E. Implement `train_model`.
# F. Implement forecast row generation.


def to_torch_tensors(dataset: PredictionDataset):
    """TODO(torch): convert the prepared dataset into X and y tensors.

    Target behavior:
    - X shape should be `(row_count, feature_count)`.
    - y shape should be `(row_count, 1)`.
    - both tensors should use `dtype=torch.float32`.

    Sketch:
        import torch

        X = torch.tensor(
            get_feature_frame(dataset).to_numpy(),
            dtype=torch.float32,
        )
        y = torch.tensor(
            get_target_frame(dataset).to_numpy(),
            dtype=torch.float32,
        )
        return X, y
    """
    raise NotImplementedError("TODO: implement tensor conversion with torch.")


def normalize_features():
    """TODO(torch): normalize feature tensors before training.

    Why this matters:
    - `steps` can be in the thousands.
    - `sleep_hours` is usually under 12.
    - Without normalization, large-scale features can dominate training.

    Sketch:
        mean = X.mean(dim=0, keepdim=True)
        std = X.std(dim=0, keepdim=True).clamp_min(1e-8)
        X_normalized = (X - mean) / std
        return X_normalized, mean, std
    """
    raise NotImplementedError("TODO: implement feature normalization with torch.")


def build_linear_model():
    """TODO(torch): create the linear regression model.

    Sketch:
        import torch

        model = torch.nn.Linear(in_features=len(FEATURE_COLUMNS), out_features=1)
        return model
    """
    raise NotImplementedError("TODO: implement a torch.nn.Linear model.")


def train_model():
    """TODO(torch): train the linear model.

    Sketch:
        loss_fn = torch.nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

        for epoch in range(epochs):
            optimizer.zero_grad()
            predictions = model(X_normalized)
            loss = loss_fn(predictions, y)
            loss.backward()
            optimizer.step()

    Return useful values:
    - trained model
    - loss history
    - normalization mean/std
    """
    raise NotImplementedError("TODO: implement the training loop.")


def build_future_feature_rows():
    """TODO(torch): create 7, 14, and 30 day forecast input rows.

    Start simple:
    - Copy the latest prepared row.
    - Increase `days_since_start` by 7, 14, and 30.
    - Keep other nutrition/activity values unchanged for the first version.

    Later, you can make this more realistic by letting users enter assumptions
    for future calories, steps, workouts, and sleep.
    """
    raise NotImplementedError("TODO: implement future feature rows.")


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
