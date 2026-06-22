import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date

st.set_page_config(
    page_title="Vedhi Finance | Retirement Strategy",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
}
div.stButton > button:hover { background-color: #138a32 !important; }
div[data-testid="stMetric"] {
    background-color: #1e1e2e !important;
    border-radius: 8px;
    padding: 10px 16px;
}
div[data-testid="stMetricValue"],
div[data-testid="stMetricLabel"],
div[data-testid="stMetricDelta"] { color: #ffffff !important; }
div[data-testid="stDataFrame"] *,
.dvn-scroller, .dvn-scroller * {
    background-color: #1e1e2e !important;
    color: #ffffff !important;
}
section[data-testid="stSidebar"] { background-color: #1e1e2e !important; }
div[data-testid="stNumberInput"] * { color: #ffffff !important; }
div[data-testid="stDateInput"] * { color: #ffffff !important; }
ul[data-testid="stSelectboxVirtualDropdown"] li {
    background-color: #1e1e2e !important; color: #ffffff !important;
}
div[data-testid="stCheckbox"] label { color: #ffffff !important; }
div[data-testid="stSlider"] * { color: #ffffff !important; }
.rule-box {
    background: #1e1e2e;
    border-left: 3px solid #1a9641;
    padding: 10px 16px;
    border-radius: 0 8px 8px 0;
    margin-bottom: 8px;
    font-size: 0.9rem;
    color: #ffffff !important;
}
.etf-box {
    background: #1a2e1a;
    border: 1px solid #1a9641;
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 10px;
}
hr { border-color: #3a3f4b !important; }
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────

def _empty_liquidcase():
    # Each row = one Liquidcase ETF purchase or interest credit or trade return
    return pd.DataFrame(columns=[
        "Date", "Action", "NAV", "Units", "Amount", "Note"
    ])

def _empty_trades():
    return pd.DataFrame(columns=[
        "ID", "Ticker", "Tranche", "Buy Date", "Buy Rate", "Qty",
        "Invested", "Stop Loss", "Target",
        "Sell Date", "Sell Rate", "Status", "P&L", "Holding Days", "Note"
    ])

for key, default in [
    ("liq_df",    _empty_liquidcase()),
    ("trades_df", _empty_trades()),
    ("page",      "Overview"),
    ("next_id",   1),
]:
    if key not in st.session_state:
        st.session_state[key] = default


def total_invested_in_liquidcase():
    """Total ₹ amount ever put into Liquidcase (deposits + interest + trade returns)."""
    if st.session_state.liq_df.empty:
        return 0.0
    return float(st.session_state.liq_df["Amount"].sum())

def total_liquidcase_units():
    if st.session_state.liq_df.empty:
        return 0.0
    return float(st.session_state.liq_df["Units"].sum())


# ── Header ─────────────────────────────────────────────────────────────────────

colA, colB = st.columns([9, 1])
with colA:
    st.markdown("<h4 style='color:#1a9641; margin-top:-10px; margin-bottom:0;'>"
                "Vedhi Finance | 💰 Retirement Strategy Dashboard</h4>",
                unsafe_allow_html=True)
with colB:
    if st.button("🔄 Reset"):
        st.session_state.liq_df    = _empty_liquidcase()
        st.session_state.trades_df = _empty_trades()
        st.session_state.next_id   = 1
        st.rerun()

st.markdown("<hr style='margin-top:5px; margin-bottom:5px;'>", unsafe_allow_html=True)

# ── Nav ────────────────────────────────────────────────────────────────────────

n1, n2, n3, n4 = st.columns(4)
with n1:
    if st.button("📊 Overview",          use_container_width=True): st.session_state.page = "Overview"
with n2:
    if st.button("🏦 Liquidcase ETF",    use_container_width=True): st.session_state.page = "Liquidcase"
with n3:
    if st.button("📈 Equity Trades",     use_container_width=True): st.session_state.page = "Trades"
with n4:
    if st.button("📉 Analytics",         use_container_width=True): st.session_state.page = "Analytics"

st.markdown("<hr style='margin-top:5px; margin-bottom:10px;'>", unsafe_allow_html=True)
page = st.session_state.page


# ══════════════════════════════════════════════════════════════════════════════
# OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════

if page == "Overview":

    total_invested  = total_invested_in_liquidcase()
    total_units     = total_liquidcase_units()
    liq_40          = total_invested * 0.40
    eq_60           = total_invested * 0.60
    liq_yld         = liq_40 * 0.055

    tdf     = st.session_state.trades_df
    closed  = tdf[tdf["Status"] == "closed"] if not tdf.empty else pd.DataFrame()
    open_t  = tdf[tdf["Status"] == "open"]   if not tdf.empty else pd.DataFrame()
    realized = float(closed["P&L"].sum()) if not closed.empty else 0.0
    combined = realized + liq_yld
    comb_pct = (combined / total_invested * 100) if total_invested else 0.0

    # Stat row
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total in Liquidcase ETF",  f"₹{total_invested:,.2f}")
    c2.metric("Total Units Held",         f"{total_units:,.4f}")
    c3.metric("40% — ETF Income Bucket",  f"₹{liq_40:,.2f}")
    c4.metric("60% — Equity Pool",        f"₹{eq_60:,.2f}")
    c5.metric("Swing Realized P&L",       f"₹{realized:,.2f}",
              delta=f"{'↑' if realized >= 0 else '↓'}")
    c6.metric("Combined Return",          f"{comb_pct:.2f}%",
              delta=f"₹{combined:,.2f}")

    st.markdown("---")

    # How the strategy works
    st.markdown("#### 🏦 How This Strategy Works")
    st.markdown("""
    <div class='etf-box'>
    <b style='color:#1a9641; font-size:1rem;'>Treasury Account = Liquidcase ETF</b><br><br>
    Every rupee you put in goes into the <b>Liquidcase ETF</b> — an overnight/liquid fund earning <b>5–6% per year</b>.<br>
    The total ETF value is then split mentally into two buckets:<br><br>
    &nbsp;&nbsp;📦 <b>40%</b> stays in the ETF permanently — earns the 5–6% interest, never touched for trading.<br>
    &nbsp;&nbsp;⚡ <b>60%</b> is your <b>Equity Pool</b> — used for swing trades. All sold proceeds return back to the ETF.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 📋 Strategy Rules")
    rules = [
        ("📊", "Entry — Tranche 1",  "RSI 35–40  ·  EMA 20–50 range  ·  Avg volume rising  ·  Last candle green"),
        ("➕", "Entry — Tranche 2",  "Stock falls <b>7%</b> from Tranche 1 buy price — add second position"),
        ("⚡", "Position size",      "Max <b>10% of equity pool</b> per trade — split across both tranches"),
        ("🛡️","Stop loss",          "<b>2%</b> below buy rate — hard exit"),
        ("🎯", "Profit target",      "Minimum <b>4%</b> — activate trailing stop loss after 4%"),
        ("⚖️", "Risk : Reward",     "<b>1 : 2</b>  (risk 2% → target minimum 4%)"),
        ("🔁", "After selling",      "100% of sale proceeds go back into <b>Liquidcase ETF</b>"),
    ]
    for icon, label, detail in rules:
        st.markdown(
            f"<div class='rule-box'><b>{icon} {label}:</b> &nbsp; {detail}</div>",
            unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 📂 Open Equity Positions")
    if open_t.empty:
        st.info("No open trades. Go to 📈 Equity Trades to log a buy.")
    else:
        show_cols = ["ID","Ticker","Tranche","Buy Date","Buy Rate","Qty","Invested","Stop Loss","Target","Note"]
        st.dataframe(open_t[show_cols].reset_index(drop=True),
                     hide_index=True, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# LIQUIDCASE ETF  (was Treasury)
# ══════════════════════════════════════════════════════════════════════════════

elif page == "Liquidcase":

    st.markdown("#### 🏦 Liquidcase ETF — Your Treasury Account")

    st.markdown("""
    <div class='etf-box'>
    Every entry here = <b>buying Liquidcase ETF units</b>.<br>
    When you deposit cash → you're buying units at today's NAV.<br>
    When a swing trade closes → sale proceeds automatically buy more ETF units.<br>
    The ETF earns <b>5–6% per year</b> on the full balance.
    </div>
    """, unsafe_allow_html=True)

    tab_buy, tab_log, tab_io = st.tabs([
        "➕ Buy Liquidcase ETF", "📜 ETF Transaction Log", "⬆️ Import / Export"])

    with tab_buy:
        total_invested = total_invested_in_liquidcase()
        total_units    = total_liquidcase_units()
        liq_40 = total_invested * 0.40
        eq_60  = total_invested * 0.60
        max_pos = eq_60 * 0.10

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total ETF Value",         f"₹{total_invested:,.2f}")
        m2.metric("Total Units Held",        f"{total_units:,.4f}")
        m3.metric("40% Income Bucket",       f"₹{liq_40:,.2f}")
        m4.metric("60% Equity Pool",         f"₹{eq_60:,.2f}")

        st.markdown("---")

        with st.form("liq_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                t_date   = st.date_input("Date", value=date.today())
                t_action = st.selectbox("Action", [
                    "buy — fresh deposit",
                    "interest credited",
                    "trade_return — sale proceeds reinvested",
                    "redemption — withdrawal"
                ])
            with col2:
                t_nav    = st.number_input("NAV (price per unit, ₹)", min_value=0.01,
                                           step=0.01, format="%.4f", value=1000.0)
                t_amount = st.number_input("Amount (₹)", min_value=0.01,
                                           step=100.0, format="%.2f")
                t_note   = st.text_input("Note (optional)")

            units_preview = t_amount / t_nav if t_nav > 0 else 0
            st.info(f"Units you will receive: **{units_preview:,.4f}** units at NAV ₹{t_nav:.4f}")

            submitted = st.form_submit_button("✅ Buy / Credit ETF Units", use_container_width=True)
            if submitted:
                is_redemption = "redemption" in t_action
                amt   = -t_amount if is_redemption else t_amount
                units = -units_preview if is_redemption else units_preview
                action_clean = t_action.split(" — ")[0]

                new_row = pd.DataFrame([{
                    "Date": str(t_date), "Action": action_clean,
                    "NAV": t_nav, "Units": round(units, 4),
                    "Amount": round(amt, 2), "Note": t_note
                }])
                st.session_state.liq_df = pd.concat(
                    [st.session_state.liq_df, new_row], ignore_index=True)

                new_total = total_invested_in_liquidcase()
                new_units = total_liquidcase_units()
                st.success(
                    f"{'Redeemed' if is_redemption else 'Bought'} "
                    f"{abs(units):.4f} units at NAV ₹{t_nav:.4f}  ·  "
                    f"Total ETF value: ₹{new_total:,.2f}  ·  "
                    f"Total units: {new_units:,.4f}"
                )
                st.rerun()

    with tab_log:
        ldf = st.session_state.liq_df
        if ldf.empty:
            st.info("No ETF transactions yet. Buy your first Liquidcase units above.")
        else:
            display = ldf.copy()
            display["Amount"] = display["Amount"].apply(lambda x: f"₹{x:,.2f}")
            display["NAV"]    = display["NAV"].apply(lambda x: f"₹{x:.4f}")
            st.dataframe(display, hide_index=True, use_container_width=True)

            total_invested = total_invested_in_liquidcase()
            total_units    = total_liquidcase_units()
            avg_nav = total_invested / total_units if total_units > 0 else 0

            s1, s2, s3 = st.columns(3)
            s1.metric("Total ETF Value",    f"₹{total_invested:,.2f}")
            s2.metric("Total Units",        f"{total_units:,.4f}")
            s3.metric("Avg Cost per Unit",  f"₹{avg_nav:.4f}")

            st.markdown("---")
            del_idx = st.number_input("Delete row (0-based index)", min_value=0,
                                      max_value=max(0, len(ldf)-1), step=1)
            if st.button("Delete Row", key="del_liq_btn"):
                st.session_state.liq_df = ldf.drop(index=del_idx).reset_index(drop=True)
                st.success("Row deleted.")
                st.rerun()

    with tab_io:
        st.markdown("**Export ETF log to CSV**")
        if not st.session_state.liq_df.empty:
            csv = st.session_state.liq_df.to_csv(index=False)
            st.download_button("⬇️ Download Liquidcase CSV", csv,
                               "liquidcase_log.csv", "text/csv", use_container_width=True)
        else:
            st.info("Nothing to export yet.")

        st.markdown("---")
        st.markdown("**Import ETF log from CSV**")
        uploaded = st.file_uploader("Upload liquidcase_log.csv", type="csv", key="up_liq")
        if uploaded:
            imported = pd.read_csv(uploaded)
            st.session_state.liq_df = imported
            st.success(f"Imported {len(imported)} rows.")
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# EQUITY TRADES
# ══════════════════════════════════════════════════════════════════════════════

elif page == "Trades":

    st.markdown("#### 📈 Equity Swing Trades")

    total_invested = total_invested_in_liquidcase()
    eq_pool  = total_invested * 0.60
    max_pos  = eq_pool * 0.10

    tab_buy, tab_sell, tab_all, tab_io = st.tabs([
        "🟢 Log Buy", "🔴 Close Trade", "📋 All Trades", "⬆️ Import / Export"])

    with tab_buy:
        if total_invested == 0:
            st.warning("Buy Liquidcase ETF units first — your equity pool comes from the ETF balance.")
        else:
            st.info(
                f"ETF Total: ₹{total_invested:,.2f}  ·  "
                f"Equity Pool (60%): ₹{eq_pool:,.2f}  ·  "
                f"Max per trade (10%): ₹{max_pos:,.2f}"
            )

        with st.form("buy_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                ticker   = st.text_input("Ticker (e.g. RELIANCE)").upper().strip()
                buy_date = st.date_input("Buy Date", value=date.today())
                tranche  = st.selectbox("Tranche", [
                    "1 — Initial entry (RSI/EMA setup)",
                    "2 — Add-on at −7% from T1"
                ])
            with col2:
                buy_rate = st.number_input("Buy Rate (₹)", min_value=0.01,
                                           step=0.5, format="%.4f")
                qty      = st.number_input("Quantity (shares)", min_value=0.01,
                                           step=1.0, format="%.2f")
            with col3:
                note = st.text_input("Entry note (e.g. RSI 38, EMA20 cross)")
                if buy_rate and qty:
                    invested_preview = buy_rate * qty
                    sl_preview       = buy_rate * 0.98
                    tgt_preview      = buy_rate * 1.04
                    st.markdown(f"**Invested:** ₹{invested_preview:,.2f}")
                    st.markdown(f"**Stop loss (−2%):** ₹{sl_preview:.4f}")
                    st.markdown(f"**Min target (+4%):** ₹{tgt_preview:.4f}")

            submitted = st.form_submit_button("Log Buy ✅", use_container_width=True)
            if submitted:
                if not ticker:
                    st.error("Ticker cannot be empty.")
                elif buy_rate == 0 or qty == 0:
                    st.error("Rate and quantity must be > 0.")
                else:
                    tranche_num = int(tranche[0])
                    invested    = round(buy_rate * qty, 2)
                    sl          = round(buy_rate * 0.98, 4)
                    target      = round(buy_rate * 1.04, 4)
                    trade_id    = st.session_state.next_id
                    st.session_state.next_id += 1

                    new_trade = pd.DataFrame([{
                        "ID": trade_id, "Ticker": ticker, "Tranche": tranche_num,
                        "Buy Date": str(buy_date), "Buy Rate": buy_rate, "Qty": qty,
                        "Invested": invested, "Stop Loss": sl, "Target": target,
                        "Sell Date": None, "Sell Rate": None, "Status": "open",
                        "P&L": None, "Holding Days": None, "Note": note
                    }])
                    st.session_state.trades_df = pd.concat(
                        [st.session_state.trades_df, new_trade], ignore_index=True)
                    st.success(
                        f"✅ {ticker} Tranche {tranche_num} logged  ·  "
                        f"Stop: ₹{sl}  ·  Target: ₹{target}"
                    )
                    st.rerun()

    with tab_sell:
        tdf = st.session_state.trades_df
        open_trades = tdf[tdf["Status"] == "open"] if not tdf.empty else pd.DataFrame()

        if open_trades.empty:
            st.info("No open trades to close.")
        else:
            st.dataframe(
                open_trades[["ID","Ticker","Tranche","Buy Date","Buy Rate",
                             "Qty","Invested","Stop Loss","Target"]].reset_index(drop=True),
                hide_index=True, use_container_width=True)

            with st.form("sell_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    trade_id_sel = st.number_input("Trade ID to close", min_value=1, step=1)
                    sell_date    = st.date_input("Sell Date", value=date.today())
                with col2:
                    sell_rate    = st.number_input("Sell Rate (₹)", min_value=0.01,
                                                   step=0.5, format="%.4f")
                    sell_nav     = st.number_input("Liquidcase NAV today (₹)",
                                                   min_value=0.01, step=0.01,
                                                   format="%.4f", value=1000.0,
                                                   help="Used to calculate ETF units received from proceeds")

                st.info("✅ Sale proceeds will automatically be reinvested into Liquidcase ETF units.")

                submitted = st.form_submit_button("Close Trade & Reinvest in ETF 🔁", use_container_width=True)
                if submitted:
                    match = tdf[(tdf["ID"] == trade_id_sel) & (tdf["Status"] == "open")]
                    if match.empty:
                        st.error(f"No open trade with ID {trade_id_sel}.")
                    else:
                        idx      = match.index[0]
                        row      = tdf.loc[idx]
                        pnl      = round((sell_rate - float(row["Buy Rate"])) * float(row["Qty"]), 2)
                        sell_amt = round(sell_rate * float(row["Qty"]), 2)
                        units_received = round(sell_amt / sell_nav, 4)
                        try:
                            days = (pd.to_datetime(sell_date).date() -
                                    pd.to_datetime(row["Buy Date"]).date()).days
                        except:
                            days = 0

                        # Close the trade
                        st.session_state.trades_df.at[idx, "Sell Date"]    = str(sell_date)
                        st.session_state.trades_df.at[idx, "Sell Rate"]    = sell_rate
                        st.session_state.trades_df.at[idx, "Status"]       = "closed"
                        st.session_state.trades_df.at[idx, "P&L"]          = pnl
                        st.session_state.trades_df.at[idx, "Holding Days"] = days

                        # Auto-reinvest proceeds back into Liquidcase ETF
                        pnl_txt = f"+₹{pnl:,.2f}" if pnl >= 0 else f"₹{pnl:,.2f}"
                        note_txt = (f"Trade #{trade_id_sel} {row['Ticker']} closed — "
                                    f"proceeds ₹{sell_amt:,.2f} ({pnl_txt} P&L) reinvested")
                        new_etf_row = pd.DataFrame([{
                            "Date":   str(sell_date),
                            "Action": "trade_return",
                            "NAV":    sell_nav,
                            "Units":  units_received,
                            "Amount": sell_amt,
                            "Note":   note_txt
                        }])
                        st.session_state.liq_df = pd.concat(
                            [st.session_state.liq_df, new_etf_row], ignore_index=True)

                        emoji = "🟢" if pnl >= 0 else "🔴"
                        st.success(
                            f"{emoji} Trade #{trade_id_sel} closed  ·  P&L ₹{pnl:,.2f}  ·  "
                            f"{days} days  ·  "
                            f"{units_received:.4f} ETF units bought back at NAV ₹{sell_nav:.4f}"
                        )
                        st.rerun()

    with tab_all:
        tdf = st.session_state.trades_df
        if tdf.empty:
            st.info("No trades logged yet.")
        else:
            display = tdf.copy()
            display["P&L"]       = display["P&L"].apply(lambda x: f"₹{x:,.2f}" if pd.notna(x) else "—")
            display["Invested"]  = display["Invested"].apply(lambda x: f"₹{x:,.2f}")
            display["Buy Rate"]  = display["Buy Rate"].apply(lambda x: f"₹{x:.4f}")
            display["Sell Rate"] = display["Sell Rate"].apply(
                lambda x: f"₹{x:.4f}" if pd.notna(x) else "—")
            st.dataframe(display.reset_index(drop=True),
                         hide_index=True, use_container_width=True)

    with tab_io:
        st.markdown("**Export all trades to CSV**")
        if not st.session_state.trades_df.empty:
            csv = st.session_state.trades_df.to_csv(index=False)
            st.download_button("⬇️ Download Trades CSV", csv,
                               "trades_log.csv", "text/csv", use_container_width=True)
        else:
            st.info("Nothing to export yet.")

        st.markdown("---")
        st.markdown("**Import trades from CSV**")
        uploaded = st.file_uploader("Upload trades_log.csv", type="csv", key="up_trades")
        if uploaded:
            imported = pd.read_csv(uploaded)
            st.session_state.trades_df = imported
            max_id = int(imported["ID"].max()) + 1 if "ID" in imported.columns else 1
            st.session_state.next_id = max_id
            st.success(f"Imported {len(imported)} trades.")
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════

elif page == "Analytics":

    st.markdown("#### 📉 Analytics & Performance")

    total_invested = total_invested_in_liquidcase()
    total_units    = total_liquidcase_units()
    liq_40   = total_invested * 0.40
    eq_60    = total_invested * 0.60
    liq_yld  = liq_40 * 0.055
    max_pos  = eq_60 * 0.10

    tdf    = st.session_state.trades_df
    closed = tdf[tdf["Status"] == "closed"] if not tdf.empty else pd.DataFrame()
    open_t = tdf[tdf["Status"] == "open"]   if not tdf.empty else pd.DataFrame()

    wins   = closed[closed["P&L"] > 0]  if not closed.empty else pd.DataFrame()
    losses = closed[closed["P&L"] <= 0] if not closed.empty else pd.DataFrame()

    total_pnl  = float(closed["P&L"].sum())          if not closed.empty else 0.0
    avg_win    = float(wins["P&L"].mean())            if not wins.empty   else 0.0
    avg_loss   = float(losses["P&L"].mean())          if not losses.empty else 0.0
    avg_days   = float(closed["Holding Days"].mean()) if not closed.empty else 0.0
    win_rate   = len(wins) / len(closed) * 100        if not closed.empty else 0.0
    combined   = total_pnl + liq_yld
    comb_pct   = combined / total_invested * 100      if total_invested   else 0.0

    tab_summary, tab_charts, tab_history = st.tabs(
        ["📋 Summary", "📊 Charts", "📜 Closed Trade History"])

    with tab_summary:
        c1, c2, c3 = st.columns(3)
        c1.metric("Liquidcase ETF Total",   f"₹{total_invested:,.2f}")
        c2.metric("Total Units Held",       f"{total_units:,.4f}")
        c3.metric("Max Position / Trade",   f"₹{max_pos:,.2f}")

        c4, c5, c6 = st.columns(3)
        c4.metric("40% Income Bucket",              f"₹{liq_40:,.2f}")
        c5.metric("Liquidcase Yield (est. 5.5%)",   f"₹{liq_yld:,.2f}")
        c6.metric("60% Equity Pool",                f"₹{eq_60:,.2f}")

        c7, c8, c9 = st.columns(3)
        c7.metric("Total Trades",    len(tdf) if not tdf.empty else 0)
        c8.metric("Closed Trades",   len(closed))
        c9.metric("Open Trades",     len(open_t))

        c10, c11, c12 = st.columns(3)
        c10.metric("Win Rate",       f"{win_rate:.1f}%")
        c11.metric("Avg Win",        f"₹{avg_win:,.2f}")
        c12.metric("Avg Loss",       f"₹{avg_loss:,.2f}")

        c13, c14, c15 = st.columns(3)
        c13.metric("Avg Holding Days",                     f"{avg_days:.1f}")
        c14.metric("Swing Realized P&L",                   f"₹{total_pnl:,.2f}",
                   delta=f"{'profit' if total_pnl >= 0 else 'loss'}")
        c15.metric("Combined Return (ETF yield + Swing)",  f"₹{combined:,.2f}",
                   delta=f"{comb_pct:.2f}% of ETF total")

    with tab_charts:
        if closed.empty:
            st.info("Close some trades to see charts.")
        else:
            colors = ["#1a9641" if v >= 0 else "#d7191c" for v in closed["P&L"].values]
            fig1 = go.Figure()
            fig1.add_trace(go.Bar(
                x=closed["Ticker"].astype(str) + " T" + closed["Tranche"].astype(str),
                y=closed["P&L"],
                marker_color=colors,
                text=[f"₹{v:,.2f}" for v in closed["P&L"]],
                textposition="outside"
            ))
            fig1.update_layout(
                title="P&L per Closed Trade",
                template="plotly_dark", height=350,
                margin=dict(l=20, r=20, t=40, b=20),
                yaxis_title="P&L (₹)"
            )
            st.plotly_chart(fig1, use_container_width=True)

            cum_pnl = closed["P&L"].cumsum().values
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=list(range(1, len(cum_pnl)+1)), y=cum_pnl,
                mode="lines+markers",
                line=dict(color="#1a9641", width=2),
                fill="tozeroy", fillcolor="rgba(26,150,65,0.15)"
            ))
            fig2.update_layout(
                title="Cumulative Swing Trade P&L",
                template="plotly_dark", height=300,
                margin=dict(l=20, r=20, t=40, b=20),
                xaxis_title="Trade #", yaxis_title="Cumulative P&L (₹)"
            )
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("---")
        st.markdown("##### 📆 10-Year Projection")
        col1, col2, col3 = st.columns(3)
        proj_trades  = col1.slider("Trades / year",  1, 52, 12)
        proj_winrate = col2.slider("Win rate (%)",  30, 90, 60)
        proj_avgwin  = col3.slider("Avg win (%)",    4, 20,  6)

        proj_liq = liq_40 if liq_40 > 0 else 100000
        proj_eq  = eq_60  if eq_60  > 0 else 150000

        years, liq_data, swing_data, cum_liq, cum_swing = [], [], [], [], []
        rl, rs = 0, 0
        for y in range(1, 11):
            lp = proj_liq * 0.055
            wins_n = round(proj_trades * proj_winrate / 100)
            loss_n = proj_trades - wins_n
            sp = max(0, wins_n * (proj_eq * 0.10) * (proj_avgwin / 100)
                        - loss_n * (proj_eq * 0.10) * 0.02)
            rl += lp; rs += sp
            years.append(f"Yr {y}")
            liq_data.append(round(lp, 2))
            swing_data.append(round(sp, 2))
            cum_liq.append(round(rl, 2))
            cum_swing.append(round(rs, 2))

        fig3 = go.Figure()
        fig3.add_trace(go.Bar(name="Liquidcase ETF Yield", x=years,
                              y=liq_data, marker_color="#0077b6"))
        fig3.add_trace(go.Bar(name="Swing Trade Profit",   x=years,
                              y=swing_data, marker_color="#1a9641"))
        fig3.update_layout(
            barmode="group",
            title="Annual Projection — Liquidcase ETF Yield vs Swing",
            template="plotly_dark", height=350,
            margin=dict(l=20, r=20, t=40, b=20), yaxis_title="₹"
        )
        st.plotly_chart(fig3, use_container_width=True)

        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(x=years, y=cum_liq,
                                  name="Cumulative ETF Yield",
                                  line=dict(color="#0077b6", width=2)))
        fig4.add_trace(go.Scatter(x=years, y=cum_swing,
                                  name="Cumulative Swing",
                                  line=dict(color="#1a9641", width=2)))
        fig4.add_trace(go.Scatter(x=years,
                                  y=[a+b for a, b in zip(cum_liq, cum_swing)],
                                  name="Combined Total",
                                  line=dict(color="#f4a261", width=2, dash="dot")))
        fig4.update_layout(
            title="Cumulative 10-Year Growth",
            template="plotly_dark", height=350,
            margin=dict(l=20, r=20, t=40, b=20), yaxis_title="₹"
        )
        st.plotly_chart(fig4, use_container_width=True)

    with tab_history:
        if closed.empty:
            st.info("No closed trades yet.")
        else:
            display = closed[["ID","Ticker","Tranche","Buy Date","Sell Date",
                               "Buy Rate","Sell Rate","Qty","Invested","P&L","Holding Days"]].copy()
            display["P&L"]      = display["P&L"].apply(lambda x: f"₹{x:,.2f}" if pd.notna(x) else "—")
            display["Invested"] = display["Invested"].apply(lambda x: f"₹{x:,.2f}")
            st.dataframe(display.reset_index(drop=True),
                         hide_index=True, use_container_width=True)
            total = float(closed["P&L"].sum())
            if total >= 0:
                st.success(f"Total Realized Profit: ₹{total:,.2f}")
            else:
                st.error(f"Total Realized Loss: ₹{abs(total):,.2f}")
