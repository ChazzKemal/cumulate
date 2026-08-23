"""Signing in, from inside the tool window.

One Google button. No password, no config file to edit, nothing to provision by
hand — the person opens a tool and clicks once.

Two details this has to get right:

PKCE, not the default flow. Google hands tokens back in the URL *fragment*
(#access_token=…), and a fragment never reaches the server — Streamlit would
never see it. PKCE returns a `?code=` query parameter instead, which it can.

A file-backed session store. PKCE generates a verifier before the redirect and
needs it again when the person comes back, and Streamlit re-runs this script on
every interaction. In-memory storage — the library default — loses the verifier
the moment the browser leaves. The same file keeps them signed in next time.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import streamlit as st

from paths import load_settings

load_settings()

CONFIG = Path(os.environ.get("CUMULATE_HOME", Path.home() / ".cumulate"))
SESSION_FILE = CONFIG / "session.json"


class _FileStorage:
    """What supabase-py expects for storage, backed by one small file."""

    def _read(self) -> dict:
        try:
            return json.loads(SESSION_FILE.read_text())
        except Exception:
            return {}

    def _write(self, data: dict) -> None:
        CONFIG.mkdir(parents=True, exist_ok=True)
        SESSION_FILE.write_text(json.dumps(data))
        try:
            SESSION_FILE.chmod(0o600)   # it holds a live token
        except OSError:
            pass

    def get_item(self, key: str):
        return self._read().get(key)

    def set_item(self, key: str, value: str) -> None:
        d = self._read()
        d[key] = value
        self._write(d)

    def remove_item(self, key: str) -> None:
        d = self._read()
        d.pop(key, None)
        self._write(d)


def configured() -> bool:
    return bool(os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_PUBLISHABLE_KEY"))


@st.cache_resource
def client():
    """One client for the session, so the PKCE verifier survives reruns."""
    from supabase import ClientOptions, create_client

    return create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_PUBLISHABLE_KEY"],
        options=ClientOptions(flow_type="pkce", storage=_FileStorage(),
                              persist_session=True, auto_refresh_token=True),
    )


def _redirect_to() -> str:
    # Must match a Redirect URL allowed in the Supabase dashboard, or Google
    # sends the person back to a page that refuses them.
    return os.environ.get("CUMULATE_REDIRECT", "http://localhost:8501")


def current_user() -> dict | None:
    """Who is signed in, or None. Silent on every failure — a tool must work
    whether or not anyone ever signs in."""
    if not configured():
        return None
    try:
        c = client()
        # Coming back from Google: turn the code into a session, once.
        code = st.query_params.get("code")
        if code:
            try:
                c.auth.exchange_code_for_session({"auth_code": code})
            except Exception:
                pass
            st.query_params.clear()   # don't leave the code in the address bar
        session = c.auth.get_session()
        if not session:
            return None
        user = session.user
        return {"id": user.id, "email": user.email,
                "name": (user.user_metadata or {}).get("name") or user.email}
    except Exception:
        return None


def sign_in_panel() -> dict | None:
    """Render sign-in if needed. Returns the user, or None."""
    if not configured():
        return None

    user = current_user()
    if user:
        with st.sidebar:
            st.caption(f"Signed in as {user['name']}")
            if st.button("Sign out", key="_signout"):
                try:
                    client().auth.sign_out()
                except Exception:
                    pass
                SESSION_FILE.unlink(missing_ok=True)
                st.cache_resource.clear()
                st.rerun()
        return user

    with st.sidebar:
        st.caption("Sign in to keep your work and see your past sessions.")
        try:
            res = client().auth.sign_in_with_oauth(
                {"provider": "google", "options": {"redirect_to": _redirect_to()}}
            )
            st.link_button("Sign in with Google", res.url, use_container_width=True)
        except Exception:
            st.caption("Sign-in is unavailable right now. The tool still works.")
    return None
