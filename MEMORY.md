# 🧠 Project Memory

This file is our shared notebook. It explains **what we are building, what we've done, what we're doing now, and what comes next**.

> ### 🚀 Quick reminder: open the app
> In **PowerShell**, inside the `finance-app` folder:
> ```powershell
> .venv\Scripts\Activate.ps1      # turn on the virtual environment — you'll see (.venv)
> streamlit run dashboard.py      # opens the app at http://localhost:8501
> ```
> To stop the app: press **Ctrl + C** in the terminal.
> Explore the bank sandbox again: `python scripts\explore_sandbox.py` (BBVA test login: `user1` / `1234` / OTP `012345`).

## How we work together

The file reads like a timeline, from top (past) to bottom (future):

```
✅ Past iterations    →   🔨 Current iteration   →   📋 Pending steps
   (done, summarized)      (what we're on now)        (waiting for your OK)
```

1. **Claude** writes the next steps in **📋 Pending steps**, in plain English.
2. **You** read them and say "OK" (or ask for changes).
3. The confirmed step moves up to **🔨 Current iteration** and Claude does the work.
4. When it's finished, it moves up to **✅ Past iterations** as a short summary: what we did and what changed.

**Words we use**
- **Step** = a part of the plan that is still pending (e.g. "Basic dashboard").
- **Iteration** = one round of work, with a number (#1, #2, #3…). One step can take several iterations (build it, then adjust it…). So we can always say *"in Iteration 5 we changed X"*.

---

## 🗺️ The big picture

The app has three pieces that pass data along, like a chain:

```
BBVA bank ──► Enable Banking API ──► Python + SQLite (our "engine") ──► Streamlit dashboard
```

- **Enable Banking** is a licensed middleman. Banks in Europe must let you read your own data (a law called **PSD2**), and Enable Banking gives us a single, clean way to ask BBVA for it.
- **SQLite** is a database that lives in **one file** on your computer. No server, no cloud. Your data never leaves your machine.
- **SQLModel** is a Python library that lets us describe database tables as normal Python classes. It's easier to read than raw SQL.
- **Streamlit** turns a Python script into a web page with buttons and charts. **Plotly** draws the charts.

**Key idea:** we build the app with **fake data first** and connect the real bank **last**. That way we can build and test everything without waiting for bank approvals, and without touching your real money data while we experiment.

---

## ✅ Past iterations

### Iteration #0 — Repo setup
- **Before working with Claude.** Repo created on GitHub with `README.md` and `.gitignore`.

### Iteration #1 — Memory file created (2026-10-18)
- Created this `MEMORY.md` with the big picture and a 6-step plan.

### Iteration #2 — Iterations numbering (2026-10-18)
- Added numbered iterations so we can refer to them later.

### Iteration #3 — Timeline layout (2026-10-18)
- Reorganized this file as a timeline: past iterations → current iteration → pending steps.

### Iteration #4 — Project skeleton (2026-10-18)
- Created the folder structure: `app/` (engine code), `scripts/`, `data/`, `secrets/`, plus `dashboard.py`.
- The Python files are **placeholders** for now: each one says which step will fill it.
- `requirements.txt` lists the libraries we need: SQLModel (database), Streamlit + Plotly + pandas (dashboard), python-dotenv, requests and PyJWT (bank connection).
- `.env.example` is a template for your private settings, with no real values.
- `.gitignore` now also ignores `.venv/`, and **everything inside `data/` and `secrets/`**. The empty folders stay in Git thanks to a tiny `.gitkeep` file.
- **You:** set up your Python environment (see "🛠️ How to run the project" below).

### Iteration #5 — Explore the Enable Banking sandbox (2026-10-18)
- Registered the sandbox app (you), created `.env` and `scripts/explore_sandbox.py` (Claude).
- Connected to the **BBVA test bank** (user `user1` / `1234` / OTP `012345`) and downloaded 7 test accounts, 239 transactions (Jun–Sep 2026) into `data/sandbox_sample.json` (stays on your computer, ignored by Git).
- **Lesson learned:** test banks use fake public credentials — never your real ones. Claude will always give you all needed test data *before* you run something.

**What BBVA gives us** (useful fields only):

| For each… | Field | Example | Notes |
|---|---|---|---|
| Account | IBAN | ES84 0182 … | |
| Account | Product / description | "CUENTA ORDINARIA BBVA", "CUENTA PARA AHORROS" | |
| Account | Balance | 7,251.29 € | |
| Transaction | `entry_reference` | 2100000006…354159 | **Unique ID** → our duplicate protection |
| Transaction | Booking date / value date | 2026-06-08 / 2026-06-04 | |
| Transaction | Amount + currency | 313.34 EUR | Always positive… |
| Transaction | Direction | `CRDT` (money in) / `DBIT` (money out) | …so this tells us the sign |
| Transaction | Concept | "ALQUILER", "COMPRA", "RECIBO" | Main input for auto-categories |
| Transaction | Who paid / who got paid | "Miguel", "David" | |
| Transaction | Status | `BOOK` (done) / `PDNG` (pending) | |

**Things to keep in mind:**
- Sandbox data is fake and a bit odd: *all* 239 transactions are money **in**, and concepts are generic words. Real BBVA data will have money out and real merchant names (e.g. "MERCADONA").
- Fields like `transaction_id`, merchant category or balance-after-transaction came **empty**. Your real bank may fill some of them.

---

## 🔨 Current iteration

### Iteration #6 — Database model ⏳ *waiting for your OK*

**Goal:** Save accounts and transactions in our SQLite file, using what we learned in Iteration #5.

**Claude's proposal:**

**`Account` table** — one row per bank account
- IBAN, product name, description, currency
- Current balance and when we last updated it

**`Transaction` table** — one row per money movement
- `entry_reference` — the bank's unique ID. **The database refuses duplicates**, so syncing many times is safe.
- Account it belongs to
- Booking date and value date
- **Signed amount**: positive = money in, negative = money out (we calculate it from `CRDT`/`DBIT`). This makes totals easy: just add everything up.
- Concept (e.g. "ALQUILER") and counterparty (who paid / who got paid)
- Status (done / pending)
- **Category** — added by us (filled in the Auto-categorization step)
- **Note** — your own free text, optional
- **Raw data** — the original bank record, saved untouched, so if later you want a field we skipped today, we still have it

**`Category` table** — the list of categories (Groceries, Rent, Salary…)

**What Claude will do:** write `app/models.py` and `app/db.py`, plus a small script that loads `data/sandbox_sample.json` into the database, so we can check that everything fits.

**What you will do:** say OK, or tell Claude what to add/remove.

---

## 📋 Pending steps

### Fake data *(maybe not needed — the sandbox may give us enough test data)*
**Goal:** Have realistic data to play with, without using your real bank.

**What Claude will do:** a small script that fills the database with ~6 months of invented transactions (salary, rent, supermarket, Netflix, restaurants…).

**Why:** we can build and test the dashboard right away. If something breaks, nothing real is lost — we just delete the file and run the script again.

**What you will do:** run the script with one command and check the database file appears in `data/`.

### Basic dashboard
**Goal:** See your money on screen.

**What Claude will do:** a first Streamlit page with:
- A **date filter** (this month, last 3 months, custom…)
- **Summary cards**: total income, total spending, balance
- **Spending by category** (pie or bar chart)
- **Month by month** evolution (line chart)
- A **table** with all transactions

**What you will do:** run `streamlit run dashboard.py`, open it in your browser and tell Claude what you like and what you would change.

### Auto-categorization
**Goal:** Transactions get their category automatically.

**What Claude will do:** simple **rules based on keywords** in the transaction text. Example: if the text contains "MERCADONA" or "LIDL" → *Groceries*. Rules will be easy to edit, and you'll be able to fix a category by hand from the dashboard.

**Why:** rules are simple, predictable and you understand exactly why each transaction got its category. We can make it smarter later.

**What you will do:** review the rules and add your own usual shops/merchants.

### Real bank connection (Enable Banking + BBVA)
**Goal:** Replace fake data with your real transactions.

**What Claude will do:**
- Code the **login flow**: the app opens a BBVA page in your browser, you approve access, and the app gets a permission that lasts ~90–180 days.
- Code the **"Sync" button**: it checks the date of the last saved transaction and asks the bank **only for newer ones** (this is called a *delta* or *incremental* sync). Then it categorizes them and refreshes the charts.

**What you will do (you can start this now, in parallel!):**
1. Create an account at [enablebanking.com](https://enablebanking.com) (Control Panel).
2. Register a new **application**. You'll get an **Application ID** and a **private key (.pem file)**.
3. Save the `.pem` file inside `secrets/` and the ID in your `.env` file. **Never share these or upload them to GitHub.**
4. Tell Claude when it's ready — Claude will **never** need to see the content of your key.

### Later ideas (not planned yet)
- Monthly budgets per category with alerts
- Savings goals with a progress bar
- Export to Excel/CSV

---

## 🎨 Design preferences

- **Minimalist.** Few elements, lots of space.
- **Colors:** greys and matte tones. A *minimalist cyberpunk* feel (dark background, one subtle accent color).
- **Font:** similar to the one in the Claude.ai interface. That exact font isn't free, so we'll pick a free look-alike.
- To be polished later; for now we just keep it in mind.

---

## 🛠️ How to run the project

Open **PowerShell** in the `finance-app` folder and run these once:

```powershell
py -m venv .venv                 # 1. create the virtual environment (the "isolated box")
.venv\Scripts\Activate.ps1       # 2. turn it on — you'll see (.venv) at the start of the line
pip install -r requirements.txt  # 3. install the libraries
copy .env.example .env           # 4. create your private settings file
streamlit run dashboard.py       # 5. open the app in your browser
```

Next times you only need steps 2 and 5.

> If step 2 gives a "running scripts is disabled" error, run this once:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`
>
> If `py` is not found, install Python 3.12 from python.org (tick "Add Python to PATH").

---

## ✅ Your to-do list

- [x] Push Iterations #1–#4 to GitHub
- [x] Set up your Python environment and check the app opens
- [x] Register the Enable Banking sandbox app and save the `.pem` in `secrets/`
- [x] Run `scripts\explore_sandbox.py` and get the sandbox data
- [ ] Review and confirm Iteration #6 (Database model)
