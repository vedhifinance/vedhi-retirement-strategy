import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

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
.pass  { color: #1a9641 !important; font-weight: bold; }
.fail  { color: #d7191c !important; font-weight: bold; }
.card  {
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
.filter-row  { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 6px; }
.badge       { display: inline-block; padding: 3px 10px; border-radius: 5px;
               font-size: 0.78rem; font-weight: bold; margin: 2px; }
.badge-pass  { background: #1a3d1a; color: #1a9641; border: 1px solid #1a9641; }
.badge-fail  { background: #3d1a1a; color: #d7191c; border: 1px solid #d7191c; }
</style>
""", unsafe_allow_html=True)

# ── Nifty stock list (ticker: display name) ────────────────────────────────────
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
    "ADANIENT.NS":    "Adani Enterprises",
    "ADANIPORTS.NS":  "Adani Ports",
    "SUNPHARMA.NS":   "Sun Pharma",
    "DRREDDY.NS":     "Dr. Reddy's",
    "CIPLA.NS":       "Cipla",
    "HINDUNILVR.NS":  "HUL",
    "ITC.NS":         "ITC",
    "NESTLEIND.NS":   "Nestle India",
    "BRITANNIA.NS":   "Britannia",
    "ULTRACEMCO.NS":  "UltraTech Cement",
    "GRASIM.NS":      "Grasim",
    "TECHM.NS":       "Tech Mahindra",
}

DEFAULT_WATCHLIST = ["SBIN.NS", "BEL.NS", "ICICIBANK.NS", "RELIANCE.NS", "LT.NS"]

# ── Session state ──────────────────────────────────────────────────────────────
if "watchlist" not in st.session_state:
    st.session_state.watchlist = DEFAULT_WATCHLIST.copy()

# ── Indicator functions ────────────────────────────────────────────────────────
def compute_rsi(series, period=14):
    delta = series.diff()
    gain  = delta.clip(lower=0)
    loss  = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs  = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def analyse_stock(ticker):
    try:
        df = yf.download(ticker, period="90d", interval="1d",
                         auto_adjust=True, progress=False)
        if df is None or len(df) < 55:
            return None

        # Flatten MultiIndex columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        close  = df["Close"]
        volume = df["Volume"]

        rsi    = compute_rsi(close, 14)
        ema20  = compute_ema(close, 20)
        ema50  = compute_ema(close, 50)
        vol_avg20 = volume.rolling(20).mean()

        latest_close   = float(close.iloc[-1])
        latest_rsi     = float(rsi.iloc[-1])
        latest_ema20   = float(ema20.iloc[-1])
        latest_ema50   = float(ema50.iloc[-1])
        latest_vol     = float(volume.iloc[-1])
        latest_vol_avg = float(vol_avg20.iloc[-1])
        vol_ratio      = latest_vol / latest_vol_avg if latest_vol_avg > 0 else 0

        # Previous close for change %
        prev_close  = float(close.iloc[-2]) if len(close) > 1 else latest_close
        change_pct  = ((latest_close - prev_close) / prev_close) * 100

        # Filter checks
        f1_rsi     = 35 <= latest_rsi <= 45
        f2_price   = latest_close > latest_ema50
        f3_ema     = latest_ema20 > latest_ema50
        f4_volume  = vol_ratio >= 1.2

        filters_passed = sum([f1_rsi, f2_price, f3_ema, f4_volume])

        return {
            "ticker":       ticker,
            "name":         NIFTY_STOCKS.get(ticker, ticker),
            "price":        latest_close,
            "change_pct":   change_pct,
            "rsi":          latest_rsi,
            "ema20":        latest_ema20,
            "ema50":        latest_ema50,
            "vol_ratio":    vol_ratio,
            "f1_rsi":       f1_rsi,
            "f2_price":     f2_price,
            "f3_ema":       f3_ema,
            "f4_volume":    f4_volume,
            "filters_passed": filters_passed,
            "all_pass":     filters_passed == 4,
        }
    except Exception as e:
        return None


def badge(label, passed):
    cls = "badge-pass" if passed else "badge-fail"
    icon = "✔" if passed else "✖"
    return f"<span class='badge {cls}'>{icon} {label}</span>"


# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    "<h4 style='color:#1a9641; margin-top:-10px; margin-bottom:4px;'>"
    "Vedhi Finance 📡 Stock Scanner</h4>",
    unsafe_allow_html=True)
st.markdown(
    "<p style='color:#8b92a5; margin-top:0; font-size:0.85rem;'>"
    "RSI 35–45 &nbsp;·&nbsp; Price > 50 EMA &nbsp;·&nbsp; "
    "20 EMA > 50 EMA &nbsp;·&nbsp; Volume > 1.2× 20-day avg</p>",
    unsafe_allow_html=True)
st.markdown("<hr style='margin:8px 0 14px;'>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# WATCHLIST MANAGER
# ══════════════════════════════════════════════════════════════════════════════
with st.expander("⚙️ Manage Watchlist", expanded=False):
    st.markdown("**Current watchlist:**")
    for i, t in enumerate(st.session_state.watchlist):
        c1, c2 = st.columns([5, 1])
        c1.markdown(f"&nbsp;&nbsp;{i+1}. {NIFTY_STOCKS.get(t, t)}")
        with c2:
            if st.button("Remove", key=f"rm_{t}"):
                st.session_state.watchlist.remove(t)
                st.rerun()

    st.markdown("---")
    st.markdown("**Add a stock from Nifty:**")
    available = [t for t in NIFTY_STOCKS if t not in st.session_state.watchlist]
    if available:
        col1, col2 = st.columns([4, 1])
        with col1:
            add_ticker = st.selectbox(
                "Select stock",
                options=available,
                format_func=lambda x: NIFTY_STOCKS[x],
                label_visibility="collapsed"
            )
        with col2:
            if st.button("Add ➕"):
                st.session_state.watchlist.append(add_ticker)
                st.rerun()
    else:
        st.info("All Nifty stocks already in watchlist.")

# ══════════════════════════════════════════════════════════════════════════════
# SCAN BUTTON
# ══════════════════════════════════════════════════════════════════════════════
col_btn, col_time = st.columns([2, 5])
with col_btn:
    run_scan = st.button("🔍 Run Scanner", use_container_width=True)
with col_time:
    st.markdown(
        f"<p style='color:#8b92a5; margin-top:8px; font-size:0.82rem;'>"
        f"Last scanned: {datetime.now().strftime('%d %b %Y, %I:%M %p') if run_scan else '—'}"
        f"</p>", unsafe_allow_html=True)

if run_scan:
    results = []
    progress = st.progress(0, text="Fetching data...")
    for i, ticker in enumerate(st.session_state.watchlist):
        progress.progress(
            (i + 1) / len(st.session_state.watchlist),
            text=f"Analysing {NIFTY_STOCKS.get(ticker, ticker)}...")
        result = analyse_stock(ticker)
        if result:
            results.append(result)
    progress.empty()

    if not results:
        st.error("Could not fetch data. Check your internet connection.")
    else:
        # Sort: all-pass first, then by filters passed desc
        results.sort(key=lambda x: (-x["all_pass"], -x["filters_passed"]))

        passed_all = [r for r in results if r["all_pass"]]
        partial    = [r for r in results if not r["all_pass"]]

        # Summary row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Stocks Scanned",    len(results))
        m2.metric("✅ All Filters Pass", len(passed_all))
        m3.metric("⚠️ Partial Match",  len(partial))
        m4.metric("Watchlist Size",    len(st.session_state.watchlist))

        st.markdown("---")

        if passed_all:
            st.markdown("### ✅ Ready to Watch — All 4 Filters Passed")
        else:
            st.markdown(
                "### ⚠️ No stock passes all 4 filters right now",
                )
            st.markdown(
                "<p style='color:#8b92a5; font-size:0.85rem;'>"
                "Showing partial matches below.</p>",
                unsafe_allow_html=True)

        # Render each stock card
        for r in results:
            card_class = "card-pass" if r["all_pass"] else \
                         ("card-part" if r["filters_passed"] >= 2 else "card-fail")

            change_color = "#1a9641" if r["change_pct"] >= 0 else "#d7191c"
            change_sign  = "+" if r["change_pct"] >= 0 else ""

            b1 = badge(f"RSI {r['rsi']:.1f} (35–45)", r["f1_rsi"])
            b2 = badge(f"Price ₹{r['price']:.2f} > EMA50 ₹{r['ema50']:.2f}", r["f2_price"])
            b3 = badge(f"EMA20 ₹{r['ema20']:.2f} > EMA50 ₹{r['ema50']:.2f}", r["f3_ema"])
            b4 = badge(f"Vol {r['vol_ratio']:.2f}× avg (need 1.2×)", r["f4_volume"])

            filters_text = b1 + b2 + b3 + b4

            st.markdown(f"""
            <div class='card {card_class}'>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <span class='ticker-name'>{r['name']}</span>
                    <span class='price-tag'>
                        ₹{r['price']:,.2f}
                        &nbsp;<span style='font-size:0.85rem; color:{change_color};'>
                        {change_sign}{r['change_pct']:.2f}%</span>
                    </span>
                </div>
                <div style='margin-top:8px;'>{filters_text}</div>
                <div style='margin-top:6px; color:#8b92a5; font-size:0.78rem;'>
                    {r['filters_passed']}/4 filters passed
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Summary table
        st.markdown("---")
        st.markdown("#### 📋 Quick Summary Table")
        table_data = []
        for r in results:
            table_data.append({
                "Stock":       r["name"],
                "Price (₹)":  f"₹{r['price']:,.2f}",
                "Change":      f"{'+' if r['change_pct'] >= 0 else ''}{r['change_pct']:.2f}%",
                "RSI":         f"{r['rsi']:.1f}",
                "EMA20":       f"₹{r['ema20']:.2f}",
                "EMA50":       f"₹{r['ema50']:.2f}",
                "Vol Ratio":   f"{r['vol_ratio']:.2f}×",
                "Filters":     f"{r['filters_passed']}/4",
                "Signal":      "✅ BUY SETUP" if r["all_pass"] else (
                               "⚠️ Partial" if r["filters_passed"] >= 2 else "❌ No signal")
            })
        st.dataframe(pd.DataFrame(table_data), hide_index=True, use_container_width=True)

else:
    st.markdown(
        "<div style='text-align:center; color:#8b92a5; padding:40px 0;'>"
        "<p style='font-size:2rem;'>📡</p>"
        "<p>Click <b>Run Scanner</b> to analyse your watchlist</p>"
        f"<p style='font-size:0.8rem;'>Watching: "
        f"{', '.join([NIFTY_STOCKS.get(t,t).split(' — ')[0] for t in st.session_state.watchlist])}"
        f"</p></div>",
        unsafe_allow_html=True)
