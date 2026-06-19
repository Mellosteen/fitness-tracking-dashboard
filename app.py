from __future__ import annotations

import streamlit as st

from src.auth import current_user, render_auth_sidebar, sign_in, sign_up


st.set_page_config(page_title="Fitness Dashboard", layout="wide")
render_auth_sidebar()

st.title("Fitness Dashboard")
st.write("Private shared progress tracking for two friends.")

user = current_user()
if user:
    st.success(f"Signed in as {user.display_name}.")
    st.info("Use the page navigation to enter data, review dashboards, or run predictions.")
    st.stop()

tab_login, tab_signup = st.tabs(["Log in", "Sign up"])

with tab_login:
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in", use_container_width=True)
    if submitted:
        try:
            sign_in(email, password)
            st.rerun()
        except Exception as exc:
            st.error(f"Login failed: {exc}")

with tab_signup:
    with st.form("signup_form"):
        display_name = st.text_input("Display name")
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")
        submitted = st.form_submit_button("Create account", use_container_width=True)
    if submitted:
        if not display_name:
            st.error("Display name is required.")
        else:
            try:
                sign_up(new_email, new_password, display_name)
                st.rerun()
            except Exception as exc:
                st.error(f"Sign-up failed: {exc}")
