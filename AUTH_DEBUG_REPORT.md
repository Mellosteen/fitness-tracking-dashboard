# Authentication Persistence Investigation

Date: 2026-06-20

## Executive Summary

The application authenticates users with Supabase Auth using email and password. After a successful login, it copies the Supabase access token, refresh token, and a small user record into `st.session_state`.

The application does not persist that session in the browser. It does not use cookies, browser local storage, a durable server-side session store, or a startup restoration flow. Streamlit documents that `st.session_state` is tied to the browser's WebSocket connection and is reset when the browser tab is reloaded. A browser restart also creates a new connection. Therefore the current implementation cannot meet the requested persistence behavior.

**Most likely root cause:** authentication depends exclusively on `st.session_state`, which is lost when the Streamlit WebSocket session ends.

**Confidence:** High (approximately 95%). This conclusion follows directly from the code and Streamlit's documented state lifecycle. The remaining uncertainty concerns device-specific browser behavior and Supabase dashboard session limits, neither of which can correct the missing browser persistence layer.

There is also a secondary token-refresh defect: `get_authed_client()` calls `set_session()`, which can refresh expired tokens, but ignores the returned replacement token pair. The stale tokens remain in `st.session_state`, so a user who stays connected may later encounter refresh failures even before the Streamlit state is lost.

No implementation files were changed during this investigation.

## 1. Authentication Architecture

### Implemented authentication

- Provider: Supabase Auth.
- Method: email and password.
- Sign-up: `client.auth.sign_up(...)` in `src/auth.py:59-71`.
- Sign-in: `client.auth.sign_in_with_password(...)` in `src/auth.py:74-78`.
- Sign-out: `client.auth.sign_out()` in `src/auth.py:81-86`.
- Authorization: Supabase JWTs are applied to database requests by calling `client.auth.set_session(...)` before PostgREST operations.
- Database protection: `sql/schema.sql` enables Row Level Security and uses `auth.uid()` for ownership checks.

### Not implemented

- OAuth or social login: not present.
- Magic-link or one-time-password login: not present.
- Custom username/password authentication: not present; Supabase performs credential verification.
- WebAuthn, FIDO2, or passkeys: not present.
- Browser-side Supabase client: not present.
- Auth-state listener such as `on_auth_state_change`: not present.

**The application does not currently support passkeys.**

## 2. Session Persistence

### What is stored

After sign-in, `_store_auth_response()` stores these values in Streamlit state (`src/auth.py:34-47`):

- `access_token`
- `refresh_token`
- `user`, containing ID, email, and display name

No authentication data is stored anywhere else in the repository.

### Session restoration

There is no application-startup restoration flow:

- `get_session()` is never called.
- `refresh_session()` is never called.
- No cookie is read.
- No browser local-storage value is read.
- No persistent session ID is exchanged for a server-side session.
- `current_user()` only reads `st.session_state["user"]` (`src/auth.py:89-97`).

If `st.session_state` is empty, the application immediately treats the visitor as logged out.

### Expected behavior by lifecycle event

| Event | Current behavior | Reason |
| --- | --- | --- |
| Normal Streamlit rerun on the same WebSocket | Usually survives | `st.session_state` survives ordinary reruns within the connection. |
| Built-in multipage navigation | Usually survives | Pages share the active Streamlit session. |
| Browser page refresh | Does not reliably survive | Reloading resets the WebSocket and associated Session State. |
| Browser restart or Android process eviction | Does not survive | The new connection has no browser-backed session to restore. |
| Streamlit session expiration/reconnection | Does not survive | No durable restoration source exists. |

Streamlit explicitly documents that Session State is tied to a WebSocket and resets on browser reload: [Streamlit Session State limitations](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state#caveats-and-limitations).

### Token refresh behavior

`get_authed_client()` creates a new Supabase client and calls:

```python
client.auth.set_session(access_token, refresh_token)
```

Supabase documents that `set_session()` refreshes an expired session when possible. However, this application discards its `AuthResponse`. If the refresh token is rotated, the newly issued access and refresh tokens are held only by that temporary client instance and are not copied back to `st.session_state`.

Supabase refresh tokens are normally exchanged for a new token pair, with limited reuse exceptions. Retaining the old token can therefore cause later failures. See [Supabase user sessions](https://supabase.com/docs/guides/auth/sessions) and [Python `set_session`](https://supabase.com/docs/reference/python/auth-setsession).

## 3. Streamlit State Review

Authentication depends solely on `st.session_state`:

- Tokens are written at `src/auth.py:41-42`.
- The user record is written at `src/auth.py:43-47`.
- Tokens are read at `src/auth.py:52-53`.
- Login status is determined from the user record at `src/auth.py:89-97`.
- Logout removes all three state entries at `src/auth.py:85-86`.

All protected pages call `require_login()`, which stops the page when the in-memory user record is absent. Loss of Streamlit state therefore forces a new login even if the corresponding Supabase session remains active on Supabase's servers.

This explains why the symptom can appear device-specific. A browser that keeps its tab and WebSocket alive may appear to remember the user, while Android may terminate a background browser or installed-web-app process more aggressively. The architecture is nevertheless nonpersistent on every platform.

## 4. Supabase Configuration

### Client initialization

`get_client()` calls `create_client(url, anon_key)` with no explicit auth options (`src/auth.py:17-23`). A fresh Python client is created on every call.

The local Conda environment currently contains `supabase` 2.31.0. Its default synchronous client options report:

- `persist_session=True`
- `auto_refresh_token=True`
- storage provider: `SyncMemoryStorage`

These defaults do **not** provide browser persistence in this architecture. `SyncMemoryStorage` exists in the Python server process, and each `get_client()` call creates a new client with a new memory store. It is not Android Chrome local storage and is not a durable Streamlit session store.

`requirements.txt` specifies `supabase>=2.6` rather than an exact version, so the exact Streamlit Cloud version cannot be established from the repository. This does not change the root cause: the app never supplies a browser-backed or durable storage adapter.

### Configuration verdict

- Persistent sessions enabled in the application: **No, not at the browser/application level.**
- Supabase-Python persistence flag: **Defaulted on locally, but backed only by temporary Python memory.**
- Automatic refresh enabled: **Defaulted on locally, but ineffective as a continuous mechanism because clients are short-lived.**
- Opportunistic refresh: **Possible through `set_session()`, but rotated tokens are not saved by the app.**
- Startup restoration implemented: **No.**
- Auth-state listener implemented: **No.**

### Configuration not verifiable from the repository

The following Supabase dashboard settings require live project access and were not verified:

- Time-boxed session duration
- Inactivity timeout
- Single-session-per-user enforcement
- JWT expiration duration
- Refresh-token reuse interval

These settings should be checked before implementation, but they are unlikely to explain a logout on every fresh visit because the application has no restoration mechanism at all.

## 5. Android Compatibility

The login UI uses `st.text_input("Email")` and `st.text_input("Password", type="password")` inside a Streamlit form (`app.py:22-30`). These are recognizable email/password-style controls, and Chrome Password Manager may offer to save and autofill them.

However:

- The code does not control HTML `autocomplete` attributes such as `username` and `current-password`.
- Streamlit submits the form through its application runtime rather than a conventional server-rendered HTML form action.
- Password-manager detection can therefore vary by Chrome, Android version, keyboard, and whether the app was opened from a home-screen shortcut.
- Saved credentials would only reduce typing; they would not provide an authenticated session or satisfy the expected persistence behavior.

No Android-only authentication branch, user-agent check, cookie policy, or storage implementation exists. The primary defect is platform-independent. Android process eviction likely makes it more visible by ending the Streamlit connection.

Hardware-level Chrome autofill behavior was not tested during this repository investigation.

## 6. Passkey Support

No WebAuthn, passkey, or FIDO2 dependency, browser API, challenge endpoint, credential registration flow, or authentication flow exists in the codebase.

**The application does not currently support passkeys.**

Supabase's availability of other authentication methods does not enable them automatically; the application must implement the corresponding browser and server flow.

## 7. Root Cause Analysis

### Primary root cause

Authentication state is stored only in `st.session_state`. The state is tied to one Streamlit WebSocket connection and cannot be restored after a reload, browser restart, Android process termination, or session reconnection.

### Supporting evidence

1. `_store_auth_response()` writes the only token copies to `st.session_state`.
2. `current_user()` reads only the in-memory `user` entry.
3. Repository-wide search finds no cookie, local-storage, durable session, or startup-restoration implementation.
4. No code calls `get_session()`, `refresh_session()`, or an auth-state listener.
5. Streamlit's documented lifecycle says a reload resets Session State.
6. A new Supabase Python client is created for each operation, using temporary in-memory storage by default.

### Secondary defect

When `set_session()` refreshes an expired access token, the application does not save the returned rotated tokens. This can cause authentication failure during a still-active Streamlit connection.

### Confidence

**High, approximately 95%.**

The only meaningful unknowns are live Supabase session policies and the affected Android browser's autofill/process behavior. Neither supplies the missing cross-connection persistence.

## 8. Ranked Remediation Plan

### 1. Add browser-backed Supabase session persistence and startup restoration

**Probability of resolving the reported issue:** Very high.

Use a browser-side authentication component, preferably backed by `supabase-js`, with persistent browser storage, automatic token refresh, and an auth-state listener. On each Streamlit connection, restore the browser session and pass the current token to Python. Python must validate the user with Supabase before accepting the restored identity.

This matches Supabase's normal browser model and naturally survives page refreshes and browser restarts. It also avoids pretending that Python process memory is browser storage.

**Files affected:**

- `src/auth.py`
- `app.py`
- New browser auth component files/package configuration
- Potentially each page's authentication bootstrap call
- `requirements.txt` and/or frontend package metadata
- Tests and README documentation

**Estimated effort:** Medium to high, approximately 1-2 development days including mobile testing.

### 2. Add a secure cookie-backed restoration layer

**Probability of resolving the reported issue:** Very high.

As a Streamlit-focused alternative, persist an opaque, signed/encrypted session value in a secure browser cookie and restore it at startup. Refresh-token rotation must update the cookie. Logout must revoke the Supabase session and clear the cookie. Avoid plain-text token cookies and avoid shared global Python clients because multiple users share the Streamlit server process.

A robust design stores only an opaque session identifier in the browser and keeps token data in a durable server-side store. A smaller two-user implementation could use an encrypted cookie, but its replay and JavaScript-access risks must be reviewed.

**Files affected:**

- `src/auth.py`
- New `src/session_storage.py` or equivalent
- `app.py` and protected-page bootstrap
- `requirements.txt`
- Tests and README documentation

**Estimated effort:** Medium, approximately 0.5-2 development days depending on whether a durable server-side store is used.

### 3. Correct refresh-token propagation

**Probability of resolving browser-restart logouts alone:** Low. **Probability of preventing later session expiry failures:** High.

Capture the `AuthResponse` returned by `set_session()` or call a centralized refresh function, then atomically replace the access token, refresh token, and verified user data in the chosen persistent store and `st.session_state`.

This is required alongside either persistence approach above. It is not sufficient by itself because Streamlit state will still disappear on a new WebSocket connection.

**Files affected:**

- `src/auth.py`
- Authentication tests

**Estimated effort:** Small, approximately 1-3 hours after the storage design is selected.

### 4. Verify Supabase dashboard session policies

**Probability of being the primary fix:** Low.

Check time-boxed sessions, inactivity timeout, single-session enforcement, JWT expiry, and refresh-token rotation settings. Keep the normal default session lifetime unless the application has a specific security requirement to shorten it.

**Files affected:** None; Supabase dashboard configuration and optional README documentation.

**Estimated effort:** Small, approximately 15-30 minutes.

### 5. Improve password-manager compatibility as a fallback convenience

**Probability of resolving session persistence:** None. **Probability of reducing Android login friction:** Moderate.

If Android Chrome does not offer credential saving, use a login component that exposes conventional email/password inputs with explicit `autocomplete="username"` and `autocomplete="current-password"` semantics. Test Chrome, Samsung Internet if relevant, and the installed home-screen context.

This should remain a usability enhancement, not the authentication persistence mechanism.

**Files affected:**

- `app.py` or the new browser auth component
- Mobile UI tests/documentation

**Estimated effort:** Small to medium, approximately 2-6 hours depending on the component approach.

## Recommended Implementation Direction

For a durable cross-platform result, use browser-side Supabase Auth session handling (`supabase-js`) and treat Streamlit/Python as the protected application backend. Restore and refresh the browser session before protected content is rendered, validate tokens server-side, and keep all users isolated.

If minimizing implementation scope is more important for this private two-user project, an encrypted persistent-cookie bridge is the pragmatic second choice. It still needs explicit startup restoration, refresh-token replacement, logout cleanup, expiry handling, and mobile testing.

Do not use a globally cached Supabase client or a global token variable. Streamlit Cloud serves multiple users from the same Python process, so global authentication state could leak one user's identity into another user's requests.

## Proposed Verification Criteria After Remediation

1. Log in on Android Chrome and refresh the page; the user remains logged in.
2. Fully close Chrome, reopen it, and launch the saved home-screen icon; the session restores.
3. Repeat after the access-token lifetime has elapsed; refreshed tokens are persisted.
4. Navigate between all Streamlit pages without authentication errors.
5. Log out; refresh and browser restart both remain logged out.
6. Log in as both users in separate browsers and verify that identity and RLS access never cross.
7. Confirm invalid, expired, or revoked refresh tokens clear local state and return cleanly to login.
8. Confirm password saving/autofill behavior separately; do not use it as the persistence acceptance criterion.
