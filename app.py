import streamlit as st

st.title("📊 Mi Trading Desk")
st.write("App funcionando 🚀")
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(layout="wide")

st.title("📊 Options Trading Desk PRO")

tickers = ["AAPL","MSFT","AMZN","TSLA","NVDA","META"]

resultados = []

# =========================
# SCANNER PRINCIPAL
# =========================
for symbol in tickers:
    try:
        # -------------------------
        # DAILY DATA (Fase 1)
        # -------------------------
        daily = yf.download(symbol, period="30d", interval="1d", progress=False)

        if len(daily) < 10:
            continue

        daily["Week"] = daily.index.isocalendar().week
        daily["IsFirstDay"] = daily["Week"] != daily["Week"].shift(1)

        first_day = daily[daily["IsFirstDay"]].iloc[-1]

        is_red_first_day = first_day["Close"] < first_day["Open"]

        # -------------------------
        # INTRADAY DATA (Fase 2)
        # -------------------------
        intraday = yf.download(symbol, period="5d", interval="10m", progress=False)

        if len(intraday) < 20:
            continue

        weekly_open = intraday["Open"].iloc[0]
        current = intraday["Close"].iloc[-1]
        prev = intraday["Close"].iloc[-2]

        breakout_up = current > weekly_open and prev <= weekly_open

        # -------------------------
        # VOLATILITY FILTER
        # -------------------------
        vol = intraday["Volume"]
        vol_ratio = vol.iloc[-1] / vol.rolling(20).mean().iloc[-1]

        # -------------------------
        # SIGNAL ENGINE
        # -------------------------
        signal = ""

        if is_red_first_day:
            signal = "🔴 PUT WATCH"

        if breakout_up and vol_ratio > 1.3:
            signal = "🟢 CALL BREAKOUT"

        resultados.append({
            "Ticker": symbol,
            "First Day Red": is_red_first_day,
            "Breakout": breakout_up,
            "Vol x": round(vol_ratio, 2),
            "Signal": signal
        })

    except:
        pass

df = pd.DataFrame(resultados)

# =========================
# DASHBOARD UI
# =========================

col1, col2 = st.columns([1.2, 2])

with col1:
    st.subheader("📊 Scanner")
    st.dataframe(df, use_container_width=True)

    st.subheader("🔥 Setups activos")
    st.dataframe(df[df["Signal"] != ""], use_container_width=True)

with col2:

    selected = st.selectbox("Selecciona ticker", df["Ticker"] if not df.empty else ["AAPL"])

    chart = yf.download(selected, period="5d", interval="10m")

    weekly_open = chart["Open"].iloc[0]

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=chart.index,
        open=chart["Open"],
        high=chart["High"],
        low=chart["Low"],
        close=chart["Close"],
        name="Price"
    ))

    fig.add_hline(
        y=weekly_open,
        line_dash="dash",
        line_color="yellow",
        annotation_text="Weekly Open"
    )

    fig.update_layout(
        template="plotly_dark",
        height=700,
        margin=dict(l=10, r=10, t=30, b=10)
    )

    st.plotly_chart(fig, use_container_width=True)

# =========================
# FOOTER
# =========================
st.caption(f"Última actualización: {datetime.now()}")
