from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import streamlit as st
from supabase import Client, create_client


_BROWSER_SESSION_VERSION = 1
_BROWSER_STORAGE_KEY = "fitness-tracking-dashboard.auth-session.v1"
_BROWSER_ACTION_STATE_KEY = "_auth_browser_action"
_BROWSER_ERROR_STATE_KEY = "_auth_browser_error"

_BROWSER_SESSION_BRIDGE_JS = r"""
export default function(component) {
    const { data, setStateValue } = component;
    const storageKey = data.storage_key;

    const publishSnapshot = () => {
        let sessionJson = null;
        let error = null;

        try {
            sessionJson = window.localStorage.getItem(storageKey);
        } catch (exception) {
            error = exception instanceof Error ? exception.message : String(exception);
        }

        setStateValue(
            "snapshot_json",
            JSON.stringify({ session_json: sessionJson, error })
        );
    };

    try {
        if (data.action === "store" && typeof data.session_json === "string") {
            window.localStorage.setItem(storageKey, data.session_json);
        } else if (data.action === "clear") {
            window.localStorage.removeItem(storageKey);
        }
    } catch (exception) {
        const error = exception instanceof Error ? exception.message : String(exception);
        setStateValue(
            "snapshot_json",
            JSON.stringify({ session_json: null, error })
        );
        return;
    }

    publishSnapshot();

    const handleStorage = (event) => {
        if (event.storageArea === window.localStorage && event.key === storageKey) {
            publishSnapshot();
        }
    };
    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
}
"""

_browser_session_bridge = st.components.v2.component(
    "browser_session_bridge",
    js=_BROWSER_SESSION_BRIDGE_JS,
)


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


def _serialize_browser_session(access_token: str, refresh_token: str) -> str:
    return json.dumps(
        {
            "version": _BROWSER_SESSION_VERSION,
            "access_token": access_token,
            "refresh_token": refresh_token,
        },
        separators=(",", ":"),
        sort_keys=True,
    )


def _parse_browser_session(session_json: str) -> tuple[str, str]:
    value = json.loads(session_json)
    if not isinstance(value, dict) or value.get("version") != _BROWSER_SESSION_VERSION:
        raise ValueError("Unsupported browser session format.")

    access_token = value.get("access_token")
    refresh_token = value.get("refresh_token")
    if not isinstance(access_token, str) or not access_token:
        raise ValueError("Browser session is missing an access token.")
    if not isinstance(refresh_token, str) or not refresh_token:
        raise ValueError("Browser session is missing a refresh token.")
    return access_token, refresh_token


def _schedule_browser_store(access_token: str, refresh_token: str) -> None:
    st.session_state[_BROWSER_ACTION_STATE_KEY] = {
        "action": "store",
        "session_json": _serialize_browser_session(access_token, refresh_token),
    }


def _clear_local_auth(*, clear_browser: bool) -> None:
    for key in ("access_token", "refresh_token", "user"):
        st.session_state.pop(key, None)
    if clear_browser:
        st.session_state[_BROWSER_ACTION_STATE_KEY] = {"action": "clear"}


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

    access_token = session.access_token
    refresh_token = session.refresh_token
    tokens_changed = (
        st.session_state.get("access_token") != access_token
        or st.session_state.get("refresh_token") != refresh_token
    )

    email = getattr(user, "email", "") or ""
    st.session_state["access_token"] = access_token
    st.session_state["refresh_token"] = refresh_token
    st.session_state["user"] = {
        "id": user.id,
        "email": email,
        "display_name": _display_name_from_user(user, email),
    }
    if tokens_changed:
        _schedule_browser_store(access_token, refresh_token)


def get_authed_client() -> Client:
    client = get_client()
    access_token = st.session_state.get("access_token")
    refresh_token = st.session_state.get("refresh_token")
    if access_token and refresh_token:
        response = client.auth.set_session(access_token, refresh_token)
        _store_auth_response(response)
    return client


def _restore_browser_session(session_json: str) -> None:
    access_token, refresh_token = _parse_browser_session(session_json)
    response = get_client().auth.set_session(access_token, refresh_token)
    _store_auth_response(response)


def _browser_snapshot(snapshot_json: str | None) -> tuple[bool, str | None, str | None]:
    if snapshot_json is None:
        return False, None, None
    try:
        snapshot = json.loads(snapshot_json)
    except (TypeError, json.JSONDecodeError):
        return True, None, "Browser session storage returned invalid data."
    if not isinstance(snapshot, dict):
        return True, None, "Browser session storage returned invalid data."

    session_json = snapshot.get("session_json")
    error = snapshot.get("error")
    return (
        True,
        session_json if isinstance(session_json, str) else None,
        error if isinstance(error, str) and error else None,
    )


def restore_auth_session() -> None:
    pending_action = st.session_state.get(_BROWSER_ACTION_STATE_KEY)
    component_data = {
        "storage_key": _BROWSER_STORAGE_KEY,
        "action": "read",
        "session_json": None,
    }
    if isinstance(pending_action, dict):
        component_data.update(pending_action)

    result = _browser_session_bridge(
        key="auth_browser_session",
        data=component_data,
        default={"snapshot_json": None},
        height=0,
        on_snapshot_json_change=lambda: None,
    )
    initialized, browser_session_json, storage_error = _browser_snapshot(
        getattr(result, "snapshot_json", None)
    )

    if storage_error:
        st.session_state[_BROWSER_ERROR_STATE_KEY] = storage_error
        st.session_state.pop(_BROWSER_ACTION_STATE_KEY, None)
        return
    if initialized:
        st.session_state.pop(_BROWSER_ERROR_STATE_KEY, None)

    if isinstance(pending_action, dict):
        action = pending_action.get("action")
        action_completed = (
            action == "clear" and initialized and browser_session_json is None
        ) or (
            action == "store"
            and browser_session_json == pending_action.get("session_json")
        )
        if action_completed:
            st.session_state.pop(_BROWSER_ACTION_STATE_KEY, None)
        return

    if not initialized:
        return

    if current_user():
        if browser_session_json is None:
            _clear_local_auth(clear_browser=False)
            st.rerun()
        return

    if not browser_session_json:
        return

    try:
        _restore_browser_session(browser_session_json)
    except Exception:
        _clear_local_auth(clear_browser=True)
    st.rerun()


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
        _clear_local_auth(clear_browser=True)


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
    restore_auth_session()
    user = current_user()
    with st.sidebar:
        st.header("Account")
        if st.session_state.get(_BROWSER_ERROR_STATE_KEY):
            st.warning("This browser blocked persistent sign-in storage.")
        if user:
            st.caption(user.email)
            st.write(user.display_name)
            if st.button("Log out", use_container_width=True):
                sign_out()
                st.rerun()
        else:
            st.caption("Not signed in")
