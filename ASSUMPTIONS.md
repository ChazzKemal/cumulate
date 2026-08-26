# Assumptions

What the tool takes for granted. Written by the agent, corrected by you.
If a line here is wrong, say so — that correction is the point.

<!-- The agent appends here. Format:

## <tool name> — <date>
- [confirmed] Rows where `qty` is negative are returns and are included.
- [corrected] "Status = 3" means cancelled, not on-hold.  ← was wrong, fixed
- [open] Unclear whether the report should exclude internal transfers.

**Why it matters:** <the reason, when they gave one>
**Breaks when:** <their answer to "what would break this">
-->

## projects/ — previous work archive — 2026-08-23

- [open] "Previous projects" means work made before Cumulate existed or outside it —
  old spreadsheets, and also scripts and code people wrote themselves.
- [open] The files stay on the machine they are on. `projects/` is gitignored like
  `inbox/`; what reaches the team is the knowledge written into this ledger, not the
  data. Same split the rest of Cumulate already uses.
- [open] One folder per project, files left exactly as they are — not tidied, renamed
  or converted. A hardcoded number in the wrong place is a rule somebody decided.
- [open] A `notes.txt` is optional. Its first line is taken as the description.
- [open] The agent never edits anything in `projects/`. It reads, and builds the new
  thing in `tools/`.
- [open] A single loose file dropped into `projects/` counts as a project on its own,
  because people will do that.
- [open] The rules worth recovering are the hardcoded constants in scripts and the
  distinct formulas in workbooks — not the structure of either.

**Why it matters:** Cumulate accumulates forward from install day. Everything before
that is knowledge nobody wrote down, held in files that are still in use.

**Breaks when:** _(not yet asked)_

## shared tools — 2026-08-24

- [open] A tool worth having is worth the whole team having. Right now knowledge
  reaches everyone and a working tool reaches nobody.
- [open] Sharing goes through the Google sign-in that already exists. No GitHub
  account, no git, no keys — adding a second account would undo the one-click setup.
- [open] `shared_tools` is the one table in the store readable by everyone. Safe
  because a row is something a person MADE and published on purpose, not a record
  OF them — unlike sessions, chats and corrections.
- [open] Publishing is deliberate and never automatic, same rule as committing.
  It sends the tool and its assumptions, which can name rates and customers, so
  the author sees exactly what will go before it goes.
- [open] Publishing is append-only. A fix is a new version; old ones stay readable
  so "what did it assume when I used it in March" has an answer.
- [open] Fetching never overwrites a tool of the same name. Someone else's
  shipment-cost is not yours — yours has your corrections in it.
- [open] Someone else's assumptions are not automatically true for you. The agent
  reads them with you line by line rather than adopting them.
- [open] Author names travel with a tool; email addresses do not.

**Why it matters:** Two people solving the same problem twice, with rules that
quietly disagree, is the exact split the agent is told to avoid — and until now
it could only ever see one person's shelf.

**Breaks when:** _(not yet asked)_
