import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Vedhi Finance | Retirement Strategy",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Dark theme CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
html, body, [class*="css"], .stApp {
    background-color: #0e1117 !important;
    color: #ffffff !important;
}
.block-container { padding-top: 1rem; padding-bottom: 1rem; }
p, span, label, div, h1, h2, h3, h4, h5, h6, li, td, th {
    color: #ffffff !important;
}
input, textarea, select,
div[data-baseweb="select"] *,
div[data-baseweb="input"] *,
div[data-baseweb="textarea"] * {
    background-color: #1e1e2e !important;
    color: #ffffff !important;
    border-color: #3a3f4b !important;
}
button[data-baseweb="tab"] {
    background-color: #1e1e2e !important;
    color: #aaaaaa !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #1a9641 !important;
    border-bottom: 2px solid #1a9641 !important;
}
div.stButton > button {
    background-color: #1a9641 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: bold;
}
div.stButton > button:hover { background-color: #138a32 !important; }
div[data-testid="stMetric"] {
    background-color: #1e1e2e !important;
    border-radius: 8px;
    padding: 12px 16px;
}
div[data-testid="stMetricValue"],
div[data-testid="stMetricLabel"],
div[data-testid="stMetricDelta"] { color: #ffffff !important; }
div[data-testid="stDataFrame"] * { background-color: #1e1e2e !important; color: #ffffff !important; }
div[data-testid="stNumberInput"] * { color: #ffffff !important; }
div[data-testid="stDateInput"] *   { color: #ffffff !important; }
div[data-testid="stCheckbox"] label { color: #ffffff !important; }
div[data-testid="stSlider"] *      { color: #ffffff !important; }
ul[data-testid="stSelectboxVirtualDropdown"] li {
    background-color: #1e1e2e !important; color: #ffffff !important;
}
hr { border-color: #3a3f4b !important; }
.info-box {
    background: #1a2e1a;
    border-left: 4px solid #1a9641;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "treasury" not in st.session_state:
    st.session_state.treasury = pd.DataFrame(
        columns=["Date", "Amount", "NAV", "Units", "Note"])

if "trades" not in st.session_state:
    st.session_state.trades = pd.DataFrame(
        columns=["ID", "Ticker", "Tranche", "Buy Date", "Buy Rate",
                 "Qty", "Invested", "Stop Loss", "Target",
                 "Sell Date", "Sell Rate", "Status", "P&L", "Holding Days", "Note"])

if "page" not in st.session_state:
    st.session_state.page = "Overview"

if "next_id" not in st.session_state:
    st.session_state.next_id = 1

# ── Helper functions ───────────────────────────────────────────────────────────
def get_treasury_total():
    if st.session_state.treasury.empty:
        return 0.0
    return float(st.session_state.treasury["Amount"].sum())

def get_total_units():
    if st.session_state.treasury.empty:
        return 0.0
    return float(st.session_state.treasury["Units"].sum())

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(
    "<h4 style='color:#1a9641; margin-top:-10px; margin-bottom:0;'>"
    "Vedhi Finance 💰 Retirement Strategy Dashboard</h4>",
    unsafe_allow_html=True)
st.markdown("<hr style='margin-top:6px; margin-bottom:8px;'>", unsafe_allow_html=True)

# ── Navigation ─────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1:
    if st.button("📊  Overview",         use_container_width=True):
        st.session_state.page = "Overview"
with c2:
    if st.button("🏦  Treasury Account", use_container_width=True):
        st.session_state.page = "Treasury"
with c3:
    if st.button("📈  Equity Trades",    use_container_width=True):
        st.session_state.page = "Trades"
with c4:
    if st.button("📉  Analytics",        use_container_width=True):
        st.session_state.page = "Analytics"

st.markdown("<hr style='margin-top:8px; margin-bottom:14px;'>", unsafe_allow_html=True)
page = st.session_state.page


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if page == "Overview":

    total    = get_treasury_total()
    liq_40   = total * 0.40
    eq_60    = total * 0.60
    liq_yld  = liq_40 * 0.055

    tdf     = st.session_state.trades
    closed  = tdf[tdf["Status"] == "closed"] if not tdf.empty else pd.DataFrame()
    open_t  = tdf[tdf["Status"] == "open"]   if not tdf.empty else pd.DataFrame()
    swing_pnl = float(closed["P&L"].sum()) if not closed.empty else 0.0
    combined  = swing_pnl + liq_yld
    comb_pct  = (combined / total * 100) if total else 0.0

    # ── Metric cards ──
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("💰 Total Treasury",      f"₹{total:,.2f}")
    m2.metric("🏦 Liquidcase 40%",      f"₹{liq_40:,.2f}")
    m3.metric("⚡ Equity Pool 60%",     f"₹{eq_60:,.2f}")
    m4.metric("📈 Combined Return",     f"{comb_pct:.2f}%",
              delta=f"₹{combined:,.2f}")

    st.markdown("---")

    # ── Allocation bar ──
    st.markdown("#### Portfolio Allocation")
    fig_alloc = go.Figure(go.Bar(
        x=[liq_40, eq_60],
        y=["Liquidcase ETF (40%)", "Equity Pool (60%)"],
        orientation="h",
        marker_color=["#0077b6", "#1a9641"],
        text=[f"₹{liq_40:,.2f}", f"₹{eq_60:,.2f}"],
        textposition="inside",
        textfont=dict(color="white", size=14)
    ))
    fig_alloc.update_layout(
        template="plotly_dark",
        height=160,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(showticklabels=False, showgrid=False),
        yaxis=dict(showgrid=False),
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117"
    )
    st.plotly_chart(fig_alloc, use_container_width=True)

    st.markdown("---")

    # ── Open positions ──
    st.markdown("#### 📂 Open Equity Positions")
    if open_t.empty:
        st.info("No open trades yet. Go to 📈 Equity Trades to log your first buy.")
    else:
        cols = ["ID", "Ticker", "Tranche", "Buy Date", "Buy Rate",
                "Qty", "Invested", "Stop Loss", "Target"]
        st.dataframe(open_t[cols].reset_index(drop=True),
                     hide_index=True, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — TREASURY ACCOUNT
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Treasury":

    st.markdown("#### 🏦 Treasury Account — Liquidcase ETF")
    st.markdown("""
    <div class='info-box'>
    Everything you invest goes into <b>Liquidcase ETF</b>.<br>
    &nbsp;&nbsp;📦 <b>40%</b> stays in the ETF — earns ~5.5% per year.<br>
    &nbsp;&nbsp;⚡ <b>60%</b> is your Equity Pool — used for swing trades.
    </div>
    """, unsafe_allow_html=True)

    total      = get_treasury_total()
    units      = get_total_units()
    avg_nav    = (total / units) if units > 0 else 0.0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Invested",       f"₹{total:,.2f}")
    m2.metric("Total Units Held",     f"{units:,.4f}")
    m3.metric("Avg NAV",              f"₹{avg_nav:.4f}")
    m4.metric("Equity Pool (60%)",    f"₹{total * 0.60:,.2f}")

    st.markdown("---")

    tab_add, tab_log, tab_io = st.tabs(
        ["➕ Add Investment", "📜 Transaction Log", "⬆️ Import / Export"])

    with tab_add:
        with st.form("treasury_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                t_date   = st.date_input("Date", value=date.today())
                t_amount = st.number_input("Amount to Invest (₹)",
                                           min_value=0.01, step=1000.0, format="%.2f")
            with col2:
                t_nav  = st.number_input("Liquidcase NAV (₹ per unit)",
                                         min_value=0.01, step=0.01,
                                         format="%.4f", value=1000.0)
                t_note = st.text_input("Note (optional)")

            if t_nav > 0 and t_amount > 0:
                preview_units = t_amount / t_nav
                st.info(f"You will receive **{preview_units:,.4f} units** at NAV ₹{t_nav:.4f}")

            if st.form_submit_button("✅ Invest in Liquidcase ETF", use_container_width=True):
                units_bought = round(t_amount / t_nav, 4)
                new_row = pd.DataFrame([{
                    "Date": str(t_date), "Amount": round(t_amount, 2),
                    "NAV": t_nav, "Units": units_bought, "Note": t_note
                }])
                st.session_state.treasury = pd.concat(
                    [st.session_state.treasury, new_row], ignore_index=True)
                new_total = get_treasury_total()
                st.success(
                    f"✅ Bought {units_bought:,.4f} units at ₹{t_nav:.4f}  ·  "
                    f"Treasury total: ₹{new_total:,.2f}"
                )
                st.rerun()

    with tab_log:
        df = st.session_state.treasury
        if df.empty:
            st.info("No investments yet.")
        else:
            # Running balance column
            display = df.copy()
            display["Running Balance"] = display["Amount"].cumsum().apply(lambda x: f"₹{x:,.2f}")
            display["Amount"] = display["Amount"].apply(lambda x: f"₹{x:,.2f}")
            display["NAV"]    = display["NAV"].apply(lambda x: f"₹{x:.4f}")
            st.dataframe(display, hide_index=True, use_container_width=True)

            st.markdown("---")
            del_idx = st.number_input("Delete row number (0 = first row)",
                                      min_value=0, max_value=max(0, len(df)-1), step=1)
            if st.button("🗑️ Delete Row"):
                st.session_state.treasury = df.drop(index=del_idx).reset_index(drop=True)
                st.success("Row deleted.")
                st.rerun()

    with tab_io:
        st.markdown("**💾 Save your data — download before closing the app**")
        if not st.session_state.treasury.empty:
            st.download_button("⬇️ Download Treasury CSV",
                               st.session_state.treasury.to_csv(index=False),
                               "treasury.csv", "text/csv", use_container_width=True)
        else:
            st.info("Nothing to export yet.")
        st.markdown("---")
        st.markdown("**📂 Restore from a previous session**")
        up = st.file_uploader("Upload treasury.csv", type="csv", key="up_t")
        if up:
            st.session_state.treasury = pd.read_csv(up)
            st.success(f"Loaded {len(st.session_state.treasury)} rows.")
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — EQUITY TRADES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Trades":

    st.markdown("#### 📈 Equity Swing Trades")

    total   = get_treasury_total()
    eq_pool = total * 0.60
    max_pos = eq_pool * 0.10

    if total > 0:
        st.markdown(
            f"<div class='info-box'>"
            f"Treasury: <b>₹{total:,.2f}</b> &nbsp;·&nbsp; "
            f"Equity Pool (60%): <b>₹{eq_pool:,.2f}</b> &nbsp;·&nbsp; "
            f"Max per trade (10%): <b>₹{max_pos:,.2f}</b>"
            f"</div>", unsafe_allow_html=True)
    else:
        st.warning("Add funds to Treasury Account first.")

    tab_buy, tab_sell, tab_open, tab_closed, tab_io = st.tabs([
        "🟢 Log Buy", "🔴 Close Trade",
        "📂 Open Trades", "📜 Closed Trades", "⬆️ Import / Export"])

    with tab_buy:
        with st.form("buy_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                ticker   = st.text_input("Ticker (e.g. RELIANCE)").upper().strip()
                buy_date = st.date_input("Buy Date", value=date.today())
                tranche  = st.selectbox("Tranche",
                    ["1 — Initial entry", "2 — Add-on at −7%"])
            with col2:
                buy_rate = st.number_input("Buy Rate (₹)", min_value=0.01,
                                           step=0.5, format="%.2f")
                qty      = st.number_input("Quantity", min_value=1, step=1)
            with col3:
                note = st.text_input("Entry note (optional)")
                if buy_rate > 0 and qty > 0:
                    st.markdown(f"**Invested:** ₹{buy_rate * qty:,.2f}")
                    st.markdown(f"**Stop Loss (−2%):** ₹{buy_rate * 0.98:.2f}")
                    st.markdown(f"**Min Target (+4%):** ₹{buy_rate * 1.04:.2f}")

            if st.form_submit_button("✅ Log Buy", use_container_width=True):
                if not ticker:
                    st.error("Enter a ticker symbol.")
                elif buy_rate == 0 or qty == 0:
                    st.error("Rate and quantity must be > 0.")
                else:
                    tid = st.session_state.next_id
                    st.session_state.next_id += 1
                    new_trade = pd.DataFrame([{
                        "ID": tid, "Ticker": ticker,
                        "Tranche": int(tranche[0]),
                        "Buy Date": str(buy_date),
                        "Buy Rate": buy_rate, "Qty": qty,
                        "Invested": round(buy_rate * qty, 2),
                        "Stop Loss": round(buy_rate * 0.98, 2),
                        "Target": round(buy_rate * 1.04, 2),
                        "Sell Date": None, "Sell Rate": None,
                        "Status": "open", "P&L": None,
                        "Holding Days": None, "Note": note
                    }])
                    st.session_state.trades = pd.concat(
                        [st.session_state.trades, new_trade], ignore_index=True)
                    st.success(
                        f"✅ {ticker} T{tranche[0]} logged  ·  "
                        f"Stop ₹{buy_rate * 0.98:.2f}  ·  "
                        f"Target ₹{buy_rate * 1.04:.2f}"
                    )
                    st.rerun()

    with tab_sell:
        tdf      = st.session_state.trades
        open_tdf = tdf[tdf["Status"] == "open"] if not tdf.empty else pd.DataFrame()

        if open_tdf.empty:
            st.info("No open trades to close.")
        else:
            st.dataframe(
                open_tdf[["ID","Ticker","Tranche","Buy Date",
                           "Buy Rate","Qty","Invested","Stop Loss","Target"]
                         ].reset_index(drop=True),
                hide_index=True, use_container_width=True)

            with st.form("sell_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    sel_id    = st.number_input("Trade ID to close", min_value=1, step=1)
                    sell_date = st.date_input("Sell Date", value=date.today())
                with col2:
                    sell_rate = st.number_input("Sell Rate (₹)", min_value=0.01,
                                                step=0.5, format="%.2f")
                    sell_nav  = st.number_input("Liquidcase NAV today (₹)",
                                                min_value=0.01, step=0.01,
                                                format="%.4f", value=1000.0)

                st.info("Sale proceeds will be reinvested automatically into Liquidcase ETF.")

                if st.form_submit_button("🔴 Close Trade & Reinvest", use_container_width=True):
                    match = tdf[(tdf["ID"] == sel_id) & (tdf["Status"] == "open")]
                    if match.empty:
                        st.error(f"No open trade with ID {sel_id}.")
                    else:
                        idx      = match.index[0]
                        row      = tdf.loc[idx]
                        pnl      = round((sell_rate - float(row["Buy Rate"])) * float(row["Qty"]), 2)
                        sell_amt = round(sell_rate * float(row["Qty"]), 2)
                        try:
                            days = (pd.to_datetime(sell_date).date() -
                                    pd.to_datetime(row["Buy Date"]).date()).days
                        except:
                            days = 0

                        # Close trade
                        st.session_state.trades.at[idx, "Sell Date"]    = str(sell_date)
                        st.session_state.trades.at[idx, "Sell Rate"]    = sell_rate
                        st.session_state.trades.at[idx, "Status"]       = "closed"
                        st.session_state.trades.at[idx, "P&L"]          = pnl
                        st.session_state.trades.at[idx, "Holding Days"] = days

                        # Reinvest proceeds into ETF
                        units_back = round(sell_amt / sell_nav, 4)
                        pnl_str    = f"+₹{pnl:,.2f}" if pnl >= 0 else f"₹{pnl:,.2f}"
                        note_txt   = (f"Closed trade #{sel_id} {row['Ticker']} — "
                                      f"₹{sell_amt:,.2f} reinvested ({pnl_str} P&L)")
                        new_row = pd.DataFrame([{
                            "Date": str(sell_date), "Amount": sell_amt,
                            "NAV": sell_nav, "Units": units_back, "Note": note_txt
                        }])
                        st.session_state.treasury = pd.concat(
                            [st.session_state.treasury, new_row], ignore_index=True)

                        emoji = "🟢" if pnl >= 0 else "🔴"
                        st.success(
                            f"{emoji} Trade #{sel_id} closed  ·  "
                            f"P&L ₹{pnl:,.2f}  ·  {days} days held  ·  "
                            f"{units_back:.4f} ETF units reinvested"
                        )
                        st.rerun()

    with tab_open:
        tdf    = st.session_state.trades
        open_t = tdf[tdf["Status"] == "open"] if not tdf.empty else pd.DataFrame()
        if open_t.empty:
            st.info("No open trades.")
        else:
            st.dataframe(
                open_t[["ID","Ticker","Tranche","Buy Date","Buy Rate",
                         "Qty","Invested","Stop Loss","Target","Note"]
                       ].reset_index(drop=True),
                hide_index=True, use_container_width=True)

    with tab_closed:
        tdf      = st.session_state.trades
        closed_t = tdf[tdf["Status"] == "closed"] if not tdf.empty else pd.DataFrame()
        if closed_t.empty:
            st.info("No closed trades yet.")
        else:
            display = closed_t[["ID","Ticker","Tranche","Buy Date","Sell Date",
                                  "Buy Rate","Sell Rate","Qty","Invested",
                                  "P&L","Holding Days"]].copy()
            display["P&L"] = display["P&L"].apply(
                lambda x: f"₹{x:,.2f}" if pd.notna(x) else "—")
            st.dataframe(display.reset_index(drop=True),
                         hide_index=True, use_container_width=True)
            total_pnl = float(closed_t["P&L"].sum())
            if total_pnl >= 0:
                st.success(f"Total Realized Profit: ₹{total_pnl:,.2f}")
            else:
                st.error(f"Total Realized Loss: ₹{abs(total_pnl):,.2f}")

    with tab_io:
        st.markdown("**💾 Export trades**")
        if not st.session_state.trades.empty:
            st.download_button("⬇️ Download Trades CSV",
                               st.session_state.trades.to_csv(index=False),
                               "trades.csv", "text/csv", use_container_width=True)
        else:
            st.info("Nothing to export yet.")
        st.markdown("---")
        st.markdown("**📂 Import trades**")
        up = st.file_uploader("Upload trades.csv", type="csv", key="up_tr")
        if up:
            imported = pd.read_csv(up)
            st.session_state.trades = imported
            st.session_state.next_id = int(imported["ID"].max()) + 1 \
                if "ID" in imported.columns and not imported.empty else 1
            st.success(f"Loaded {len(imported)} trades.")
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Analytics":

    st.markdown("#### 📉 Analytics & Performance")

    total    = get_treasury_total()
    liq_40   = total * 0.40
    eq_60    = total * 0.60
    liq_yld  = liq_40 * 0.055
    max_pos  = eq_60 * 0.10

    tdf     = st.session_state.trades
    closed  = tdf[tdf["Status"] == "closed"] if not tdf.empty else pd.DataFrame()
    open_t  = tdf[tdf["Status"] == "open"]   if not tdf.empty else pd.DataFrame()

    wins    = closed[closed["P&L"] > 0]  if not closed.empty else pd.DataFrame()
    losses  = closed[closed["P&L"] <= 0] if not closed.empty else pd.DataFrame()

    swing_pnl = float(closed["P&L"].sum())          if not closed.empty else 0.0
    avg_win   = float(wins["P&L"].mean())            if not wins.empty   else 0.0
    avg_loss  = float(losses["P&L"].mean())          if not losses.empty else 0.0
    avg_days  = float(closed["Holding Days"].mean()) if not closed.empty else 0.0
    win_rate  = len(wins) / len(closed) * 100        if not closed.empty else 0.0
    combined  = swing_pnl + liq_yld
    comb_pct  = combined / total * 100               if total            else 0.0

    # Metric cards
    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    r1c1.metric("Treasury Total",        f"₹{total:,.2f}")
    r1c2.metric("Liquidcase 40%",        f"₹{liq_40:,.2f}")
    r1c3.metric("ETF Yield (est 5.5%)",  f"₹{liq_yld:,.2f}")
    r1c4.metric("Equity Pool 60%",       f"₹{eq_60:,.2f}")

    r2c1, r2c2, r2c3, r2c4 = st.columns(4)
    r2c1.metric("Total Trades",    len(tdf) if not tdf.empty else 0)
    r2c2.metric("Win Rate",        f"{win_rate:.1f}%")
    r2c3.metric("Avg Win",         f"₹{avg_win:,.2f}")
    r2c4.metric("Avg Loss",        f"₹{avg_loss:,.2f}")

    r3c1, r3c2, r3c3, r3c4 = st.columns(4)
    r3c1.metric("Avg Holding Days",  f"{avg_days:.1f}")
    r3c2.metric("Swing P&L",         f"₹{swing_pnl:,.2f}",
                delta=f"{'profit' if swing_pnl >= 0 else 'loss'}")
    r3c3.metric("Combined Return",   f"₹{combined:,.2f}",
                delta=f"{comb_pct:.2f}% of treasury")
    r3c4.metric("Open Trades",       len(open_t))

    st.markdown("---")

    if closed.empty:
        st.info("Close some trades to see charts.")
    else:
        # P&L per trade
        colors = ["#1a9641" if v >= 0 else "#d7191c"
                  for v in closed["P&L"].values]
        fig1 = go.Figure(go.Bar(
            x=closed["Ticker"].astype(str) + " T" + closed["Tranche"].astype(str),
            y=closed["P&L"],
            marker_color=colors,
            text=[f"₹{v:,.2f}" for v in closed["P&L"]],
            textposition="outside",
            textfont=dict(color="white")
        ))
        fig1.update_layout(
            title="P&L per Closed Trade",
            template="plotly_dark", height=350,
            margin=dict(l=20, r=20, t=40, b=20),
            yaxis_title="P&L (₹)",
            plot_bgcolor="#0e1117", paper_bgcolor="#0e1117"
        )
        st.plotly_chart(fig1, use_container_width=True)

        # Cumulative P&L
        cum = closed["P&L"].cumsum().values
        fig2 = go.Figure(go.Scatter(
            x=list(range(1, len(cum)+1)), y=cum,
            mode="lines+markers",
            line=dict(color="#1a9641", width=2),
            fill="tozeroy", fillcolor="rgba(26,150,65,0.15)"
        ))
        fig2.update_layout(
            title="Cumulative Swing P&L",
            template="plotly_dark", height=300,
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis_title="Trade #", yaxis_title="₹",
            plot_bgcolor="#0e1117", paper_bgcolor="#0e1117"
        )
        st.plotly_chart(fig2, use_container_width=True)
