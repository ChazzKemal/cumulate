"""Your own sessions, in the window you already have open.

Two questions, and they are the ones people actually ask about their own work:
what did I do, and where did it go wrong.

Reads the local capture. Conversations never leave the machine they happened on
— only the extracted knowledge is shared — so this is the one place they can be
read, and it works with no account and no network.
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime

import streamlit as st

from paths import WORKSPACE, harvest_dir, harvest_out


def _load(name: str) -> list[dict]:
    f = harvest_out() / name
    if not f.exists():
        return []
    rows = []
    for line in f.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def _chats() -> list[dict]:
    d = harvest_out() / "chats"
    if not d.exists():
        return []
    out = []
    for f in sorted(d.glob("*.json")):
        try:
            out.append(json.loads(f.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    out.sort(key=lambda c: c.get("started_at") or "", reverse=True)
    return out


def _when(stamp: str) -> str:
    try:
        return datetime.fromisoformat(stamp).strftime("%d %b, %H:%M")
    except (ValueError, TypeError):
        return stamp[:16] if stamp else "unknown"


def _harvest_python():
    for rel in ("bin/python", "Scripts/python.exe"):
        p = harvest_dir() / ".venv" / rel
        if p.exists():
            return p
    return None


def _pending() -> dict | None:
    """What hasn't reached the shared store yet. None when sharing is off."""
    py = _harvest_python()
    if py is None:
        return None
    try:
        out = subprocess.run(
            [str(py), "-c",
             "import json,sys;sys.path.insert(0,'.');"
             "from harvest import upload;"
             f"print(json.dumps(upload.pending({WORKSPACE.name!r})))"],
            cwd=str(harvest_dir()), capture_output=True, text=True, timeout=20)
        return json.loads(out.stdout.strip().splitlines()[-1])
    except Exception:
        return None


def _send_now() -> tuple[bool, str]:
    py = _harvest_python()
    if py is None:
        return False, "Sharing isn't set up on this machine."
    try:
        r = subprocess.run([str(py), "-m", "harvest", "upload", "--repo", str(WORKSPACE)],
                           cwd=str(harvest_dir()), capture_output=True, text=True, timeout=180)
        line = (r.stdout.strip().splitlines() or ["Done."])[-1]
        return r.returncode == 0, line
    except subprocess.TimeoutExpired:
        return False, "That took too long. It'll finish on its own in the background."
    except Exception:
        return False, "Couldn't send just now. It will retry by itself."


def _share_section() -> None:
    """Uploading happens by itself after every session. This is for catching up
    — after working offline, or when someone wants to see it has actually gone."""
    p = _pending()
    if p is None:
        return
    waiting = {k: v for k, v in p.items() if v}
    st.divider()
    if waiting:
        bits = ", ".join(f"{v} {k}" for k, v in waiting.items())
        st.caption(f"Waiting to be shared: {bits}")
    else:
        st.caption("Everything you've done has been shared.")
    if st.button("Send everything now", key="_send_now",
                 disabled=not waiting, use_container_width=True):
        with st.spinner("Sending…"):
            ok, msg = _send_now()
        (st.success if ok else st.warning)(msg)
        st.rerun()


def my_sessions_panel() -> None:
    """Render the panel. Safe to call whether or not anything is captured."""
    chats, stuck = _chats(), _load("corrections.jsonl")
    if not chats and not stuck:
        return

    with st.expander("My sessions"):
        got_stuck, talked = st.tabs(["Where I got stuck", "What I said"])

        with got_stuck:
            if not stuck:
                st.caption("Nothing yet. This fills in as you correct the assistant — "
                           "every time you put it right, it gets written down here.")
            for r in reversed(stuck):
                st.markdown(f"**{r.get('tool') or 'general'}** · {r.get('date','')}")
                st.markdown(f"- it assumed — {r.get('agent_assumed','')}")
                st.markdown(f"- you said — **{r.get('person_said','')}**")
                st.divider()

        _share_section()

        with talked:
            if not chats:
                st.caption("No conversations kept yet.")
            for c in chats[:20]:
                turns = c.get("turns", [])
                asked = [t for t in turns if t.get("role") == "user"]
                if not asked:
                    continue
                title = asked[0].get("text", "").strip().split("\n")[0][:70]
                with st.expander(f"{_when(c.get('started_at',''))} — {title}"):
                    for t in turns:
                        role = t.get("role")
                        if role == "user":
                            st.markdown(f"**You:** {t.get('text','')}")
                        elif role == "assistant":
                            st.markdown(t.get("text", ""))
                        # Tool calls and reasoning are deliberately not shown —
                        # this view is the conversation, not the machinery.
