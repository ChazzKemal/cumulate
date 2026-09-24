# Getting started, step by step

Two roles. The **admin** (you) sets up the backend once and approves each
engineer's email. The **engineer** double-clicks two files and signs in with
Google — no terminal, no keys to paste.

Works on **64-bit Windows 10 (fully updated) or 11**, and **macOS**. Everything
installs per-user; no admin rights are needed on the engineer's machine, and
nothing needs to be installed on it first. The installer checks the machine
and says plainly if it is too old.

No engineer ever holds your OpenAI key. It lives only on the gateway; each
person is given their own gateway key, with its own budget, that works nowhere
else and can be revoked on its own.

---

## Admin: one-time backend setup

All of this happens in the [Supabase dashboard](https://supabase.com/dashboard)
for your project (the one `config.env` points at).

1. **Create the tables.** SQL Editor → paste the entire contents of
   `supabase/schema.sql` from the Harvest repo → Run. It is idempotent — safe
   to re-run, never deletes data.
2. **Enable Google sign-in.** Authentication → Providers → Google → paste a
   Google OAuth client id and secret (from Google Cloud Console, with the
   Supabase callback URL). Authentication → URL Configuration → add
   `http://localhost:8501` to the allowed redirect URLs.
3. **Set up the gateway and the key-issuing function.** Follow
   `gateway/README.md` in the Harvest repo (about 15 minutes, free, nothing to
   host). It sets up the gateway, a Cloudflare Worker and the only place your
   OpenAI key goes, deploys `issue-key`, and ends with two lines in this
   repo's `config.env` (`CUMULATE_GATEWAY`, `CUMULATE_MODEL`).

4. **The installer to send out.** For Windows there is nothing to build:
   send `install-cumulate.cmd` from the cumulate repo as it is (it always
   fetches the latest installer), or have the engineer paste this into
   PowerShell:

       irm https://raw.githubusercontent.com/ChazzKemal/cumulate/master/install.ps1 | iex

   For macOS, from the cumulate repo in any Unix shell:

       ./make-installer.sh <token> you/cumulate you/harvest            # macOS installer

   (The token is only needed if the repos are private; the Windows installer
   can be token-baked the same way with `windows` on the end.)

## Admin: adding an engineer

One step per person. SQL Editor:

    insert into allowed_emails (email) values ('engineer@company.com');

(Lowercase — the table enforces it.) Then send them the installer file.
Sign-in is open to anyone with a Google account, but the key — and therefore
anything that costs money — is only issued to emails in this table. Everyone
else gets a 403 and spends nothing.

To remove someone later: delete their row from `allowed_emails`. Their key
stops working within 30 seconds. Budgets and spend per person are a few lines
of SQL, given in `gateway/README.md` in the Harvest repo.

---

## Engineer: install and sign in

### Windows

1. **Double-click `install-cumulate.cmd`** (the file the admin sent). It
   installs both repos under `%LOCALAPPDATA%\Cumulate`, creates the
   `%USERPROFILE%\Cumulate` workspace, and opens it in Explorer. Per-user
   only; no admin prompt will ever appear. Nothing needs installing first —
   if the machine has no Git, it fetches a private copy.
   If Windows warns about a file from the internet, choose **Run** (or
   **More info → Run anyway**).
2. **Double-click `Start.cmd`** in that workspace. First run sets everything
   up (a few minutes): Python venvs, Codex, the Entire session recorder.
3. **A browser page opens — click "Sign in with Google"** and pick the
   approved account. The page says you're all set; your personal key is
   written into the workspace `.env` automatically. Nothing to copy or paste.
4. Back in the window, **Codex asks once whether to trust this folder and its
   hooks — press `y`/`t` to accept.** Then it greets you; type what you need.

### macOS

Identical flow: double-click the installer the admin sent, then
**start.command** in the `~/Cumulate` workspace, sign in with Google in the
browser, trust the folder once.

### Every launch after the first

Just double-click **Start.cmd** / **start.command**. Sign-in is remembered
(`~/.cumulate/session.json`), setup is skipped, and both repos `git pull`
first — so pushing to the repos is how the admin ships updates; engineers get
them automatically on next launch.

---

## Admin: seeing what engineers did

Every session is captured automatically on the engineer's machine and uploaded
to the shared store (row-level security: engineers read only their own rows;
you read everything).

On your machine, in the Harvest folder:

1. Put your OpenAI key and the Supabase secret key in Harvest's `.env`.
2. **Summarise everyone's uploaded sessions** (runs on your key only):

       python -m harvest extract --dry-run   # see what it would cost
       python -m harvest extract             # do it

3. **Double-click `admin.cmd`** (Windows) / `admin.command` (macOS). It builds
   and opens `out/admin.html`: every session with the full conversation and
   diff, where people got stuck, what they asked for, and the extracted
   claims — filterable by person, tool and project.

`admin.cmd` reads the secret key and bypasses every access policy — never
share the file or its output.

Engineers have their own view: `view.cmd` / `view.command` in the Harvest
folder shows their own local sessions and knowledge. It needs no account.

---

## If something goes wrong

- **Sign-in page never opens / "no key" loop** — check the email is in
  `allowed_emails` (exact address, lowercase), that `issue-key` is deployed,
  and that `CUMULATE_GATEWAY` in `config.env` is the gateway's address.
- **Codex says "This key is not valid any more"** — they were removed from
  `allowed_emails`. Once they are approved again, starting Cumulate again
  issues a new key.
- **Codex says the budget is used up** — raise it (`gateway/README.md`).
- **Session recording missing** — startup continues without it by design.
  Re-run `Start.cmd`; the bootstrap retries the Entire install (Scoop or a
  direct download on Windows, Homebrew/install.sh on macOS).
- **`view.cmd` says "Not set up yet"** — start Cumulate once first; it
  provisions Harvest too.
