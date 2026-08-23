# Previous projects

Work you did before this existed, or somewhere else. Old spreadsheets, the
report someone rebuilds by hand every month, a script a leaver wrote, a folder
of queries nobody has touched in two years.

Put each one in its own folder in here. Exactly as it is — do not tidy it,
rename it, or strip anything out. The mess is often the point: a hardcoded
number in the wrong place is a rule somebody decided once.

    projects/
      monthly-freight-recon/
        Freight Recon 2023.xlsx
        notes.txt
      duty-calculator/
        duty.py
        rates.csv

Add a `notes.txt` if you have thirty seconds. First line is what it was for.
Anything after that is free text — what it got wrong, who used it, why it
stopped being used.

    Reconciles the carrier invoice against what we shipped.
    Breaks whenever a carrier changes their reference format.
    Karl kept a manual list of exceptions in column P.

No notes is fine too. The files alone are worth having here.

## What happens to them

Nothing, unless you ask. Nothing runs, nothing is rewritten, nothing is
uploaded. The assistant is told what is in here so that when you ask for
something it already sees whether you have done it before — and can read the
old one instead of guessing from scratch.

**These files stay on this machine.** This folder is git-ignored, same as
`inbox/`. What gets shared with the team is what gets written down in
`ASSUMPTIONS.md` — the rules, not the data.
