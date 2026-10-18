# 🧠 Project Memory

This is the shared notebook of the project. It records **what has been done, what is happening now, and what comes next**, and who does each thing: **Claude** (the AI assistant) or **José** (the user).

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

## How Claude and José work together

The file reads like a timeline, from top (past) to bottom (future):

```
✅ Past iterations    →   🔨 Current iteration   →   📋 Pending steps
   (done, summarized)      (what's happening now)     (ideas not confirmed yet)
```

1. Claude writes the next iteration in plain English: what Claude will do and what José will do.
2. José reads it and says "OK" (or asks for changes).
3. Claude does the work, commits it, and moves the iteration to **✅ Past iterations** with a short summary.
4. José pushes the commit to GitHub (`git push`).

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
- **SQLite** is a database that lives in **one file** (`data/finance.db`) on José's computer. No server, no cloud: the data never leaves the machine.
- **SQLModel** lets the database tables be written as normal Python classes.
- **Streamlit** turns a Python script into a web page with buttons and charts. **Plotly** draws the charts.

**Safety rule:** private things (`.env`, the `.pem` keys in `secrets/`, everything in `data/`) are ignored by Git and never reach GitHub.

---

## ✅ Past iterations

### Iteration #0 — Repo setup
- Before working with Claude, José created the GitHub repo with `README.md` and `.gitignore`.

### Iterations #1–#3 — This memory file (2026-10-18)
- Claude created `MEMORY.md` with the plan, then added numbered iterations and the timeline layout at José's request.

### Iteration #4 — Project skeleton (2026-10-18)
- Claude created the folder structure: `app/` (engine code), `scripts/`, `data/`, `secrets/` and `dashboard.py`, plus `requirements.txt` (libraries) and `.env.example` (settings template without real values).
- Claude made `.gitignore` also ignore `.venv/` and everything inside `data/` and `secrets/`.
- José created the virtual environment, installed the libraries and checked that the app opens.

### Iteration #5 — Explore the Enable Banking sandbox (2026-10-18)
- José registered a **sandbox** (test) app in Enable Banking and saved its `.pem` key in `secrets/`.
- Claude created `.env` (José's private settings) and wrote `scripts/explore_sandbox.py`, which signs requests with the key, opens the bank login and downloads the data.
- José logged in to the **BBVA test bank** and downloaded 7 test accounts and 239 transactions into `data/sandbox_sample.json`.
- **Lesson learned:** test banks use fake public credentials, never real ones. From now on, Claude always gives José all the test data needed *before* he runs something.

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
  - **Transaction** — bank's unique ID, dates, **signed amount** (+ money in, − money out), concept, counterparty, status, category, José's note, and the **original bank record** saved untouched (so no field is ever lost).
  - **Category** — 12 default categories (Groceries, Rent & home, Salary, Transfers…).
- Claude wrote `app/db.py` (connects to `data/finance.db` and creates the tables) and `app/importer.py` (turns bank data into database rows; the future "Sync" button will reuse it).
- Claude wrote `scripts/load_sandbox.py` and tested it: 7 accounts and 239 transactions loaded. **Running it a second time saved 0 new transactions**, which proves the duplicate protection works.
- For now, only finished (`BOOK`) transactions are saved, because pending ones can still change.
- The fake-data step was dropped: the sandbox gives enough test data.

---

## 🔨 Current iteration

### Iteration #7 — Basic dashboard ⏳ *waiting for José's OK*

**Goal:** see the money on screen for the first time, using the sandbox data in the database.

**Claude will:**
- Build a first page in `dashboard.py` with:
  - **Filters:** date range and account.
  - **Summary cards:** money in, money out, balance of the period.
  - **Month by month** chart (money in vs. money out).
  - **Spending by concept** chart (later it will be by category).
  - **Table** with all transactions.
- Apply a first version of José's style (see 🎨 Design preferences): dark, minimal, greys and matte tones, one subtle accent color.

**José will:**
1. Run `python scripts\load_sandbox.py` once, to create `data/finance.db` on his computer.
2. Open the app (see 🚀 Quick reminder) and tell Claude what he likes and what he would change.

**In parallel, José will prepare the real BBVA connection** (it can take some time, so it's good to start now):
1. In the Enable Banking Control Panel, register a **new application**, this time choosing **Production**.
   - Name: `finance-app-prod`
   - Allowed redirect URL: `https://localhost:8501/`
   - Key: "Generate in the browser", same as before.
2. Save the new `.pem` file in `secrets/`. It will have a different name than the sandbox one; both can live there.
3. In the list of applications, click **"Activate by linking accounts"** on the new app.
4. He will be sent to the **real BBVA login**: here he uses his **real** BBVA credentials (this is the real bank, not the test one). BBVA may ask him to confirm in the BBVA mobile app.
5. Select the accounts he wants the app to read and accept. The app status should change to **Active** (restricted mode: free, and it can only read the accounts he linked).
6. Tell Claude when it's done. Claude never needs to see the content of the key.

---

## 📋 Pending steps

### Auto-categorization
- **Claude will** write simple **keyword rules**: e.g. if the concept contains "MERCADONA" or "LIDL" → *Groceries*. Rules will be easy to edit, and José will be able to fix a category by hand from the dashboard.
- **José will** review the rules and add his usual shops. Best done once real BBVA data is in, since sandbox concepts are generic.

### Real bank connection and "Sync" button
- **Claude will** connect the app to the Production app: login flow from the dashboard, and a **"Sync" button** that asks the bank only for transactions newer than the last one saved (an *incremental* or *delta* sync), categorizes them and refreshes the charts.
- **José will** log in to BBVA when asked. The permission lasts about 90–180 days; after that, he logs in again.

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

## ✅ José's to-do list

- [ ] `git push` the latest commits
- [ ] Review and confirm Iteration #7 (Basic dashboard)
- [ ] Register the **Production** app in Enable Banking and link the real BBVA accounts (see Iteration #7)
