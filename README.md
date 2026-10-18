# Finance App

> 🚧 Work in progress

A local, self-hosted personal finance dashboard that syncs bank transactions via European Open Banking (PSD2), categorizes them automatically, and tracks budgets and savings goals — no third-party subscriptions.

## Planned stack

- **Bank sync:** Enable Banking API (PSD2)
- **Storage:** SQLite + SQLModel
- **UI:** Streamlit + Plotly

## Privacy

All data stays local. Credentials live in a git-ignored `.env`; only `.env.example` is committed.
