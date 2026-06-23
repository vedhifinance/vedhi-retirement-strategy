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
section[data-testid="stSidebar"] * { color: #ffffff !important; }
section[data-testid="stSidebar"] input {
    background-color: #1a3a5c !important;
    border: 1px solid #1a9641 !important;
    color: #ffffff !important;
}
hr { border-color: #3a3f4b !important; }

/* Scanner table styling */
.scan-table { width:100%; border-collapse:collapse; font-size:0.85rem; }
.scan-table th {
    background:#1a2a3a; color:#8b92a5; padding:8px 10px;
    text-align:left; border-bottom:1px solid #3a3f4b;
    font-size:0.75rem; text-transform:uppercase; letter-spacing:0.5px;
}
.scan-table td { padding:8px 10px; border-bottom:1px solid #1e2a38; vertical-align:middle; }
.scan-table tr:hover td { background:#1a2535; }
.stock-name { font-weight:bold; color:#ffffff; }
.chg-pos { color:#1a9641; font-weight:bold; }
.chg-neg { color:#d7191c; font-weight:bold; }
.signal-buy    { background:#1a3d1a; color:#1a9641; padding:3px 10px;
                 border-radius:5px; font-weight:bold; font-size:0.78rem;
                 border:1px solid #1a9641; white-space:nowrap; }
.signal-avoid  { background:#3d1a1a; color:#d7191c; padding:3px 10px;
                 border-radius:5px; font-weight:bold; font-size:0.78rem;
                 border:1px solid #d7191c; }
.signal-neutral{ background:#2a2a1a; color:#f4a261; padding:3px 10px;
                 border-radius:5px; font-weight:bold; font-size:0.78rem;
                 border:1px solid #f4a261; }
.strength-strong { background:#1a9641; color:#fff; padding:2px 8px;
                   border-radius:4px; font-size:0.78rem; font-weight:bold; }
.strength-avoid  { background:#d7191c; color:#fff; padding:2px 8px;
                   border-radius:4px; font-size:0.78rem; font-weight:bold; }
.strength-neutral{ background:#555; color:#fff; padding:2px 8px;
                   border-radius:4px; font-size:0.78rem; }
</style>
""", unsafe_allow_html=True)

# ── All Nifty 50 stocks with Angel One tokens ──────────────────────────────────
ALL_STOCKS = [
    {"symbol":"ADANIENT",   "token":"25",    "name":"Adani Enterprises"},
    {"symbol":"ADANIPORTS",  "token":"15083", "name":"Adani Ports"},
    {"symbol":"APOLLOHOSP",  "token":"157",   "name":"Apollo Hospitals"},
    {"symbol":"ASIANPAINT",  "token":"236",   "name":"Asian Paints"},
    {"symbol":"AXISBANK",    "token":"5900",  "name":"Axis Bank"},
    {"symbol":"BAJAJ-AUTO",  "token":"16669", "name":"Bajaj Auto"},
    {"symbol":"BAJFINANCE",  "token":"317",   "name":"Bajaj Finance"},
    {"symbol":"BAJAJFINSV",  "token":"16675", "name":"Bajaj Finserv"},
    {"symbol":"BEL",         "token":"383",   "name":"Bharat Electronics"},
    {"symbol":"BPCL",        "token":"526",   "name":"BPCL"},
    {"symbol":"BHARTIARTL",  "token":"10604", "name":"Bharti Airtel"},
    {"symbol":"BRITANNIA",   "token":"547",   "name":"Britannia"},
    {"symbol":"CIPLA",       "token":"694",   "name":"Cipla"},
    {"symbol":"COALINDIA",   "token":"20374", "name":"Coal India"},
    {"symbol":"DRREDDY",     "token":"881",   "name":"Dr Reddy's"},
    {"symbol":"EICHERMOT",   "token":"910",   "name":"Eicher Motors"},
    {"symbol":"GRASIM",      "token":"1232",  "name":"Grasim"},
    {"symbol":"HCLTECH",     "token":"7229",  "name":"HCL Tech"},
    {"symbol":"HDFCBANK",    "token":"1333",  "name":"HDFC Bank"},
    {"symbol":"HDFCLIFE",    "token":"467",   "name":"HDFC Life"},
    {"symbol":"HEROMOTOCO",  "token":"1348",  "name":"Hero MotoCorp"},
    {"symbol":"HINDALCO",    "token":"1363",  "name":"Hindalco"},
    {"symbol":"HINDUNILVR",  "token":"1394",  "name":"HUL"},
    {"symbol":"ICICIBANK",   "token":"4963",  "name":"ICICI Bank"},
    {"symbol":"ITC",         "token":"1660",  "name":"ITC"},
    {"symbol":"INDUSINDBK",  "token":"5258",  "name":"IndusInd Bank"},
    {"symbol":"INFY",        "token":"1594",  "name":"Infosys"},
    {"symbol":"JSWSTEEL",    "token":"11723", "name":"JSW Steel"},
    {"symbol":"KOTAKBANK",   "token":"1922",  "name":"Kotak Mahindra Bank"},
    {"symbol":"LT",          "token":"11483", "name":"Larsen & Toubro"},
    {"symbol":"LTIM",        "token":"17818", "name":"LTIMindtree"},
    {"symbol":"M&M",         "token":"2031",  "name":"Mahindra & Mahindra"},
    {"symbol":"MARUTI",      "token":"10999", "name":"Maruti Suzuki"},
    {"symbol":"NESTLEIND",   "token":"17963", "name":"Nestle India"},
    {"symbol":"NTPC",        "token":"11630", "name":"NTPC"},
    {"symbol":"ONGC",        "token":"2475",  "name":"ONGC"},
    {"symbol":"POWERGRID",   "token":"14977", "name":"Power Grid"},
    {"symbol":"RELIANCE",    "token":"2885",  "name":"Reliance Industries"},
    {"symbol":"SBILIFE",     "token":"21808", "name":"SBI Life"},
    {"symbol":"SBIN",        "token":"3045",  "name":"State Bank of India"},
    {"symbol":"SUNPHARMA",   "token":"3351",  "name":"Sun Pharma"},
    {"symbol":"TCS",         "token":"11536", "name":"TCS"},
    {"symbol":"TATACONSUM",  "token":"3432",  "name":"Tata Consumer"},
    {"symbol":"TATAMOTORS",  "token":"3456",  "name":"Tata Motors"},
    {"symbol":"TATASTEEL",   "token":"3499",  "name":"Tata Steel"},
    {"symbol":"TECHM",       "token":"13538", "name":"Tech Mahindra"},
    {"symbol":"TITAN",       "token":"3506",  "name":"Titan"},
    {"symbol":"ULTRACEMCO",  "token":"11532", "name":"UltraTech Cement"},
    {"symbol":"WIPRO",       "token":"3787",  "name":"Wipro"},
    {"symbol":"ZOMATO",      "token":"5097",  "name":"Zomato"},
]

MY5 = ["SBIN","BEL","ICICIBANK","RELIANCE","LT"]
MY5_STOCKS = [s for s in ALL_STOCKS if s["symbol"] in MY5]

# ── Session state ──────────────────────────────────────────────────────────────
if "smart_api"  not in st.session_state: st.session_state.smart_api  = None
if "logged_in"  not in st.session_state: st.session_state.logged_in  = False
if "scan_mode"  not in st.session_state: st.session_state.scan_mode  = "My 5 Stocks"

# ── Sidebar login ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔐 Angel One Login")
    st.markdown("<p style='font-size:0.8rem; color:#a0b8d0;'>Credentials stay in your browser only — never saved to GitHub.</p>", unsafe_allow_html=True)
    api_key      = st.text_input("API Key",       type="password")
    client_id    = st.text_input("Client ID")
    password     = st.text_input("PIN / Password",type="password")
    totp_secret  = st.text_input("TOTP Secret",   type="password",
                                  help="Base secret from Smart API TOTP setup")

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
        st.markdown("---")
        st.success("🟢 Angel One Connected")
        if st.button("Disconnect", use_container_width=True):
            st.session_state.smart_api = None
            st.session_state.logged_in = False
            st.rerun()

# ── Indicators ────────────────────────────────────────────────────────────────
def rsi(s, p=14):
    d = s.diff()
    g = d.clip(lower=0).ewm(com=p-1, min_periods=p).mean()
    l = (-d.clip(upper=0)).ewm(com=p-1, min_periods=p).mean()
    return 100 - 100/(1 + g/l)

def ema(s, p):
    return s.ewm(span=p, adjust=False).mean()

def analyse(obj, stock):
    try:
        to_dt   = datetime.now().strftime("%Y-%m-%d %H:%M")
        fr_dt   = (datetime.now() - timedelta(days=150)).strftime("%Y-%m-%d %H:%M")
        resp    = obj.getCandleData({
            "exchange": "NSE", "symboltoken": stock["token"],
            "interval": "ONE_DAY", "fromdate": fr_dt, "todate": to_dt
        })
        if not resp or not resp.get("status") or not resp.get("data"):
            return None
        candles = resp["data"]
        if len(candles) < 60:
            return None

        df           = pd.DataFrame(candles, columns=["ts","o","h","l","c","v"])
        df["c"]      = pd.to_numeric(df["c"])
        df["v"]      = pd.to_numeric(df["v"])
        close        = df["c"]
        volume       = df["v"]

        r14   = rsi(close, 14)
        e20   = ema(close, 20)
        e50   = ema(close, 50)
        e200  = ema(close, 200) if len(close) >= 200 else ema(close, len(close))
        vavg  = volume.rolling(20).mean()

        price      = float(close.iloc[-1])
        prev       = float(close.iloc[-2])
        chg_pct    = (price - prev) / prev * 100
        r_rsi      = float(r14.iloc[-1])
        r_e20      = float(e20.iloc[-1])
        r_e50      = float(e50.iloc[-1])
        r_e200     = float(e200.iloc[-1])
        r_vol      = float(volume.iloc[-1])
        r_vavg     = float(vavg.iloc[-1])
        vol_ratio  = r_vol / r_vavg if r_vavg > 0 else 0
        pct_200    = (price - r_e200) / r_e200 * 100

        # Last candle color
        last_open  = float(df["o"].iloc[-1])
        candle     = "🟢 Green" if price >= last_open else "🔴 Red"

        # Filter checks
        f1 = 35 <= r_rsi <= 45          # RSI in zone
        f2 = price > r_e50              # Price > EMA50
        f3 = r_e20 > r_e50             # EMA20 > EMA50
        f4 = vol_ratio >= 1.2           # Volume surge
        f5 = price > r_e200            # Price > EMA200 (bonus)
        f6 = price >= last_open         # Green candle

        passed = sum([f1, f2, f3, f4])

        # Strength & Signal
        if passed == 4 and f6:
            strength = "Strong"
            signal   = "✅ BUY SETUP"
        elif passed == 4:
            strength = "Strong"
            signal   = "⚠️ Watch — red candle"
        elif passed >= 3:
            strength = "Neutral"
            signal   = "🔍 Partial setup"
        elif f2 is False or f3 is False:
            strength = "Avoid"
            signal   = "❌ Avoid"
        else:
            strength = "Neutral"
            signal   = "— Monitoring"

        return {
            "symbol":    stock["symbol"],
            "name":      stock["name"],
            "price":     price,
            "chg":       chg_pct,
            "rsi":       r_rsi,
            "ema20":     r_e20,
            "ema50":     r_e50,
            "ema200":    r_e200,
            "pct200":    pct_200,
            "vol_ratio": vol_ratio,
            "candle":    candle,
            "strength":  strength,
            "signal":    signal,
            "passed":    passed,
            "all_pass":  passed == 4 and f6,
        }
    except:
        return None

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(
    "<h4 style='color:#1a9641; margin-top:-10px; margin-bottom:4px;'>"
    "Vedhi Finance 📡 Stock Scanner</h4>", unsafe_allow_html=True)
st.markdown(
    "<p style='color:#8b92a5; font-size:0.85rem; margin-top:0;'>"
    "Live NSE data via Angel One &nbsp;·&nbsp; "
    "RSI 35–45 &nbsp;·&nbsp; Price > EMA50 &nbsp;·&nbsp; "
    "EMA20 > EMA50 &nbsp;·&nbsp; Volume > 1.2× avg</p>",
    unsafe_allow_html=True)
st.markdown("<hr style='margin:8px 0 14px;'>", unsafe_allow_html=True)

if not st.session_state.logged_in:
    st.markdown(
        "<div style='text-align:center; padding:80px 0;'>"
        "<p style='font-size:2.5rem;'>🔐</p>"
        "<p style='font-size:1.1rem; color:#ffffff;'>Connect your Angel One account</p>"
        "<p style='color:#8b92a5;'>Enter credentials in the left sidebar → click Connect</p>"
        "</div>", unsafe_allow_html=True)
    st.stop()

# ── Controls ───────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns([2, 2, 4])
with c1:
    run_scan = st.button("🔍 Run Scanner", use_container_width=True)
with c2:
    mode = st.radio("Scan mode", ["My 5 Stocks", "All Nifty 50"],
                    horizontal=True, label_visibility="collapsed")
with c3:
    st.markdown(
        f"<p style='color:#8b92a5; margin-top:8px; font-size:0.82rem;'>"
        f"{'Scanning your 5 watchlist stocks' if mode == 'My 5 Stocks' else 'Scanning all 50 Nifty stocks — takes ~30 sec'}"
        f"</p>", unsafe_allow_html=True)

if run_scan:
    stocks_to_scan = MY5_STOCKS if mode == "My 5 Stocks" else ALL_STOCKS
    obj     = st.session_state.smart_api
    results = []
    errors  = []
    bar     = st.progress(0)

    for i, stock in enumerate(stocks_to_scan):
        bar.progress((i+1)/len(stocks_to_scan),
                     text=f"Fetching {stock['symbol']}...")
        r = analyse(obj, stock)
        if r:
            results.append(r)
        else:
            errors.append(stock["symbol"])
    bar.empty()

    if errors:
        st.caption(f"⚠️ Could not fetch: {', '.join(errors)}")

    if not results:
        st.error("No data returned. Angel One session may have expired — reconnect from sidebar.")
        st.stop()

    # Sort: all_pass first, then by filters passed
    results.sort(key=lambda x: (-x["all_pass"], -x["passed"]))

    # Summary
    buy_setups = [r for r in results if r["all_pass"]]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Scanned",         len(results))
    m2.metric("✅ Buy Setups",   len(buy_setups))
    m3.metric("⚠️ Partial",      len([r for r in results if r["passed"] >= 3 and not r["all_pass"]]))
    m4.metric("Time",            datetime.now().strftime("%I:%M %p"))

    st.markdown("---")

    # ── Table ──────────────────────────────────────────────────────────────────
    rows_html = ""
    for r in results:
        chg_cls  = "chg-pos" if r["chg"] >= 0 else "chg-neg"
        sign     = "+" if r["chg"] >= 0 else ""
        pct200_s = f"+{r['pct200']:.1f}%" if r["pct200"] >= 0 else f"{r['pct200']:.1f}%"
        pct200_c = "#1a9641" if r["pct200"] >= 0 else "#d7191c"

        if r["strength"] == "Strong":
            str_html = f"<span class='strength-strong'>Strong</span>"
        elif r["strength"] == "Avoid":
            str_html = f"<span class='strength-avoid'>Avoid</span>"
        else:
            str_html = f"<span class='strength-neutral'>Neutral</span>"

        if "BUY" in r["signal"]:
            sig_html = f"<span class='signal-buy'>{r['signal']}</span>"
        elif "Avoid" in r["signal"]:
            sig_html = f"<span class='signal-avoid'>{r['signal']}</span>"
        else:
            sig_html = f"<span class='signal-neutral'>{r['signal']}</span>"

        rows_html += f"""
        <tr>
            <td><span class='stock-name'>{r['symbol']}</span><br>
                <span style='color:#8b92a5; font-size:0.75rem;'>{r['name']}</span></td>
            <td>₹{r['price']:,.2f}</td>
            <td><span class='{chg_cls}'>{sign}{r['chg']:.2f}%</span></td>
            <td>{r['rsi']:.1f}</td>
            <td>₹{r['ema20']:,.2f}</td>
            <td>₹{r['ema50']:,.2f}</td>
            <td>₹{r['ema200']:,.2f}</td>
            <td><span style='color:{pct200_c};'>{pct200_s}</span></td>
            <td>{r['vol_ratio']:.2f}×</td>
            <td>{r['candle']}</td>
            <td>{str_html}</td>
            <td>{sig_html}</td>
        </tr>"""

    st.markdown(f"""
    <table class='scan-table'>
        <thead>
            <tr>
                <th>Stock</th>
                <th>LTP ₹</th>
                <th>Chg%</th>
                <th>RSI</th>
                <th>EMA 20</th>
                <th>EMA 50</th>
                <th>EMA 200</th>
                <th>% vs 200</th>
                <th>Vol Ratio</th>
                <th>Candle</th>
                <th>Strength</th>
                <th>Signal</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    """, unsafe_allow_html=True)

    st.markdown(
        "<p style='color:#8b92a5; font-size:0.78rem; margin-top:8px;'>"
        f"Scanned at {datetime.now().strftime('%d %b %Y, %I:%M %p')} &nbsp;·&nbsp; "
        "Data from Angel One NSE</p>", unsafe_allow_html=True)

else:
    watching = " · ".join([s["symbol"] for s in MY5_STOCKS])
    st.markdown(
        f"<div style='text-align:center; color:#8b92a5; padding:80px 0;'>"
        f"<p style='font-size:2.5rem;'>📡</p>"
        f"<p style='font-size:1rem; color:#ffffff;'>Click <b>Run Scanner</b> to get live data</p>"
        f"<p style='font-size:0.82rem;'>Default watchlist: {watching}</p>"
        f"</div>", unsafe_allow_html=True)
