"""The 'ask for a feature' box every tool carries.

Harvest already infers what people wanted by reading their sessions. This is the
other kind: someone typing a request on purpose. Rarer, much higher intent, and
it catches the ask that never became a session because they gave up before
opening the tool builder. Stored with `deliberate = true` so the two stay
distinguishable.

Degrades quietly. No Supabase configured, no network, bad credentials — the
request lands in the local knowledge store instead and the tool carries on. A
tool must never break because the database is having a day.
"""
from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path

import streamlit as st

from paths import harvest_out, load_settings

load_settings()


def _save(tool: str, text: str) -> str:
    row = {
        "ask": text,
        "tool": tool,
        "deliberate": True,
        "asked_on": date.today().isoformat(),
    }

    try:
        import account

        user = account.current_user()
        if user:
            account.client().table("asks").insert(
                {**row, "engineer": user["id"]}
            ).execute()
            return "sent"
    except Exception:
        pass  # fall through to local; the request is never lost

    try:
        local = harvest_out() / "asks.jsonl"
        local.parent.mkdir(parents=True, exist_ok=True)
        with local.open("a") as f:
            f.write(json.dumps(row) + "\n")
        return "saved"
    except Exception:
        return "failed"


def feature_box(tool: str) -> None:
    """Render the box. Call once, at the bottom of a tool."""
    with st.expander("Ask for something"):
        st.caption(
            "Something this tool should do and doesn't? Say it here — it reaches "
            "the person who builds these."
        )
        text = st.text_area(
            "What would you like it to do?", key=f"ask_{tool}", label_visibility="collapsed"
        )
        if st.button("Send", key=f"ask_send_{tool}"):
            if not text.strip():
                st.warning("Write what you need first.")
                return
            result = _save(tool, text.strip())
            if result == "failed":
                st.error("Couldn't save that. Tell someone directly.")
            else:
                st.success("Got it. Thanks.")
