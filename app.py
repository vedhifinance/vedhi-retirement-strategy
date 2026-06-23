import streamlit as st
import pandas as pd
import numpy as np
import pyotp
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Vedhi Finance | Stock Scanner",
    layout="wide",
    initial_sidebar_state="expanded"
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
section[data-testid="stSidebar"] {
    background-color: #0d2137 !important;
    border-right: 2px solid #1a9641 !important;
}
section[data-testid="stSidebar"] * {
    color: #ffffff !important;
}
section[data-testid="stSidebar"] input {
    background-color: #1a3a5c !important;
    border: 1px solid #1a9641 !important;
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
.badge { display: inline-block; padding: 3px 10px; border-radius: 5px;
         font-size: 0.78rem; font-weight: bold; margin: 2px; }
.badge-pass { background:#1a3d1a; color:#1a9641; border:1px solid #1a9641; }
.badge-fail { background:#3d1a1a; color:#d7191c; border:1px solid #d7191c; }
</style>
""", unsafe_allow_html=True)

# ── Stock list with Angel One token IDs ───────────────────────────────────────
# symboltoken from Angel One instrument list (NSE)
WATCHLIST_DEFAULT = [
    {"symbol": "SBIN",      "token": "3045",  "name": "State Bank of India"},
    {"symbol": "BEL",       "token": "383",   "name": "Bharat Electronics"},
    {"symbol": "ICICIBANK", "token": "4963",  "name": "ICICI Bank"},
    {"symbol": "RELIANCE",  "token": "2885",  "name": "Reliance Industries"},
    {"symbol": "LT",        "token": "11483", "name": "Larsen & Toubro"},
]

NIFTY_EXTRA = [
    {"symbol": "HDFCBANK",   "token": "1333",  "name": "HDFC Bank"},
    {"symbol": "INFY",       "token": "1594",  "name": "Infosys"},
    {"symbol": "TCS",        "token": "11536", "name": "TCS"},
    {"symbol": "WIPRO",      "token": "3787",  "name": "Wipro"},
    {"symbol": "AXISBANK",   "token": "5900",  "name": "Axis Bank"},
    {"symbol": "BAJFINANCE", "token": "317",   "name": "Bajaj Finance"},
    {"symbol": "MARUTI",     "token": "10999", "name": "Maruti Suzuki"},
    {"symbol": "TATAMOTORS", "token": "3456",  "name": "Tata Motors"},
    {"symbol": "TATASTEEL",  "token": "3499",  "name": "Tata Steel"},
    {"symbol": "NTPC",       "token": "11630", "name": "NTPC"},
    {"symbol": "ONGC",       "token": "2475",  "name": "ONGC"},
    {"symbol": "COALINDIA",  "token": "20374", "name": "Coal India"},
    {"symbol": "SUNPHARMA",  "token": "3351",  "name": "Sun Pharma"},
    {"symbol": "DRREDDY",    "token": "881",   "name": "Dr Reddy's"},
    {"symbol": "CIPLA",      "token": "694",   "name": "Cipla"},
    {"symbol": "ITC",        "token": "1660",  "name": "ITC"},
    {"symbol": "POWERGRID",  "token": "14977", "name": "Power Grid"},
    {"symbol": "ADANIPORTS", "token": "15083", "name": "Adani Ports"},
    {"symbol": "TECHM",      "token": "13538", "name": "Tech Mahindra"},
    {"symbol": "ULTRACEMCO", "token": "11532", "name": "UltraTech Cement"},
]

if "watchlist" not in st.session_state:
    st.session_state.watchlist = WATCHLIST_DEFAULT.copy()
if "smart_api" not in st.session_state:
    st.session_state.smart_api = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ── Sidebar — credentials ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔐 Angel One Login")
    st.markdown("<p style='font-size:0.8rem; color:#8b92a5;'>Credentials stay in your browser session only — never saved to file or GitHub.</p>", unsafe_allow_html=True)

    api_key   = st.text_input("API Key",      type="password", key="api_key_input")
    client_id = st.text_input("Client ID",    key="client_id_input")
    password  = st.text_input("PIN/Password", type="password", key="password_input")
    totp_secret = st.text_input("TOTP Secret", type="password", key="totp_input",
                                help="The base secret from Smart API TOTP setup — not the 6-digit code")

    if st.button("🔗 Connect to Angel One", use_container_width=True):
        if not all([api_key, client_id, password, totp_secret]):
            st.error("Please fill in all fields.")
        else:
            try:
                from SmartApi import SmartConnect
                obj   = SmartConnect(api_key=api_key)
                totp  = pyotp.TOTP(totp_secret).now()
                data  = obj.generateSession(client_id, password, totp)
                if data["status"]:
                    st.session_state.smart_api = obj
                    st.session_state.logged_in = True
                    st.success(f"✅ Connected — {client_id}")
                else:
                    st.error(f"Login failed: {data.get('message','Unknown error')}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    if st.session_state.logged_in:
        st.markdown("---")
        st.success("🟢 Connected to Angel One")
        if st.button("Disconnect", use_container_width=True):
            st.session_state.smart_api = None
            st.session_state.logged_in = False
            st.rerun()

# ── Indicator helpers ──────────────────────────────────────────────────────────
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

def analyse_stock(obj, stock):
    try:
        # Fetch 90 days of daily candles
        to_date   = datetime.now().strftime("%Y-%m-%d %H:%M")
        from_date = (datetime.now() - timedelta(days=120)).strftime("%Y-%m-%d %H:%M")

        params = {
            "exchange":    "NSE",
            "symboltoken": stock["token"],
            "interval":    "ONE_DAY",
            "fromdate":    from_date,
            "todate":      to_date,
        }
        resp = obj.getCandleData(params)

        if not resp or not resp.get("status") or not resp.get("data"):
            return {"symbol": stock["symbol"], "name": stock["name"],
                    "error": resp.get("message", "No data") if resp else "No response"}

        # Parse candles: [timestamp, open, high, low, close, volume]
        candles = resp["data"]
        if len(candles) < 55:
            return {"symbol": stock["symbol"], "name": stock["name"],
                    "error": f"Not enough data ({len(candles)} bars)"}

        df          = pd.DataFrame(candles, columns=["ts","open","high","low","close","volume"])
        df["close"] = pd.to_numeric(df["close"])
        df["volume"]= pd.to_numeric(df["volume"])

        close  = df["close"]
        volume = df["volume"]

        rsi    = compute_rsi(close, 14)
        ema20  = compute_ema(close, 20)
        ema50  = compute_ema(close, 50)
        vavg20 = volume.rolling(20).mean()

        price      = float(close.iloc[-1])
        prev_price = float(close.iloc[-2])
        change_pct = (price - prev_price) / prev_price * 100

        r_rsi   = float(rsi.iloc[-1])
        r_ema20 = float(ema20.iloc[-1])
        r_ema50 = float(ema50.iloc[-1])
        r_vol   = float(volume.iloc[-1])
        r_vavg  = float(vavg20.iloc[-1])
        vol_ratio = r_vol / r_vavg if r_vavg > 0 else 0

        f1 = 35 <= r_rsi <= 45
        f2 = price > r_ema50
        f3 = r_ema20 > r_ema50
        f4 = vol_ratio >= 1.2

        return {
            "symbol":    stock["symbol"],
            "name":      stock["name"],
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
        return {"symbol": stock["symbol"], "name": stock["name"], "error": str(e)}

def badge(label, ok):
    cls  = "badge-pass" if ok else "badge-fail"
    icon = "✔" if ok else "✖"
    return f"<span class='badge {cls}'>{icon} {label}</span>"

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(
    "<h4 style='color:#1a9641; margin-top:-10px; margin-bottom:4px;'>"
    "Vedhi Finance 📡 Stock Scanner</h4>", unsafe_allow_html=True)
st.markdown(
    "<p style='color:#8b92a5; font-size:0.85rem; margin-top:0;'>"
    "Live data via Angel One &nbsp;·&nbsp; "
    "RSI 35–45 &nbsp;·&nbsp; Price > 50 EMA &nbsp;·&nbsp; "
    "20 EMA > 50 EMA &nbsp;·&nbsp; Volume > 1.2× 20-day avg</p>",
    unsafe_allow_html=True)
st.markdown("<hr style='margin:8px 0 14px;'>", unsafe_allow_html=True)

# ── Watchlist manager ──────────────────────────────────────────────────────────
with st.expander("⚙️ Manage Watchlist", expanded=False):
    st.markdown(f"**Watching {len(st.session_state.watchlist)} stocks:**")
    for s in st.session_state.watchlist:
        c1, c2 = st.columns([6, 1])
        c1.markdown(f"&nbsp;&nbsp;• **{s['symbol']}** — {s['name']}")
        with c2:
            if st.button("Remove", key=f"rm_{s['symbol']}"):
                st.session_state.watchlist = [
                    x for x in st.session_state.watchlist if x["symbol"] != s["symbol"]]
                st.rerun()

    st.markdown("---")
    current_symbols = [s["symbol"] for s in st.session_state.watchlist]
    available = [s for s in NIFTY_EXTRA if s["symbol"] not in current_symbols]
    if available:
        col1, col2 = st.columns([4, 1])
        with col1:
            add_s = st.selectbox("Add from Nifty",
                                  options=available,
                                  format_func=lambda x: f"{x['symbol']} — {x['name']}",
                                  label_visibility="collapsed")
        with col2:
            if st.button("Add ➕"):
                st.session_state.watchlist.append(add_s)
                st.rerun()

# ── Not logged in state ────────────────────────────────────────────────────────
if not st.session_state.logged_in:
    st.markdown(
        "<div style='text-align:center; color:#8b92a5; padding:60px 0;'>"
        "<p style='font-size:2.5rem;'>🔐</p>"
        "<p style='font-size:1rem; color:#ffffff;'>Connect your Angel One account to get live data</p>"
        "<p style='font-size:0.85rem;'>Enter your credentials in the left sidebar</p>"
        "</div>", unsafe_allow_html=True)
    st.stop()

# ── Scan button ────────────────────────────────────────────────────────────────
col_btn, col_note = st.columns([2, 6])
with col_btn:
    run_scan = st.button("🔍 Run Scanner", use_container_width=True)
with col_note:
    st.markdown(
        "<p style='color:#8b92a5; margin-top:8px; font-size:0.82rem;'>"
        "Fetches live daily candles from Angel One</p>",
        unsafe_allow_html=True)

if run_scan:
    results, errors = [], []
    obj = st.session_state.smart_api
    bar = st.progress(0)

    for i, stock in enumerate(st.session_state.watchlist):
        bar.progress((i+1) / len(st.session_state.watchlist),
                     text=f"Analysing {stock['symbol']}...")
        r = analyse_stock(obj, stock)
        if "error" in r:
            errors.append(r)
        else:
            results.append(r)
    bar.empty()

    if errors:
        with st.expander(f"⚠️ {len(errors)} stock(s) failed"):
            for e in errors:
                st.warning(f"{e['symbol']}: {e['error']}")

    if not results:
        st.error("No data returned. Check your Angel One session — it may have expired. Reconnect from the sidebar.")
        st.stop()

    results.sort(key=lambda x: (-x["all_pass"], -x["passed"]))
    passed  = [r for r in results if r["all_pass"]]
    partial = [r for r in results if not r["all_pass"]]

    # Summary metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Stocks Scanned",    len(results))
    m2.metric("✅ All 4 Pass",     len(passed))
    m3.metric("⚠️ Partial Match",  len(partial))
    m4.metric("Scanned At",        datetime.now().strftime("%I:%M %p"))

    st.markdown("---")

    if passed:
        st.markdown("### ✅ Setup Ready — All 4 Filters Passed")
    else:
        st.markdown("### ⚠️ No stock passes all 4 filters right now")
        st.markdown("<p style='color:#8b92a5; font-size:0.85rem;'>Showing partial matches below.</p>",
                    unsafe_allow_html=True)

    # Stock cards
    for r in results:
        cc       = "card-pass" if r["all_pass"] else ("card-part" if r["passed"] >= 2 else "card-fail")
        chg_col  = "#1a9641" if r["change"] >= 0 else "#d7191c"
        sign     = "+" if r["change"] >= 0 else ""

        b1 = badge(f"RSI {r['rsi']:.1f}  (35–45)",                        r["f1"])
        b2 = badge(f"Price ₹{r['price']:.2f} > EMA50 ₹{r['ema50']:.2f}", r["f2"])
        b3 = badge(f"EMA20 ₹{r['ema20']:.2f} > EMA50 ₹{r['ema50']:.2f}", r["f3"])
        b4 = badge(f"Volume {r['vol_ratio']:.2f}× avg  (need ≥ 1.2×)",   r["f4"])

        st.markdown(f"""
        <div class='card {cc}'>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <span style='font-size:1.1rem; font-weight:bold;'>{r['symbol']} — {r['name']}</span>
                <span style='font-size:1.4rem; font-weight:bold;'>
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

    # Summary table
    st.markdown("---")
    st.markdown("#### 📋 Summary Table")
    rows = []
    for r in results:
        rows.append({
            "Stock":     f"{r['symbol']} — {r['name']}",
            "Price":     f"₹{r['price']:,.2f}",
            "Change":    f"{'+' if r['change']>=0 else ''}{r['change']:.2f}%",
            "RSI":       f"{r['rsi']:.1f}",
            "EMA20":     f"₹{r['ema20']:.2f}",
            "EMA50":     f"₹{r['ema50']:.2f}",
            "Vol Ratio": f"{r['vol_ratio']:.2f}×",
            "Filters":   f"{r['passed']}/4",
            "Signal":    "✅ BUY SETUP" if r["all_pass"] else
                         ("⚠️ Partial"  if r["passed"] >= 2 else "❌ No signal"),
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

else:
    watching = ", ".join([s["symbol"] for s in st.session_state.watchlist])
    st.markdown(
        f"<div style='text-align:center; color:#8b92a5; padding:60px 0;'>"
        f"<p style='font-size:2.5rem;'>📡</p>"
        f"<p style='font-size:1rem; color:#ffffff;'>Click <b>Run Scanner</b> to get live data</p>"
        f"<p style='font-size:0.82rem;'>Watching: {watching}</p>"
        f"</div>", unsafe_allow_html=True)
