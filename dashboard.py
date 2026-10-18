"""Finance App dashboard. Run with:  streamlit run dashboard.py"""
from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.db import engine, init_db

# ---------- Look & feel ----------
IN_COLOR = "#38a596"    # money in  (matte teal)
OUT_COLOR = "#a77ac0"   # money out (matte violet)
TEXT, MUTED, GRID, SURFACE = "#d9d9d6", "#8b8d92", "#26282c", "#1c1d20"

st.set_page_config(page_title="Finance App", page_icon="◐", layout="wide")
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&family=Source+Serif+4:opsz,wght@8..60,400;8..60,500&display=swap');
    html, body, [class*="css"], .stMarkdown, .stDataFrame, button, input { font-family: 'Inter', sans-serif; }
    h1, h2, h3 { font-family: 'Source Serif 4', Georgia, serif !important; font-weight: 400 !important; letter-spacing: -0.01em; }
    .block-container { padding-top: 2.5rem; max-width: 1200px; }
    #MainMenu, footer, header [data-testid="stToolbar"] { visibility: hidden; }
    .card { background: #1c1d20; border: 1px solid #26282c; border-radius: 6px; padding: 18px 20px; }
    .card .label { color: #8b8d92; font-size: 0.72rem; letter-spacing: 0.12em; text-transform: uppercase; }
    .card .value { font-family: 'JetBrains Mono', monospace; font-size: 1.7rem; color: #d9d9d6; margin-top: 6px; }
    .card .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 8px; }
    .subtle { color: #8b8d92; font-size: 0.85rem; }
    .stMultiSelect [data-tag] { background: #2a2c30 !important; color: #d9d9d6 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


def euros(x: float) -> str:
    s = f"{abs(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{'−' if x < 0 else ''}{s} €"


def card(label: str, value: float, color: str | None = None) -> str:
    dot = f'<span class="dot" style="background:{color}"></span>' if color else ""
    return f'<div class="card"><div class="label">{dot}{label}</div><div class="value">{euros(value)}</div></div>'


def style_fig(fig: go.Figure, height: int = 320) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=8, r=8, t=8, b=8),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=MUTED, size=12),
        legend=dict(orientation="h", y=1.08, x=0, font=dict(color=TEXT)),
        hoverlabel=dict(bgcolor=SURFACE, bordercolor=GRID, font=dict(color=TEXT, family="JetBrains Mono")),
        bargap=0.35, bargroupgap=0.08,
    )
    fig.update_xaxes(showgrid=False, linecolor=GRID, tickcolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, ticksuffix=" €")
    return fig


# ---------- Data ----------
@st.cache_data(ttl=60)
def load_data() -> pd.DataFrame:
    init_db()
    df = pd.read_sql(
        'SELECT t.booking_date, t.amount, t.concept, t.counterparty, '
        'a.identifier, a.product, a.description '
        'FROM "transaction" t JOIN account a ON a.id = t.account_id',
        engine,
    )
    if df.empty:
        return df
    df["booking_date"] = pd.to_datetime(df["booking_date"])
    df["account"] = (df["description"].fillna(df["product"]).fillna("Account")
                     + " ··" + df["identifier"].str[-4:])
    df["concept"] = df["concept"].fillna("(no concept)")
    return df


df = load_data()

st.markdown("# Finance")
if df.empty:
    st.info("No data yet. In the terminal, run:  `python scripts\\load_sandbox.py`")
    st.stop()

# ---------- Filters (one row) ----------
first, last = df["booking_date"].min().date(), df["booking_date"].max().date()
c1, c2 = st.columns([1, 2])
with c1:
    period = st.date_input("Period", value=(first, last), min_value=first, max_value=last, format="DD/MM/YYYY")
with c2:
    accounts = sorted(df["account"].unique())
    chosen = st.multiselect("Accounts", accounts, default=accounts, placeholder="All accounts")

start, end = (period if isinstance(period, tuple) and len(period) == 2 else (first, last))
mask = df["booking_date"].dt.date.between(start, end) & df["account"].isin(chosen or accounts)
view = df[mask]

money_in = view.loc[view["amount"] > 0, "amount"].sum()
money_out = view.loc[view["amount"] < 0, "amount"].sum()

# ---------- Summary cards ----------
st.write("")
k1, k2, k3 = st.columns(3)
k1.markdown(card("Money in", money_in, IN_COLOR), unsafe_allow_html=True)
k2.markdown(card("Money out", money_out, OUT_COLOR), unsafe_allow_html=True)
k3.markdown(card("Net", money_in + money_out), unsafe_allow_html=True)
st.markdown(f'<p class="subtle">{len(view)} transactions · {start:%d %b %Y} – {end:%d %b %Y}</p>',
            unsafe_allow_html=True)

# ---------- Charts ----------
left, right = st.columns([3, 2], gap="large")

with left:
    st.markdown("### Month by month")
    monthly = (view.assign(month=view["booking_date"].dt.to_period("M").dt.to_timestamp(),
                           inflow=view["amount"].clip(lower=0), outflow=-view["amount"].clip(upper=0))
               .groupby("month")[["inflow", "outflow"]].sum().reset_index())
    fig = go.Figure()
    fig.add_bar(x=monthly["month"], y=monthly["inflow"], name="Money in", marker_color=IN_COLOR,
                hovertemplate="%{x|%b %Y}<br>In: %{y:,.2f} €<extra></extra>")
    fig.add_bar(x=monthly["month"], y=monthly["outflow"], name="Money out", marker_color=OUT_COLOR,
                hovertemplate="%{x|%b %Y}<br>Out: %{y:,.2f} €<extra></extra>")
    fig.update_traces(marker_line_width=0, marker_cornerradius=4)
    fig.update_xaxes(dtick="M1", tickformat="%b %Y")
    st.plotly_chart(style_fig(fig), width="stretch", config={"displayModeBar": False})

with right:
    st.markdown("### By concept")
    has_out = (view["amount"] < 0).any()
    direction = st.radio("Show", ["Money out", "Money in"], index=0 if has_out else 1,
                         horizontal=True, label_visibility="collapsed")
    sel = view[view["amount"] < 0] if direction == "Money out" else view[view["amount"] > 0]
    if sel.empty:
        st.markdown(f'<p class="subtle">No {direction.lower()} in this period.</p>', unsafe_allow_html=True)
    else:
        by = sel.groupby("concept")["amount"].sum().abs().sort_values().tail(8)
        bar = go.Figure(go.Bar(
            x=by.values, y=by.index, orientation="h",
            marker_color=OUT_COLOR if direction == "Money out" else IN_COLOR,
            marker_line_width=0, marker_cornerradius=4,
            text=[euros(v) for v in by.values], textposition="outside", textfont=dict(color=MUTED),
            hovertemplate="%{y}: %{x:,.2f} €<extra></extra>", cliponaxis=False,
        ))
        bar = style_fig(bar)
        bar.update_xaxes(showticklabels=False, showgrid=False, range=[0, by.max() * 1.35])
        bar.update_yaxes(gridcolor="rgba(0,0,0,0)", ticksuffix="  ", tickfont=dict(color=TEXT))
        st.plotly_chart(bar, width="stretch", config={"displayModeBar": False})

# ---------- Transactions table ----------
st.markdown("### Transactions")
table = (view.sort_values("booking_date", ascending=False)
         [["booking_date", "account", "concept", "counterparty", "amount"]])
st.dataframe(
    table, hide_index=True, width="stretch", height=380,
    column_config={
        "booking_date": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
        "account": "Account", "concept": "Concept", "counterparty": "Counterparty",
        "amount": st.column_config.NumberColumn("Amount", format="%.2f €"),
    },
)
