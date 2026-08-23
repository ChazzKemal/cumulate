# Tool Builder

Engineers describe a data problem in plain language and get a working GUI tool.
Every session is captured by Entire, linked to the commit it produced.

## For the engineer

Double-click **start.command** (macOS) or **start.bat** (Windows). Type what you need.

Give it a file two ways: drop it in **inbox/**, or drag it onto the window. Finished tools land in **tools/**.

## One-time setup per machine

    cp .env.example .env      # then paste the OpenAI key into .env
    uv venv --python 3.12 && uv pip install -r requirements.txt

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
| `tools/` | Published tools, one folder each |
| `.codex/hooks.json` | Entire's 7 capture hooks |

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
