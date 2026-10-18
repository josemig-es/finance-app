# 🧠 Project Memory

This is the shared notebook of the project. It records **what has been done, what is happening now, and what comes next**, and who does each thing: **Claude** (the AI assistant) or **the User** (the project owner).

> ### 🚀 Quick reminder: open the app
> In **PowerShell**, inside the `finance-app` folder:
> ```powershell
> .venv\Scripts\Activate.ps1      # turns on the virtual environment — "(.venv)" appears
> streamlit run dashboard.py      # opens the app at http://localhost:8501
> ```
> To stop the app: **Ctrl + C** in the terminal.
>
> Other useful commands:
> - `python scripts\explore_sandbox.py` — downloads test data from the BBVA test bank (login: `user1` / `1234` / OTP `012345`)
> - `python scripts\load_sandbox.py` — loads that test data into the database

---

## How Claude and the User work together

The file reads like a timeline, from top (past) to bottom (future):

```
✅ Past iterations    →   🔨 Current iteration   →   📋 Pending steps
   (done, summarized)      (what's happening now)     (ideas not confirmed yet)
```

1. Claude writes the next iteration in plain English: what Claude will do and what the User will do.
2. The User reads it and says "OK" (or asks for changes).
3. Claude does the work, commits it, and moves the iteration to **✅ Past iterations** with a short summary.
4. The User pushes the commit to GitHub (`git push`).

**Words used here**
- **Step** = a part of the plan that is still pending.
- **Iteration** = one round of work, with a number (#1, #2, #3…), so anyone can say *"in Iteration 5 we changed X"*.

---

## 🗺️ The big picture

The app is a chain of pieces that pass data along:

```
BBVA bank ──► Enable Banking API ──► Python + SQLite (the "engine") ──► Streamlit dashboard
```

- **Enable Banking** is a licensed middleman. A European law called **PSD2** makes banks let people read their own data, and Enable Banking offers one clean way to ask BBVA for it.
- **SQLite** is a database that lives in **one file** (`data/finance.db`) on the User's computer. No server, no cloud: the data never leaves the machine.
- **SQLModel** lets the database tables be written as normal Python classes.
- **Streamlit** turns a Python script into a web page with buttons and charts. **Plotly** draws the charts.

**Safety rule:** private things (`.env`, the `.pem` keys in `secrets/`, everything in `data/`) are ignored by Git and never reach GitHub.

---

## ✅ Past iterations

### Iteration #0 — Repo setup
- Before working with Claude, the User created the GitHub repo with `README.md` and `.gitignore`.

### Iterations #1–#3 — This memory file (2026-10-18)
- Claude created `MEMORY.md` with the plan, then added numbered iterations and the timeline layout at the User's request.

### Iteration #4 — Project skeleton (2026-10-18)
- Claude created the folder structure: `app/` (engine code), `scripts/`, `data/`, `secrets/` and `dashboard.py`, plus `requirements.txt` (libraries) and `.env.example` (settings template without real values).
- Claude made `.gitignore` also ignore `.venv/` and everything inside `data/` and `secrets/`.
- The User created the virtual environment, installed the libraries and checked that the app opens.

### Iteration #5 — Explore the Enable Banking sandbox (2026-10-18)
- The User registered a **sandbox** (test) app in Enable Banking and saved its `.pem` key in `secrets/`.
- Claude created `.env` (the User's private settings) and wrote `scripts/explore_sandbox.py`, which signs requests with the key, opens the bank login and downloads the data.
- The User logged in to the **BBVA test bank** and downloaded 7 test accounts and 239 transactions into `data/sandbox_sample.json`.
- **Lesson learned:** test banks use fake public credentials, never real ones. From now on, Claude always gives the User all the test data needed *before* he runs something.

**What BBVA provides** (useful fields only):

| For each… | Field | Example | Notes |
|---|---|---|---|
| Account | IBAN | ES84 0182 … | |
| Account | Product / description | "CUENTA ORDINARIA BBVA", "CUENTA PARA AHORROS" | |
| Account | Balance | 7,251.29 € | |
| Transaction | `entry_reference` | 2100000006…354159 | **Unique ID** → protection against duplicates |
| Transaction | Booking date / value date | 2026-06-08 / 2026-06-04 | |
| Transaction | Amount + currency | 313.34 EUR | Always positive… |
| Transaction | Direction | `CRDT` (money in) / `DBIT` (money out) | …so this gives the sign |
| Transaction | Concept | "ALQUILER", "COMPRA", "RECIBO" | Main input for auto-categories |
| Transaction | Who paid / who got paid | "Miguel", "David" | |
| Transaction | Status | `BOOK` (done) / `PDNG` (pending) | |

Sandbox data is fake and a bit odd: all transactions are money **in** and the concepts are generic words. Real BBVA data will have money out and real merchant names.

### Iteration #6 — Database model (2026-10-18)
- Claude wrote the three tables in `app/models.py`:
  - **Account** — IBAN, product, description, currency, balance.
  - **Transaction** — bank's unique ID, dates, **signed amount** (+ money in, − money out), concept, counterparty, status, category, the User's note, and the **original bank record** saved untouched (so no field is ever lost).
  - **Category** — 12 default categories (Groceries, Rent & home, Salary, Transfers…).
- Claude wrote `app/db.py` (connects to `data/finance.db` and creates the tables) and `app/importer.py` (turns bank data into database rows; the future "Sync" button will reuse it).
- Claude wrote `scripts/load_sandbox.py` and tested it: 7 accounts and 239 transactions loaded. **Running it a second time saved 0 new transactions**, which proves the duplicate protection works.
- For now, only finished (`BOOK`) transactions are saved, because pending ones can still change.
- The fake-data step was dropped: the sandbox gives enough test data.

### Iteration #7 — Basic dashboard (2026-10-18)
- Claude built the first dashboard in `dashboard.py`, reading the sandbox data from the database:
  - **Filters** in one row: period and accounts.
  - **Summary cards:** money in, money out and net for the period.
  - **Month by month** chart (money in vs. money out) and **By concept** chart (top 8 concepts).
  - **Transactions** table, newest first.
- First version of the User's style: dark background, matte greys, `Source Serif 4` for titles (close to Claude.ai), `Inter` for text, `JetBrains Mono` for numbers. Theme colors live in `.streamlit/config.toml`.
- Chart colors: **teal = money in**, **violet = money out**. Claude checked them with a color-blindness validator; they always come with a legend or labels.
- Claude tested the page and checked a screenshot before delivering it.
- While registering the Production app, Enable Banking asked for privacy and terms links, so Claude added `PRIVACY.md` and `TERMS.md` to the repo.
- The User did: load the sandbox data (`python scripts\load_sandbox.py`), open the app and give feedback on the look.

---

### Iteration #7b — Security audit (2026-10-18)
- Claude checked every file in the repo and the **whole Git history**: no `.env`, no `.pem` keys, no database and no bank data were ever committed. No private key, Application ID or real IBAN appears in any commit.
- Claude extended `.gitignore` to also ignore other key formats (`.key`, `.p12`, `.pfx`), variants like `.env.local`, `.streamlit/secrets.toml`, and exports of personal data (`.csv`, `.xlsx`).
- Claude added a **local safety net** (a Git *pre-commit hook*): if a commit ever includes a key, `.env`, a database or anything inside `data/` or `secrets/`, Git refuses it. It lives only on the User's computer (in `.git/hooks/`), not on GitHub.
- **Good to know:** the email address used to sign each commit is visible on GitHub. The User switched to GitHub's private "noreply" email, Claude set it for this repo and **rewrote the whole history** so every commit uses it. The User published the cleaned history with `git push --force`.

---

## 🔨 Current iteration

### Iteration #8 — Real BBVA connection and "Sync" button ⏳ *waiting for the User's Production app*

**Goal:** replace the test data with the User's real BBVA transactions.

**Claude will:**
- Move the bank code into `app/bank/` so both the script and the dashboard can use it.
- Add a **"Sync" button** to the dashboard. It asks the bank only for transactions newer than the last one saved (an *incremental* sync), saves them with the duplicate protection from Iteration #6, and refreshes the charts.
- Add a **"Connect bank"** flow for when the permission expires (every ~90–180 days).
- Keep the sandbox and the real data **separate** (different database files), so test data never mixes with real money.

**The User will:**
1. Finish the Production app registration (see the steps in the chat).
2. Tell Claude the app is **Active**. Claude will then add the new Application ID and key path to `.env`.
3. Log in to the real BBVA once, when the app asks.

---

## 📋 Pending steps

### Auto-categorization
- **Claude will** write simple **keyword rules**: e.g. if the concept contains "MERCADONA" or "LIDL" → *Groceries*. Rules will be easy to edit, and the User will be able to fix a category by hand from the dashboard.
- **The User will** review the rules and add his usual shops. Best done once real BBVA data is in, since sandbox concepts are generic.

### Later ideas (not planned yet)
- Monthly budgets per category with alerts
- Savings goals with a progress bar
- Export to Excel/CSV

---

## 🎨 Design preferences

- **Minimalist.** Few elements, lots of space.
- **Colors:** greys and matte tones. A *minimalist cyberpunk* feel: dark background, one subtle accent color.
- **Font:** similar to the one in the Claude.ai interface. That exact font isn't free, so Claude will pick a free look-alike.

---

## ✅ User's to-do list

- [ ] `git push` the latest commits (needed for the Privacy/Terms links)
- [ ] Run `python scripts\load_sandbox.py`, open the app and tell Claude what to change
- [ ] Finish the **Production** app in Enable Banking and link the real BBVA accounts
