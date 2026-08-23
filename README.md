# Tool Builder

Engineers describe a data problem in plain language and get a working GUI tool.
Every session is captured by Entire, linked to the commit it produced.

## For the engineer

Double-click **start.command** (macOS) or **start.bat** (Windows). Type what you need.

Give it a file two ways: drop it in **inbox/**, or drag it onto the window. Finished tools land in **tools/**.

## Signing in

One Google button, in the tool's own window. Nobody edits a config file and
nobody gets provisioned by hand — they open a tool, click once, and that is the
whole setup. The session is cached in `~/.cumulate/session.json`, so it asks
once and not again.

Set up once, by you, in the Supabase dashboard:

1. Authentication → Providers → enable Google, paste in a Google OAuth client id
   and secret.
2. Authentication → URL Configuration → add `http://localhost:8501` to the
   allowed redirect URLs (or whatever `CUMULATE_REDIRECT` is set to).

Signing in is optional everywhere. With no Supabase configured, every tool still
runs, the feature box still records what people ask for, and "My sessions" still
works — it reads the local capture. Sign-in adds the shared store, nothing else.

## My sessions

Every tool carries a **My sessions** panel: what you said, and where you got
stuck. Conversations never leave the machine they happened on — only the
extracted knowledge is shared — so this panel is the only place to read them,
and it needs no account and no network.

## What already exists

    .venv/bin/python scaffold/tools_index.py

Prints every tool, what it does, and how many assumptions it records — read straight
from each `app.py`, no model involved. The launcher shows this before anything starts,
and hands the same list to the agent so it offers to extend an existing tool instead
of quietly building a second one.

## Work you already did

Cumulate only knows what has happened since it was installed. Everything before
that — the spreadsheet someone has maintained for six years, the script a leaver
wrote, the report rebuilt by hand every month — walks in the door invisible.

    projects/
      monthly-freight-recon/
        Freight Recon 2023.xlsx
        notes.txt

One folder per thing, files exactly as they are. A `notes.txt` whose first line
says what it was for, if you have thirty seconds; nothing if you don't.

    .venv/bin/python scaffold/projects_index.py

The launcher prints this alongside the tools list and hands it to the agent, so
when you ask for something you have done before it offers to read the old one
instead of guessing at rules somebody already worked out.

What it reads them *for* is the rules, which are rarely where you'd expect:

- A script's hardcoded values. `DE_MINIMIS = 135` is a threshold with a reason
  behind it, and the reason is not in the file.
- A workbook's formulas. `formulas()` collapses five thousand copies of one
  formula into the single rule they all are — the thing pandas throws away when
  it reads the numbers.

Each one becomes a line in `ASSUMPTIONS.md` you can confirm or correct. Nothing
in `projects/` is ever edited, moved or rewritten — it is a record, not a working
copy.

**These files never leave the machine.** `projects/` is git-ignored, same as
`inbox/`, for the same reason. What reaches the team is what gets written down.

## One-time setup per machine

None. Double-click **start.command** (macOS) or **start.bat** (Windows) and it
installs what it needs, opens the browser for a Google sign-in, and starts.

It brings in the runner, the workspace's tools, the assistant, and Entire —
Homebrew or `entire.io/install.sh` on macOS, Scoop on Windows, per their docs.
If the recorder can't be installed it carries on without it: a missing recorder
must never stop someone getting their work done.

Codex will ask once whether to trust this folder. Click yes.

## What's here

| Path | What it is |
|---|---|
| `AGENTS.md` | The elicitation protocol — how the agent interviews, when it asks why |
| `ASSUMPTIONS.md` | The ledger. Agent writes, engineer corrects. This is the knowledge record |
| `scaffold/ingest.py` | One way in for any file type — `profile`, `load`, `describe` |
| `scaffold/readers/` | One module per file type. Add a module, get a new type |
| `scaffold/app_template.py` | Streamlit shell every tool starts from |
| `inbox/` | Engineers drop files here (git-ignored) |
| `projects/` | Work from before this existed — old spreadsheets, scripts (git-ignored) |
| `tools/` | Published tools, one folder each |
| `.codex/hooks.json` | Entire's 7 capture hooks |

## Automatic extraction

When a session ends, `hooks/on_session_end.py` fires and runs Harvest in the
background. It returns in ~30ms, so nobody waits. Output goes to `.harvest.log`,
summaries to `../Harvest/out/`.

    .venv/bin/python scaffold/install_hooks.py   # idempotent; re-run after `entire enable --force`

The trigger is `hooks/on_session_end.py` rather than a shell script, so it fires
on Windows too — the old `sh -c` version simply never ran there, which meant
nothing was captured at all.

If a session is killed hard and `SessionEnd` never fires, nothing is lost — Harvest
is incremental, so the next session's run picks up whatever was missed.

## Putting it on a team

Every engineer runs their own copy — the transcripts only exist on the machine
where the session happened, so capture cannot be centralised. What gets pooled
is what Harvest extracts.

Per machine: double-click the launcher and sign in with Google. That is the
whole setup. No keys to paste, no files to edit, nothing to provision.

Capturing and uploading are free and automatic. Summarising costs money and
runs in one place — yours:

    cd ../Harvest && .venv/bin/python -m harvest extract

That reads everyone's uploaded sessions on your key and writes the claims back
attributed to whoever did the work. Nobody else ever needs a key for it.

## Reading the captured knowledge

    entire session list              # sessions
    entire checkpoint list           # checkpoints, linked to commits
    entire checkpoint explain <id>   # full transcript for one
    entire search "why do we exclude returns"
    entire why <file> <line>         # why a line of code exists
    entire recap                     # summary of recent work

`entire why` and `entire search` are the two that matter for the knowledge goal.

## Where the data lives

Git refs in this repo (`--checkpoint-backend refs`). Not on Entire's servers.
Never pushed unless you add a remote. Delete the repo and it's gone.
