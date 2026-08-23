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
