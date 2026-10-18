# 🧠 Project Memory

Shared notebook of the project: what has been done, what is happening now, and what comes next — and who does each thing: **Claude** (AI assistant) or **the User** (project owner).

> ### 🚀 Quick reminder
> In **PowerShell**, inside the `finance-app` folder:
> ```powershell
> .venv\Scripts\Activate.ps1          # turn on the virtual environment — "(.venv)" appears
> streamlit run dashboard.py          # open the app → http://localhost:8501  (stop: Ctrl + C)
> ```
> | Command | What it does |
> |---|---|
> | `python scripts\connect_bank.py` | Log in to the **real** bank and download the full history (first time, and every ~180 days) |
> | `python scripts\sync.py` | Download only new transactions (same as the **⟳ Refresh** button in the app) |
> | `python scripts\connect_bank.py sandbox` | Same with the **test** bank — login `user1` / `1234` / OTP `012345` |
>
> In the app, the **Real / Sandbox** switch (top right) chooses which data to show. They live in separate files and never mix.

---

## How Claude and the User work together

```
✅ Past iterations  →  🔨 Current iteration  →  📋 Pending steps
```
1. Claude writes the next iteration: what Claude will do and what the User will do.
2. The User says "OK" (or asks for changes).
3. Claude does the work, commits it, and moves it to **✅ Past iterations** as a short summary.
4. The User runs `git push`.

---

## 🗺️ The big picture

```
Bank ──► Enable Banking API (PSD2) ──► Python + SQLite on the User's PC ──► Streamlit dashboard
```
- **Enable Banking**: licensed middleman that lets the app read the User's own bank data (EU law **PSD2**).
- **SQLite**: the database is just a file in `data/`. No cloud; data never leaves the computer.
- **Streamlit + Plotly**: the web page and its charts.
- Design principles and features: see `README.md`.

| File / folder | What it is |
|---|---|
| `dashboard.py` | The app (web page) |
| `app/models.py` | Database tables: Account, Transaction, Category |
| `app/db.py`, `app/config.py` | Database connection and settings from `.env` |
| `app/importer.py` | Turns bank data into database rows, skipping duplicates |
| `app/bank/client.py` | Talks to the Enable Banking API |
| `app/bank/sync.py` | Login, sync and data report |
| `scripts/` | Commands to run from the terminal |
| `data/` 🔒 | `finance.db` (real data), `sandbox.db` (test data), bank session files |
| `secrets/` 🔒 | The `.pem` private keys |
| `.env` 🔒 | Private settings (app IDs, key paths) |

🔒 = private: ignored by Git and blocked by a local safety check. Never reaches GitHub.

---

## ✅ Past iterations

| # | Date | Summary |
|---|---|---|
| 0 | — | The User created the GitHub repo. |
| 1–3 | 18 Oct | Claude created this `MEMORY.md` and its timeline layout. |
| 4 | 18 Oct | Claude created the project structure; the User set up Python (`.venv`). |
| 5 | 18 Oct | The User registered a **sandbox** app in Enable Banking; together they downloaded test data from a test bank. *Lesson: test banks use fake public credentials, never real ones.* |
| 6 | 18 Oct | Claude built the database (accounts, transactions with unique bank ID, categories). Re-importing creates **0 duplicates**. |
| 7 | 18 Oct | Claude built the first dashboard: filters, summary cards, monthly and by-concept charts, transactions table. Dark minimal style, colors checked for color blindness. Added `PRIVACY.md` / `TERMS.md` (required by Enable Banking). |
| 7b | 18 Oct | **Security audit**: nothing private ever reached GitHub. Claude hardened `.gitignore`, added a local pre-commit safety check, and rewrote the history with the User's private GitHub email. |
| 8 | 18 Oct | **Real bank connected.** Claude built login, incremental sync, the **Sync** button and the Real/Sandbox switch (real and test data in separate files). The User logged in to the bank and the full history (~5 years) was downloaded. |
| 9 | 18 Oct | **Dashboard redesign.** Claude made the app focus on the **last 5 months**: latest movements, month cards (in / out / net / change vs previous month) and a month-in-detail view. Older data moved to *Explore all history*. **⟳ Refresh** button gets new transactions. Transfers between the User's own accounts are left out of income/spending. New `README.md` with a demo screenshot; design principles moved there. |

---

## 🔨 Current iteration

### #10 — Auto-categorization ⏳ *waiting for the User's OK*

**Goal:** every transaction gets a category (Groceries, Rent, Salary…), so the app shows *where the money goes* instead of hundreds of different concepts.

**Claude will:**
- Study the most frequent concepts and counterparties **on the User's computer** (nothing is uploaded) and propose keyword rules: e.g. "MERCADONA", "LIDL" → *Groceries*; "IBERDROLA" → *Bills & utilities*; "BIZUM" → *Bizum*.
- Keep rules in two files, for privacy:
  - `app/rules_default.py` — **generic** rules (big shops, utilities). Safe for GitHub.
  - `data/my_rules.json` 🔒 — **personal** rules (people's names, own transfers). Never uploaded.
- Apply the rules to all transactions and to every refresh.
- Dashboard: spending **by category** in the month view, and a way to change a transaction's category by hand (the manual choice always wins).
- Show how many transactions are still *uncategorized*.

**The User will:**
1. Say OK (or suggest other categories).
2. Review the proposed rules and fix anything wrong.

---

## 📋 Pending steps

- **Connect from the app** — log in to the bank from the dashboard instead of the terminal.
- **Later ideas** — monthly budgets with alerts, savings goals, export to Excel/CSV.

---

## ✅ User's to-do list

- [ ] `git push`
- [ ] Open the app and check the new design
- [ ] Review and confirm Iteration #10 (Auto-categorization)
- [ ] Remember: bank access expires in **180 days** (mid-April 2027) → run `python scripts\connect_bank.py` again
