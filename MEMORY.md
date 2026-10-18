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
> | `python scripts\connect_bank.py` | Log in to the **real** BBVA and download the full history (first time, and every ~180 days) |
> | `python scripts\sync.py` | Download only new transactions (same as the **Sync** button in the app) |
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
BBVA ──► Enable Banking API (PSD2) ──► Python + SQLite on the User's PC ──► Streamlit dashboard
```
- **Enable Banking**: licensed middleman that lets the app read the User's own bank data (EU law **PSD2**).
- **SQLite**: the database is just a file in `data/`. No cloud; data never leaves the computer.
- **Streamlit + Plotly**: the web page and its charts.

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

## 🏦 What data BBVA can give us

**Per account:** IBAN, product name ("CUENTA ORDINARIA BBVA"), description ("CUENTA PARA AHORROS"), currency, holder name, and current **balance**.

**Per transaction:**

| Field | Example | Use in the app |
|---|---|---|
| Unique ID (`entry_reference`) | 2100000006…354159 | Avoids duplicates |
| Booking date / value date | 2026-06-08 / 2026-06-04 | Filters, monthly charts |
| Amount + direction | 45.30 € · `DBIT` (out) / `CRDT` (in) | Totals (+ in / − out) |
| Concept (`remittance_information`) | "MERCADONA VALENCIA", "RECIBO" | Auto-categories |
| Counterparty name + account | "Iberdrola" · ES12… | Who paid / who got paid |
| Status | `BOOK` done / `PDNG` pending | Only finished ones are saved |
| Others (often empty) | merchant category code, balance after transaction, notes | Saved in the raw record, just in case |

**How much history:** Enable Banking says most banks give **at least 1 year**, many **2–3 years or more**.
⚠️ The full history is only available during **about 1 hour after logging in**; after that, the bank only gives the **last 90 days**. That's why `connect_bank.py` downloads everything right after the login, and why we keep it all in our own database.

**Limits:**
- Bank access lasts up to **180 days**; then the User logs in again (`connect_bank.py`).
- Automatic syncs: usually **max 4 per day**.
- Only **one active login** per user: a new login replaces the previous one.
- PSD2 covers **payment accounts** (current/savings). Credit cards, loans or investments may not appear.

**Real numbers for the User's accounts** (first connection, 18 Oct 2026 — counts only):

| Account | Transactions | History from |
|---|---|---|
| CUENTA ONLINE | 2,977 | Dec 2021 |
| CUENTA METAS | 125 | Oct 2023 |
| **Total** | **3,102** | **~5 years** |

- **Direction:** 2,482 money out · 620 money in.
- **Per year:** 2022: 466 · 2023: 873 · 2024: 626 · 2025: 620 · 2026 (so far): 495.
- **Always filled (100 %):** unique ID, dates, amount, direction, status, concept. The concept is one line of ~84 characters, with **891 different concepts**: good material for auto-categories.
- **Usually filled:** counterparty name (98 %), own account (85 %).
- **Sometimes filled:** counterparty account (22–28 %), bank transaction code (27 %, e.g. transfers / standing orders).
- **Never filled:** merchant category code, balance after each transaction. Categories will have to come from our own rules.

---

## ✅ Past iterations

| # | Date | Summary |
|---|---|---|
| 0 | — | The User created the GitHub repo. |
| 1–3 | 18 Oct | Claude created this `MEMORY.md` and its timeline layout. |
| 4 | 18 Oct | Claude created the project structure; the User set up Python (`.venv`). |
| 5 | 18 Oct | The User registered a **sandbox** app in Enable Banking; together they downloaded test data from the BBVA test bank. *Lesson: test banks use fake public credentials, never real ones.* |
| 6 | 18 Oct | Claude built the database (accounts, transactions with unique bank ID, categories). Re-importing creates **0 duplicates**. |
| 7 | 18 Oct | Claude built the first dashboard: filters, summary cards, monthly and by-concept charts, transactions table. Dark minimal style, colors checked for color blindness. Added `PRIVACY.md` / `TERMS.md` (required by Enable Banking). |
| 7b | 18 Oct | **Security audit**: nothing private ever reached GitHub. Claude hardened `.gitignore`, added a local pre-commit safety check, and rewrote the history with the User's private GitHub email. |
| 8 | 18 Oct | **Real BBVA connected.** Claude built login, incremental sync, the **Sync** button and the Real/Sandbox switch (real and test data in separate files). The User logged in to BBVA: **3,102 transactions, ~5 years** downloaded. |

---

## 🔨 Current iteration

### #9 — Auto-categorization ⏳ *waiting for the User's OK*

**Goal:** every transaction gets a category (Groceries, Rent, Salary…) automatically, so the charts show *where the money goes* instead of 891 different concepts.

**Claude will:**
- Look at the most frequent concepts and counterparties **on the User's computer** (nothing is uploaded) and propose keyword rules, e.g. "MERCADONA", "LIDL" → *Groceries*; "IBERDROLA" → *Bills & utilities*.
- Split rules in two files, for privacy:
  - `app/rules_default.py` — **generic** rules (big shops, utilities). Safe to publish on GitHub.
  - `data/my_rules.json` 🔒 — **personal** rules (people's names, the User's own transfers). Never uploaded.
- Apply the rules to all existing transactions and to every new sync.
- Dashboard: **"By category"** chart instead of "By concept", a category filter, and a way to change a transaction's category by hand (the manual choice always wins over the rules).
- Show what percentage of transactions are still *uncategorized*, so rules can be improved.

**The User will:**
1. Say OK (or suggest changes, e.g. other categories).
2. Review the list of proposed rules and fix anything wrong.

---

 copy the **full address** and paste it into the terminal.
6. Open the app and check the data. Then tell Claude, who will read the summary file (`data/bank_report_real.json`, counts only) and complete **"What data BBVA can give us"**.

---

## 📋 Pending steps

- **Connect from the app** — log in to the bank from the dashboard instead of the terminal.
- **Later ideas** — monthly budgets with alerts, savings goals, export to Excel/CSV.

---

## 🎨 Design preferences

Minimalist · greys and matte tones · *minimalist cyberpunk* (dark background, one subtle accent) · fonts close to Claude.ai (`Source Serif 4` titles, `Inter` text, `JetBrains Mono` numbers).

---

## ✅ User's to-do list

- [ ] `git push`
- [ ] Review and confirm Iteration #9 (Auto-categorization)
- [ ] Remember: bank access expires in **180 days** (mid-April 2027) → run `python scripts\connect_bank.py` again
