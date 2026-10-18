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

**Real numbers for the User's accounts:** *pending — Claude will fill this in after the first real connection (Iteration #8).*

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

---

## 🔨 Current iteration

### #8 — Real BBVA connection + Sync button 🔨 *code ready, the User's turn*

**Claude did:**
- Rebuilt the bank code (`app/bank/`): login, **incremental sync** (only new transactions, with a 7-day overlap that duplicates protection absorbs) and a data report with counts only.
- First sync uses the bank's **"longest"** mode: as much history as BBVA allows.
- Real and test data now live in **separate files**: `data/finance.db` and `data/sandbox.db`. The User's earlier test data was moved to `sandbox.db`.
- `.env` now holds both apps (sandbox + real) and `APP_MODE=real`.
- Dashboard: **Real / Sandbox** switch, **Sync** button, and "bank access valid until…" status.
- Tested with simulated bank data: 1st sync → full history; 2nd sync → 0 new, only recent days requested.

**The User will:**
1. Make sure the Production app shows **Active** in the Enable Banking Control Panel.
2. Run `python scripts\connect_bank.py`.
3. Log in with the **real** BBVA credentials (on the real BBVA page) and confirm in the BBVA app if asked.
4. Select the accounts to share and accept.
5. On the final "This site can't be reached" page, copy the **full address** and paste it into the terminal.
6. Open the app and check the data. Then tell Claude, who will read the summary file (`data/bank_report_real.json`, counts only) and complete **"What data BBVA can give us"**.

---

## 📋 Pending steps

- **Auto-categorization** — Claude writes keyword rules (e.g. "MERCADONA" → Groceries) based on the User's real concepts; the User reviews them and can fix categories by hand in the app.
- **Connect from the app** — log in to the bank from the dashboard instead of the terminal.
- **Later ideas** — monthly budgets with alerts, savings goals, export to Excel/CSV.

---

## 🎨 Design preferences

Minimalist · greys and matte tones · *minimalist cyberpunk* (dark background, one subtle accent) · fonts close to Claude.ai (`Source Serif 4` titles, `Inter` text, `JetBrains Mono` numbers).

---

## ✅ User's to-do list

- [ ] `git push`
- [ ] Run `python scripts\connect_bank.py` and connect the real BBVA (see Iteration #8)
