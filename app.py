import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import yfinance as yf
import requests

st.set_page_config(
    page_title="Vedhi Finance | Stock Scanner",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Dark theme ─────────────────────────────────────────────────────────────────
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
    border-radius: 8px; padding: 12px 16px;
}
div[data-testid="stMetricValue"],
div[data-testid="stMetricLabel"],
div[data-testid="stMetricDelta"] { color: #ffffff !important; }
div[data-testid="stDataFrame"] * {
    background-color: #1e1e2e !important;
    color: #ffffff !important;
}
div[data-testid="stNumberInput"] * { color: #ffffff !important; }
div[data-testid="stCheckbox"] label { color: #ffffff !important; }
ul[data-testid="stSelectboxVirtualDropdown"] li {
    background-color: #1e1e2e !important;
    color: #ffffff !important;
}
hr { border-color: #3a3f4b !important; }
.card {
    background: #1e1e2e;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 12px;
    border: 1px solid #2a2f3a;
}
.card-pass { border-left: 4px solid #1a9641 !important; }
.card-fail { border-left: 4px solid #d7191c !important; }
.card-part { border-left: 4px solid #f4a261 !important; }
.ticker-name { font-size: 1.1rem; font-weight: bold; color: #ffffff; }
.price-tag   { font-size: 1.4rem; font-weight: bold; color: #ffffff; }
.badge       { display: inline-block; padding: 3px 10px; border-radius: 5px;
               font-size: 0.78rem; font-weight: bold; margin: 2px; }
.badge-pass  { background: #1a3d1a; color: #1a9641; border: 1px solid #1a9641; }
.badge-fail  { background: #3d1a1a; color: #d7191c; border: 1px solid #d7191c; }
</style>
""", unsafe_allow_html=True)

# ── Stock list ─────────────────────────────────────────────────────────────────
NIFTY_STOCKS = {
    "SBIN.NS":        "SBIN — State Bank of India",
    "BEL.NS":         "BEL — Bharat Electronics",
    "ICICIBANK.NS":   "ICICI Bank",
    "RELIANCE.NS":    "Reliance Industries",
    "LT.NS":          "L&T — Larsen & Toubro",
    "HDFCBANK.NS":    "HDFC Bank",
    "INFY.NS":        "Infosys",
    "TCS.NS":         "TCS",
    "WIPRO.NS":       "Wipro",
    "AXISBANK.NS":    "Axis Bank",
    "BAJFINANCE.NS":  "Bajaj Finance",
    "MARUTI.NS":      "Maruti Suzuki",
    "TATAMOTORS.NS":  "Tata Motors",
    "TATASTEEL.NS":   "Tata Steel",
    "NTPC.NS":        "NTPC",
    "POWERGRID.NS":   "Power Grid",
    "ONGC.NS":        "ONGC",
    "COALINDIA.NS":   "Coal India",
    "SUNPHARMA.NS":   "Sun Pharma",
    "DRREDDY.NS":     "Dr. Reddy's",
    "CIPLA.NS":       "Cipla",
    "HINDUNILVR.NS":  "HUL",
    "ITC.NS":         "ITC",
    "ULTRACEMCO.NS":  "UltraTech Cement",
    "TECHM.NS":       "Tech Mahindra",
    "ADANIPORTS.NS":  "Adani Ports",
    "BAJAJFINSV.NS":  "Bajaj Finserv",
    "NESTLEIND.NS":   "Nestle India",
    "BRITANNIA.NS":   "Britannia",
    "GRASIM.NS":      "Grasim",
}

DEFAULT_WATCHLIST = ["SBIN.NS", "BEL.NS", "ICICIBANK.NS", "RELIANCE.NS", "LT.NS"]

if "watchlist" not in st.session_state:
    st.session_state.watchlist = DEFAULT_WATCHLIST.copy()

# ── Indicators ────────────────────────────────────────────────────────────────
def compute_rsi(series, period=14):
    delta    = series.diff()
    gain     = delta.clip(lower=0)
    loss     = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs       = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def compute_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

@st.cache_data(ttl=300)   # cache 5 minutes so re-runs don't re-fetch
def fetch_stock(ticker):
    try:
        # Use a requests session with proper headers — fixes Streamlit Cloud issue
        session = requests.Session()
        session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        })
        t  = yf.Ticker(ticker, session=session)
        df = t.history(period="90d", interval="1d", auto_adjust=True)

        if df is None or len(df) < 55:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        close  = df["Close"].squeeze()
        volume = df["Volume"].squeeze()

        rsi    = compute_rsi(close, 14)
        ema20  = compute_ema(close, 20)
        ema50  = compute_ema(close, 50)
        vol_avg = volume.rolling(20).mean()

        price      = float(close.iloc[-1])
        prev_price = float(close.iloc[-2])
        change_pct = (price - prev_price) / prev_price * 100

        r_rsi   = float(rsi.iloc[-1])
        r_ema20 = float(ema20.iloc[-1])
        r_ema50 = float(ema50.iloc[-1])
        r_vol   = float(volume.iloc[-1])
        r_vavg  = float(vol_avg.iloc[-1])
        vol_ratio = r_vol / r_vavg if r_vavg > 0 else 0

        f1 = 35 <= r_rsi <= 45
        f2 = price > r_ema50
        f3 = r_ema20 > r_ema50
        f4 = vol_ratio >= 1.2

        return {
            "ticker":    ticker,
            "name":      NIFTY_STOCKS.get(ticker, ticker),
            "price":     price,
            "change":    change_pct,
            "rsi":       r_rsi,
            "ema20":     r_ema20,
            "ema50":     r_ema50,
            "vol_ratio": vol_ratio,
            "f1": f1, "f2": f2, "f3": f3, "f4": f4,
            "passed":    sum([f1, f2, f3, f4]),
            "all_pass":  all([f1, f2, f3, f4]),
        }
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}

def badge(label, ok):
    cls = "badge-pass" if ok else "badge-fail"
    icon = "✔" if ok else "✖"
    return f"<span class='badge {cls}'>{icon} {label}</span>"

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(
    "<h4 style='color:#1a9641; margin-top:-10px; margin-bottom:4px;'>"
    "Vedhi Finance 📡 Stock Scanner</h4>",
    unsafe_allow_html=True)
st.markdown(
    "<p style='color:#8b92a5; font-size:0.85rem; margin-top:0;'>"
    "RSI 35–45 &nbsp;·&nbsp; Price > 50 EMA &nbsp;·&nbsp; "
    "20 EMA > 50 EMA &nbsp;·&nbsp; Volume > 1.2× 20-day avg</p>",
    unsafe_allow_html=True)
st.markdown("<hr style='margin:8px 0 14px;'>", unsafe_allow_html=True)

# ── Watchlist manager ──────────────────────────────────────────────────────────
with st.expander("⚙️ Manage Watchlist", expanded=False):
    st.markdown(f"**Watching {len(st.session_state.watchlist)} stocks:**")
    for t in st.session_state.watchlist:
        c1, c2 = st.columns([6, 1])
        c1.markdown(f"&nbsp;&nbsp;• {NIFTY_STOCKS.get(t, t)}")
        with c2:
            if st.button("Remove", key=f"rm_{t}"):
                st.session_state.watchlist.remove(t)
                st.rerun()
    st.markdown("---")
    available = [t for t in NIFTY_STOCKS if t not in st.session_state.watchlist]
    if available:
        col1, col2 = st.columns([4, 1])
        with col1:
            add_t = st.selectbox("Add from Nifty",
                                  options=available,
                                  format_func=lambda x: NIFTY_STOCKS[x],
                                  label_visibility="collapsed")
        with col2:
            if st.button("Add ➕"):
                st.session_state.watchlist.append(add_t)
                st.rerun()

# ── Scan ───────────────────────────────────────────────────────────────────────
col_btn, col_note = st.columns([2, 6])
with col_btn:
    run_scan = st.button("🔍 Run Scanner", use_container_width=True)
with col_note:
    st.markdown(
        "<p style='color:#8b92a5; margin-top:8px; font-size:0.82rem;'>"
        "Data from Yahoo Finance · refreshes every 5 min</p>",
        unsafe_allow_html=True)

if run_scan:
    results, errors = [], []
    bar = st.progress(0)
    for i, ticker in enumerate(st.session_state.watchlist):
        bar.progress((i+1) / len(st.session_state.watchlist),
                     text=f"Fetching {NIFTY_STOCKS.get(ticker, ticker)}...")
        r = fetch_stock(ticker)
        if r and "error" not in r:
            results.append(r)
        elif r and "error" in r:
            errors.append(r)
        else:
            errors.append({"ticker": ticker, "error": "No data returned"})
    bar.empty()

    if errors:
        with st.expander(f"⚠️ {len(errors)} stock(s) could not be fetched"):
            for e in errors:
                st.warning(f"{e['ticker']}: {e.get('error','unknown error')}")

    if not results:
        st.error("No data fetched. Yahoo Finance may be temporarily unavailable — try again in a minute.")
        st.stop()

    results.sort(key=lambda x: (-x["all_pass"], -x["passed"]))
    passed = [r for r in results if r["all_pass"]]
    partial = [r for r in results if not r["all_pass"]]

    # Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Scanned",          len(results))
    m2.metric("✅ All 4 Pass",    len(passed))
    m3.metric("⚠️ Partial",       len(partial))
    m4.metric("Last Scan",        datetime.now().strftime("%I:%M %p"))

    st.markdown("---")

    if passed:
        st.markdown("### ✅ Setup Ready — All 4 Filters Passed")
    else:
        st.markdown("### ⚠️ No stock passes all 4 filters right now")

    # Stock cards
    for r in results:
        cc = "card-pass" if r["all_pass"] else ("card-part" if r["passed"] >= 2 else "card-fail")
        chg_col = "#1a9641" if r["change"] >= 0 else "#d7191c"
        sign    = "+" if r["change"] >= 0 else ""

        b1 = badge(f"RSI {r['rsi']:.1f}  (35–45)",               r["f1"])
        b2 = badge(f"Price ₹{r['price']:.2f} > EMA50 ₹{r['ema50']:.2f}", r["f2"])
        b3 = badge(f"EMA20 ₹{r['ema20']:.2f} > EMA50 ₹{r['ema50']:.2f}", r["f3"])
        b4 = badge(f"Volume {r['vol_ratio']:.2f}× avg  (need ≥1.2×)",    r["f4"])

        st.markdown(f"""
        <div class='card {cc}'>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <span class='ticker-name'>{r['name']}</span>
                <span class='price-tag'>
                    ₹{r['price']:,.2f}
                    &nbsp;<span style='font-size:0.85rem; color:{chg_col};'>
                    {sign}{r['change']:.2f}%</span>
                </span>
            </div>
            <div style='margin-top:8px;'>{b1}{b2}{b3}{b4}</div>
            <div style='color:#8b92a5; font-size:0.78rem; margin-top:6px;'>
                {r['passed']}/4 filters passed
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Table
    st.markdown("---")
    st.markdown("#### 📋 Summary Table")
    rows = []
    for r in results:
        rows.append({
            "Stock":      r["name"],
            "Price":      f"₹{r['price']:,.2f}",
            "Change":     f"{'+' if r['change']>=0 else ''}{r['change']:.2f}%",
            "RSI":        f"{r['rsi']:.1f}",
            "EMA20":      f"₹{r['ema20']:.2f}",
            "EMA50":      f"₹{r['ema50']:.2f}",
            "Vol Ratio":  f"{r['vol_ratio']:.2f}×",
            "Filters":    f"{r['passed']}/4",
            "Signal":     "✅ BUY SETUP" if r["all_pass"] else
                          ("⚠️ Partial"  if r["passed"] >= 2 else "❌ No signal"),
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

else:
    watching = ", ".join([NIFTY_STOCKS.get(t,t).split(" — ")[0] for t in st.session_state.watchlist])
    st.markdown(
        f"<div style='text-align:center; color:#8b92a5; padding:60px 0;'>"
        f"<p style='font-size:2.5rem;'>📡</p>"
        f"<p style='font-size:1rem;'>Click <b style='color:#ffffff;'>Run Scanner</b> to analyse your watchlist</p>"
        f"<p style='font-size:0.82rem;'>Watching: {watching}</p>"
        f"</div>",
        unsafe_allow_html=True)
