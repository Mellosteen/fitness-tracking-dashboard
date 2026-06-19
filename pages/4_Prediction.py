from __future__ import annotations

import streamlit as st

from src.auth import render_auth_sidebar, require_login
from src.charts import prediction_chart
from src.database import fetch_user_entries
from src.ml import train_weight_model
from src.metrics import prepare_entries


st.set_page_config(page_title="Prediction", layout="wide")
render_auth_sidebar()
user = require_login()

st.title("Weight Prediction")

raw_entries = fetch_user_entries(user.id)
if raw_entries.empty or len(raw_entries) < 14:
    st.info("More data is needed. Add at least 14 daily entries to train the model.")
    st.stop()

entries = prepare_entries(raw_entries)
result = train_weight_model(entries)
if result is None:
    st.info("More complete data is needed to train the model.")
    st.stop()

st.metric("Model R^2 score", f"{result.r2_score:.3f}")

left, right = st.columns([2, 1])
with left:
    st.plotly_chart(
        prediction_chart(entries, result.predictions),
        use_container_width=True,
    )
with right:
    st.subheader("Predictions")
    st.dataframe(result.predictions, use_container_width=True, hide_index=True)

st.subheader("Model Coefficients")
st.dataframe(result.coefficients, use_container_width=True, hide_index=True)
