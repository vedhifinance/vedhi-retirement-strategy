import streamlit as st
import pandas as pd
import numpy as np
import pyotp
import pytz
from datetime import datetime, timedelta
import time

st.set_page_config(
    page_title="Vedhi Finance | Stock Scanner",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── All Nifty 50 — verified tokens + EQ suffix ────────────────────────────────
ALL_STOCKS = [
    {"symbol":"ADANIENT",   "token":"25",    "name":"Adani Enterprises"},
    {"symbol":"ADANIPORTS", "token":"15083", "name":"Adani Ports"},
    {"symbol":"APOLLOHOSP", "token":"157",   "name":"Apollo Hospitals"},
    {"symbol":"ASIANPAINT", "token":"236",   "name":"Asian Paints"},
    {"symbol":"AXISBANK",   "token":"5900",  "name":"Axis Bank"},
    {"symbol":"BAJAJ-AUTO", "token":"16669", "name":"Bajaj Auto"},
    {"symbol":"BAJFINANCE", "token":"317",   "name":"Bajaj Finance"},
    {"symbol":"BAJAJFINSV", "token":"16675", "name":"Bajaj Finserv"},
    {"symbol":"BEL",        "token":"383",   "name":"Bharat Electronics"},
    {"symbol":"BPCL",       "token":"526",   "name":"BPCL"},
    {"symbol":"BHARTIARTL", "token":"10604", "name":"Bharti Airtel"},
    {"symbol":"BRITANNIA",  "token":"547",   "name":"Britannia"},
    {"symbol":"CIPLA",      "token":"694",   "name":"Cipla"},
    {"symbol":"COALINDIA",  "token":"20374", "name":"Coal India"},
    {"symbol":"DRREDDY",    "token":"881",   "name":"Dr Reddy's"},
    {"symbol":"EICHERMOT",  "token":"910",   "name":"Eicher Motors"},
    {"symbol":"GRASIM",     "token":"1232",  "name":"Grasim"},
    {"symbol":"HCLTECH",    "token":"7229",  "name":"HCL Tech"},
    {"symbol":"HDFCBANK",   "token":"1333",  "name":"HDFC Bank"},
    {"symbol":"HDFCLIFE",   "token":"467",   "name":"HDFC Life"},
    {"symbol":"HEROMOTOCO", "token":"1348",  "name":"Hero MotoCorp"},
    {"symbol":"HINDALCO",   "token":"1363",  "name":"Hindalco"},
    {"symbol":"HINDUNILVR", "token":"1394",  "name":"HUL"},
    {"symbol":"ICICIBANK",  "token":"4963",  "name":"ICICI Bank"},
    {"symbol":"ITC",        "token":"1660",  "name":"ITC"},
    {"symbol":"INDUSINDBK", "token":"5258",  "name":"IndusInd Bank"},
    {"symbol":"INFY",       "token":"1594",  "name":"Infosys"},
    {"symbol":"JSWSTEEL",   "token":"11723", "name":"JSW Steel"},
    {"symbol":"KOTAKBANK",  "token":"1922",  "name":"Kotak Bank"},
    {"symbol":"LT",         "token":"11483", "name":"Larsen & Toubro"},
    {"symbol":"LTIM",       "token":"17818", "name":"LTIMindtree"},
    {"symbol":"M&M",        "token":"2031",  "name":"Mahindra & Mahindra"},
    {"symbol":"MARUTI",     "token":"10999", "name":"Maruti Suzuki"},
    {"symbol":"NESTLEIND",  "token":"17963", "name":"Nestle India"},
    {"symbol":"NTPC",       "token":"11630", "name":"NTPC"},
    {"symbol":"ONGC",       "token":"2475",  "name":"ONGC"},
    {"symbol":"POWERGRID",  "token":"14977", "name":"Power Grid"},
    {"symbol":"RELIANCE",   "token":"2885",  "name":"Reliance Industries"},
    {"symbol":"SBILIFE",    "token":"21808", "name":"SBI Life"},
    {"symbol":"SBIN",       "token":"3045",  "name":"State Bank of India"},
    {"symbol":"SUNPHARMA",  "token":"3351",  "name":"Sun Pharma"},
    {"symbol":"TCS",        "token":"11536", "name":"TCS"},
    {"symbol":"TATACONSUM", "token":"3432",  "name":"Tata Consumer"},
    {"symbol":"TATAMOTORS", "token":"3456",  "name":"Tata Motors"},
    {"symbol":"TATASTEEL",  "token":"3499",  "name":"Tata Steel"},
    {"symbol":"TECHM",      "token":"13538", "name":"Tech Mahindra"},
    {"symbol":"TITAN",      "token":"3506",  "name":"Titan"},
    {"symbol":"ULTRACEMCO", "token":"1624",  "name":"UltraTech Cement"},
    {"symbol":"WIPRO",      "token":"3787",  "name":"Wipro"},
    {"symbol":"ZOMATO",     "token":"5097",  "name":"Zomato"},
]

MY5 = ["SBIN","BEL","ICICIBANK","RELIANCE","LT"]
MY5_STOCKS = [s for s in ALL_STOCKS if s["symbol"] in MY5]

if "smart_api" not in st.session_state: st.session_state.smart_api = None
if "logged_in"  not in st.session_state: st.session_state.logged_in  = False

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔐 Angel One Login")
    st.caption("Credentials stay in your browser only.")
    api_key     = st.text_input("API Key",        type="password")
    client_id   = st.text_input("Client ID")
    password    = st.text_input("PIN / Password", type="password")
    totp_secret = st.text_input("TOTP Secret",    type="password")

    if st.button("🔗 Connect", use_container_width=True):
        if not all([api_key, client_id, password, totp_secret]):
            st.error("Fill in all 4 fields.")
        else:
            try:
                from SmartApi import SmartConnect
                obj  = SmartConnect(api_key=api_key)
                totp = pyotp.TOTP(totp_secret).now()
                data = obj.generateSession(client_id, password, totp)
                if data["status"]:
                    st.session_state.smart_api = obj
                    st.session_state.logged_in = True
                    st.success(f"✅ Connected — {client_id}")
                else:
                    st.error(f"Failed: {data.get('message','Unknown')}")
            except Exception as e:
                st.error(f"Error: {e}")

    if st.session_state.logged_in:
        st.divider()
        st.success("🟢 Angel One Connected")
        if st.button("Disconnect", use_container_width=True):
            st.session_state.smart_api = None
            st.session_state.logged_in = False
            st.rerun()

# ── Indicators ────────────────────────────────────────────────────────────────
def calc_rsi(s, p=14):
    d = s.diff()
    g = d.clip(lower=0).ewm(com=p-1, min_periods=p).mean()
    l = (-d.clip(upper=0)).ewm(com=p-1, min_periods=p).mean()
    return 100 - 100/(1 + g/l)

def calc_ema(s, p):
    return s.ewm(span=p, adjust=False).mean()

def analyse(obj, stock):
    try:
        ist      = pytz.timezone("Asia/Kolkata")
        to_dt    = datetime.now(ist).strftime("%Y-%m-%d %H:%M")
        fr_dt    = (datetime.now(ist) - timedelta(days=300)).strftime("%Y-%m-%d %H:%M")

        # Angel One requires SYMBOL-EQ format for tradingsymbol in candle API
        trading_symbol = stock["symbol"] + "-EQ"

        resp = obj.getCandleData({
            "exchange":    "NSE",
            "symboltoken": stock["token"],
            "interval":    "ONE_DAY",
            "fromdate":    fr_dt,
            "todate":      to_dt,
        })

        if not resp or not resp.get("status") or not resp.get("data"):
            return None
        if len(resp["data"]) < 60:
            return None

        df       = pd.DataFrame(resp["data"], columns=["ts","o","h","l","c","v"])
        df["c"]  = pd.to_numeric(df["c"])
        df["v"]  = pd.to_numeric(df["v"])
        df["o"]  = pd.to_numeric(df["o"])
        close    = df["c"]
        volume   = df["v"]

        r14   = calc_rsi(close, 14)
        e20   = calc_ema(close, 20)
        e50   = calc_ema(close, 50)
        e200  = calc_ema(close, 200) if len(close) >= 200 else calc_ema(close, len(close))
        vavg  = volume.rolling(20).mean()

        price     = float(close.iloc[-1])
        prev      = float(close.iloc[-2])
        chg_pct   = (price - prev) / prev * 100
        r_rsi     = float(r14.iloc[-1])
        r_e20     = float(e20.iloc[-1])
        r_e50     = float(e50.iloc[-1])
        r_e200    = float(e200.iloc[-1])
        vol_ratio = float(volume.iloc[-1]) / float(vavg.iloc[-1]) \
                    if float(vavg.iloc[-1]) > 0 else 0
        pct_200   = (price - r_e200) / r_e200 * 100
        last_open = float(df["o"].iloc[-1])
        candle    = "🟢 Green" if price >= last_open else "🔴 Red"

        f1 = 35 <= r_rsi <= 45
        f2 = price > r_e50
        f3 = r_e20 > r_e50
        f4 = vol_ratio >= 1.2
        f5 = price >= last_open
        passed = sum([f1, f2, f3, f4])

        if passed == 4 and f5:
            signal = "✅ BUY SETUP"
        elif passed == 4:
            signal = "⚠️ Watch (red candle)"
        elif passed >= 3 and f1:
            # RSI in zone + 2 other filters = genuine partial setup
            signal = "🔍 Partial — watch"
        elif not f1 and r_rsi > 60:
            # RSI overbought — already ran up, wait for pullback
            signal = "⏳ Wait — RSI overbought"
        elif not f1 and r_rsi < 35:
            # RSI too oversold — falling knife
            signal = "⚠️ RSI too low — wait"
        elif not f2 or not f3:
            signal = "❌ Avoid — trend weak"
        else:
            signal = "— Monitor"

        return {
            "Stock":     stock["symbol"],
            "LTP ₹":     round(price, 2),
            "Chg %":     round(chg_pct, 2),
            "RSI":       round(r_rsi, 1),
            "_rsi":      r_rsi,
            "EMA 20":    round(r_e20, 2),
            "EMA 50":    round(r_e50, 2),
            "EMA 200":   round(r_e200, 2),
            "% vs 200":  round(pct_200, 1),
            "Vol Ratio": round(vol_ratio, 2),
            "Candle":    candle,
            "Signal":    signal,
            "_passed":   passed,
            "_all_pass": passed == 4 and f5,
        }
    except Exception as e:
        return None

def trades_page():
    from trades_db import load_trades, save_trades
    import pytz
    from datetime import date

    st.title("📒 My Trades")
    st.caption("All trade records saved permanently to GitHub.")
    st.divider()

    # Load trades
    if "trades_data" not in st.session_state:
        with st.spinner("Loading trades..."):
            st.session_state.trades_data = load_trades()

    trades = st.session_state.trades_data

    tab_buy, tab_sell, tab_open, tab_closed = st.tabs([
        "🟢 Log Buy", "🔴 Close Trade", "📂 Open Trades", "📜 Closed Trades"
    ])

    # ── Log Buy ───────────────────────────────────────────────────────────────
    with tab_buy:
        st.subheader("Log a Buy Trade")
        with st.form("buy_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                ticker   = st.text_input("Ticker (e.g. SBIN)").upper().strip()
                buy_date = st.date_input("Buy Date", value=date.today())
                tranche  = st.selectbox("Tranche", ["1", "2", "3"])
            with c2:
                buy_rate  = st.number_input("Buy Rate (₹)", min_value=0.01, step=0.5, format="%.2f")
                qty       = st.number_input("Quantity", min_value=1, step=1)

            with c3:
                note = st.text_input("Note (optional)")
                if buy_rate > 0 and qty > 0:
                    invested = buy_rate * qty
                    sl       = buy_rate * 0.98
                    target   = buy_rate * 1.04
                    st.markdown(f"**Invested:** ₹{invested:,.2f}")
                    st.markdown(f"**Stop Loss (−2%):** ₹{sl:.2f}")
                    st.markdown(f"**Target (+4%):** ₹{target:.2f}")
                    # Show average price if this ticker already has open trades
                    if ticker:
                        existing = [t for t in trades
                                    if t.get("ticker") == ticker
                                    and t.get("status") == "open"]
                        if existing:
                            total_qty = sum(t["qty"] for t in existing) + qty
                            total_val = sum(t["buy_rate"] * t["qty"] for t in existing) + (buy_rate * qty)
                            avg       = total_val / total_qty
                            st.markdown(f"**📊 Avg Price (all tranches):** ₹{avg:.2f}")


            if st.form_submit_button("✅ Log Buy", use_container_width=True):
                if not ticker:
                    st.error("Enter a ticker.")
                elif buy_rate == 0 or qty == 0:
                    st.error("Rate and qty must be > 0.")
                else:
                    new_trade = {
                        "id":         len(trades) + 1,
                        "ticker":     ticker,
                        "tranche":    int(tranche[0]),
                        "buy_date":   str(buy_date),
                        "buy_rate":   round(buy_rate, 2),
                        "qty":        int(qty),
                        "invested":   round(buy_rate * qty, 2),
                        "stop_loss":  round(buy_rate * 0.98, 2),
                        "target":     round(buy_rate * 1.04, 2),

                        "sell_date":  None,
                        "sell_rate":  None,
                        "status":     "open",
                        "pnl":        None,
                        "pnl_after_brokerage": None,
                        "holding_days": None,
                        "note":       note,
                    }
                    trades.append(new_trade)
                    with st.spinner("Saving..."):
                        ok = save_trades(trades)
                    st.session_state.trades_data = trades
                    if ok:
                        st.success(
                            f"✅ {ticker} T{tranche[0]} saved  ·  "
                            f"Stop ₹{buy_rate*0.98:.2f}  ·  Target ₹{buy_rate*1.04:.2f}  ·  "
)
                    else:
                        st.warning("Trade logged locally but could not save to GitHub. Check your token.")
                    st.rerun()

    # ── Close Trade ───────────────────────────────────────────────────────────
    with tab_sell:
        open_trades = [t for t in trades if t.get("status") == "open"]
        if not open_trades:
            st.info("No open trades to close.")
        else:
            st.subheader("Close a Trade")
            df_open = pd.DataFrame(open_trades)[
                ["id","ticker","tranche","buy_date","buy_rate","qty","invested","stop_loss","target","brokerage"]
            ]
            st.dataframe(df_open, hide_index=True, use_container_width=True)

            with st.form("sell_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    trade_id  = st.number_input("Trade ID to close", min_value=1, step=1)
                    sell_date = st.date_input("Sell Date", value=date.today())
                with c2:
                    sell_rate      = st.number_input("Sell Rate (₹)", min_value=0.01,
                                                     step=0.5, format="%.2f")


                if st.form_submit_button("🔴 Close Trade", use_container_width=True):
                    match = [t for t in trades
                             if t["id"] == trade_id and t["status"] == "open"]
                    if not match:
                        st.error(f"No open trade with ID {trade_id}.")
                    else:
                        t    = match[0]
                        idx  = trades.index(t)
                        pnl  = round((sell_rate - t["buy_rate"]) * t["qty"], 2)
                        pnl_after = pnl
                        try:
                            days = (pd.to_datetime(sell_date) -
                                    pd.to_datetime(t["buy_date"])).days
                        except:
                            days = 0

                        trades[idx].update({
                            "sell_date":   str(sell_date),
                            "sell_rate":   round(sell_rate, 2),
                            "status":      "closed",
                            "pnl":         pnl,
                            "holding_days": days,
                        })
                        with st.spinner("Saving..."):
                            ok = save_trades(trades)
                        st.session_state.trades_data = trades
                        emoji = "🟢" if pnl_after >= 0 else "🔴"
                        st.success(
                            f"{emoji} Trade #{trade_id} closed  ·  "
                            f"P&L ₹{pnl:,.2f}  ·  "
                            f"{days} days held"
                        )
                        st.rerun()

    # ── Open Trades ───────────────────────────────────────────────────────────
    with tab_open:
        open_trades = [t for t in trades if t.get("status") == "open"]
        if not open_trades:
            st.info("No open trades.")
        else:
            st.subheader(f"{len(open_trades)} Open Trade(s)")
            df = pd.DataFrame(open_trades)[[
                "id","ticker","tranche","buy_date","buy_rate",
                "qty","invested","stop_loss","target","note"
            ]]
            st.dataframe(df, hide_index=True, use_container_width=True)

            total_invested = sum(t["invested"] for t in open_trades)
            st.metric("Total Invested", f"₹{total_invested:,.2f}")

    # ── Closed Trades ─────────────────────────────────────────────────────────
    with tab_closed:
        closed_trades = [t for t in trades if t.get("status") == "closed"]
        if not closed_trades:
            st.info("No closed trades yet.")
        else:
            st.subheader(f"{len(closed_trades)} Closed Trade(s)")
            df = pd.DataFrame(closed_trades)[[
                "id","ticker","tranche","buy_date","sell_date",
                "buy_rate","sell_rate","qty","invested",
                "pnl","holding_days"
            ]]
            st.dataframe(df, hide_index=True, use_container_width=True)

            total_pnl = sum(t["pnl"] or 0 for t in closed_trades)
            c1, c2 = st.columns(2)
            c1.metric("Total P&L", f"₹{total_pnl:,.2f}")
            c2.metric("Trades Closed", len(closed_trades))

        # Reload button
        if st.button("🔄 Reload from GitHub"):
            with st.spinner("Loading..."):
                st.session_state.trades_data = load_trades()
            st.success("Reloaded.")
            st.rerun()


# ── Header ─────────────────────────────────────────────────────────────────────
ist = pytz.timezone("Asia/Kolkata")
now_ist = datetime.now(ist).strftime("%d %b %Y, %I:%M %p IST")

st.title("📡 Vedhi Finance — Stock Scanner")
st.caption(f"Live NSE data via Angel One · RSI 35–45 · Price > EMA50 · EMA20 > EMA50 · Volume > 1.2× avg · {now_ist}")
st.divider()

if not st.session_state.logged_in:
    st.info("👈 Enter your Angel One credentials in the left sidebar and click Connect.")
    st.stop()

# Page navigation
page = st.radio("", ["📡 Scanner", "📒 My Trades"],
                horizontal=True, label_visibility="collapsed")
st.divider()

if page == "📒 My Trades":
    trades_page()
    st.stop()

# ── Controls ───────────────────────────────────────────────────────────────────
c1, c2 = st.columns([2, 3])
with c1:
    run_scan = st.button("🔍 Run Scanner", use_container_width=True)
with c2:
    mode = st.radio("Mode", ["My 5 Stocks", "All Nifty 50"], horizontal=True)

if run_scan:
    stocks_to_scan = MY5_STOCKS if mode == "My 5 Stocks" else ALL_STOCKS
    obj     = st.session_state.smart_api
    results = []
    errors  = []
    bar     = st.progress(0)

    for i, stock in enumerate(stocks_to_scan):
        bar.progress((i+1)/len(stocks_to_scan),
                     text=f"Fetching {stock['symbol']}...")
        # Try up to 3 times with increasing delay
        r = None
        for attempt in range(3):
            r = analyse(obj, stock)
            if r:
                break
            time.sleep(1.0 * (attempt + 1))  # 1s, 2s, 3s
        if r:
            results.append(r)
        else:
            errors.append(stock["symbol"])
        time.sleep(0.5)  # rate limit buffer between stocks
    bar.empty()

    if errors:
        st.caption(f"⚠️ Could not fetch: {', '.join(errors)}")

    if not results:
        st.error("No data returned. Session may have expired — reconnect from sidebar.")
        st.stop()

    results.sort(key=lambda x: (-x["_all_pass"], -x["_passed"]))

    buy_setups = sum(1 for r in results if r["_all_pass"])
    # Partial = RSI in zone + at least 2 other filters (genuine watch candidate)
    partial    = sum(1 for r in results
                     if not r["_all_pass"]
                     and r["_passed"] >= 3
                     and 35 <= r.get("_rsi", 0) <= 45)

    c1, c2, c3 = st.columns(3)
    c1.metric("Stocks Scanned",   len(results))
    c2.metric("✅ Buy Setups",    buy_setups)
    c3.metric("🔍 Partial (RSI in zone)", partial)

    st.divider()

    df = pd.DataFrame(results).drop(columns=["_passed","_all_pass","_rsi"])
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.caption(f"Scanned at {datetime.now(ist).strftime('%d %b %Y, %I:%M %p IST')} · Angel One NSE")

else:
    watching = " · ".join([s["symbol"] for s in MY5_STOCKS])
    st.info(f"Click **Run Scanner** to get live data · Watching: {watching}")


# ══════════════════════════════════════════════════════════════════════════════
# TRADES PAGE
# ══════════════════════════════════════════════════════════════════════════════
