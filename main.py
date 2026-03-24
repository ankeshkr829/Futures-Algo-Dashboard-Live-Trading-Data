import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit.components.v1 as components
from binance.client import Client
from binance.enums import *
import datetime
import json

# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(
    layout="wide",
    page_title="Futures Algo Dashboard Live Trading Data",
    page_icon="📈"
)

# ---------------------------
# THEME STATE
# ---------------------------
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

# Theme toggle button — top right
_tcol1, _tcol2 = st.columns([6, 1])
with _tcol2:
    _btn_label = "☀️ Light" if st.session_state.theme == "dark" else "🌙 Dark"
    if st.button(_btn_label, key="theme_toggle", use_container_width=True):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()

IS_DARK = st.session_state.theme == "dark"

# ---------------------------
# THEME VARIABLES
# ---------------------------
if IS_DARK:
    BG_MAIN      = "#0a0e1a"
    BG_SURFACE   = "#0d1425"
    BG_CARD      = "linear-gradient(145deg,#111827,#1a2235)"
    BORDER_CARD  = "#1e3a5f"
    TEXT_PRIMARY = "#e0e6f0"
    TEXT_MUTED   = "#7eb3e8"
    TEXT_DIM     = "#aaa"
    GRID_COLOR   = "#111827"
    PLOT_BG      = "#0d1425"
    PAPER_BG     = "#0a0e1a"
    LEGEND_FG    = "#7eb3e8"
else:
    BG_MAIN      = "#f0f4f8"
    BG_SURFACE   = "#ffffff"
    BG_CARD      = "linear-gradient(145deg,#ffffff,#f0f4f8)"
    BORDER_CARD  = "#c0cfe0"
    TEXT_PRIMARY = "#0d1425"
    TEXT_MUTED   = "#1a5296"
    TEXT_DIM     = "#555"
    GRID_COLOR   = "#dde5ef"
    PLOT_BG      = "#ffffff"
    PAPER_BG     = "#f0f4f8"
    LEGEND_FG    = "#1a5296"

# ---------------------------
# CUSTOM CSS — Theme-aware
# ---------------------------
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;600&display=swap');

html, body, [class*="css"] {{
    font-family: 'DM Sans', sans-serif;
    background-color: {BG_MAIN};
    color: {TEXT_PRIMARY};
}}
.stApp {{
    background: {BG_MAIN};
}}
h1,h2,h3 {{ font-family:'Space Mono',monospace; color:{TEXT_PRIMARY}; }}

.metric-card {{
    background: {BG_CARD};
    border: 1px solid {BORDER_CARD};
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 12px;
}}
.paper-badge {{
    background: {'#1a2a4a' if IS_DARK else '#ddeeff'};
    border: 1px solid {'#2a5298' if IS_DARK else '#6699cc'};
    color: {'#5b9bd5' if IS_DARK else '#1a5296'};
    padding: 4px 12px;
    border-radius: 20px;
    font-family: 'Space Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 2px;
}}
.risk-warning {{
    background: {'#1a1200' if IS_DARK else '#fff8e1'};
    border-left: 4px solid #ffc107;
    padding: 10px 16px;
    border-radius: 0 8px 8px 0;
    color: {'#ffc107' if IS_DARK else '#7a5000'};
    font-size: 0.85rem;
    margin: 8px 0;
}}
/* Streamlit overrides */
.stTabs [data-baseweb="tab-list"] {{
    background: {'#0d1425' if IS_DARK else '#e8edf3'};
    border-radius: 10px;
    padding: 4px;
}}
.stTabs [data-baseweb="tab"] {{
    color: {TEXT_MUTED};
    border-radius: 8px;
}}
.stTabs [aria-selected="true"] {{
    background: {'#1e3a5f' if IS_DARK else '#ffffff'} !important;
    color: {TEXT_PRIMARY} !important;
}}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# HEADER
# ---------------------------
with _tcol1:
    st.markdown(f"""
    <div style="padding:4px 0 14px 0;">
        <span style="font-family:'Space Mono',monospace;font-size:1.7rem;font-weight:700;
            background:linear-gradient(90deg,#00e676 0%,#00bcd4 40%,#7eb3e8 100%);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">
            📡 Futures Algo Dashboard
        </span>
        <span style="font-size:0.75rem;color:{TEXT_MUTED};font-family:'Space Mono',monospace;
            margin-left:14px;vertical-align:middle;">
            {'🌙 DARK' if IS_DARK else '☀️ LIGHT'} MODE
        </span>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------
# SESSION STATE — Paper Trading
# ---------------------------
if "paper_balance" not in st.session_state:
    st.session_state.paper_balance = 30000.0
if "paper_trades" not in st.session_state:
    st.session_state.paper_trades = []
if "paper_position" not in st.session_state:
    st.session_state.paper_position = None  # {"side","entry","qty","sl","tp","time"}

# ---------------------------
# SIDEBAR CONFIG
# ---------------------------
# Theme-aware sidebar colors
SB_HDR_BG     = "#0d1a2e" if IS_DARK else "#e8f0fb"
SB_HDR_BORDER = "#1e3a5f" if IS_DARK else "#a0bde0"
SB_HDR_TEXT   = "#7eb3e8" if IS_DARK else "#1a4a8a"
SB_HDR_ICON   = "#00bcd4" if IS_DARK else "#0077cc"

def sb_header(icon, title):
    st.markdown(f"""
    <div style="background:{SB_HDR_BG};border-left:3px solid {SB_HDR_ICON};
        border-radius:0 8px 8px 0;padding:7px 12px;margin:12px 0 8px 0;">
        <span style="font-family:'Space Mono',monospace;font-size:0.78rem;
            font-weight:700;color:{SB_HDR_TEXT};letter-spacing:1px;">
            {icon} {title}
        </span>
    </div>""", unsafe_allow_html=True)

with st.sidebar:
    sb_header("⚙️", "CONFIGURATION")

    mode = st.radio("Trading Mode", ["📄 Paper Trading", "🔴 Live Trading"], index=0)
    is_paper = "Paper" in mode

    if is_paper:
        st.markdown('<span class="paper-badge">PAPER MODE — NO REAL MONEY</span>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="risk-warning">⚠️ LIVE MODE: Real funds at risk</div>', unsafe_allow_html=True)

    sb_header("🔑", "API KEYS")
    API_KEY    = st.text_input("API Key",    value="", type="password")
    API_SECRET = st.text_input("API Secret", value="", type="password")

    sb_header("📊", "MARKET")
    coin     = st.selectbox("Pair", ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT"])
    interval = st.selectbox("Timeframe", ["1m", "3m", "5m", "15m", "30m", "1h", "4h"])

    sb_header("💰", "RISK MANAGEMENT")
    capital      = st.number_input("Capital (₹)", value=30000, step=1000)
    risk_pct     = st.slider("Risk per Trade (%)", 0.5, 5.0, 1.5, step=0.5) / 100
    leverage     = st.slider("Leverage", 1, 20, 5)
    tp_ratio     = st.slider("TP Ratio (R:R)", 1.0, 5.0, 2.0, step=0.5)
    max_trades   = st.slider("Max Concurrent Trades", 1, 5, 1)

    sb_header("🎚", "INDICATOR SETTINGS")
    ema_fast   = st.number_input("EMA Fast",        value=9,  step=1)
    ema_mid    = st.number_input("EMA Mid",         value=21, step=1)
    ema_slow   = st.number_input("EMA Slow",        value=45, step=1)
    rsi_period = st.number_input("RSI Period",      value=14, step=1)
    bb_period  = st.number_input("BB Period",       value=20, step=1)
    bb_std     = st.slider("BB Std Dev",            1.5, 3.0, 2.0, step=0.5)
    atr_period = st.number_input("ATR Period (SL)", value=14, step=1)

    if is_paper and st.button("🔄 Reset Paper Account"):
        st.session_state.paper_balance  = float(capital)
        st.session_state.paper_trades   = []
        st.session_state.paper_position = None
        st.success("Paper account reset!")

# ---------------------------
# BINANCE CLIENT (only if live)
# ---------------------------
client = None
if not is_paper and API_KEY and API_SECRET:
    try:
        client = Client(API_KEY, API_SECRET)
        client.futures_ping()
        st.sidebar.success("✅ Futures connected")
    except Exception as e:
        st.sidebar.error(f"Connection failed: {e}")

# ---------------------------
# FETCH FUTURES KLINES
# ---------------------------
@st.cache_data(ttl=30)
def get_futures_data(symbol, interval, limit=500):
    url = (
        f"https://fapi.binance.com/fapi/v1/klines"
        f"?symbol={symbol}&interval={interval}&limit={limit}"
    )
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        st.error(f"Data fetch failed: {e}")
        return pd.DataFrame()

    df = pd.DataFrame(data, columns=[
        "time","open","high","low","close","volume",
        "close_time","qav","trades","tbbav","tbqav","ignore"
    ])
    for col in ["open","high","low","close","volume"]:
        df[col] = df[col].astype(float)
    df["time"] = pd.to_datetime(df["time"], unit="ms")
    return df

df = get_futures_data(coin, interval)

if df.empty:
    st.error("Could not load market data. Check your connection.")
    st.stop()

# ---------------------------
# INDICATORS
# ---------------------------
def calc_indicators(df):
    # EMA
    df["EMA_fast"] = df["close"].ewm(span=ema_fast,  adjust=False).mean()
    df["EMA_mid"]  = df["close"].ewm(span=ema_mid,   adjust=False).mean()
    df["EMA_slow"] = df["close"].ewm(span=ema_slow,  adjust=False).mean()

    # RSI
    delta = df["close"].diff()
    gain  = delta.clip(lower=0).rolling(rsi_period).mean()
    loss  = (-delta.clip(upper=0)).rolling(rsi_period).mean()
    rs    = gain / loss.replace(0, np.nan)
    df["RSI"] = 100 - (100 / (1 + rs))

    # MACD (12/26/9)
    ema12      = df["close"].ewm(span=12, adjust=False).mean()
    ema26      = df["close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_hist"]   = df["MACD"] - df["MACD_signal"]

    # Bollinger Bands
    df["BB_mid"]   = df["close"].rolling(bb_period).mean()
    rolling_std    = df["close"].rolling(bb_period).std()
    df["BB_upper"] = df["BB_mid"] + bb_std * rolling_std
    df["BB_lower"] = df["BB_mid"] - bb_std * rolling_std
    df["BB_pct"]   = (df["close"] - df["BB_lower"]) / (df["BB_upper"] - df["BB_lower"])

    # ATR (for dynamic SL)
    high_low   = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close  = (df["low"]  - df["close"].shift()).abs()
    tr         = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["ATR"]  = tr.rolling(atr_period).mean()

    # Volume SMA
    df["Vol_SMA"] = df["volume"].rolling(20).mean()

    return df

df = calc_indicators(df)
last = df.iloc[-1]
prev = df.iloc[-2]

# ---------------------------
# MULTI-CONFIRMATION SIGNAL ENGINE
# ---------------------------
def generate_signal(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]
    scores = {"BUY": 0, "SELL": 0}

    # 1. EMA stack (weight 2)
    if last["EMA_fast"] > last["EMA_mid"] > last["EMA_slow"]:
        scores["BUY"] += 2
    elif last["EMA_fast"] < last["EMA_mid"] < last["EMA_slow"]:
        scores["SELL"] += 2

    # 2. RSI (weight 1)
    if 40 < last["RSI"] < 65:
        scores["BUY"] += 1
    elif last["RSI"] > 70 or last["RSI"] < 30:
        scores["SELL"] += 1

    # 3. MACD crossover (weight 2)
    if prev["MACD"] < prev["MACD_signal"] and last["MACD"] > last["MACD_signal"]:
        scores["BUY"] += 2
    elif prev["MACD"] > prev["MACD_signal"] and last["MACD"] < last["MACD_signal"]:
        scores["SELL"] += 2
    elif last["MACD_hist"] > 0:
        scores["BUY"] += 1
    elif last["MACD_hist"] < 0:
        scores["SELL"] += 1

    # 4. Bollinger Band position (weight 1)
    if last["BB_pct"] < 0.35:
        scores["BUY"] += 1
    elif last["BB_pct"] > 0.65:
        scores["SELL"] += 1

    # 5. Volume confirmation (weight 1)
    if last["volume"] > last["Vol_SMA"] * 1.2:
        # Amplify dominant direction
        if scores["BUY"] > scores["SELL"]:
            scores["BUY"] += 1
        elif scores["SELL"] > scores["BUY"]:
            scores["SELL"] += 1

    total = scores["BUY"] + scores["SELL"]
    confidence = max(scores["BUY"], scores["SELL"]) / 7 * 100 if total else 0

    if scores["BUY"] >= 4:
        return "BUY",  round(confidence), scores
    elif scores["SELL"] >= 4:
        return "SELL", round(confidence), scores
    return "HOLD", round(confidence), scores

signal, confidence, scores = generate_signal(df)

# ---------------------------
# DYNAMIC SL/TP via ATR
# ---------------------------
atr_val = last["ATR"]
entry   = last["close"]
sl_long  = entry - (1.5 * atr_val)
tp_long  = entry + (tp_ratio * 1.5 * atr_val)
sl_short = entry + (1.5 * atr_val)
tp_short = entry - (tp_ratio * 1.5 * atr_val)

# Position sizing: risk / (entry - SL)
sl_distance = abs(entry - sl_long)
position_size_usdt = (capital * risk_pct) / (sl_distance / entry)
position_size_usdt = min(position_size_usdt, capital * 0.2)  # cap at 20% of capital

# ---------------------------
# LAYOUT — Main Dashboard
# ---------------------------
tab1, tab2, tab3, tab4 = st.tabs(["📡 Live Signal", "📊 Backtest", "📄 Paper Trades", "👤 About"])

with tab1:
    # Row 1: Price + Signal
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div style="color:#7eb3e8;font-family:'Space Mono',monospace;font-size:0.7rem;letter-spacing:2px">LAST PRICE</div>
            <div style="font-size:2rem;font-weight:700;color:#e0e6f0">₹{entry:,.2f}</div>
            <div style="font-size:0.8rem;color:#aaa">{coin} • {interval} • Futures</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        rsi_color = "#ff1744" if last["RSI"] > 70 else "#00e676" if last["RSI"] < 30 else "#7eb3e8"
        st.markdown(f"""
        <div class="metric-card">
            <div style="color:#7eb3e8;font-family:'Space Mono',monospace;font-size:0.7rem;letter-spacing:2px">RSI ({rsi_period})</div>
            <div style="font-size:2rem;font-weight:700;color:{rsi_color}">{last['RSI']:.1f}</div>
            <div style="font-size:0.8rem;color:#aaa">{"Overbought ⚠️" if last['RSI']>70 else "Oversold ⚠️" if last['RSI']<30 else "Neutral"}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        macd_color = "#00e676" if last["MACD_hist"] > 0 else "#ff1744"
        st.markdown(f"""
        <div class="metric-card">
            <div style="color:#7eb3e8;font-family:'Space Mono',monospace;font-size:0.7rem;letter-spacing:2px">MACD HISTOGRAM</div>
            <div style="font-size:2rem;font-weight:700;color:{macd_color}">{last['MACD_hist']:.4f}</div>
            <div style="font-size:0.8rem;color:#aaa">{"Bullish momentum" if last['MACD_hist']>0 else "Bearish momentum"}</div>
        </div>
        """, unsafe_allow_html=True)

    # Row 2: Single unified signal card
    st.markdown("### Signal")

    # Colors and labels based on signal
    if signal == "BUY":
        sig_bg       = "linear-gradient(135deg, #062a1e, #0a3d28)"
        sig_border   = "#00e676"
        sig_color    = "#00e676"
        sig_icon     = "▲"
        sig_text     = f"LONG  ·  {coin}"
        sig_sub      = "Bullish — enter long position"
        conf_color   = "#00e676" if confidence > 65 else "#ffc107"
        bar_color    = "#00e676"
    elif signal == "SELL":
        sig_bg       = "linear-gradient(135deg, #2a0608, #3d0a0e)"
        sig_border   = "#ff1744"
        sig_color    = "#ff5252"
        sig_icon     = "▼"
        sig_text     = f"SHORT  ·  {coin}"
        sig_sub      = "Bearish — enter short position"
        conf_color   = "#ff5252"
        bar_color    = "#ff1744"
    else:
        sig_bg       = "linear-gradient(135deg, #111827, #1a2235)"
        sig_border   = "#444"
        sig_color    = "#888"
        sig_icon     = "—"
        sig_text     = f"HOLD  ·  {coin}"
        sig_sub      = "No clear setup — wait for confirmation"
        conf_color   = "#888"
        bar_color    = "#555"

    bar_pct = int(max(scores["BUY"], scores["SELL"]) / 7 * 100)

    # Indicator pills
    ind_names = ["EMA stack", "RSI zone", "MACD cross", "MACD hist", "BB position", "Volume"]
    dominant  = "BUY" if signal == "BUY" else "SELL"
    ind_active = scores[dominant] if signal != "HOLD" else 0
    pills_html = ""
    for i, name in enumerate(ind_names):
        active = i < ind_active
        pill_bg    = sig_border if active else "#1e2a3a"
        pill_color = "#0a0e1a"  if active else "#556"
        pills_html += f'<span style="background:{pill_bg};color:{pill_color};padding:3px 12px;border-radius:20px;font-size:0.72rem;font-family:\'Space Mono\',monospace;">{"✓ " if active else ""}{name}</span> '

    st.markdown(f"""
    <div style="background:{sig_bg};border:1px solid {sig_border};border-radius:14px;padding:22px 28px;">
        <div style="display:flex;align-items:center;justify-content:space-between;">
            <div style="display:flex;align-items:center;gap:18px;">
                <div style="font-size:2.8rem;color:{sig_color};line-height:1;">{sig_icon}</div>
                <div>
                    <div style="font-family:'Space Mono',monospace;font-size:1.6rem;font-weight:700;color:{sig_color};letter-spacing:1px;">{sig_text}</div>
                    <div style="font-size:0.82rem;color:#aaa;margin-top:4px;">{sig_sub}</div>
                </div>
            </div>
            <div style="text-align:right;">
                <div style="font-family:'Space Mono',monospace;font-size:0.65rem;color:#7eb3e8;letter-spacing:2px;">CONFIDENCE</div>
                <div style="font-size:2.2rem;font-weight:700;color:{conf_color};">{confidence}%</div>
                <div style="font-size:0.7rem;color:#666;">Score {scores['BUY']} buy / {scores['SELL']} sell</div>
            </div>
        </div>
        <div style="margin-top:16px;">
            <div style="height:5px;background:#1a2235;border-radius:99px;overflow:hidden;">
                <div style="width:{bar_pct}%;height:100%;background:{bar_color};border-radius:99px;"></div>
            </div>
        </div>
        <div style="margin-top:12px;display:flex;flex-wrap:wrap;gap:6px;">
            {pills_html}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Row 3: SL/TP/Position
    st.markdown("### Trade Plan")
    c1, c2, c3, c4 = st.columns(4)
    side_sl = sl_long  if signal != "SELL" else sl_short
    side_tp = tp_long  if signal != "SELL" else tp_short
    with c1:
        st.markdown(f"""<div class="metric-card">
            <div style="color:#7eb3e8;font-family:'Space Mono',monospace;font-size:0.7rem">ENTRY</div>
            <div style="font-size:1.4rem;color:#e0e6f0">₹{entry:,.2f}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card">
            <div style="color:#ff1744;font-family:'Space Mono',monospace;font-size:0.7rem">STOP LOSS</div>
            <div style="font-size:1.4rem;color:#ff7043">₹{side_sl:,.2f}</div>
            <div style="font-size:0.75rem;color:#aaa">ATR × 1.5</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="metric-card">
            <div style="color:#00e676;font-family:'Space Mono',monospace;font-size:0.7rem">TAKE PROFIT</div>
            <div style="font-size:1.4rem;color:#69f0ae">₹{side_tp:,.2f}</div>
            <div style="font-size:0.75rem;color:#aaa">R:R = 1:{tp_ratio}</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="metric-card">
            <div style="color:#ffc107;font-family:'Space Mono',monospace;font-size:0.7rem">POSITION SIZE</div>
            <div style="font-size:1.4rem;color:#ffd740">₹{position_size_usdt:,.0f}</div>
            <div style="font-size:0.75rem;color:#aaa">Leverage {leverage}x</div>
        </div>""", unsafe_allow_html=True)

    # Row 4: Plotly Candlestick Chart with exact BUY/SELL arrows on candles
    st.markdown("### Chart")

    # Use last 120 candles for clean display
    plot_df = df.tail(120).copy().reset_index(drop=True)

    # ── Category-axis trick: format timestamps as strings so Plotly treats x
    #    as a category axis (no time gaps). This matches TradingView bar-for-bar.
    def fmt_x(ts):
        if hasattr(ts, "strftime"):
            return ts.strftime("%d %b %H:%M")
        return str(ts)
    plot_df["x_label"] = plot_df["time"].apply(fmt_x)
    XS = plot_df["x_label"]   # shorthand used throughout

    # --- Backtest signals on visible candles for arrow markers ---
    buy_times, buy_prices   = [], []
    sell_times, sell_prices = [], []

    for i in range(5, len(plot_df)):
        r  = plot_df.iloc[i]
        pr = plot_df.iloc[i - 1]
        s  = {"BUY": 0, "SELL": 0}

        if r["EMA_fast"] > r["EMA_mid"] > r["EMA_slow"]:   s["BUY"]  += 2
        elif r["EMA_fast"] < r["EMA_mid"] < r["EMA_slow"]: s["SELL"] += 2
        if 40 < r["RSI"] < 65:                             s["BUY"]  += 1
        elif r["RSI"] > 70 or r["RSI"] < 30:               s["SELL"] += 1
        if pr["MACD"] < pr["MACD_signal"] and r["MACD"] > r["MACD_signal"]: s["BUY"]  += 2
        elif pr["MACD"] > pr["MACD_signal"] and r["MACD"] < r["MACD_signal"]: s["SELL"] += 2
        elif r["MACD_hist"] > 0: s["BUY"] += 1
        else:                    s["SELL"] += 1
        if r["BB_pct"] < 0.35:   s["BUY"]  += 1
        elif r["BB_pct"] > 0.65: s["SELL"] += 1

        if s["BUY"] >= 4:
            buy_times.append(r["x_label"])
            buy_prices.append(r["low"] * 0.9985)   # just below candle low
        elif s["SELL"] >= 4:
            sell_times.append(r["x_label"])
            sell_prices.append(r["high"] * 1.0015)  # just above candle high

    # --- Build subplots: price + volume + RSI + MACD ---
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.55, 0.15, 0.15, 0.15],
        subplot_titles=("", "Volume", "RSI", "MACD")
    )

    # 1. Candlesticks
    fig.add_trace(go.Candlestick(
        x=XS,
        open=plot_df["open"], high=plot_df["high"],
        low=plot_df["low"],   close=plot_df["close"],
        increasing_line_color="#00e676", decreasing_line_color="#ff1744",
        increasing_fillcolor="#00e676",  decreasing_fillcolor="#ff1744",
        name="Price", showlegend=False,
        line=dict(width=1),
        whiskerwidth=0.3,
    ), row=1, col=1)

    # 2. Bollinger Bands
    fig.add_trace(go.Scatter(
        x=XS, y=plot_df["BB_upper"],
        line=dict(color="rgba(126,179,232,0.35)", width=1, dash="dot"),
        name="BB Upper", showlegend=False,
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=XS, y=plot_df["BB_lower"],
        line=dict(color="rgba(126,179,232,0.35)", width=1, dash="dot"),
        fill="tonexty", fillcolor="rgba(126,179,232,0.04)",
        name="BB Lower", showlegend=False,
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=XS, y=plot_df["BB_mid"],
        line=dict(color="rgba(126,179,232,0.2)", width=1),
        name="BB Mid", showlegend=False,
    ), row=1, col=1)

    # 3. EMAs
    fig.add_trace(go.Scatter(
        x=XS, y=plot_df["EMA_fast"],
        line=dict(color="#ffd740", width=1.2),
        name=f"EMA{ema_fast}", showlegend=True,
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=XS, y=plot_df["EMA_mid"],
        line=dict(color="#40c4ff", width=1.2),
        name=f"EMA{ema_mid}", showlegend=True,
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=XS, y=plot_df["EMA_slow"],
        line=dict(color="#ea80fc", width=1.2),
        name=f"EMA{ema_slow}", showlegend=True,
    ), row=1, col=1)

    # 4. BUY arrows — green triangles below candle
    if buy_times:
        fig.add_trace(go.Scatter(
            x=buy_times, y=buy_prices,
            mode="markers+text",
            marker=dict(
                symbol="triangle-up",
                size=14,
                color="#00e676",
                line=dict(color="#004d20", width=1.5),
            ),
            text=["BUY"] * len(buy_times),
            textposition="bottom center",
            textfont=dict(color="#00e676", size=10, family="Space Mono"),
            name="BUY Signal", showlegend=True,
        ), row=1, col=1)

    # 5. SELL arrows — red triangles above candle
    if sell_times:
        fig.add_trace(go.Scatter(
            x=sell_times, y=sell_prices,
            mode="markers+text",
            marker=dict(
                symbol="triangle-down",
                size=14,
                color="#ff1744",
                line=dict(color="#4d0010", width=1.5),
            ),
            text=["SELL"] * len(sell_times),
            textposition="top center",
            textfont=dict(color="#ff1744", size=10, family="Space Mono"),
            name="SELL Signal", showlegend=True,
        ), row=1, col=1)

    # 6. Current SL / TP lines (only if signal is active)
    if signal in ("BUY", "SELL"):
        fig.add_hline(
            y=side_sl, line=dict(color="#ff5252", width=1.2, dash="dash"),
            annotation_text=f"SL {side_sl:,.0f}",
            annotation_font_color="#ff5252",
            annotation_position="right",
            row=1, col=1,
        )
        fig.add_hline(
            y=side_tp, line=dict(color="#69f0ae", width=1.2, dash="dash"),
            annotation_text=f"TP {side_tp:,.0f}",
            annotation_font_color="#69f0ae",
            annotation_position="right",
            row=1, col=1,
        )

    # 6b. Support & Resistance levels (pivot-point clustering)
    sr_window = 10  # local high/low lookback

    raw_supports    = []
    raw_resistances = []

    for i in range(sr_window, len(plot_df) - sr_window):
        lo = plot_df["low"].iloc[i]
        hi = plot_df["high"].iloc[i]
        # local low = support
        if lo == plot_df["low"].iloc[i - sr_window : i + sr_window + 1].min():
            raw_supports.append(lo)
        # local high = resistance
        if hi == plot_df["high"].iloc[i - sr_window : i + sr_window + 1].max():
            raw_resistances.append(hi)

    def cluster_levels(levels, tolerance_pct=0.003):
        """Merge nearby levels into single representative price."""
        if not levels:
            return []
        levels = sorted(levels)
        clusters, group = [], [levels[0]]
        for lvl in levels[1:]:
            if abs(lvl - group[-1]) / group[-1] < tolerance_pct:
                group.append(lvl)
            else:
                clusters.append(np.mean(group))
                group = [lvl]
        clusters.append(np.mean(group))
        return clusters

    support_levels    = cluster_levels(raw_supports,    tolerance_pct=0.004)
    resistance_levels = cluster_levels(raw_resistances, tolerance_pct=0.004)

    # Keep only levels within visible price range
    price_min = plot_df["low"].min()
    price_max = plot_df["high"].max()
    price_range = price_max - price_min

    support_levels    = [s for s in support_levels    if price_min - price_range * 0.05 <= s <= price_max + price_range * 0.05]
    resistance_levels = [r for r in resistance_levels if price_min - price_range * 0.05 <= r <= price_max + price_range * 0.05]

    # Draw support lines (green dashed)
    for i, lvl in enumerate(support_levels):
        fig.add_hline(
            y=lvl,
            line=dict(color="rgba(0,230,118,0.45)", width=1, dash="dot"),
            annotation_text=f"S {lvl:,.0f}" if i == 0 else f"S {lvl:,.0f}",
            annotation_font_color="rgba(0,230,118,0.8)",
            annotation_font_size=9,
            annotation_position="left",
            row=1, col=1,
        )

    # Draw resistance lines (red dashed)
    for i, lvl in enumerate(resistance_levels):
        fig.add_hline(
            y=lvl,
            line=dict(color="rgba(255,23,68,0.45)", width=1, dash="dot"),
            annotation_text=f"R {lvl:,.0f}",
            annotation_font_color="rgba(255,82,82,0.8)",
            annotation_font_size=9,
            annotation_position="left",
            row=1, col=1,
        )

    # 6c. Trendlines — linear regression on pivot highs and pivot lows
    def find_pivots(series, window=8, kind="low"):
        pivots = []
        for i in range(window, len(series) - window):
            val = series.iloc[i]
            neighborhood = series.iloc[i - window : i + window + 1]
            if kind == "low"  and val == neighborhood.min():
                pivots.append((i, val))
            if kind == "high" and val == neighborhood.max():
                pivots.append((i, val))
        return pivots

    def fit_trendline(pivots, n_points=5):
        """Fit a linear regression line through the last n pivot points."""
        if len(pivots) < 2:
            return None
        pts = pivots[-n_points:]
        xs  = np.array([p[0] for p in pts], dtype=float)
        ys  = np.array([p[1] for p in pts], dtype=float)
        coeffs = np.polyfit(xs, ys, 1)
        return coeffs  # (slope, intercept)

    pivot_lows  = find_pivots(plot_df["low"],  window=8, kind="low")
    pivot_highs = find_pivots(plot_df["high"], window=8, kind="high")

    trend_x0 = plot_df["x_label"].iloc[0]
    trend_x1 = plot_df["x_label"].iloc[-1]

    # Uptrend line (through pivot lows)
    coeffs_up = fit_trendline(pivot_lows, n_points=5)
    if coeffs_up is not None:
        x0_idx = 0
        x1_idx = len(plot_df) - 1
        y0 = np.polyval(coeffs_up, x0_idx)
        y1 = np.polyval(coeffs_up, x1_idx)
        fig.add_trace(go.Scatter(
            x=[trend_x0, trend_x1],
            y=[y0, y1],
            mode="lines",
            line=dict(color="rgba(0,230,118,0.7)", width=1.5, dash="solid"),
            name="Uptrend", showlegend=True,
        ), row=1, col=1)
        # Label at midpoint
        mid_idx = len(plot_df) // 2
        fig.add_annotation(
            x=XS.iloc[mid_idx],
            y=np.polyval(coeffs_up, mid_idx),
            text="Uptrend",
            font=dict(color="rgba(0,230,118,0.9)", size=9, family="Space Mono"),
            showarrow=False, yshift=8,
            row=1, col=1,
        )

    # Downtrend line (through pivot highs)
    coeffs_dn = fit_trendline(pivot_highs, n_points=5)
    if coeffs_dn is not None:
        x0_idx = 0
        x1_idx = len(plot_df) - 1
        y0 = np.polyval(coeffs_dn, x0_idx)
        y1 = np.polyval(coeffs_dn, x1_idx)
        fig.add_trace(go.Scatter(
            x=[trend_x0, trend_x1],
            y=[y0, y1],
            mode="lines",
            line=dict(color="rgba(255,82,82,0.7)", width=1.5, dash="solid"),
            name="Downtrend", showlegend=True,
        ), row=1, col=1)
        mid_idx = len(plot_df) // 2
        fig.add_annotation(
            x=XS.iloc[mid_idx],
            y=np.polyval(coeffs_dn, mid_idx),
            text="Downtrend",
            font=dict(color="rgba(255,82,82,0.9)", size=9, family="Space Mono"),
            showarrow=False, yshift=-12,
            row=1, col=1,
        )

    # 7. Volume bars
    vol_colors = [
        "#00e676" if plot_df["close"].iloc[i] >= plot_df["open"].iloc[i] else "#ff1744"
        for i in range(len(plot_df))
    ]
    fig.add_trace(go.Bar(
        x=XS, y=plot_df["volume"],
        marker_color=vol_colors, marker_opacity=0.6,
        name="Volume", showlegend=False,
    ), row=2, col=1)
    fig.add_trace(go.Scatter(
        x=XS, y=plot_df["Vol_SMA"],
        line=dict(color="#ffd740", width=1),
        name="Vol SMA", showlegend=False,
    ), row=2, col=1)

    # 8. RSI
    fig.add_trace(go.Scatter(
        x=XS, y=plot_df["RSI"],
        line=dict(color="#40c4ff", width=1.5),
        name="RSI", showlegend=False,
    ), row=3, col=1)
    fig.add_hline(y=70, line=dict(color="#ff5252", width=0.8, dash="dot"), row=3, col=1)
    fig.add_hline(y=30, line=dict(color="#00e676", width=0.8, dash="dot"), row=3, col=1)
    fig.add_hrect(y0=30, y1=70, fillcolor="rgba(126,179,232,0.04)", line_width=0, row=3, col=1)

    # 9. MACD
    macd_bar_colors = [
        "#00e676" if v >= 0 else "#ff1744"
        for v in plot_df["MACD_hist"]
    ]
    fig.add_trace(go.Bar(
        x=XS, y=plot_df["MACD_hist"],
        marker_color=macd_bar_colors, marker_opacity=0.7,
        name="MACD Hist", showlegend=False,
    ), row=4, col=1)
    fig.add_trace(go.Scatter(
        x=XS, y=plot_df["MACD"],
        line=dict(color="#ffd740", width=1.2),
        name="MACD", showlegend=False,
    ), row=4, col=1)
    fig.add_trace(go.Scatter(
        x=XS, y=plot_df["MACD_signal"],
        line=dict(color="#ea80fc", width=1.2),
        name="Signal", showlegend=False,
    ), row=4, col=1)

    # --- Layout ---
    fig.update_layout(
        height=720,
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(family="Space Mono, monospace", color=LEGEND_FG, size=11),
        xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=80, t=30, b=10),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.01,
            xanchor="left", x=0,
            font=dict(size=10, color=LEGEND_FG),
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(0,0,0,0)",
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=BG_SURFACE,
            font_size=11,
            font_family="Space Mono, monospace",
        ),
    )

    # Style all axes — category type forces bar-for-bar alignment (no time gaps)
    axis_style = dict(
        gridcolor=GRID_COLOR, gridwidth=0.5,
        zerolinecolor=BORDER_CARD,
        tickfont=dict(color=LEGEND_FG, size=10),
        showgrid=True,
        type="category",
    )
    yaxis_style = dict(
        gridcolor=GRID_COLOR, gridwidth=0.5,
        zerolinecolor=BORDER_CARD,
        tickfont=dict(color=LEGEND_FG, size=10),
        showgrid=True,
        type="linear",
    )
    for i in range(1, 5):
        fig.update_xaxes(
            axis_style,
            row=i, col=1,
            showticklabels=(i == 4),
            nticks=10,
        )
        fig.update_yaxes(yaxis_style, row=i, col=1)

    # Subplot title colors
    for ann in fig.layout.annotations:
        ann.font.color = "#7eb3e8"
        ann.font.size  = 10

    st.plotly_chart(fig, use_container_width=True, config={
        "displayModeBar": True,
        "modeBarButtonsToRemove": ["autoScale2d", "lasso2d", "select2d"],
        "displaylogo": False,
    })

    # Row 5: TradingView Live Chart (RSI + EMA only, no BB / MACD)
    st.markdown("### Live TradingView Chart")
    tv_interval = interval.replace("m","").replace("h","60") if "h" in interval else interval.replace("m","")
    components.html(f"""
    <div style="position:relative;border-radius:14px;overflow:hidden;border:1px solid #1e3a5f;">
      <div id="tv_chart"></div>

      <div style="
        position:absolute;top:12px;left:12px;z-index:99;
        background:{'rgba(0,35,18,0.95)' if signal=='BUY' else 'rgba(35,0,8,0.95)' if signal=='SELL' else 'rgba(15,18,30,0.95)'};
        border:1.5px solid {'#00e676' if signal=='BUY' else '#ff1744' if signal=='SELL' else '#444'};
        border-radius:8px;padding:7px 16px;
        font-family:'Space Mono',monospace;font-size:0.92rem;font-weight:700;
        color:{'#00e676' if signal=='BUY' else '#ff1744' if signal=='SELL' else '#888'};
        letter-spacing:1px;pointer-events:none;">
        {'▲ BUY' if signal=='BUY' else '▼ SELL' if signal=='SELL' else '— HOLD'} &nbsp;
        <span style="font-size:0.7rem;opacity:0.8;">{confidence}%</span>
      </div>

      <div style="
        position:absolute;top:12px;right:12px;z-index:99;
        background:rgba(10,14,26,0.95);border:1px solid #1e3a5f;
        border-radius:8px;padding:7px 14px;
        font-family:'Space Mono',monospace;font-size:0.7rem;
        color:#7eb3e8;pointer-events:none;line-height:1.8;">
        <span style="color:#777;">SL</span> <span style="color:#ff5252;">{side_sl:,.0f}</span>
        &nbsp;&nbsp;
        <span style="color:#777;">TP</span> <span style="color:#69f0ae;">{side_tp:,.0f}</span>
      </div>
    </div>

    <script src="https://s3.tradingview.com/tv.js"></script>
    <script>
    new TradingView.widget({{
      "width":  "100%",
      "height": 520,
      "symbol": "BINANCE:{coin}.P",
      "interval": "{tv_interval}",
      "timezone": "Asia/Kolkata",
      "theme": "dark",
      "style": "1",
      "locale": "en",
      "toolbar_bg": "#0d1425",
      "enable_publishing": false,
      "hide_top_toolbar": false,
      "hide_legend": false,
      "studies": [
        "RSI@tv-basicstudies",
        {{"id": "MAExp@tv-basicstudies", "inputs": {{"length": {ema_fast}, "source": "close"}}}},
        {{"id": "MAExp@tv-basicstudies", "inputs": {{"length": {ema_mid},  "source": "close"}}}},
        {{"id": "MAExp@tv-basicstudies", "inputs": {{"length": {ema_slow}, "source": "close"}}}},
        {{"id": "MAExp@tv-basicstudies", "inputs": {{"length": 200,        "source": "close"}}}}
      ],
      "container_id": "tv_chart",
      "overrides": {{
        "mainSeriesProperties.candleStyle.upColor":         "#00e676",
        "mainSeriesProperties.candleStyle.downColor":       "#ff1744",
        "mainSeriesProperties.candleStyle.borderUpColor":   "#00e676",
        "mainSeriesProperties.candleStyle.borderDownColor": "#ff1744",
        "mainSeriesProperties.candleStyle.wickUpColor":     "#00e676",
        "mainSeriesProperties.candleStyle.wickDownColor":   "#ff1744",
        "paneProperties.background":                        "#0d1425",
        "paneProperties.backgroundType":                    "solid",
        "paneProperties.vertGridProperties.color":          "#111827",
        "paneProperties.horzGridProperties.color":          "#111827",
        "scalesProperties.textColor":                       "#7eb3e8",
        "scalesProperties.backgroundColor":                 "#0d1425"
      }},
      "studies_overrides": {{
        "moving average exponential.ma.color.0": "#ffd740",
        "moving average exponential.ma.linewidth": 1,
        "rsi.plot.color": "#40c4ff",
        "rsi.plot.linewidth": 1
      }}
    }});
    </script>
    """, height=560)

    # Row 6: Execute Trade — single centered button
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    exec_col, _ = st.columns([1, 2])
    with exec_col:
        btn_label = "📄 Execute Paper Trade" if is_paper else "🔴 Execute Live Trade"
        if st.button(btn_label, use_container_width=True, disabled=(signal == "HOLD")):
            if is_paper:
                qty = round(position_size_usdt / entry, 6)
                trade = {
                    "time":   str(datetime.datetime.now().strftime("%H:%M:%S")),
                    "pair":   coin,
                    "side":   "LONG" if signal == "BUY" else "SHORT",
                    "entry":  entry,
                    "sl":     side_sl,
                    "tp":     side_tp,
                    "qty":    qty,
                    "size":   round(position_size_usdt, 2),
                    "status": "OPEN",
                    "pnl":    None,
                }
                st.session_state.paper_trades.append(trade)
                st.session_state.paper_position = trade
                st.success(f"✅ Paper {trade['side']} opened @ ₹{entry:,.2f}  |  SL ₹{side_sl:,.2f}  |  TP ₹{side_tp:,.2f}")
            else:
                if client:
                    try:
                        side_enum = SIDE_BUY if signal == "BUY" else SIDE_SELL
                        order = client.futures_create_order(
                            symbol=coin,
                            side=side_enum,
                            type=ORDER_TYPE_MARKET,
                            quantity=round(position_size_usdt / entry, 3)
                        )
                        st.success(f"✅ Order placed: {order['orderId']}")
                    except Exception as e:
                        st.error(f"Order failed: {e}")
                else:
                    st.error("Client not connected. Add API keys.")

# ---------------------------
# TAB 2: BACKTEST
# ---------------------------
with tab2:
    st.markdown(f"### Backtest — Smart Multi-Filter Strategy")

    # ── Add EMA200 for trend filter ──────────────────────────────────────────
    df["EMA200"] = df["close"].ewm(span=200, adjust=False).mean()

    # ── Add higher-timeframe trend via close slope ────────────────────────
    df["EMA_slope"] = df["EMA_slow"].diff(3)   # slope of EMA45 over 3 bars

    bt_balance  = float(capital)
    bt_position = None
    bt_trades   = []
    bt_equity   = [bt_balance]
    cooldown    = 0

    start_i = max(210, atr_period + 10)

    for i in range(start_i, len(df)):
        row  = df.iloc[i]
        prow = df.iloc[i - 1]
        p2   = df.iloc[i - 2]

        if cooldown > 0:
            cooldown -= 1
            bt_equity.append(bt_balance)
            continue

        atr_i = row["ATR"]
        if pd.isna(atr_i) or atr_i == 0 or pd.isna(row["EMA200"]):
            bt_equity.append(bt_balance)
            continue

        # ── Signal scoring (max 10) ───────────────────────────────────────
        s = {"BUY": 0, "SELL": 0}

        # 1. EMA stack alignment (weight 3) — strongest trend signal
        if row["EMA_fast"] > row["EMA_mid"] > row["EMA_slow"]:
            s["BUY"] += 3
        elif row["EMA_fast"] < row["EMA_mid"] < row["EMA_slow"]:
            s["SELL"] += 3

        # 2. EMA200 macro trend (weight 2) — only trade with big trend
        margin = atr_i * 0.5   # price must be clearly above/below EMA200
        if row["close"] > row["EMA200"] + margin:
            s["BUY"] += 2
        elif row["close"] < row["EMA200"] - margin:
            s["SELL"] += 2

        # 3. EMA45 slope — trend accelerating (weight 1)
        if not pd.isna(row["EMA_slope"]):
            if row["EMA_slope"] > 0:  s["BUY"]  += 1
            elif row["EMA_slope"] < 0: s["SELL"] += 1

        # 4. RSI momentum zone (weight 1)
        if 52 < row["RSI"] < 70:    s["BUY"]  += 1
        elif 30 < row["RSI"] < 48:  s["SELL"] += 1

        # 5. MACD fresh crossover only (weight 2) — highest quality signal
        if   prow["MACD"] < prow["MACD_signal"] and row["MACD"] > row["MACD_signal"] and row["MACD"] < 0:
            s["BUY"] += 2   # crossover from below zero = strongest
        elif prow["MACD"] < prow["MACD_signal"] and row["MACD"] > row["MACD_signal"]:
            s["BUY"] += 1
        elif prow["MACD"] > prow["MACD_signal"] and row["MACD"] < row["MACD_signal"] and row["MACD"] > 0:
            s["SELL"] += 2
        elif prow["MACD"] > prow["MACD_signal"] and row["MACD"] < row["MACD_signal"]:
            s["SELL"] += 1

        # 6. Volume surge confirms move (weight 1)
        if row["volume"] > row["Vol_SMA"] * 1.5:
            if s["BUY"] > s["SELL"]:   s["BUY"]  += 1
            elif s["SELL"] > s["BUY"]: s["SELL"] += 1

        # ── Entry — require 7/10 AND no conflicting opposite score ────────
        if bt_position is None:
            long_ok  = s["BUY"]  >= 7 and s["SELL"] <= 1
            short_ok = s["SELL"] >= 7 and s["BUY"]  <= 1

            if long_ok:
                sl = row["close"] - 1.5 * atr_i
                tp = row["close"] + tp_ratio * 1.5 * atr_i
                bt_position = {"side": "LONG",  "entry": row["close"],
                               "sl": sl, "tp": tp, "bars": 0,
                               "peak": row["close"]}

            elif short_ok:
                sl = row["close"] + 1.5 * atr_i
                tp = row["close"] - tp_ratio * 1.5 * atr_i
                bt_position = {"side": "SHORT", "entry": row["close"],
                               "sl": sl, "tp": tp, "bars": 0,
                               "peak": row["close"]}

        # ── Exit logic ────────────────────────────────────────────────────
        else:
            bt_position["bars"] += 1
            max_bars = 30

            closed = False

            if bt_position["side"] == "LONG":
                # Update peak
                if row["high"] > bt_position["peak"]:
                    bt_position["peak"] = row["high"]
                # Trailing stop: tighter once in profit
                profit_pct = (bt_position["peak"] - bt_position["entry"]) / bt_position["entry"]
                trail_mult = 0.8 if profit_pct > 0.01 else 1.2
                trail_sl   = bt_position["peak"] - trail_mult * atr_i
                if trail_sl > bt_position["sl"]:
                    bt_position["sl"] = trail_sl

                if row["low"] <= bt_position["sl"]:
                    pnl_r = bt_position["sl"] - bt_position["entry"]
                    pnl   = (pnl_r / bt_position["entry"]) * bt_balance * leverage * risk_pct * 10
                    pnl   = max(pnl, -bt_balance * risk_pct)
                    pnl   = min(pnl,  bt_balance * risk_pct * tp_ratio)
                    bt_balance += pnl
                    bt_trades.append({"result": "WIN" if pnl > 0 else "LOSS", "pnl": round(pnl, 2)})
                    closed = True

                elif row["high"] >= bt_position["tp"]:
                    gain = bt_balance * risk_pct * tp_ratio
                    bt_balance += gain
                    bt_trades.append({"result": "WIN", "pnl": round(gain, 2)})
                    closed = True

                elif bt_position["bars"] >= max_bars:
                    pnl = (row["close"] - bt_position["entry"]) / bt_position["entry"] * bt_balance * risk_pct * 5
                    pnl = max(pnl, -bt_balance * risk_pct * 0.5)
                    bt_balance += pnl
                    bt_trades.append({"result": "WIN" if pnl > 0 else "LOSS", "pnl": round(pnl, 2)})
                    closed = True

            else:  # SHORT
                if row["low"] < bt_position["peak"]:
                    bt_position["peak"] = row["low"]
                profit_pct = (bt_position["entry"] - bt_position["peak"]) / bt_position["entry"]
                trail_mult = 0.8 if profit_pct > 0.01 else 1.2
                trail_sl   = bt_position["peak"] + trail_mult * atr_i
                if trail_sl < bt_position["sl"]:
                    bt_position["sl"] = trail_sl

                if row["high"] >= bt_position["sl"]:
                    pnl_r = bt_position["entry"] - bt_position["sl"]
                    pnl   = (pnl_r / bt_position["entry"]) * bt_balance * leverage * risk_pct * 10
                    pnl   = max(pnl, -bt_balance * risk_pct)
                    pnl   = min(pnl,  bt_balance * risk_pct * tp_ratio)
                    bt_balance += pnl
                    bt_trades.append({"result": "WIN" if pnl > 0 else "LOSS", "pnl": round(pnl, 2)})
                    closed = True

                elif row["low"] <= bt_position["tp"]:
                    gain = bt_balance * risk_pct * tp_ratio
                    bt_balance += gain
                    bt_trades.append({"result": "WIN", "pnl": round(gain, 2)})
                    closed = True

                elif bt_position["bars"] >= max_bars:
                    pnl = (bt_position["entry"] - row["close"]) / bt_position["entry"] * bt_balance * risk_pct * 5
                    pnl = max(pnl, -bt_balance * risk_pct * 0.5)
                    bt_balance += pnl
                    bt_trades.append({"result": "WIN" if pnl > 0 else "LOSS", "pnl": round(pnl, 2)})
                    closed = True

            if closed:
                cooldown    = 5 if bt_trades[-1]["result"] == "LOSS" else 2
                bt_position = None

        bt_equity.append(bt_balance)

    # ── Stats ─────────────────────────────────────────────────────────────
    total_trades  = len(bt_trades)
    wins          = sum(1 for t in bt_trades if t["result"] == "WIN")
    losses        = total_trades - wins
    win_rate      = (wins / total_trades * 100) if total_trades else 0
    net_pnl       = bt_balance - capital
    pnl_pct       = (net_pnl / capital) * 100
    avg_win       = np.mean([t["pnl"] for t in bt_trades if t["pnl"] > 0]) if wins   else 0
    avg_loss      = np.mean([t["pnl"] for t in bt_trades if t["pnl"] < 0]) if losses else 0
    gross_win     = sum(t["pnl"] for t in bt_trades if t["pnl"] > 0)
    gross_loss    = abs(sum(t["pnl"] for t in bt_trades if t["pnl"] < 0))
    profit_factor = (gross_win / gross_loss) if gross_loss > 0 else float("inf")

    equity_arr   = np.array(bt_equity)
    rolling_max  = np.maximum.accumulate(equity_arr)
    drawdown_arr = (equity_arr - rolling_max) / rolling_max * 100
    max_drawdown = drawdown_arr.min()

    # ── Stats cards ──────────────────────────────────────────────────────
    sc1, sc2, sc3, sc4 = st.columns(4)
    for col, label, val, color in [
        (sc1, "FINAL BALANCE",
         f"₹{bt_balance:,.0f}", TEXT_PRIMARY),
        (sc2, "NET P&L",
         f"{'+'if net_pnl>=0 else ''}₹{net_pnl:,.0f} ({pnl_pct:.1f}%)",
         "#00e676" if net_pnl >= 0 else "#ff1744"),
        (sc3, "WIN RATE",
         f"{win_rate:.1f}%", "#00e676" if win_rate >= 55 else "#ffc107"),
        (sc4, "MAX DRAWDOWN",
         f"{max_drawdown:.1f}%", "#ff7043"),
    ]:
        col.markdown(f"""<div class="metric-card">
            <div style="color:{TEXT_MUTED};font-family:'Space Mono',monospace;font-size:0.7rem">{label}</div>
            <div style="font-size:1.5rem;font-weight:700;color:{color}">{val}</div>
        </div>""", unsafe_allow_html=True)

    sc5, sc6, sc7, sc8 = st.columns(4)
    for col, label, val, color in [
        (sc5, "TOTAL TRADES",  str(total_trades),              TEXT_PRIMARY),
        (sc6, "PROFIT FACTOR", f"{profit_factor:.2f}",
         "#00e676" if profit_factor >= 1.5 else "#ffc107"),
        (sc7, "AVG WIN",       f"₹{avg_win:,.0f}",  "#69f0ae"),
        (sc8, "AVG LOSS",      f"₹{avg_loss:,.0f}", "#ff7043"),
    ]:
        col.markdown(f"""<div class="metric-card">
            <div style="color:{TEXT_MUTED};font-family:'Space Mono',monospace;font-size:0.7rem">{label}</div>
            <div style="font-size:1.5rem;font-weight:700;color:{color}">{val}</div>
        </div>""", unsafe_allow_html=True)

    # ── Plotly charts (theme-aware) ───────────────────────────────────────
    bt_fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("Equity Curve", "Trade P&L Bars",
                        "Drawdown %",   "Win / Loss Distribution"),
        vertical_spacing=0.18, horizontal_spacing=0.1,
        specs=[
            [{"type": "xy"},     {"type": "xy"}],
            [{"type": "xy"},     {"type": "domain"}],
        ],
    )

    # Equity curve
    bt_fig.add_trace(go.Scatter(
        x=list(range(len(bt_equity))), y=bt_equity,
        line=dict(color="#5b9bd5", width=1.8),
        fill="tozeroy", fillcolor="rgba(91,155,213,0.07)",
        name="Equity",
    ), row=1, col=1)
    bt_fig.add_hline(y=capital,
                     line=dict(color="#555", width=1, dash="dash"),
                     row=1, col=1)
    # shade profitable / loss zones
    bt_fig.add_trace(go.Scatter(
        x=list(range(len(bt_equity))),
        y=[e if e >= capital else capital for e in bt_equity],
        fill="tozeroy", fillcolor="rgba(0,230,118,0.07)",
        line=dict(width=0), showlegend=False,
    ), row=1, col=1)

    # Trade P&L bar chart
    pnl_vals   = [t["pnl"] for t in bt_trades]
    pnl_colors = ["#00e676" if p > 0 else "#ff1744" for p in pnl_vals]
    bt_fig.add_trace(go.Bar(
        x=list(range(len(pnl_vals))), y=pnl_vals,
        marker_color=pnl_colors, marker_opacity=0.85,
        name="Trade P&L",
    ), row=1, col=2)

    # Drawdown
    bt_fig.add_trace(go.Scatter(
        x=list(range(len(drawdown_arr))), y=drawdown_arr,
        line=dict(color="#ff5252", width=1.2),
        fill="tozeroy", fillcolor="rgba(255,23,68,0.12)",
        name="Drawdown",
    ), row=2, col=1)

    # Win/Loss pie
    bt_fig.add_trace(go.Pie(
        labels=["Wins", "Losses"],
        values=[wins, losses],
        marker=dict(colors=["#00e676", "#ff1744"]),
        hole=0.5,
        textfont=dict(size=12, color=TEXT_PRIMARY),
        showlegend=True,
    ), row=2, col=2)

    bt_fig.update_layout(
        height=580,
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(family="Space Mono, monospace", color=LEGEND_FG, size=10),
        margin=dict(l=10, r=10, t=40, b=10),
        showlegend=False,
        hovermode="x unified",
    )
    bt_axis = dict(
        gridcolor=GRID_COLOR, gridwidth=0.5,
        tickfont=dict(color=LEGEND_FG, size=9),
        showgrid=True,
        zerolinecolor=BORDER_CARD,
    )
    for r in range(1, 3):
        for c in range(1, 3):
            bt_fig.update_xaxes(bt_axis, row=r, col=c)
            bt_fig.update_yaxes(bt_axis, row=r, col=c)
    for ann in bt_fig.layout.annotations:
        ann.font.color = TEXT_MUTED
        ann.font.size  = 11

    st.plotly_chart(bt_fig, use_container_width=True,
                    config={"displaylogo": False})

# ---------------------------
# TAB 3: PAPER TRADES LOG
# ---------------------------
with tab3:
    st.markdown("### 📄 Paper Trading Journal")

    # ── Helpers ──────────────────────────────────────────────────────────────
    current_price = entry  # live last price from df

    def calc_unrealised(pos, current_price):
        if pos is None:
            return 0.0
        if pos["side"] == "LONG":
            return (current_price - pos["entry"]) * pos["qty"]
        else:
            return (pos["entry"] - current_price) * pos["qty"]

    def check_sl_tp(pos, current_price):
        """Return 'SL', 'TP', or None depending on whether price has hit SL/TP."""
        if pos is None:
            return None
        if pos["side"] == "LONG":
            if current_price <= pos["sl"]: return "SL"
            if current_price >= pos["tp"]: return "TP"
        else:
            if current_price >= pos["sl"]: return "SL"
            if current_price <= pos["tp"]: return "TP"
        return None

    # ── Auto-close if SL/TP hit ──────────────────────────────────────────────
    pos = st.session_state.paper_position
    hit = check_sl_tp(pos, current_price)
    if hit and pos:
        close_px = pos["sl"] if hit == "SL" else pos["tp"]
        pnl = (close_px - pos["entry"]) * pos["qty"] if pos["side"] == "LONG" \
              else (pos["entry"] - close_px) * pos["qty"]
        st.session_state.paper_balance += pnl
        for t in st.session_state.paper_trades:
            if t["status"] == "OPEN" and t["entry"] == pos["entry"]:
                t["status"] = f"CLOSED ({hit})"
                t["pnl"]    = round(pnl, 2)
                t["close_price"] = round(close_px, 2)
        st.session_state.paper_position = None
        st.warning(f"{'🔴 Stop Loss' if hit=='SL' else '🟢 Take Profit'} hit! "
                   f"Closed @ ₹{close_px:,.2f}  |  P&L: ₹{pnl:+,.2f}")

    # ── Stats row ────────────────────────────────────────────────────────────
    unrealised  = calc_unrealised(st.session_state.paper_position, current_price)
    closed_pnls = [t["pnl"] for t in st.session_state.paper_trades
                   if t["status"] != "OPEN" and isinstance(t.get("pnl"), (int, float))]
    total_realised = sum(closed_pnls)
    total_trades_p = len(closed_pnls)
    wins_p  = sum(1 for p in closed_pnls if p > 0)
    wr_p    = round(wins_p / total_trades_p * 100, 1) if total_trades_p else 0

    s1, s2, s3, s4 = st.columns(4)
    for col, label, val, color in [
        (s1, "PAPER BALANCE",
         f"₹{st.session_state.paper_balance:,.2f}",
         TEXT_PRIMARY),
        (s2, "UNREALISED P&L",
         f"{'+'if unrealised>=0 else ''}₹{unrealised:,.2f}",
         "#00e676" if unrealised >= 0 else "#ff1744"),
        (s3, "REALISED P&L",
         f"{'+'if total_realised>=0 else ''}₹{total_realised:,.2f}",
         "#00e676" if total_realised >= 0 else "#ff1744"),
        (s4, "WIN RATE",
         f"{wr_p}%  ({wins_p}/{total_trades_p})",
         "#ffc107"),
    ]:
        col.markdown(f"""<div class="metric-card">
            <div style="color:{TEXT_MUTED};font-family:'Space Mono',monospace;font-size:0.7rem">{label}</div>
            <div style="font-size:1.4rem;font-weight:700;color:{color}">{val}</div>
        </div>""", unsafe_allow_html=True)

    # ── Open position card ───────────────────────────────────────────────────
    st.markdown(f"#### Open Position")
    pos = st.session_state.paper_position
    if pos:
        unr  = calc_unrealised(pos, current_price)
        pct  = unr / (pos["entry"] * pos["qty"]) * 100 if pos["entry"] else 0
        side_color = "#00e676" if pos["side"] == "LONG" else "#ff1744"
        st.markdown(f"""
        <div class="metric-card" style="border-color:{side_color};">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
                <div>
                    <span style="font-family:'Space Mono',monospace;font-size:1.2rem;
                        font-weight:700;color:{side_color};">
                        {'▲ LONG' if pos['side']=='LONG' else '▼ SHORT'}
                    </span>
                    <span style="color:{TEXT_MUTED};font-size:0.85rem;margin-left:10px;">
                        {pos['pair']} · {pos['time']}
                    </span>
                </div>
                <div style="font-family:'Space Mono',monospace;font-size:1.1rem;
                    color:{'#00e676' if unr>=0 else '#ff1744'};font-weight:700;">
                    {'+'if unr>=0 else ''}₹{unr:,.2f}
                    <span style="font-size:0.8rem;opacity:0.8;">({pct:+.2f}%)</span>
                </div>
            </div>
            <div style="display:flex;gap:24px;margin-top:10px;font-size:0.82rem;
                color:{TEXT_DIM};font-family:'Space Mono',monospace;flex-wrap:wrap;">
                <span>Entry <b style="color:{TEXT_PRIMARY}">₹{pos['entry']:,.2f}</b></span>
                <span>Now &nbsp;<b style="color:#ffd740">₹{current_price:,.2f}</b></span>
                <span>SL &nbsp;&nbsp;<b style="color:#ff5252">₹{pos['sl']:,.2f}</b></span>
                <span>TP &nbsp;&nbsp;<b style="color:#69f0ae">₹{pos['tp']:,.2f}</b></span>
                <span>Qty &nbsp;<b style="color:{TEXT_PRIMARY}">{pos['qty']}</b></span>
                <span>Size <b style="color:{TEXT_PRIMARY}">₹{pos['size']:,.0f}</b></span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        close_col, _ = st.columns([1, 3])
        with close_col:
            if st.button("✅ Close at Market Price", use_container_width=True):
                pnl = calc_unrealised(pos, current_price)
                st.session_state.paper_balance += pnl
                for t in st.session_state.paper_trades:
                    if t["status"] == "OPEN" and t["entry"] == pos["entry"]:
                        t["status"]      = "CLOSED (MKT)"
                        t["pnl"]         = round(pnl, 2)
                        t["close_price"] = round(current_price, 2)
                st.session_state.paper_position = None
                st.success(f"✅ Closed @ ₹{current_price:,.2f}  |  P&L: ₹{pnl:+,.2f}")
                st.rerun()
    else:
        st.markdown(f"""<div class="metric-card">
            <div style="color:{TEXT_DIM};font-family:'Space Mono',monospace;font-size:0.85rem;">
                No open position. Go to <b>Live Signal</b> tab and execute a paper trade.
            </div>
        </div>""", unsafe_allow_html=True)

    # ── Trade journal table ──────────────────────────────────────────────────
    st.markdown(f"#### Trade History")
    if st.session_state.paper_trades:
        journal = []
        for t in reversed(st.session_state.paper_trades):
            pnl_val = t.get("pnl")
            journal.append({
                "Time":        t.get("time", "—"),
                "Pair":        t.get("pair", "—"),
                "Side":        t.get("side", "—"),
                "Entry ₹":     f"₹{t['entry']:,.2f}" if isinstance(t.get("entry"), float) else "—",
                "Close ₹":     f"₹{t['close_price']:,.2f}" if isinstance(t.get("close_price"), float) else "Open",
                "SL ₹":        f"₹{t['sl']:,.2f}" if isinstance(t.get("sl"), float) else "—",
                "TP ₹":        f"₹{t['tp']:,.2f}" if isinstance(t.get("tp"), float) else "—",
                "Size ₹":      f"₹{t['size']:,.0f}" if isinstance(t.get("size"), (int, float)) else "—",
                "P&L ₹":       f"{'+'if isinstance(pnl_val,(int,float)) and pnl_val>=0 else ''}₹{pnl_val:,.2f}"
                               if isinstance(pnl_val, (int, float)) else "Open",
                "Status":      t.get("status", "—"),
            })
        st.dataframe(pd.DataFrame(journal), use_container_width=True, hide_index=True)

        # Download button
        dl_df = pd.DataFrame(journal)
        st.download_button(
            "⬇️ Export Journal CSV",
            data=dl_df.to_csv(index=False).encode("utf-8"),
            file_name=f"paper_trades_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
        )
    else:
        st.info("No paper trades yet.")

    st.markdown("---")
    rst_col, _ = st.columns([1, 3])
    with rst_col:
        if st.button("🔄 Reset Paper Account", use_container_width=True):
            st.session_state.paper_balance  = float(capital)
            st.session_state.paper_trades   = []
            st.session_state.paper_position = None
            st.success("Paper account reset to ₹{:,.0f}".format(capital))
            st.rerun()

# ---------------------------
# TAB 4: ABOUT
# ---------------------------
with tab4:

    # ── Developer card ───────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="background:{BG_CARD};border:1px solid {BORDER_CARD};border-radius:16px;
        padding:32px 36px;margin-bottom:24px;">
        <div style="display:flex;align-items:center;gap:24px;flex-wrap:wrap;">
            <div style="width:80px;height:80px;border-radius:50%;
                background:linear-gradient(135deg,#00e676,#00bcd4);
                display:flex;align-items:center;justify-content:center;
                font-size:2rem;font-weight:700;color:#0a0e1a;flex-shrink:0;">
                AK
            </div>
            <div>
                <div style="font-family:'Space Mono',monospace;font-size:1.6rem;
                    font-weight:700;background:linear-gradient(90deg,#00e676,#00bcd4,#7eb3e8);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                    background-clip:text;">
                    ANKESH KUMAR
                </div>
                <div style="color:{TEXT_MUTED};font-size:0.9rem;margin-top:4px;
                    font-family:'Space Mono',monospace;">
                    Algo Trader · Quantitative Developer
                </div>
                <div style="color:{TEXT_DIM};font-size:0.82rem;margin-top:8px;">
                    Futures Algo Dashboard — Live Trading Data
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Two column layout ────────────────────────────────────────────────────
    ab1, ab2 = st.columns(2)

    with ab1:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-family:'Space Mono',monospace;font-size:0.75rem;
                color:{TEXT_MUTED};letter-spacing:2px;margin-bottom:12px;">
                📊 ABOUT THIS DASHBOARD
            </div>
            <div style="color:{TEXT_PRIMARY};font-size:0.88rem;line-height:1.8;">
                A professional-grade <b>Binance Futures</b> algorithmic trading dashboard
                built in Python with Streamlit. Combines real-time market data,
                multi-indicator signal generation, ATR-based risk management,
                and a full paper trading simulator — all in one interface.
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="metric-card">
            <div style="font-family:'Space Mono',monospace;font-size:0.75rem;
                color:{TEXT_MUTED};letter-spacing:2px;margin-bottom:12px;">
                🧠 SIGNAL ENGINE
            </div>
            <div style="color:{TEXT_PRIMARY};font-size:0.85rem;line-height:1.9;">
                {'<br>'.join([
                    f'<span style="color:#00e676;">✓</span> EMA 9 / 21 / 45 / 200 stack alignment',
                    f'<span style="color:#00e676;">✓</span> MACD fresh crossover detection',
                    f'<span style="color:#00e676;">✓</span> RSI momentum zone filter',
                    f'<span style="color:#00e676;">✓</span> Bollinger Band squeeze / breakout',
                    f'<span style="color:#00e676;">✓</span> Volume surge confirmation',
                    f'<span style="color:#00e676;">✓</span> EMA200 macro trend gate',
                    f'<span style="color:#ffd740;">→</span> Requires 7 / 10 score to trigger',
                ])}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with ab2:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-family:'Space Mono',monospace;font-size:0.75rem;
                color:{TEXT_MUTED};letter-spacing:2px;margin-bottom:12px;">
                🛡️ RISK MANAGEMENT
            </div>
            <div style="color:{TEXT_PRIMARY};font-size:0.85rem;line-height:1.9;">
                {'<br>'.join([
                    f'<span style="color:#00e676;">✓</span> ATR-based dynamic stop loss',
                    f'<span style="color:#00e676;">✓</span> Trailing stop — locks in profits',
                    f'<span style="color:#00e676;">✓</span> Configurable R:R ratio (1:1 to 1:5)',
                    f'<span style="color:#00e676;">✓</span> Position size = % risk / SL distance',
                    f'<span style="color:#00e676;">✓</span> 20% capital cap per trade',
                    f'<span style="color:#00e676;">✓</span> Post-loss cooldown (no revenge trading)',
                    f'<span style="color:#ffd740;">→</span> Works on Binance Futures (Perpetual)',
                ])}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="metric-card">
            <div style="font-family:'Space Mono',monospace;font-size:0.75rem;
                color:{TEXT_MUTED};letter-spacing:2px;margin-bottom:12px;">
                ⚙️ TECH STACK
            </div>
            <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:4px;">
                {''.join([
                    f'<span style="background:{"#1a2a4a" if IS_DARK else "#ddeeff"};'
                    f'color:{TEXT_MUTED};padding:4px 12px;border-radius:20px;'
                    f'font-family:Space Mono,monospace;font-size:0.72rem;">{t}</span>'
                    for t in ["Python 3.8+","Streamlit","Plotly","pandas","NumPy",
                              "python-binance","Binance Futures API","TradingView Widget"]
                ])}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Version + disclaimer ──────────────────────────────────────────────────
    st.markdown(f"""
    <div style="margin-top:8px;background:{"#1a1200" if IS_DARK else "#fff8e1"};
        border-left:4px solid #ffc107;border-radius:0 10px 10px 0;padding:14px 20px;">
        <div style="font-family:'Space Mono',monospace;font-size:0.72rem;
            color:{"#ffc107" if IS_DARK else "#7a5000"};letter-spacing:1px;
            margin-bottom:6px;">⚠️ DISCLAIMER</div>
        <div style="font-size:0.82rem;color:{"#c8a400" if IS_DARK else "#5a3a00"};
            line-height:1.7;">
            This dashboard is built for <b>educational and research purposes only</b>.
            Algorithmic trading involves substantial risk of loss.
            Past backtest performance does not guarantee future results.
            Always use paper trading to validate strategies before going live.
            The developer <b>Ankesh Kumar</b> is not responsible for any financial losses.
        </div>
    </div>

    <div style="text-align:right;margin-top:16px;
        font-family:'Space Mono',monospace;font-size:0.72rem;color:{TEXT_DIM};">
        v3.0 · Built by <span style="color:#00e676;">Ankesh Kumar</span> ·
        Futures Algo Dashboard Live Trading Data
    </div>
    """, unsafe_allow_html=True)