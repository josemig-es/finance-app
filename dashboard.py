"""Finance App dashboard. Run with:  streamlit run dashboard.py"""
import html
import json
from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.bank.sync import session_valid_until, sync
from app.config import DEFAULT_MODE
from app.db import get_engine

# ---------- Look & feel ----------
IN_COLOR = "#38a596"    # money in  (matte teal)
OUT_COLOR = "#a77ac0"   # money out (matte violet)
TEXT, MUTED, GRID, SURFACE = "#d9d9d6", "#8b8d92", "#26282c", "#1c1d20"
MONTHS_SHOWN = 5

st.set_page_config(page_title="Finance App", page_icon="◐", layout="wide")
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&family=Source+Serif+4:opsz,wght@8..60,400;8..60,500&display=swap');
    html, body, [class*="css"], .stMarkdown, .stDataFrame, button, input { font-family: 'Inter', sans-serif; }
    h1, h2, h3 { font-family: 'Source Serif 4', Georgia, serif !important; font-weight: 400 !important; letter-spacing: -0.01em; }
    .block-container { padding-top: 2.5rem; max-width: 1200px; }
    #MainMenu, footer, header [data-testid="stToolbar"] { visibility: hidden; }
    .stMultiSelect [data-tag] { background: #2a2c30 !important; color: #d9d9d6 !important; }
    .subtle { color: #8b8d92; font-size: 0.85rem; margin: 0; }
    .label { color: #8b8d92; font-size: 0.7rem; letter-spacing: 0.12em; text-transform: uppercase; }
    .mono { font-family: 'JetBrains Mono', monospace; }
    .dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; margin-right: 7px; vertical-align: middle; }
    .card { background: #1c1d20; border: 1px solid #26282c; border-radius: 6px; padding: 16px 18px; height: 100%; }
    .card.current { border-color: #38a59666; }
    .card .big { font-family: 'JetBrains Mono', monospace; font-size: 1.35rem; color: #d9d9d6; margin: 6px 0 10px; }
    .card .row { display: flex; justify-content: space-between; font-size: 0.8rem; color: #8b8d92; margin-top: 3px; }
    .card .row span:last-child { font-family: 'JetBrains Mono', monospace; color: #d9d9d6; }
    .card .delta { font-size: 0.75rem; color: #8b8d92; margin-top: 10px; border-top: 1px solid #26282c; padding-top: 8px; }
    .feed { background: #1c1d20; border: 1px solid #26282c; border-radius: 6px; padding: 4px 18px; }
    .feed .item { display: grid; grid-template-columns: 64px 1fr auto; gap: 14px; align-items: center;
                  padding: 11px 0; border-bottom: 1px solid #26282c; }
    .feed .item:last-child { border-bottom: none; }
    .feed .d { color: #8b8d92; font-size: 0.78rem; }
    .feed .t { color: #d9d9d6; font-size: 0.9rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .feed .s { color: #8b8d92; font-size: 0.75rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .feed .a { font-family: 'JetBrains Mono', monospace; color: #d9d9d6; font-size: 0.9rem; text-align: right; }
    .feed .main { min-width: 0; }
    div[data-testid="stExpander"] details { border-color: #26282c; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- Helpers ----------
def euros(x: float, signed: bool = False) -> str:
    s = f"{abs(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    sign = "−" if x < 0 else ("+" if signed and x > 0 else "")
    return f"{sign}{s} €"


def style_fig(fig: go.Figure, height: int = 300) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=8, r=8, t=8, b=8),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=MUTED, size=12),
        legend=dict(orientation="h", y=1.1, x=0, font=dict(color=TEXT)),
        hoverlabel=dict(bgcolor=SURFACE, bordercolor=GRID, font=dict(color=TEXT, family="JetBrains Mono")),
        bargap=0.35, bargroupgap=0.08,
    )
    fig.update_xaxes(showgrid=False, linecolor=GRID, tickcolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, ticksuffix=" €")
    return fig


def in_out_by_month(data: pd.DataFrame) -> pd.DataFrame:
    return (data.assign(inflow=data["amount"].clip(lower=0), outflow=-data["amount"].clip(upper=0))
            .groupby("month")[["inflow", "outflow"]].sum())


def in_out_chart(monthly: pd.DataFrame, height: int = 300) -> go.Figure:
    fig = go.Figure()
    fig.add_bar(x=monthly.index, y=monthly["inflow"], name="Money in", marker_color=IN_COLOR,
                hovertemplate="%{x|%b %Y}<br>In: %{y:,.2f} €<extra></extra>")
    fig.add_bar(x=monthly.index, y=monthly["outflow"], name="Money out", marker_color=OUT_COLOR,
                hovertemplate="%{x|%b %Y}<br>Out: %{y:,.2f} €<extra></extra>")
    fig.update_traces(marker_line_width=0, marker_cornerradius=4)
    fig.update_xaxes(dtick="M1", tickformat="%b %Y")
    return style_fig(fig, height)


def top_chart(data: pd.DataFrame, money_out: bool, n: int = 8) -> go.Figure | None:
    sel = data[data["amount"] < 0] if money_out else data[data["amount"] > 0]
    if sel.empty:
        return None
    by = sel.groupby("label")["amount"].sum().abs().sort_values().tail(n)
    names = [x if len(x) <= 28 else x[:27] + "…" for x in by.index]
    fig = go.Figure(go.Bar(
        x=by.values, y=names, orientation="h", marker_color=OUT_COLOR if money_out else IN_COLOR,
        marker_line_width=0, marker_cornerradius=4, cliponaxis=False,
        text=[euros(v) for v in by.values], textposition="outside", textfont=dict(color=MUTED),
        customdata=by.index, hovertemplate="%{customdata}: %{x:,.2f} €<extra></extra>",
    ))
    fig = style_fig(fig, height=max(220, 34 * len(by) + 30))
    fig.update_xaxes(showticklabels=False, showgrid=False, range=[0, by.max() * 1.4])
    fig.update_yaxes(gridcolor="rgba(0,0,0,0)", ticksuffix="  ", tickfont=dict(color=TEXT))
    return fig


def transactions_table(data: pd.DataFrame, height: int = 380):
    table = data.sort_values("booking_date", ascending=False)[["booking_date", "label", "amount", "concept", "account"]]
    st.dataframe(
        table, hide_index=True, width="stretch", height=height,
        column_config={
            "booking_date": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
            "label": "Description", "concept": "Bank concept", "account": "Account",
            "amount": st.column_config.NumberColumn("Amount", format="%.2f €"),
        },
    )


# ---------- Data ----------
def _other_account(raw) -> str | None:
    r = json.loads(raw) if isinstance(raw, str) else (raw or {})
    side = (r.get("debtor_account") if r.get("credit_debit_indicator") == "CRDT" else r.get("creditor_account")) or {}
    return side.get("iban") or (side.get("other") or {}).get("identification")


@st.cache_data(ttl=60)
def load_data(mode: str) -> pd.DataFrame:
    df = pd.read_sql(
        'SELECT t.booking_date, t.amount, t.concept, t.counterparty, t.raw, '
        'a.identifier, a.product, a.description '
        'FROM "transaction" t JOIN account a ON a.id = t.account_id',
        get_engine(mode),
    )
    if df.empty:
        return df
    df["booking_date"] = pd.to_datetime(df["booking_date"])
    df["month"] = df["booking_date"].dt.to_period("M").dt.to_timestamp()
    df["account"] = (df["description"].fillna(df["product"]).fillna("Account")
                     + " ··" + df["identifier"].str[-4:])
    df["concept"] = df["concept"].fillna("")
    df["label"] = df["counterparty"].where(df["counterparty"].fillna("").str.strip() != "", df["concept"])
    df["label"] = df["label"].replace("", "(no description)")
    # Transfers between the User's own accounts are not real income/spending.
    own = set(df["identifier"])
    other = df["raw"].map(_other_account)
    df["internal"] = other.isin(own) & (other != df["identifier"])
    return df.drop(columns=["raw"])


# ---------- Header: title, data source, refresh ----------
h1, h2, h3 = st.columns([3, 1.4, 1], vertical_alignment="bottom")
h1.markdown("# Finance")
with h2:
    mode = st.segmented_control("Data", ["real", "sandbox"], default=DEFAULT_MODE,
                                format_func=str.capitalize, label_visibility="collapsed") or DEFAULT_MODE
until = session_valid_until(mode)
with h3:
    if st.button("⟳  Refresh", disabled=until is None, width="stretch",
                 help="Download the latest transactions from the bank" if until else "Connect the bank first"):
        lines = []
        try:
            with st.spinner("Getting the latest transactions from the bank..."):
                sync(mode, log=lines.append)
            st.cache_data.clear()
            new = sum(int(l.split("new:")[1].split()[0]) for l in lines if "new:" in l)
            st.toast(f"Up to date ✓ — {new} new transaction{'s' if new != 1 else ''}")
        except Exception as e:  # friendly message instead of a crash
            st.error(str(e))

df_all = load_data(mode)
last_tx = df_all["booking_date"].max() if not df_all.empty else None
status = (f"Bank access valid until {until:%d %b %Y}" if until
          else "Bank not connected — run `python scripts\\connect_bank.py" + (" sandbox" if mode == "sandbox" else "") + "`")
if last_tx is not None:
    status += f"  ·  latest transaction {last_tx:%d %b %Y}"
st.markdown(f'<p class="subtle">{"● " if until else "○ "}{status}</p>', unsafe_allow_html=True)

if df_all.empty:
    st.info("No transactions yet. Connect the bank with:  `python scripts\\connect_bank.py"
            + (" sandbox" if mode == "sandbox" else "") + "`")
    st.stop()

df = df_all[~df_all["internal"]]  # real income/spending only
this_month = pd.Timestamp(date.today().replace(day=1))
months = pd.date_range(end=this_month, periods=MONTHS_SHOWN, freq="MS")
recent = df[df["month"].isin(months)]

# ---------- Latest movements ----------
st.write("")
left, right = st.columns([2, 3], gap="large")
with left:
    st.markdown("### Latest movements")
    items = []
    for _, r in df_all.sort_values("booking_date", ascending=False).head(8).iterrows():
        color = IN_COLOR if r["amount"] > 0 else OUT_COLOR
        sub = r["concept"] if r["concept"] and r["concept"] != r["label"] else r["account"]
        if r["internal"]:
            sub = "Transfer between my accounts"
        items.append(
            f'<div class="item"><div class="d">{r["booking_date"]:%d %b}</div>'
            f'<div class="main"><div class="t">{html.escape(str(r["label"]))}</div>'
            f'<div class="s">{html.escape(str(sub))}</div></div>'
            f'<div class="a"><span class="dot" style="background:{color}"></span>{euros(r["amount"], signed=True)}</div></div>'
        )
    st.markdown(f'<div class="feed">{"".join(items)}</div>', unsafe_allow_html=True)

with right:
    st.markdown(f"### Last {MONTHS_SHOWN} months")
    monthly = in_out_by_month(recent).reindex(months, fill_value=0)
    st.plotly_chart(in_out_chart(monthly, height=470), width="stretch", config={"displayModeBar": False})

# ---------- Month by month cards ----------
st.write("")
cols = st.columns(MONTHS_SHOWN)
prev_out = None
full = in_out_by_month(df)
for col, m in zip(cols, months):
    inflow, outflow = monthly.loc[m, "inflow"], monthly.loc[m, "outflow"]
    before = full["outflow"].get(m - pd.offsets.MonthBegin(1))
    if before:
        change = (outflow - before) / before * 100
        delta = f"Spending {'▲' if change > 0 else '▼'} {abs(change):.0f}% vs {(m - pd.offsets.MonthBegin(1)):%b}"
    else:
        delta = "—"
    current = m == this_month
    col.markdown(
        f'<div class="card{" current" if current else ""}">'
        f'<div class="label">{m:%b %Y}{" · so far" if current else ""}</div>'
        f'<div class="big">{euros(inflow - outflow, signed=True)}</div>'
        f'<div class="row"><span><span class="dot" style="background:{IN_COLOR}"></span>In</span><span>{euros(inflow)}</span></div>'
        f'<div class="row"><span><span class="dot" style="background:{OUT_COLOR}"></span>Out</span><span>{euros(-outflow)}</span></div>'
        f'<div class="delta">{delta}</div></div>',
        unsafe_allow_html=True,
    )

# ---------- One month in detail ----------
st.write("")
st.markdown("### Month in detail")
labels = {f"{m:%b %Y}": m for m in months}
picked = st.segmented_control("Month", list(labels), default=list(labels)[-1],
                              label_visibility="collapsed") or list(labels)[-1]
month_df = df[df["month"] == labels[picked]]
d1, d2 = st.columns([2, 3], gap="large")
with d1:
    has_out = (month_df["amount"] < 0).any()
    direction = st.radio("Show", ["Where the money went", "Where it came from"], index=0 if has_out else 1,
                         horizontal=True, label_visibility="collapsed", key="dir_month")
    fig = top_chart(month_df, money_out=direction.startswith("Where the money"))
    if fig is None:
        st.markdown('<p class="subtle">Nothing here this month.</p>', unsafe_allow_html=True)
    else:
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
with d2:
    st.markdown(f'<p class="subtle">{len(month_df)} transactions in {picked}</p>', unsafe_allow_html=True)
    transactions_table(month_df, height=320)

# ---------- Full history (optional) ----------
st.write("")
with st.expander("Explore all history"):
    first, last = df_all["booking_date"].min().date(), df_all["booking_date"].max().date()
    f1, f2, f3 = st.columns([1.2, 2, 1])
    with f1:
        period = st.date_input("Period", value=(first, last), min_value=first, max_value=last, format="DD/MM/YYYY")
    with f2:
        accounts = sorted(df_all["account"].unique())
        chosen = st.multiselect("Accounts", accounts, default=accounts, placeholder="All accounts")
    with f3:
        st.write("")
        include_internal = st.toggle("Include transfers between my accounts", value=False)
    start, end = (period if isinstance(period, tuple) and len(period) == 2 else (first, last))
    base = df_all if include_internal else df
    view = base[base["booking_date"].dt.date.between(start, end) & base["account"].isin(chosen or accounts)]
    v_in, v_out = view.loc[view["amount"] > 0, "amount"].sum(), view.loc[view["amount"] < 0, "amount"].sum()
    st.markdown(
        f'<p class="subtle"><span class="dot" style="background:{IN_COLOR}"></span>In {euros(v_in)} &nbsp;·&nbsp; '
        f'<span class="dot" style="background:{OUT_COLOR}"></span>Out {euros(-v_out)} &nbsp;·&nbsp; '
        f'Net {euros(v_in + v_out, signed=True)} &nbsp;·&nbsp; {len(view)} transactions</p>',
        unsafe_allow_html=True,
    )
    if not view.empty:
        st.plotly_chart(in_out_chart(in_out_by_month(view)), width="stretch", config={"displayModeBar": False})
        e1, e2 = st.columns([2, 3], gap="large")
        with e1:
            has_out_v = (view["amount"] < 0).any()
            dir_all = st.radio("Show", ["Money out", "Money in"], index=0 if has_out_v else 1, horizontal=True,
                               label_visibility="collapsed", key="dir_all")
            fig = top_chart(view, money_out=dir_all == "Money out", n=10)
            if fig is not None:
                st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
        with e2:
            transactions_table(view, height=420)
