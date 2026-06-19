from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import streamlit as st
from supabase import Client, create_client


@dataclass(frozen=True)
class SessionUser:
    id: str
    email: str
    display_name: str


def get_client() -> Client:
    url = st.secrets.get("SUPABASE_URL")
    anon_key = st.secrets.get("SUPABASE_ANON_KEY")
    if not url or not anon_key:
        st.error("Missing SUPABASE_URL or SUPABASE_ANON_KEY in Streamlit secrets.")
        st.stop()
    return create_client(url, anon_key)


def _display_name_from_user(user: Any, fallback_email: str) -> str:
    metadata = getattr(user, "user_metadata", None) or {}
    display_name = metadata.get("display_name") or metadata.get("full_name")
    if display_name:
        return str(display_name)
    return fallback_email.split("@")[0]


def _store_auth_response(response: Any) -> None:
    session = getattr(response, "session", None)
    user = getattr(response, "user", None)
    if not session or not user:
        raise ValueError("Authentication response did not include a session.")

    email = getattr(user, "email", "") or ""
    st.session_state["access_token"] = session.access_token
    st.session_state["refresh_token"] = session.refresh_token
    st.session_state["user"] = {
        "id": user.id,
        "email": email,
        "display_name": _display_name_from_user(user, email),
    }


def get_authed_client() -> Client:
    client = get_client()
    access_token = st.session_state.get("access_token")
    refresh_token = st.session_state.get("refresh_token")
    if access_token and refresh_token:
        client.auth.set_session(access_token, refresh_token)
    return client


def sign_up(email: str, password: str, display_name: str) -> None:
    client = get_client()
    response = client.auth.sign_up(
        {
            "email": email,
            "password": password,
            "options": {"data": {"display_name": display_name}},
        }
    )
    if getattr(response, "session", None):
        _store_auth_response(response)
    else:
        st.success("Account created. Check your email if confirmation is enabled.")


def sign_in(email: str, password: str) -> None:
    response = get_client().auth.sign_in_with_password(
        {"email": email, "password": password}
    )
    _store_auth_response(response)


def sign_out() -> None:
    try:
        get_authed_client().auth.sign_out()
    finally:
        for key in ("access_token", "refresh_token", "user"):
            st.session_state.pop(key, None)


def current_user() -> SessionUser | None:
    user = st.session_state.get("user")
    if not user:
        return None
    return SessionUser(
        id=user["id"],
        email=user["email"],
        display_name=user["display_name"],
    )


def require_login() -> SessionUser:
    user = current_user()
    if not user:
        st.warning("Please log in from the Home page.")
        st.stop()
    return user


def render_auth_sidebar() -> None:
    user = current_user()
    with st.sidebar:
        st.header("Account")
        if user:
            st.caption(user.email)
            st.write(user.display_name)
            if st.button("Log out", use_container_width=True):
                sign_out()
                st.rerun()
        else:
            st.caption("Not signed in")
