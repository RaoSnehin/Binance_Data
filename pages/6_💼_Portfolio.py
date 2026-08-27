"""
CryptoSphere — Page 6: Virtual Portfolio Tracker
Add coins with quantity and buy price. See live P&L, allocation chart, and history.
Portfolio holdings are persisted in a local SQLite database (cryptosphere.db)
so they survive page refreshes and app restarts.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Portfolio · CryptoSphere", page_icon="💼", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.page-title {
    font-size:2rem; font-weight:800;
    background: linear-gradient(135deg,#F59E0B,#EF4444);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
}
.pnl-pos { color:#22C55E; font-weight:700; }
.pnl-neg { color:#EF4444; font-weight:700; }

.summary-card {
    background:rgba(19,19,43,0.95); border:1px solid rgba(124,58,237,0.25);
    border-radius:14px; padding:1.2rem 1.4rem; text-align:center;
}
.s-label { color:#64748B; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.06em; }
.s-value { color:#E2E8F0; font-size:1.6rem; font-weight:700; margin-top:0.2rem; }

.db-badge {
    display:inline-flex; align-items:center; gap:0.4rem;
    background:rgba(34,197,94,0.08); border:1px solid rgba(34,197,94,0.2);
    border-radius:999px; padding:0.3rem 0.8rem;
    font-size:0.75rem; color:#22C55E; font-weight:500;
}
.db-dot {
    width:6px; height:6px; border-radius:50%; background:#22C55E;
    display:inline-block;
}

.disclaimer {
    background:rgba(234,179,8,0.08); border:1px solid rgba(234,179,8,0.3);
    border-radius:10px; padding:0.8rem 1rem; color:#CA8A04;
    font-size:0.8rem; margin-top:1rem;
}

/* Delete button styling */
.stButton > button[kind="secondary"] {
    background: rgba(239,68,68,0.08) !important;
    border: 1px solid rgba(239,68,68,0.3) !important;
    color: #EF4444 !important;
    border-radius: 8px !important;
    padding: 0.2rem 0.6rem !important;
    font-size: 0.8rem !important;
}
</style>
""", unsafe_allow_html=True)

# ── Database & live data ────────────────────────────────────────────────────────
from src.database import (
    add_position, get_all_positions, delete_position,
    clear_all_positions, get_db_info
)
from src.live_data import get_top_coins

# ── Coin data ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def load_coins():
    df = get_top_coins(200)
    if df.empty:
        return {}
    return dict(zip(df["name"].str.lower(), df["price_usd"]))

@st.cache_data(ttl=60, show_spinner=False)
def coin_options_list():
    df = get_top_coins(200)
    if df.empty:
        return ["Bitcoin","Ethereum","BNB","Solana","XRP","Cardano","Avalanche"]
    return sorted(df["name"].dropna().unique().tolist())

coin_prices = load_coins()
all_coins   = coin_options_list()

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown('<span class="page-title">💼 Virtual Portfolio Tracker</span>', unsafe_allow_html=True)

# DB status badge
db_info = get_db_info()
col_title, col_badge = st.columns([6, 1])
with col_badge:
    st.markdown(
        f'<div class="db-badge"><span class="db-dot"></span>'
        f'SQLite · {db_info["position_count"]} positions</div>',
        unsafe_allow_html=True,
    )

st.caption(
    f"Portfolio saved in `cryptosphere.db` — survives page refresh & restarts · "
    "Simulation only, not financial advice"
)

# ── Add Coin Form ──────────────────────────────────────────────────────────────
st.subheader("➕ Add a Position")
with st.form("add_coin_form", clear_on_submit=True):
    fc1, fc2, fc3, fc4 = st.columns([3, 2, 2, 1])
    with fc1:
        selected_coin = st.selectbox("Coin", all_coins, index=0)
    with fc2:
        qty = st.number_input("Quantity", min_value=0.0001, step=0.01, value=1.0, format="%.4f")
        live_price = float(coin_prices.get(selected_coin.lower(), 0.0) or 0.0)
        default_val = live_price if live_price > 0 else 100.0
        buy_price  = st.number_input(
            "Buy Price (USD)", min_value=0.0, step=0.0001,
            value=default_val,
            format="%.6f",
        )
    with fc4:
        st.markdown("<br>", unsafe_allow_html=True)
        add_btn = st.form_submit_button("Add", use_container_width=True)

    if add_btn:
        row_id = add_position(selected_coin, qty, buy_price)
        st.success(f"✅ Added {qty:.4g} × {selected_coin} @ ${buy_price:,.4g} (ID #{row_id})")
        st.rerun()

# ── Load positions from DB ─────────────────────────────────────────────────────
positions = get_all_positions()

if not positions:
    st.info("Your portfolio is empty. Add some coins above to get started!")
    st.markdown("""
    <div class="disclaimer">
    ⚠️ <b>Disclaimer:</b> This is a virtual simulation for educational purposes only.
    It does not constitute financial advice. Always do your own research.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Build P&L DataFrame ────────────────────────────────────────────────────────
rows = []
for pos in positions:
    coin      = pos["coin"]
    qty       = pos["qty"]
    buy_price = pos["buy_price"]
    live_px   = coin_prices.get(coin.lower(), buy_price)
    cost      = qty * buy_price
    curr_val  = qty * live_px
    pnl       = curr_val - cost
    pnl_pct   = (pnl / cost * 100) if cost > 0 else 0
    rows.append({
        "_id":       pos["id"],
        "Coin":      coin,
        "Added":     pos["added_at"],
        "Quantity":  qty,
        "Buy Price": buy_price,
        "Live Price":live_px,
        "Cost Basis":cost,
        "Value":     curr_val,
        "P&L ($)":   pnl,
        "P&L (%)":   pnl_pct,
    })

port_df = pd.DataFrame(rows)

# ── Summary Cards ──────────────────────────────────────────────────────────────
total_cost    = port_df["Cost Basis"].sum()
total_val     = port_df["Value"].sum()
total_pnl     = total_val - total_cost
total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0

def fmt(n):
    if abs(n) >= 1e6: return f"${n/1e6:.2f}M"
    return f"${n:,.2f}"

sc1, sc2, sc3, sc4 = st.columns(4)
pnl_cls = "pnl-pos" if total_pnl >= 0 else "pnl-neg"

for col, label, val, sub, sub_cls in [
    (sc1, "Total Invested",  fmt(total_cost), "", ""),
    (sc2, "Current Value",   fmt(total_val),  "", ""),
    (sc3, "Total P&L",       fmt(total_pnl),  f"{total_pnl_pct:+.2f}%", pnl_cls),
    (sc4, "Positions",       str(len(rows)),  "", ""),
]:
    col.markdown(
        f'<div class="summary-card"><div class="s-label">{label}</div>'
        f'<div class="s-value">{val}</div>'
        f'<div class="{sub_cls}">{sub}</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts ─────────────────────────────────────────────────────────────────────
ch1, ch2 = st.columns(2)

with ch1:
    fig_pie = px.pie(
        port_df, values="Value", names="Coin",
        title="Portfolio Allocation",
        color_discrete_sequence=px.colors.sequential.Purples_r,
    )
    fig_pie.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#94A3B8"),
        legend=dict(font=dict(color="#E2E8F0")),
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with ch2:
    colors  = ["#22C55E" if v >= 0 else "#EF4444" for v in port_df["P&L ($)"]]
    fig_pnl = go.Figure(go.Bar(
        x=port_df["Coin"], y=port_df["P&L ($)"],
        marker_color=colors,
        text=port_df["P&L (%)"].apply(lambda x: f"{x:+.2f}%"),
        textposition="outside",
        textfont=dict(color="#E2E8F0"),
    ))
    fig_pnl.update_layout(
        title="P&L by Position",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94A3B8"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", zeroline=True, zerolinecolor="#334155"),
    )
    st.plotly_chart(fig_pnl, use_container_width=True)

# ── Position Details Table with Delete ─────────────────────────────────────────
st.subheader("📋 Position Details")
st.caption("Each row is saved in the database. Use 🗑️ to remove individual positions.")

# Display table header
hdr = st.columns([2, 1, 1.2, 1.2, 1.2, 1.2, 1.3, 0.8])
for h, label in zip(hdr, ["Coin", "Qty", "Buy $", "Live $", "Cost", "Value", "P&L", "Delete"]):
    h.markdown(f"**{label}**")

st.markdown('<hr style="border-color:rgba(124,58,237,0.15);margin:0.3rem 0 0.5rem">', unsafe_allow_html=True)

for _, row in port_df.iterrows():
    pnl_color = "#22C55E" if row["P&L ($)"] >= 0 else "#EF4444"
    pnl_arrow = "▲" if row["P&L ($)"] >= 0 else "▼"
    cols = st.columns([2, 1, 1.2, 1.2, 1.2, 1.2, 1.3, 0.8])
    cols[0].markdown(f"**{row['Coin']}**")
    cols[1].markdown(f"{row['Quantity']:.4g}")
    cols[2].markdown(f"${row['Buy Price']:,.4g}")
    cols[3].markdown(f"${row['Live Price']:,.4g}")
    cols[4].markdown(f"${row['Cost Basis']:,.2f}")
    cols[5].markdown(f"${row['Value']:,.2f}")
    cols[6].markdown(
        f'<span style="color:{pnl_color};font-weight:600">'
        f'{pnl_arrow} ${abs(row["P&L ($)"]):,.2f} ({row["P&L (%)"]:+.2f}%)</span>',
        unsafe_allow_html=True,
    )
    if cols[7].button("🗑️", key=f"del_{row['_id']}", help=f"Remove {row['Coin']} position"):
        delete_position(int(row["_id"]))
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ── Bulk Actions ───────────────────────────────────────────────────────────────
col_a1, col_a2, col_a3 = st.columns(3)

with col_a1:
    if st.button("🗑️ Clear All Positions", use_container_width=True):
        clear_all_positions()
        st.rerun()

with col_a2:
    # Export clean display version
    export_df = port_df.drop(columns=["_id"]).copy()
    for c in ["Buy Price", "Live Price", "Cost Basis", "Value", "P&L ($)"]:
        export_df[c] = export_df[c].apply(lambda x: f"${x:,.4g}")
    export_df["P&L (%)"]  = export_df["P&L (%)"].apply(lambda x: f"{x:+.2f}%")
    export_df["Quantity"] = export_df["Quantity"].apply(lambda x: f"{x:.4f}")
    csv = export_df.to_csv(index=False)
    st.download_button(
        "📥 Export as CSV", data=csv,
        file_name="cryptosphere_portfolio.csv",
        mime="text/csv", use_container_width=True,
    )

with col_a3:
    db = get_db_info()
    st.markdown(
        f'<div style="background:rgba(19,19,43,0.8);border:1px solid rgba(124,58,237,0.2);'
        f'border-radius:10px;padding:0.6rem 1rem;font-size:0.8rem;text-align:center;color:#64748B">'
        f'🗄️ <b style="color:#E2E8F0">cryptosphere.db</b><br>'
        f'{db["position_count"]} rows · {db["size_kb"]} KB</div>',
        unsafe_allow_html=True,
    )

st.markdown("""
<div class="disclaimer">
⚠️ <b>Disclaimer:</b> This virtual portfolio is for educational and demonstration purposes only.
Prices are fetched from CoinGecko and may be delayed. This is <b>NOT financial advice</b>.
Always consult a qualified financial advisor before making investment decisions.
</div>
""", unsafe_allow_html=True)
