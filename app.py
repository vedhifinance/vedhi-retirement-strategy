import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import date, datetime
import io

st.set_page_config(
    page_title="Vedhi Finance | Retirement Strategy",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
.block-container { padding-top: 1rem; padding-bottom: 1rem; }
div[data-testid="stMetric"] { background-color: #1e1e2e; border-radius: 8px; padding: 10px 16px; }
div[data-testid="stMetricValue"] { font-size: 1.4rem; font-weight: bold; }
.rule-box { background: #1e1e2e; border-left: 3px solid #1a9641; padding: 10px 16px;
            border-radius: 0 8px 8px 0; margin-bottom: 8px; font-size: 0.9rem; }
.badge-green { background: #1a9641; color: white; padding: 2px 8px;
               border-radius: 4px; font-size: 0.78rem; font-weight: bold; }
.badge-red   { background: #d7191c; color: white; padding: 2px 8px;
               border-radius: 4px; font-size: 0.78rem; font-weight: bold; }
.badge-blue  { background: #0077b6; color: white; padding: 2px 8px;
               border-radius: 4px; font-size: 0.78rem; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────

def _empty_treasury():
    return pd.DataFrame(columns=["Date", "Action", "Amount", "Note"])

def _empty_trades():
    return pd.DataFrame(columns=[
        "ID", "Ticker", "Tranche", "Buy Date", "Buy Rate", "Qty",
        "Invested", "Stop Loss", "Target",
        "Sell Date", "Sell Rate", "Status", "P&L", "Holding Days", "Note"
    ])

for key, default in [
    ("treasury_df", _empty_treasury()),
    ("trades_df",   _empty_trades()),
    ("page",        "Overview"),
    ("next_id",     1),
]:
    if key not in st.session_state:
        st.session_state[key] = default


def color_pnl(val):
    if isinstance(val, (int, float)):
        if val > 0:  return "color: #1a9641; font-weight: bold;"
        if val < 0:  return "color: #d7191c; font-weight: bold;"
    return ""


def treasury_balance():
    if st.session_state.treasury_df.empty:
        return 0.0
    return float(st.session_state.treasury_df["Amount"].sum())


# ── Header ─────────────────────────────────────────────────────────────────────

colA, colB = st.columns([9, 1])
with colA:
    st.markdown("<h4 style='color:#1a9641; margin-top:-10px; margin-bottom:0;'>"
                "Vedhi Finance | 💰 Retirement Strategy Dashboard</h4>",
                unsafe_allow_html=True)
with colB:
    if st.button("🔄 Reset"):
        for k in ["treasury_df", "trades_df", "next_id"]:
            st.session_state[k] = _empty_treasury() if k == "treasury_df" \
                                   else _empty_trades() if k == "trades_df" else 1
        st.rerun()

st.markdown("<hr style='margin-top:5px; margin-bottom:5px;'>", unsafe_allow_html=True)

# ── Nav ────────────────────────────────────────────────────────────────────────

n1, n2, n3, n4 = st.columns(4)
with n1:
    if st.button("📊 Overview",    use_container_width=True): st.session_state.page = "Overview"
with n2:
    if st.button("🏦 Treasury",    use_container_width=True): st.session_state.page = "Treasury"
with n3:
    if st.button("📈 Trades",      use_container_width=True): st.session_state.page = "Trades"
with n4:
    if st.button("📉 Analytics",   use_container_width=True): st.session_state.page = "Analytics"

st.markdown("<hr style='margin-top:5px; margin-bottom:10px;'>", unsafe_allow_html=True)
page = st.session_state.page


# ══════════════════════════════════════════════════════════════════════════════
# OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════

if page == "Overview":

    balance  = treasury_balance()
    liq      = balance * 0.40
    eq       = balance * 0.60
    liq_yld  = liq * 0.055

    tdf = st.session_state.trades_df
    closed   = tdf[tdf["Status"] == "closed"] if not tdf.empty else pd.DataFrame()
    open_t   = tdf[tdf["Status"] == "open"]   if not tdf.empty else pd.DataFrame()
    realized = float(closed["P&L"].sum()) if not closed.empty else 0.0
    combined = realized + liq_yld
    comb_pct = (combined / balance * 100) if balance else 0.0

    # ── Stat cards ──
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Treasury Balance",    f"₹{balance:,.2f}")
    c2.metric("Liquidcase 40%",      f"₹{liq:,.2f}")
    c3.metric("Equity Pool 60%",     f"₹{eq:,.2f}")
    c4.metric("Open Trades",         len(open_t))
    c5.metric("Realized P&L",        f"₹{realized:,.2f}",
              delta=f"{'↑' if realized >= 0 else '↓'} swing")
    c6.metric("Combined Return",     f"{comb_pct:.2f}%",
              delta=f"₹{combined:,.2f}")

    st.markdown("---")

    # ── Strategy rules ──
    st.markdown("#### 📋 Strategy Rules")
    rules = [
        ("🏦", "Treasury split",        "40% stays in <b>Liquidcase ETF</b> (5–6% p.a.)  ·  60% is the <b>Equity pool</b>"),
        ("🔁", "Capital recycling",     "All sale proceeds return to the <b>Treasury / Liquidcase</b>"),
        ("📊", "Entry — Tranche 1",     "RSI 35–40  ·  EMA 20–50 range  ·  Avg volume rising  ·  Last candle <b>green</b>"),
        ("➕", "Entry — Tranche 2",     "Stock falls <b>7%</b> from Tranche 1 buy price — add second position"),
        ("⚡", "Position size",         "Max <b>10% of equity pool</b> per trade — split across both tranches"),
        ("🛡️", "Stop loss",            "<b>2%</b> below buy rate — exits immediately on breach"),
        ("🎯", "Profit target",         "Minimum <b>4%</b> — activate trailing stop loss after reaching 4%"),
        ("⚖️", "Risk : Reward",        "<b>1 : 2</b>  (risk 2% → target 4%)"),
    ]
    for icon, label, detail in rules:
        st.markdown(
            f"<div class='rule-box'><b>{icon} {label}:</b> &nbsp; {detail}</div>",
            unsafe_allow_html=True
        )

    st.markdown("---")

    # ── Open positions ──
    st.markdown("#### 📂 Open Positions")
    if open_t.empty:
        st.info("No open trades. Go to 📈 Trades to log a buy.")
    else:
        show_cols = ["ID", "Ticker", "Tranche", "Buy Date", "Buy Rate",
                     "Qty", "Invested", "Stop Loss", "Target", "Note"]
        st.dataframe(open_t[show_cols].reset_index(drop=True),
                     hide_index=True, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TREASURY
# ══════════════════════════════════════════════════════════════════════════════

elif page == "Treasury":

    st.markdown("#### 🏦 Treasury Account")

    tab_add, tab_log, tab_io = st.tabs(["➕ Add Entry", "📜 Transaction Log", "⬆️ Import / Export"])

    with tab_add:
        with st.form("treasury_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                t_date   = st.date_input("Date", value=date.today())
                t_action = st.selectbox("Action", ["deposit", "withdrawal", "interest", "trade_return"])
            with col2:
                t_amount = st.number_input("Amount (₹)", min_value=0.01, step=100.0, format="%.2f")
                t_note   = st.text_input("Note (optional)")

            submitted = st.form_submit_button("Add Entry", use_container_width=True)
            if submitted:
                amt = t_amount if t_action != "withdrawal" else -t_amount
                new_row = pd.DataFrame([{
                    "Date": str(t_date), "Action": t_action,
                    "Amount": amt,       "Note": t_note
                }])
                st.session_state.treasury_df = pd.concat(
                    [st.session_state.treasury_df, new_row], ignore_index=True)
                st.success(f"Entry added — Balance now ₹{treasury_balance():,.2f}")
                st.rerun()

        balance = treasury_balance()
        liq = balance * 0.40
        eq  = balance * 0.60
        m1, m2, m3 = st.columns(3)
        m1.metric("Current Balance",  f"₹{balance:,.2f}")
        m2.metric("Liquidcase (40%)", f"₹{liq:,.2f}")
        m3.metric("Equity Pool (60%)",f"₹{eq:,.2f}")

    with tab_log:
        tdf = st.session_state.treasury_df
        if tdf.empty:
            st.info("No treasury entries yet.")
        else:
            styled = tdf.copy()
            styled["Amount"] = styled["Amount"].apply(lambda x: f"₹{x:,.2f}")
            st.dataframe(styled, hide_index=True, use_container_width=True)

            del_idx = st.number_input("Delete row (0-based index)", min_value=0,
                                      max_value=max(0, len(tdf)-1), step=1, key="del_treas")
            if st.button("Delete Row", key="del_treas_btn"):
                st.session_state.treasury_df = tdf.drop(index=del_idx).reset_index(drop=True)
                st.success("Row deleted.")
                st.rerun()

    with tab_io:
        st.markdown("**Export treasury log to CSV**")
        if not st.session_state.treasury_df.empty:
            csv = st.session_state.treasury_df.to_csv(index=False)
            st.download_button("⬇️ Download Treasury CSV", csv,
                               "treasury_log.csv", "text/csv", use_container_width=True)
        else:
            st.info("Nothing to export yet.")

        st.markdown("---")
        st.markdown("**Import treasury log from CSV**")
        uploaded = st.file_uploader("Upload treasury_log.csv", type="csv", key="up_treas")
        if uploaded:
            imported = pd.read_csv(uploaded)
            st.session_state.treasury_df = imported
            st.success(f"Imported {len(imported)} rows.")
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TRADES
# ══════════════════════════════════════════════════════════════════════════════

elif page == "Trades":

    st.markdown("#### 📈 Swing Trades")

    tab_buy, tab_sell, tab_all, tab_io = st.tabs(
        ["🟢 Log Buy", "🔴 Close Trade", "📋 All Trades", "⬆️ Import / Export"])

    balance  = treasury_balance()
    eq_pool  = balance * 0.60
    max_pos  = eq_pool * 0.10

    with tab_buy:
        if balance == 0:
            st.warning("Add funds to your Treasury first before logging trades.")
        else:
            st.info(f"Equity pool: ₹{eq_pool:,.2f}  ·  Max position (10%): ₹{max_pos:,.2f}")

        with st.form("buy_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                ticker   = st.text_input("Ticker (e.g. RELIANCE)").upper().strip()
                buy_date = st.date_input("Buy Date", value=date.today())
                tranche  = st.selectbox("Tranche", ["1 — Initial entry", "2 — −7% add-on"])
            with col2:
                buy_rate = st.number_input("Buy Rate (₹)", min_value=0.01, step=0.5, format="%.4f")
                qty      = st.number_input("Quantity (shares)", min_value=0.01, step=1.0, format="%.2f")
            with col3:
                note     = st.text_input("Note (e.g. RSI 38, EMA20 cross)")
                st.markdown(f"**Invested:** ₹{buy_rate * qty:,.2f}" if buy_rate and qty else "")
                st.markdown(f"**Stop loss:** ₹{buy_rate * 0.98:,.4f}" if buy_rate else "")
                st.markdown(f"**Target:** ₹{buy_rate * 1.04:,.4f}" if buy_rate else "")

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
                    st.success(f"✅ {ticker} T{tranche_num} logged  ·  Stop: ₹{sl}  ·  Target: ₹{target}")
                    st.rerun()

    with tab_sell:
        tdf = st.session_state.trades_df
        open_trades = tdf[tdf["Status"] == "open"] if not tdf.empty else pd.DataFrame()

        if open_trades.empty:
            st.info("No open trades to close.")
        else:
            st.dataframe(
                open_trades[["ID", "Ticker", "Tranche", "Buy Date", "Buy Rate", "Qty", "Invested", "Stop Loss", "Target"]].reset_index(drop=True),
                hide_index=True, use_container_width=True
            )

            with st.form("sell_form", clear_on_submit=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    trade_id_sel = st.number_input("Trade ID to close", min_value=1, step=1)
                    sell_date    = st.date_input("Sell Date", value=date.today())
                with col2:
                    sell_rate    = st.number_input("Sell Rate (₹)", min_value=0.01, step=0.5, format="%.4f")
                with col3:
                    return_treas = st.checkbox("Return proceeds to Treasury", value=True)

                submitted = st.form_submit_button("Close Trade 🔴", use_container_width=True)
                if submitted:
                    match = tdf[(tdf["ID"] == trade_id_sel) & (tdf["Status"] == "open")]
                    if match.empty:
                        st.error(f"No open trade with ID {trade_id_sel}.")
                    else:
                        idx = match.index[0]
                        row = tdf.loc[idx]
                        pnl  = round((sell_rate - float(row["Buy Rate"])) * float(row["Qty"]), 2)
                        sell_amt = round(sell_rate * float(row["Qty"]), 2)
                        try:
                            days = (pd.to_datetime(sell_date).date() -
                                    pd.to_datetime(row["Buy Date"]).date()).days
                        except:
                            days = 0

                        st.session_state.trades_df.at[idx, "Sell Date"]    = str(sell_date)
                        st.session_state.trades_df.at[idx, "Sell Rate"]    = sell_rate
                        st.session_state.trades_df.at[idx, "Status"]       = "closed"
                        st.session_state.trades_df.at[idx, "P&L"]          = pnl
                        st.session_state.trades_df.at[idx, "Holding Days"] = days

                        if return_treas:
                            note_txt = f"Trade #{trade_id_sel} {row['Ticker']} close — sell ₹{sell_amt:,.2f}  (P&L ₹{pnl:,.2f})"
                            new_row  = pd.DataFrame([{
                                "Date": str(sell_date), "Action": "trade_return",
                                "Amount": sell_amt,     "Note": note_txt
                            }])
                            st.session_state.treasury_df = pd.concat(
                                [st.session_state.treasury_df, new_row], ignore_index=True)

                        emoji = "🟢" if pnl >= 0 else "🔴"
                        st.success(f"{emoji} Trade #{trade_id_sel} closed  ·  P&L ₹{pnl:,.2f}  ·  {days} days held")
                        st.rerun()

    with tab_all:
        tdf = st.session_state.trades_df
        if tdf.empty:
            st.info("No trades logged yet.")
        else:
            display = tdf.copy()
            display["P&L"] = display["P&L"].apply(
                lambda x: f"₹{x:,.2f}" if pd.notna(x) else "—")
            display["Invested"] = display["Invested"].apply(lambda x: f"₹{x:,.2f}")
            display["Buy Rate"] = display["Buy Rate"].apply(lambda x: f"₹{x:.4f}")
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

    balance  = treasury_balance()
    liq      = balance * 0.40
    eq       = balance * 0.60
    liq_yld  = liq * 0.055
    max_pos  = eq * 0.10

    tdf    = st.session_state.trades_df
    closed = tdf[tdf["Status"] == "closed"] if not tdf.empty else pd.DataFrame()
    open_t = tdf[tdf["Status"] == "open"]   if not tdf.empty else pd.DataFrame()

    wins   = closed[closed["P&L"] > 0] if not closed.empty else pd.DataFrame()
    losses = closed[closed["P&L"] <= 0] if not closed.empty else pd.DataFrame()

    total_pnl  = float(closed["P&L"].sum())   if not closed.empty else 0.0
    avg_win    = float(wins["P&L"].mean())     if not wins.empty   else 0.0
    avg_loss   = float(losses["P&L"].mean())   if not losses.empty else 0.0
    avg_days   = float(closed["Holding Days"].mean()) if not closed.empty else 0.0
    win_rate   = len(wins) / len(closed) * 100 if not closed.empty else 0.0
    combined   = total_pnl + liq_yld
    comb_pct   = combined / balance * 100 if balance else 0.0

    tab_summary, tab_charts, tab_history = st.tabs(
        ["📋 Summary", "📊 Charts", "📜 Closed Trade History"])

    with tab_summary:
        c1, c2, c3 = st.columns(3)
        c1.metric("Treasury Balance",    f"₹{balance:,.2f}")
        c2.metric("Liquidcase (40%)",    f"₹{liq:,.2f}")
        c3.metric("Equity Pool (60%)",   f"₹{eq:,.2f}")

        c4, c5, c6 = st.columns(3)
        c4.metric("Max Position / Trade", f"₹{max_pos:,.2f}")
        c5.metric("Liquidcase Yield (est. 5.5%)", f"₹{liq_yld:,.2f}")
        c6.metric("Total Trades",         len(tdf) if not tdf.empty else 0)

        c7, c8, c9 = st.columns(3)
        c7.metric("Closed Trades",  len(closed))
        c8.metric("Win Rate",       f"{win_rate:.1f}%")
        c9.metric("Open Trades",    len(open_t))

        c10, c11, c12 = st.columns(3)
        c10.metric("Avg Win",       f"₹{avg_win:,.2f}")
        c11.metric("Avg Loss",      f"₹{avg_loss:,.2f}")
        c12.metric("Avg Holding",   f"{avg_days:.1f} days")

        c13, c14 = st.columns(2)
        c13.metric("Total Realized P&L (Swing)", f"₹{total_pnl:,.2f}",
                   delta=f"{'profit' if total_pnl >= 0 else 'loss'}")
        c14.metric("Combined Return (Liquidcase + Swing)",
                   f"₹{combined:,.2f}",
                   delta=f"{comb_pct:.2f}% of treasury")

    with tab_charts:

        if closed.empty:
            st.info("Close some trades to see charts.")
        else:
            # P&L per trade bar chart
            fig1 = go.Figure()
            colors = ["#1a9641" if v >= 0 else "#d7191c"
                      for v in closed["P&L"].values]
            fig1.add_trace(go.Bar(
                x=closed["Ticker"].astype(str) + " T" + closed["Tranche"].astype(str),
                y=closed["P&L"],
                marker_color=colors,
                text=[f"₹{v:,.2f}" for v in closed["P&L"]],
                textposition="outside"
            ))
            fig1.update_layout(
                title="P&L per Closed Trade",
                template="plotly_dark",
                height=350,
                margin=dict(l=20, r=20, t=40, b=20),
                yaxis_title="P&L (₹)"
            )
            st.plotly_chart(fig1, use_container_width=True)

            # Cumulative P&L line
            cum_pnl = closed["P&L"].cumsum().values
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=list(range(1, len(cum_pnl)+1)),
                y=cum_pnl,
                mode="lines+markers",
                line=dict(color="#1a9641", width=2),
                fill="tozeroy",
                fillcolor="rgba(26,150,65,0.15)"
            ))
            fig2.update_layout(
                title="Cumulative Swing Trade P&L",
                template="plotly_dark",
                height=300,
                margin=dict(l=20, r=20, t=40, b=20),
                xaxis_title="Trade #",
                yaxis_title="Cumulative P&L (₹)"
            )
            st.plotly_chart(fig2, use_container_width=True)

        # Combined 10-year projection
        st.markdown("---")
        st.markdown("##### 📆 10-Year Projection")
        col1, col2, col3 = st.columns(3)
        proj_trades  = col1.slider("Trades / year",    1, 52, 12)
        proj_winrate = col2.slider("Win rate (%)",     30, 90, 60)
        proj_avgwin  = col3.slider("Avg win (%)",       4, 20,  6)

        proj_liq  = liq if liq > 0 else 100000
        proj_eq   = eq  if eq  > 0 else 150000

        years, liq_data, swing_data, cum_liq, cum_swing = [], [], [], [], []
        rl, rs = 0, 0
        for y in range(1, 11):
            lp = proj_liq * 0.055
            wins_n  = round(proj_trades * proj_winrate / 100)
            loss_n  = proj_trades - wins_n
            sp = max(0, wins_n * (proj_eq * 0.10) * (proj_avgwin / 100)
                        - loss_n * (proj_eq * 0.10) * 0.02)
            rl += lp; rs += sp
            years.append(f"Yr {y}")
            liq_data.append(round(lp, 2))
            swing_data.append(round(sp, 2))
            cum_liq.append(round(rl, 2))
            cum_swing.append(round(rs, 2))

        fig3 = go.Figure()
        fig3.add_trace(go.Bar(name="Liquidcase Yield", x=years, y=liq_data,
                              marker_color="#0077b6"))
        fig3.add_trace(go.Bar(name="Swing Profit",     x=years, y=swing_data,
                              marker_color="#1a9641"))
        fig3.update_layout(
            barmode="group", title="Annual Projection — Liquidcase vs Swing",
            template="plotly_dark", height=350,
            margin=dict(l=20, r=20, t=40, b=20),
            yaxis_title="₹"
        )
        st.plotly_chart(fig3, use_container_width=True)

        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(x=years, y=cum_liq,
                                  name="Cumulative Liquidcase",
                                  line=dict(color="#0077b6", width=2)))
        fig4.add_trace(go.Scatter(x=years, y=cum_swing,
                                  name="Cumulative Swing",
                                  line=dict(color="#1a9641", width=2)))
        fig4.add_trace(go.Scatter(x=years,
                                  y=[a+b for a,b in zip(cum_liq, cum_swing)],
                                  name="Combined",
                                  line=dict(color="#f4a261", width=2, dash="dot")))
        fig4.update_layout(
            title="Cumulative 10-Year Growth",
            template="plotly_dark", height=350,
            margin=dict(l=20, r=20, t=40, b=20),
            yaxis_title="₹"
        )
        st.plotly_chart(fig4, use_container_width=True)

    with tab_history:
        if closed.empty:
            st.info("No closed trades yet.")
        else:
            display = closed[["ID","Ticker","Tranche","Buy Date","Sell Date",
                               "Buy Rate","Sell Rate","Qty","Invested","P&L","Holding Days"]].copy()
            display["P&L"] = display["P&L"].apply(lambda x: f"₹{x:,.2f}" if pd.notna(x) else "—")
            display["Invested"] = display["Invested"].apply(lambda x: f"₹{x:,.2f}")
            st.dataframe(display.reset_index(drop=True),
                         hide_index=True, use_container_width=True)
            total = float(closed["P&L"].sum())
            if total >= 0:
                st.success(f"Total Realized Profit: ₹{total:,.2f}")
            else:
                st.error(f"Total Realized Loss: ₹{abs(total):,.2f}")
