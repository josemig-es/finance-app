# 🧠 Project Memory

This file is our shared notebook. It explains **what we are building, what we've done, what we're doing now, and what comes next**.

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

---

## 🔨 Current iteration

### Iteration #4 — Project skeleton ⏳ *waiting for your OK to start*

**Goal:** Prepare a clean, organized folder so everything has its place.

**What Claude will do:**
- Create this folder structure:
  ```
  finance-app/
  ├── app/
  │   ├── models.py      ← database tables
  │   ├── db.py          ← connection to the SQLite file
  │   ├── categorize.py  ← auto-categorization rules
  │   └── bank/          ← Enable Banking code
  ├── scripts/
  │   └── seed_fake_data.py  ← creates fake transactions
  ├── dashboard.py       ← the Streamlit app
  ├── data/              ← where the .db file lives (ignored by Git)
  ├── secrets/           ← where your .pem key lives (ignored by Git)
  ├── requirements.txt   ← list of Python libraries we need
  └── .env.example       ← template for your private settings (no real values)
  ```
- Add `data/`, `secrets/` and `.venv/` to `.gitignore`, so private files can **never** be uploaded to GitHub by accident.

**Why:** a clear structure makes it easy to find things later. Separating "secrets" and "data" from code is what keeps your repo safe to be public.

**What you will do:**
- Create a **virtual environment** (an isolated box for this project's Python libraries) and install them. Claude will give you the exact commands.
- Note: your computer has Python 3.10. That works, but we may suggest upgrading to 3.12 later.

---

## 📋 Pending steps

### Database model
**Goal:** Decide what information we save and how.

**What Claude will do:** create three tables:

| Table | What it stores | Example |
|---|---|---|
| `Account` | Your bank accounts | "BBVA Cuenta Online" |
| `Category` | Spending groups | "Groceries", "Rent", "Salary" |
| `Transaction` | Each money movement | 2026-10-12, Mercadona, -45.30 €, Groceries |

The most important detail: every transaction has a **unique ID from the bank**. The database will refuse to save the same ID twice. This is how we **avoid duplicates** when we sync again and again.

**Why:** getting the tables right early saves a lot of pain later. Everything else (charts, budgets) reads from here.

**What you will do:** review the table list. Do you want extra info? (e.g. notes, tags, "is this a fixed expense?")

### Fake data
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

## ✅ Your to-do list

- [ ] Confirm Iteration #4 (Project skeleton)
- [ ] (Optional, anytime) Start the Enable Banking registration — see "Real bank connection"
