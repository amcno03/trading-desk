import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(layout="wide")

st.title("📊 Options Trading Desk PRO (Robusto)")

tickers = ["AAPL","MSFT","AMZN","TSLA","NVDA","META"]

resultados = []

# =========================
# SCANNER ENGINE (ROBUSTO)
# =========================
for symbol in tickers:
    try:
        daily = yf.download(symbol, period="30d", interval="1d", progress=False)

        if daily is None or daily.empty or len(daily) < 10:
            continue

        daily = daily.dropna()

        # =========================
        # FASE 1: primer día de semana
        # =========================
        daily["Week"] = daily.index.isocalendar().week
        daily["IsFirstDay"] = daily["Week"] != daily["Week"].shift(1)

        first_days = daily[daily["IsFirstDay"]]

        if first_days.empty:
            continue

        last_first_day = first_days.iloc[-1]

        is_red_first_day = bool(last_first_day["Close"] < last_first_day["Open"])

        # =========================
        # FASE 2: intradía 10m
        # =========================
        intraday = yf.download(symbol, period="5d", interval="10m", progress=False)

        if intraday is None or intraday.empty or len(intraday) < 20:
            continue

        intraday = intraday.dropna()

        weekly_open = float(intraday["Open"].iloc[0])
        current = float(intraday["Close"].iloc[-1])
        prev = float(intraday["Close"].iloc[-2])

        breakout_up = current > weekly_open and prev <= weekly_open

        # =========================
        # VOLUMEN (SAFE)
        # =========================
        vol = intraday["Volume"].fillna(0)

        avg_vol = vol.rolling(20).mean().iloc[-1]
        avg_vol = avg_vol if avg_vol and avg_vol > 0 else 1

        vol_ratio = float(vol.iloc[-1]) / float(avg_vol)

        # =========================
        # SIGNAL ENGINE (SIEMPRE EXISTE)
        # =========================
        signal = ""

        if is_red_first_day:
            signal = "🔴 PUT WATCH"

        if breakout_up and vol_ratio > 1.3:
            signal = "🟢 CALL BREAKOUT"

        resultados.append({
            "Ticker": symbol,
            "First Day Red": is_red_first_day,
            "Breakout Up": breakout_up,
            "Vol x": round(vol_ratio, 2),
            "Signal": signal
        })

    except Exception as e:
        # nunca rompe el dashboard
        continue

# =========================
# DATAFRAME ROBUSTO
# =========================
if len(resultados) == 0:
    df = pd.DataFrame(columns=["Ticker","First Day Red","Breakout Up","Vol x","Signal"])
else:
    df = pd.DataFrame(resultados)

# asegurar columnas siempre existentes
for col in ["Ticker","First Day Red","Breakout Up","Vol x","Signal"]:
    if col not in df.columns:
        df[col] = ""

# =========================
# UI DASHBOARD
# =========================
col1, col2 = st.columns([1.2, 2])

with col1:
    st.subheader("📊 Scanner")

    st.dataframe(df, use_container_width=True)

    st.subheader("🔥 Setups activos")

    signals = df[df["Signal"].astype(str) != ""]

    if signals.empty:
        st.info("No hay señales activas en este momento")
    else:
        st.dataframe(signals, use_container_width=True)

with col2:

    if df.empty:
        st.warning("Sin datos para graficar")
    else:
        selected = st.selectbox("Selecciona ticker", df["Ticker"])

        chart = yf.download(selected, period="5d", interval="10m")

        if chart is not None and not chart.empty:

            chart = chart.dropna()

            weekly_open = float(chart["Open"].iloc[0])

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
