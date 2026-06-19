from __future__ import annotations

import streamlit as st

from src.auth import render_auth_sidebar, require_login
from src.database import fetch_user_entries
from src.ml import LEARNING_TODOS, MIN_REQUIRED_ENTRIES, build_prediction_dataset


st.set_page_config(page_title="Prediction", layout="wide")
render_auth_sidebar()
user = require_login()

st.title("Weight Prediction")

raw_entries = fetch_user_entries(user.id)
dataset = build_prediction_dataset(raw_entries)

if raw_entries.empty or len(raw_entries) < MIN_REQUIRED_ENTRIES:
    st.info(
        f"More data is needed. Add at least {MIN_REQUIRED_ENTRIES} daily entries "
        "before training a model."
    )
    st.stop()

if not dataset.ready:
    st.info(dataset.message)
    if dataset.missing_columns:
        st.write("Missing columns:")
        st.code("\n".join(dataset.missing_columns), language="text")
    st.stop()

st.info(
    "The prediction model is intentionally not implemented yet. "
    "This page now prepares the data and leaves the Torch model for you to build."
)

left, right = st.columns([2, 1])
with left:
    st.subheader("Prepared Training Data")
    preview_columns = [
        "entry_date",
        dataset.target_column,
        *dataset.feature_columns,
    ]
    st.dataframe(
        dataset.frame[preview_columns],
        use_container_width=True,
        hide_index=True,
    )
with right:
    st.subheader("Model TODOs")
    for index, todo in enumerate(LEARNING_TODOS, start=1):
        st.write(f"{index}. {todo}")

    st.caption(
        f"Prepared shape: {dataset.row_count} rows x "
        f"{dataset.feature_count} features."
    )

st.subheader("Feature Columns")
st.code("\n".join(dataset.feature_columns), language="text")
