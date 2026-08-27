"""First run: sign in, get set up, close the tab.

The key has to exist before the assistant starts, which is before any tool
window exists — so this is its own small page, opened by the launcher. A browser
page is also the right surface for someone who has never used a terminal.

Nothing here asks for a key. The person signs in with Google and one is issued
to them, so there is no account to create at OpenAI and nothing to paste.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

import account  # noqa: E402
from paths import WORKSPACE, load_settings  # noqa: E402

load_settings()

ENV = WORKSPACE / ".env"

st.set_page_config(page_title="Welcome", page_icon="👋")


def _has_key(text: str) -> bool:
    """An actual assignment, not the commented example the template ships."""
    return bool(re.search(r"^\s*OPENAI_API_KEY=", text, re.M))


def _save_key(key: str) -> None:
    """Write the key without disturbing anything already in .env."""
    lines = []
    if ENV.exists():
        lines = [l for l in ENV.read_text().splitlines()
                 if not l.startswith("OPENAI_API_KEY=")]
    lines.append(f"OPENAI_API_KEY={key}")
    ENV.write_text("\n".join(lines) + "\n")
    try:
        ENV.chmod(0o600)
    except OSError:
        pass


def _issue_key(user) -> str | None:
    """Ask the endpoint for this person's key.

    The person's own sign-in token is what authorises it, so the endpoint knows
    who is asking and can meter or revoke per person. Nothing shared, nothing
    baked into the app.
    """
    endpoint = os.environ.get("CUMULATE_KEY_ENDPOINT")
    if not endpoint:
        return None
    import httpx

    session = account.client().auth.get_session()
    r = httpx.post(endpoint, headers={"Authorization": f"Bearer {session.access_token}"},
                   timeout=30)
    r.raise_for_status()
    return r.json().get("key")


st.title("Welcome")

# Sign-in comes first, always. Checking for a key first was wrong: anyone who
# already had one — every existing user — would be told "all set" and never get
# an account, so their work could never reach the shared store.
if not account.configured():
    st.warning("This copy isn't connected to an account system yet.")
    st.caption("Whoever set this up needs to finish connecting it.")
    st.stop()

user = account.current_user()
if not user:
    st.write("Sign in once, and everything else is done for you.")
    try:
        res = account.client().auth.sign_in_with_oauth(
            {"provider": "google",
             "options": {"redirect_to": os.environ.get("CUMULATE_REDIRECT",
                                                       "http://localhost:8501")}}
        )
        st.link_button("Sign in with Google", res.url, type="primary")
    except Exception:
        st.error("Sign-in isn't available right now. Try again in a moment.")
    st.stop()

st.write(f"Hello {user['name'].split()[0] if user['name'] else 'there'}.")

# Signed in and already holding a key: nothing left to do.
if os.environ.get("OPENAI_API_KEY") or (ENV.exists() and _has_key(ENV.read_text())):
    st.success("You're all set. Close this tab and you're away.")
    st.stop()

with st.spinner("Setting up your account…"):
    try:
        key = _issue_key(user)
    except Exception:
        key = None

if key:
    _save_key(key)
    st.success("Done. Close this tab and you're away.")
else:
    st.error("Couldn't finish setting up your account.")
    st.caption("Tell whoever set this up for you — nothing is wrong on your end.")
