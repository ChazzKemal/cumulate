"""Tools other people built, and a way to hand yours over.

Knowledge already reaches the team: sessions upload, Harvest extracts, everyone
benefits. A working tool reached nobody. Karl builds a duty calculator and the
next person to need one builds a second, with its own assumptions, quietly
disagreeing with his — the exact split AGENTS.md tells the agent to avoid, which
it could not see because it only ever knew one person's shelf.

So a tool goes to the same store, through the sign-in they already have. No
second account, no git, no keys.

Publishing is deliberate and it is not undoable — same instinct as never
committing unless asked. Nothing here ever fires on its own; every function
below runs because somebody pressed something.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from paths import tools_dir, load_settings  # noqa: E402

load_settings()

# The launcher runs this at startup. A slow network must never be the reason
# somebody sits looking at a blank screen, so every lookup gives up quickly and
# says nothing rather than waiting.
TIMEOUT = 6.0


def _within(seconds: float, fn, *a, **kw):
    """Run fn, or give up. Returns (ok, result).

    A thread rather than signal.alarm: alarm is POSIX-only and half this team
    is on Windows. The thread is left as a daemon if it overruns — it is a read,
    so abandoning it costs nothing.
    """
    import threading

    box: dict = {}

    def run():
        try:
            box["v"] = fn(*a, **kw)
        except Exception as e:
            box["e"] = e

    t = threading.Thread(target=run, daemon=True)
    t.start()
    t.join(seconds)
    if t.is_alive() or "e" in box:
        return False, None
    return True, box.get("v")


def _account():
    """account.py imports streamlit, which the launcher does not have loaded.
    Import it late so this module is usable from a plain script too."""
    import account

    return account


def signed_in() -> dict | None:
    try:
        a = _account()
        return a.current_user() if a.configured() else None
    except Exception:
        return None


# ----------------------------------------------------------------- publishing

def preview(slug: str) -> dict | None:
    """Exactly what would be sent. Shown to the author before anything leaves.

    A tool's app.py is code, but its ASSUMPTIONS.md is domain fact and can name
    customers, rates and internal rules. Whether that should travel is the
    author's call, and they cannot make it without seeing it.
    """
    folder = tools_dir() / slug
    app = folder / "app.py"
    if not app.exists():
        return None
    assumptions = folder / "ASSUMPTIONS.md"

    src = app.read_text(errors="replace")

    def grab(fn: str) -> str:
        m = re.search(rf'st\.{fn}\(\s*(["\'])(.+?)\1', src, re.S)
        return m.group(2).strip() if m else ""

    return {
        "slug": slug,
        "name": grab("title") or slug,
        "what": grab("caption"),
        "code": src,
        "assumptions": assumptions.read_text(errors="replace") if assumptions.exists() else "",
    }


def publish(slug: str) -> tuple[bool, str]:
    """Hand this tool to the team. Adds a version; never edits what is there."""
    body = preview(slug)
    if body is None:
        return False, "That tool isn't here to publish."

    user = signed_in()
    if not user:
        return False, "Sign in first — that's how the team knows whose tool it is."

    try:
        client = _account().client()
        existing = (client.table("shared_tools")
                    .select("version")
                    .eq("engineer", user["id"]).eq("slug", slug)
                    .order("version", desc=True).limit(1).execute())
        version = (existing.data[0]["version"] + 1) if existing.data else 1

        client.table("shared_tools").insert({
            **body,
            "engineer": user["id"],
            "author_name": user["name"] or "",
            "version": version,
        }).execute()
    except Exception:
        # No traceback in front of somebody who did not ask for one.
        return False, "Couldn't send it just now. Try again in a moment."

    return True, (f"Published as version {version}. "
                  "Everyone sees it next time they start.")


# ------------------------------------------------------------------- reading

def _fetch(user: dict) -> list[dict]:
    client = _account().client()
    rows = (client.table("shared_tools_latest")
            .select("engineer, author_name, slug, name, what, assumptions, version, published_at")
            .neq("engineer", user["id"])          # your own are already on your shelf
            .order("published_at", desc=True)
            .limit(100).execute())
    return rows.data or []


def available() -> list[dict]:
    """What colleagues have published. Empty on any failure, deliberately —
    this decorates a screen, it must never be what stops one appearing."""
    user = signed_in()
    if not user:
        return []
    ok, rows = _within(TIMEOUT, _fetch, user)
    return rows if ok and rows else []


def fetch_code(engineer: str, slug: str) -> str | None:
    """The source, pulled only when somebody actually wants this one."""
    user = signed_in()
    if not user:
        return None
    try:
        r = (_account().client().table("shared_tools_latest")
             .select("code").eq("engineer", engineer).eq("slug", slug).limit(1).execute())
        return r.data[0]["code"] if r.data else None
    except Exception:
        return None


def install(row: dict) -> tuple[bool, str]:
    """Copy a colleague's tool onto this machine.

    Never overwrites. Somebody else's shipment-cost is not yours — yours has
    your corrections in it — so a clash gets a new folder, not a merge.
    """
    code = fetch_code(row["engineer"], row["slug"])
    if code is None:
        return False, "Couldn't fetch that one. Try again in a moment."

    author = (row.get("author_name") or "").split()[0].lower()
    author = re.sub(r"[^a-z0-9]", "", author)
    folder = tools_dir() / row["slug"]
    if folder.exists():
        folder = tools_dir() / f"{row['slug']}-{author or 'shared'}"
        n = 2
        while folder.exists():
            folder = tools_dir() / f"{row['slug']}-{author or 'shared'}-{n}"
            n += 1

    try:
        folder.mkdir(parents=True)
        (folder / "app.py").write_text(code)
        notes = row.get("assumptions") or ""
        # Whose it is and what it assumed, written down beside it. Six months on,
        # "where did this come from" has an answer that is not a database query.
        header = (f"# Assumptions\n\n_From {row.get('author_name') or 'a colleague'}'s "
                  f"{row.get('name') or row['slug']}, version {row.get('version', 1)}._\n\n")
        (folder / "ASSUMPTIONS.md").write_text(header + notes)
    except OSError:
        return False, "Couldn't write it to your tools folder."

    return True, f"Added as {folder.name}."


# --------------------------------------------------------------------- panel

def _team_tools(st, ttl: float = 300.0) -> list[dict]:
    """The team's shelf, remembered for a few minutes.

    Streamlit re-runs the whole script on every click, and an expander's body
    runs whether or not it is open — so without this, every button press in
    every tool would go and ask the database again. Nobody publishes often
    enough for that to buy anything.
    """
    import time

    now = time.monotonic()
    box = st.session_state.get("_shared_cache")
    if box and now - box[0] < ttl:
        return box[1]
    rows = available()
    st.session_state["_shared_cache"] = (now, rows)
    return rows


def share_panel(slug: str) -> None:
    """Hand this tool over, or take a colleague's. Call once, at the bottom.

    Streamlit is imported here rather than at the top so the launcher can run
    this module as a plain script without paying for it.
    """
    import streamlit as st

    # account.current_user() is already what the sign-in panel called this run.
    user = signed_in()

    with st.expander("Share with your team"):
        if not user:
            st.caption("Sign in to publish this tool, or to see what colleagues "
                       "have built. The tool works either way.")
            return

        body = preview(slug)
        if body:
            st.markdown("**Give this one to the team**")
            st.caption(f"They'd get *{body['name']}* — the tool itself, and what "
                       "it assumes. Read the assumptions before you send them: "
                       "rates, customer names and internal rules end up in there, "
                       "and this is the moment they leave your machine.")
            if body["assumptions"].strip():
                with st.popover("What they'd read"):
                    st.markdown(body["assumptions"])
            else:
                st.caption("_No assumptions recorded for this tool yet._")

            if st.button("Publish", key=f"_pub_{slug}", type="primary"):
                ok, msg = publish(slug)
                (st.success if ok else st.warning)(msg)
                st.session_state.pop("_shared_cache", None)

        rows = _team_tools(st)
        if rows:
            st.divider()
            st.markdown("**What your colleagues have built**")
            for r in rows:
                c1, c2 = st.columns([4, 1])
                c1.markdown(f"**{r['name']}** — {r.get('what') or 'no description'}  \n"
                            f"<small>from {r.get('author_name') or 'a colleague'}</small>",
                            unsafe_allow_html=True)
                if c2.button("Add", key=f"_get_{r['engineer']}_{r['slug']}"):
                    ok, msg = install(r)
                    (st.success if ok else st.warning)(msg)


# ------------------------------------------------------- launcher and prompt

def as_lines() -> str:
    """For a person to read, at startup."""
    rows = available()
    if not rows:
        return ""
    return "\n".join(
        f"  {r['name']} — {r.get('what') or 'no description'}"
        f"  [from {r.get('author_name') or 'a colleague'}]"
        for r in rows[:12])


def as_prompt() -> str:
    """For the agent. Same instinct as the local tools list, one shelf wider."""
    rows = available()
    if not rows:
        return ""
    bits = "; ".join(
        f"{r['slug']} by {r.get('author_name') or 'a colleague'} "
        f"({r.get('what') or r['name']})" for r in rows[:12])
    return (f"Tools colleagues have already published: {bits}. "
            "If what I want is one of these, say whose it is and offer to fetch it "
            "before building anything — their assumptions came from the same work. "
            "scaffold/shared_tools.py has install().")


if __name__ == "__main__":
    # Run outside `streamlit run`, streamlit warns on stderr about a missing
    # script context. Harmless, but it lands in the middle of the launcher
    # screen the moment anyone stops redirecting stderr. Only silenced here,
    # at the command line — never for a tool that imports this module.
    import logging

    logging.disable(logging.WARNING)
    # The whole call, not just the query. Reading who is signed in can itself
    # refresh a token over the network, so guarding only the fetch would still
    # leave the launcher hanging on a bad connection.
    ok, out = _within(TIMEOUT, as_prompt if "--prompt" in sys.argv else as_lines)
    print(out if ok and out else "")
