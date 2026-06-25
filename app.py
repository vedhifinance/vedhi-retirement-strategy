import streamlit as st
import pandas as pd
import numpy as np
import pyotp
import pytz
import json
import os
from datetime import datetime, timedelta, date
import time

st.set_page_config(
    page_title="Vedhi Finance | Stock Scanner",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0f1117; }
    .metric-card {
        background: #1a1d27;
        border: 1px solid #2a2d3e;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.5rem;
    }
    .profit-positive { color: #00c896; font-weight: 600; }
    .profit-negative { color: #ff4b6e; font-weight: 600; }
    .section-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #a0aec0;
        margin: 1rem 0 0.5rem 0;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-size: 0.75rem;
    }
    div[data-testid="stTabs"] button {
        font-size: 0.95rem;
        font-weight: 500;
    }
    .stDataFrame { border-radius: 10px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
PORTFOLIO_FILE = "vedhi_portfolio.json"
HISTORY_FILE   = "vedhi_history.json"
BROKERAGE_RATE = 0.0003   # 0.03% each side (Angel One approx)
STT_RATE       = 0.001    # 0.1% on sell side
EXCHANGE_RATE  = 0.0000335
SEBI_RATE      = 0.000001
STAMP_RATE     = 0.00015  # on buy side

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

# ── Session state ──────────────────────────────────────────────────────────────
if "smart_api" not in st.session_state: st.session_state.smart_api = None
if "logged_in"  not in st.session_state: st.session_state.logged_in  = False

# ── Portfolio persistence helpers ──────────────────────────────────────────────
def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, "r") as f:
            return json.load(f)
    return []

def save_portfolio(data):
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_history(data):
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ── Brokerage calculator ───────────────────────────────────────────────────────
def calc_brokerage(buy_price, sell_price, qty):
    buy_val  = buy_price  * qty
    sell_val = sell_price * qty
    brok_buy  = min(buy_val  * BROKERAGE_RATE, 20)   # Angel One max ₹20/order
    brok_sell = min(sell_val * BROKERAGE_RATE, 20)
    stt       = sell_val * STT_RATE
    exchange  = (buy_val + sell_val) * EXCHANGE_RATE
    sebi      = (buy_val + sell_val) * SEBI_RATE
    stamp     = buy_val * STAMP_RATE
    total     = brok_buy + brok_sell + stt + exchange + sebi + stamp
    return round(total, 2), round(brok_buy + brok_sell, 2), round(stt, 2)

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
        ist   = pytz.timezone("Asia/Kolkata")
        to_dt = datetime.now(ist).strftime("%Y-%m-%d %H:%M")
        fr_dt = (datetime.now(ist) - timedelta(days=300)).strftime("%Y-%m-%d %H:%M")

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

        df      = pd.DataFrame(resp["data"], columns=["ts","o","h","l","c","v"])
        df["c"] = pd.to_numeric(df["c"])
        df["v"] = pd.to_numeric(df["v"])
        df["o"] = pd.to_numeric(df["o"])
        close   = df["c"]
        volume  = df["v"]

        r14  = calc_rsi(close, 14)
        e20  = calc_ema(close, 20)
        e50  = calc_ema(close, 50)
        e200 = calc_ema(close, 200) if len(close) >= 200 else calc_ema(close, len(close))
        vavg = volume.rolling(20).mean()

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
            signal = "🔍 Partial — watch"
        elif not f1 and r_rsi > 60:
            signal = "⏳ Wait — RSI overbought"
        elif not f1 and r_rsi < 35:
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
    except Exception:
        return None

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

# ── Header ─────────────────────────────────────────────────────────────────────
ist     = pytz.timezone("Asia/Kolkata")
now_ist = datetime.now(ist).strftime("%d %b %Y, %I:%M %p IST")

st.title("📡 Vedhi Finance")
st.caption(f"Stock Scanner + Portfolio Tracker · {now_ist}")
st.divider()

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_scan, tab_port, tab_hist = st.tabs([
    "🔍 Stock Scanner",
    "📊 Portfolio Tracker",
    "📜 Trade History"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — SCANNER (unchanged logic)
# ══════════════════════════════════════════════════════════════════════════════
with tab_scan:
    st.markdown('<p class="section-header">Scanner Controls</p>', unsafe_allow_html=True)

    if not st.session_state.logged_in:
        st.info("👈 Connect Angel One from the sidebar to run the scanner.")
    else:
        c1, c2 = st.columns([2, 3])
        with c1:
            run_scan = st.button("🔍 Run Scanner", use_container_width=True)
        with c2:
            mode = st.radio("Mode", ["My 5 Stocks", "All Nifty 50"], horizontal=True)

        st.caption("Strategy: RSI 35–45 · Price > EMA50 · EMA20 > EMA50 · Volume > 1.2× avg")

        if run_scan:
            stocks_to_scan = MY5_STOCKS if mode == "My 5 Stocks" else ALL_STOCKS
            obj     = st.session_state.smart_api
            results = []
            errors  = []
            bar     = st.progress(0)

            for i, stock in enumerate(stocks_to_scan):
                bar.progress((i+1)/len(stocks_to_scan),
                             text=f"Fetching {stock['symbol']}...")
                r = None
                for attempt in range(3):
                    r = analyse(obj, stock)
                    if r:
                        break
                    time.sleep(1.0 * (attempt + 1))
                if r:
                    results.append(r)
                else:
                    errors.append(stock["symbol"])
                time.sleep(0.5)
            bar.empty()

            if errors:
                st.caption(f"⚠️ Could not fetch: {', '.join(errors)}")

            if not results:
                st.error("No data returned. Session may have expired — reconnect.")
                st.stop()

            results.sort(key=lambda x: (-x["_all_pass"], -x["_passed"]))

            buy_setups = sum(1 for r in results if r["_all_pass"])
            partial    = sum(1 for r in results if r["_passed"] >= 3 and not r["_all_pass"])

            m1, m2, m3 = st.columns(3)
            m1.metric("Stocks Scanned",   len(results))
            m2.metric("✅ Buy Setups",    buy_setups)
            m3.metric("⚠️ Partial Match", partial)
            st.divider()

            df_scan = pd.DataFrame(results).drop(columns=["_passed","_all_pass"])
            st.dataframe(df_scan, use_container_width=True, hide_index=True)
            st.caption(f"Scanned at {datetime.now(ist).strftime('%d %b %Y, %I:%M %p IST')}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — PORTFOLIO TRACKER
# ══════════════════════════════════════════════════════════════════════════════
with tab_port:

    portfolio = load_portfolio()
    history   = load_history()

    # ── Summary metrics ────────────────────────────────────────────────────────
    st.markdown('<p class="section-header">Current Holdings</p>', unsafe_allow_html=True)

    if portfolio:
        total_invested = sum(h["qty"] * h["avg_price"] for h in portfolio)
        # Current value — use LTP if available, else avg_price
        total_current  = sum(h["qty"] * h.get("ltp", h["avg_price"]) for h in portfolio)
        total_pnl      = total_current - total_invested
        total_pnl_pct  = (total_pnl / total_invested * 100) if total_invested else 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Invested",  f"₹{total_invested:,.0f}")
        m2.metric("Current Value",   f"₹{total_current:,.0f}")
        m3.metric("Unrealised P&L",
                  f"₹{total_pnl:,.0f}",
                  delta=f"{total_pnl_pct:.2f}%")
        m4.metric("Holdings",        len(portfolio))
        st.divider()

    # ── Add new position ───────────────────────────────────────────────────────
    with st.expander("➕ Add New Position", expanded=len(portfolio) == 0):
        st.markdown('<p class="section-header">Enter Trade Details</p>', unsafe_allow_html=True)

        all_symbols = sorted([s["symbol"] for s in ALL_STOCKS])
        # Also allow free-text for stocks not in Nifty 50
        col1, col2 = st.columns(2)
        with col1:
            symbol_select = st.selectbox("Stock Symbol (Nifty 50)", [""] + all_symbols)
            symbol_custom = st.text_input("Or type custom symbol", placeholder="e.g. ONGC, NTPC")
            symbol = (symbol_custom.strip().upper() if symbol_custom.strip()
                      else symbol_select)
        with col2:
            buy_date = st.date_input("Buy Date", value=date.today())
            qty      = st.number_input("Quantity (shares)", min_value=1, value=1, step=1)

        col3, col4 = st.columns(2)
        with col3:
            avg_price = st.number_input("Buy Price (₹ per share)", min_value=0.01,
                                        value=100.00, step=0.05, format="%.2f")
        with col4:
            ltp = st.number_input("Current LTP ₹ (optional, for live P&L)",
                                  min_value=0.0, value=0.0, step=0.05, format="%.2f")

        notes = st.text_input("Notes (optional)", placeholder="e.g. SMA 200 bounce entry")

        # Brokerage preview
        if avg_price > 0 and qty > 0:
            buy_val = avg_price * qty
            brok_preview = min(buy_val * BROKERAGE_RATE, 20)
            stamp_preview = buy_val * STAMP_RATE
            st.caption(f"Est. buy-side cost: Brokerage ₹{brok_preview:.2f} + Stamp ₹{stamp_preview:.2f}"
                       f" = ₹{brok_preview+stamp_preview:.2f}")

        if st.button("💾 Add to Portfolio", use_container_width=True):
            if not symbol:
                st.error("Please select or enter a stock symbol.")
            else:
                holding_days = (date.today() - buy_date).days
                new_pos = {
                    "symbol":       symbol,
                    "qty":          int(qty),
                    "avg_price":    round(float(avg_price), 2),
                    "buy_date":     str(buy_date),
                    "holding_days": holding_days,
                    "ltp":          round(float(ltp), 2) if ltp > 0 else round(float(avg_price), 2),
                    "notes":        notes,
                    "added_on":     str(date.today()),
                }
                # If same symbol exists, ask to merge (average down/up)
                existing = [p for p in portfolio if p["symbol"] == symbol]
                if existing:
                    # Weighted average
                    ex = existing[0]
                    total_qty   = ex["qty"] + int(qty)
                    new_avg     = (ex["qty"] * ex["avg_price"] + int(qty) * float(avg_price)) / total_qty
                    ex["qty"]       = total_qty
                    ex["avg_price"] = round(new_avg, 2)
                    ex["holding_days"] = (date.today() - date.fromisoformat(ex["buy_date"])).days
                    if ltp > 0:
                        ex["ltp"] = round(float(ltp), 2)
                    if notes:
                        ex["notes"] = (ex.get("notes","") + " | " + notes).strip(" | ")
                    st.success(f"✅ Averaged {symbol} — new avg ₹{new_avg:.2f} × {total_qty} shares")
                else:
                    portfolio.append(new_pos)
                    st.success(f"✅ Added {symbol} — {qty} shares @ ₹{avg_price:.2f}")

                save_portfolio(portfolio)
                st.rerun()

    # ── Holdings table ─────────────────────────────────────────────────────────
    if portfolio:
        st.markdown('<p class="section-header">Holdings Detail</p>', unsafe_allow_html=True)

        rows = []
        for h in portfolio:
            qty_h      = h["qty"]
            avg_h      = h["avg_price"]
            ltp_h      = h.get("ltp", avg_h)
            invested   = qty_h * avg_h
            curr_val   = qty_h * ltp_h
            unreal_pnl = curr_val - invested
            unreal_pct = (unreal_pnl / invested * 100) if invested else 0
            hdays      = (date.today() - date.fromisoformat(h["buy_date"])).days

            rows.append({
                "Symbol":        h["symbol"],
                "Qty":           qty_h,
                "Avg Price ₹":   avg_h,
                "LTP ₹":         ltp_h,
                "Invested ₹":    round(invested, 2),
                "Curr Value ₹":  round(curr_val, 2),
                "P&L ₹":         round(unreal_pnl, 2),
                "P&L %":         round(unreal_pct, 2),
                "Holding Days":  hdays,
                "Buy Date":      h["buy_date"],
                "Notes":         h.get("notes",""),
            })

        df_port = pd.DataFrame(rows)

        # Colour coding
        def colour_pnl(val):
            color = "#00c896" if val >= 0 else "#ff4b6e"
            return f"color: {color}; font-weight: 600"

        styled = df_port.style.map(colour_pnl, subset=["P&L ₹","P&L %"])
        st.dataframe(styled, use_container_width=True, hide_index=True)

        # ── Update LTP + Sell ──────────────────────────────────────────────────
        st.divider()
        st.markdown('<p class="section-header">Update LTP / Sell Position</p>',
                    unsafe_allow_html=True)

        symbols_held = [h["symbol"] for h in portfolio]
        sel_symbol   = st.selectbox("Select holding", symbols_held, key="sel_sym")
        sel_holding  = next((h for h in portfolio if h["symbol"] == sel_symbol), None)

        if sel_holding:

            # ── Row 1: Update LTP ──────────────────────────────────────────────
            st.markdown("**① Update current price (LTP)**")
            ltp_col1, ltp_col2 = st.columns([2, 1])
            with ltp_col1:
                new_ltp = st.number_input(
                    f"LTP for {sel_symbol} ₹",
                    min_value=0.01,
                    value=float(sel_holding.get("ltp", sel_holding["avg_price"])),
                    step=0.05, format="%.2f",
                    key="ltp_input"
                )
            with ltp_col2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🔄 Update LTP", use_container_width=True):
                    for h in portfolio:
                        if h["symbol"] == sel_symbol:
                            h["ltp"] = round(float(new_ltp), 2)
                    save_portfolio(portfolio)
                    st.success(f"✅ LTP updated → ₹{new_ltp:.2f}")
                    st.rerun()

            st.divider()

            # ── Row 2: Sell ────────────────────────────────────────────────────
            st.markdown("**② Sell this position**")

            sell_col1, sell_col2, sell_col3 = st.columns(3)
            with sell_col1:
                sell_qty = st.number_input(
                    "Sell Quantity",
                    min_value=1,
                    max_value=sel_holding["qty"],
                    value=sel_holding["qty"],
                    step=1,
                    key="sell_qty"
                )
            with sell_col2:
                # Use LTP if it differs from avg_price, else default to avg_price
                _ltp_val = sel_holding.get("ltp", sel_holding["avg_price"])
                _sell_default = float(_ltp_val) if float(_ltp_val) != float(sel_holding["avg_price"]) else float(sel_holding["avg_price"])
                sell_price = st.number_input(
                    "Sell Price ₹  ← enter your actual sell price",
                    min_value=0.01,
                    value=_sell_default,
                    step=0.05, format="%.2f",
                    key="sell_price"
                )
            with sell_col3:
                sell_date = st.date_input("Sell Date", value=date.today(), key="sell_date")

            # Live P&L breakdown — always visible
            gross_pnl    = (sell_price - sel_holding["avg_price"]) * sell_qty
            total_brok, brok_only, stt_only = calc_brokerage(
                sel_holding["avg_price"], sell_price, sell_qty)
            net_pnl      = gross_pnl - total_brok
            invested_sel = sel_holding["avg_price"] * sell_qty
            net_pnl_pct  = (net_pnl / invested_sel * 100) if invested_sel else 0
            hold_days    = (sell_date - date.fromisoformat(sel_holding["buy_date"])).days

            st.markdown("**📊 P&L Breakdown**")
            pc1, pc2, pc3, pc4, pc5, pc6, pc7 = st.columns(7)
            pc1.metric("Invested ₹",  f"{invested_sel:,.2f}")
            pc2.metric("Gross P&L ₹", f"{gross_pnl:,.2f}",
                       delta=f"{gross_pnl/invested_sel*100:.2f}%" if invested_sel else "0%")
            pc3.metric("Brokerage ₹", f"{brok_only:.2f}")
            pc4.metric("STT ₹",        f"{stt_only:.2f}")
            pc5.metric("Other ₹",      f"{total_brok - brok_only - stt_only:.2f}")
            pc6.metric("Net P&L ₹",   f"{net_pnl:,.2f}",
                       delta=f"{net_pnl_pct:.2f}%")
            pc7.metric("Held",         f"{hold_days} days")

            if st.button("✅ Confirm Sell & Record to History",
                         use_container_width=True, type="primary", key="confirm_sell"):
                trade_record = {
                    "symbol":       sel_symbol,
                    "buy_date":     sel_holding["buy_date"],
                    "sell_date":    str(sell_date),
                    "holding_days": hold_days,
                    "qty":          int(sell_qty),
                    "buy_price":    sel_holding["avg_price"],
                    "sell_price":   round(float(sell_price), 2),
                    "invested":     round(invested_sel, 2),
                    "gross_pnl":    round(gross_pnl, 2),
                    "brokerage":    round(total_brok, 2),
                    "net_pnl":      round(net_pnl, 2),
                    "net_pnl_pct":  round(net_pnl_pct, 2),
                    "notes":        sel_holding.get("notes",""),
                    "recorded_on":  str(date.today()),
                }
                history.append(trade_record)
                save_history(history)

                if int(sell_qty) >= sel_holding["qty"]:
                    portfolio = [h for h in portfolio if h["symbol"] != sel_symbol]
                else:
                    for h in portfolio:
                        if h["symbol"] == sel_symbol:
                            h["qty"] -= int(sell_qty)
                save_portfolio(portfolio)

                emoji = "🟢" if net_pnl >= 0 else "🔴"
                st.success(f"{emoji} Sold {sell_qty} × {sel_symbol} @ ₹{sell_price:.2f} "
                           f"| Net P&L: ₹{net_pnl:,.2f} ({net_pnl_pct:.2f}%)")
                st.rerun()

        # ── Delete a holding ───────────────────────────────────────────────────
        st.divider()
        with st.expander("🗑️ Remove a holding without recording a sale"):
            del_symbol = st.selectbox("Select to remove", symbols_held, key="del_sym")
            if st.button("Remove from portfolio", type="secondary", key="del_btn"):
                portfolio = [h for h in portfolio if h["symbol"] != del_symbol]
                save_portfolio(portfolio)
                st.warning(f"Removed {del_symbol} from portfolio.")
                st.rerun()

    else:
        st.info("No holdings yet. Use **Add New Position** above to get started.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — TRADE HISTORY
# ══════════════════════════════════════════════════════════════════════════════
with tab_hist:
    history = load_history()

    st.markdown('<p class="section-header">Closed Trade History</p>', unsafe_allow_html=True)

    if not history:
        st.info("No closed trades yet. Sell a position from the Portfolio Tracker tab to record history.")
    else:
        # Summary
        total_net    = sum(h["net_pnl"] for h in history)
        total_winners = sum(1 for h in history if h["net_pnl"] >= 0)
        total_losers  = len(history) - total_winners
        win_rate      = (total_winners / len(history) * 100) if history else 0
        total_brok    = sum(h["brokerage"] for h in history)
        avg_hold      = sum(h["holding_days"] for h in history) / len(history)

        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Total Trades",    len(history))
        m2.metric("Net P&L",         f"₹{total_net:,.0f}")
        m3.metric("Win Rate",         f"{win_rate:.0f}%")
        m4.metric("Winners",          total_winners)
        m5.metric("Losers",           total_losers)
        m6.metric("Avg Hold Days",    f"{avg_hold:.0f}d")

        st.divider()

        # Best and worst trade
        if len(history) > 0:
            best  = max(history, key=lambda x: x["net_pnl"])
            worst = min(history, key=lambda x: x["net_pnl"])
            bc, wc = st.columns(2)
            with bc:
                st.success(f"🏆 Best trade: **{best['symbol']}** — "
                           f"₹{best['net_pnl']:,.2f} ({best['net_pnl_pct']:.2f}%) "
                           f"in {best['holding_days']}d")
            with wc:
                st.error(f"📉 Worst trade: **{worst['symbol']}** — "
                         f"₹{worst['net_pnl']:,.2f} ({worst['net_pnl_pct']:.2f}%) "
                         f"in {worst['holding_days']}d")

        st.divider()

        # Full history table
        df_hist = pd.DataFrame(history)
        df_hist = df_hist[[
            "symbol","buy_date","sell_date","holding_days",
            "qty","buy_price","sell_price",
            "invested","gross_pnl","brokerage","net_pnl","net_pnl_pct","notes"
        ]].rename(columns={
            "symbol":       "Symbol",
            "buy_date":     "Buy Date",
            "sell_date":    "Sell Date",
            "holding_days": "Days",
            "qty":          "Qty",
            "buy_price":    "Buy ₹",
            "sell_price":   "Sell ₹",
            "invested":     "Invested ₹",
            "gross_pnl":    "Gross P&L ₹",
            "brokerage":    "Brokerage ₹",
            "net_pnl":      "Net P&L ₹",
            "net_pnl_pct":  "Net P&L %",
            "notes":        "Notes",
        })
        df_hist = df_hist.sort_values("Sell Date", ascending=False)

        def colour_hist(val):
            color = "#00c896" if val >= 0 else "#ff4b6e"
            return f"color: {color}; font-weight: 600"

        styled_hist = df_hist.style.map(
            colour_hist, subset=["Net P&L ₹","Net P&L %","Gross P&L ₹"])
        st.dataframe(styled_hist, use_container_width=True, hide_index=True)

        # ── Export ─────────────────────────────────────────────────────────────
        st.divider()
        col_exp1, col_exp2 = st.columns(2)
        with col_exp1:
            csv = df_hist.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Download History as CSV",
                data=csv,
                file_name=f"vedhi_trade_history_{date.today()}.csv",
                mime="text/csv",
                use_container_width=True
            )
        with col_exp2:
            # Clear all history
            if st.button("🗑️ Clear All History", type="secondary", use_container_width=True):
                save_history([])
                st.warning("History cleared.")
                st.rerun()

        # ── Monthly P&L summary ────────────────────────────────────────────────
        st.divider()
        st.markdown('<p class="section-header">Monthly P&L Summary</p>', unsafe_allow_html=True)

        df_hist["Month"] = pd.to_datetime(df_hist["Sell Date"]).dt.strftime("%b %Y")
        monthly = df_hist.groupby("Month").agg(
            Trades=("Symbol","count"),
            Net_PnL=("Net P&L ₹","sum"),
            Brokerage=("Brokerage ₹","sum")
        ).reset_index().sort_values("Month", ascending=False)

        monthly.columns = ["Month","Trades","Net P&L ₹","Brokerage ₹"]
        styled_monthly = monthly.style.map(colour_hist, subset=["Net P&L ₹"])
        st.dataframe(styled_monthly, use_container_width=True, hide_index=True)
