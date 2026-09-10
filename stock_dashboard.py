
import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ============================================================
# INDIAN STOCK MARKET | EXECUTIVE ANALYTICS DASHBOARD
# ============================================================

st.set_page_config(
    page_title="Indian Stock Market Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_PATH = r"C:\StockMarketProject\stock_market.db"

# ============================================================
# STYLE
# ============================================================

st.markdown("""
<style>

.main {
    background-color: #f7f9fc;
}

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
}

h1 {
    font-weight: 800;
}

h2 {
    font-weight: 750;
}

.metric-card {
    background: linear-gradient(135deg, #102a56, #1d4e89);
    padding: 18px;
    border-radius: 2px;
    color: white;
    min-height: 110px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.12);
}

.metric-title {
    font-size: 13px;
    opacity: 0.85;
}

.metric-value {
    font-size: 25px;
    font-weight: 800;
    margin-top: 8px;
}

.section-title {
    font-size: 25px;
    font-weight: 800;
    margin-top: 35px;
    margin-bottom: 15px;
}

.question-box {
    background: white;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #e1e6ef;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# DATABASE
# =========================

numeric_cols = [
    "Open",
    "High",
    "Low",
    "Close",
    "Volume"
]

@st.cache_data
def load_data():
    import sqlite3
    from pathlib import Path

    # Find the correct database
    possible_dbs = [
        Path(r"C:\StockMarketProject\stock_market.db"),
        Path.cwd() / "stock_market.db",
        Path(__file__).parent / "stock_market.db",
    ]

    db_path = None

    for p in possible_dbs:
        if p.exists():
            try:
                test_conn = sqlite3.connect(str(p))
                tables = test_conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
                test_conn.close()

                table_names = [row[0] for row in tables]

                if "stock_data" in table_names:
                    db_path = p
                    break
            except Exception:
                pass

    if db_path is None:
        raise RuntimeError(
            "Could not find a database containing the stock_data table."
        )

    conn = sqlite3.connect(str(db_path))

    try:
        df = pd.read_sql_query(
            "SELECT * FROM stock_data",
            conn
        )
    finally:
        conn.close()

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["Date", "Symbol"])
    return df

try:

    df = load_data()

except Exception as e:

    st.error("Unable to load the stock database.")
    st.code(str(e))
    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("📊 MARKET CONTROL PANEL")

symbols = sorted(
    df["Symbol"].dropna().astype(str).unique().tolist()
)

selected_symbol = st.sidebar.selectbox(
    "Select Stock",
    symbols
)
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
min_date = df["Date"].min().date()
max_date = df["Date"].max().date()

date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if isinstance(date_range, tuple) and len(date_range) == 2:

    start_date = pd.Timestamp(date_range[0])
    end_date = pd.Timestamp(date_range[1])

else:

    start_date = pd.Timestamp(min_date)
    end_date = pd.Timestamp(max_date)


# ============================================================
# FILTER DATA
# ============================================================

stock = df[
    (df["Symbol"].astype(str) == str(selected_symbol))
    &
    (df["Date"] >= start_date)
    &
    (df["Date"] <= end_date)
].copy()

stock = stock.sort_values("Date")
if stock.empty:
    st.warning("No data available for the selected stock and date range.")
    st.stop()

stock["SMA_20"] = stock["Close"].rolling(20).mean()
stock["SMA_50"] = stock["Close"].rolling(50).mean()
# TREND ANALYSIS
latest_sma20 = stock["SMA_20"].iloc[-1]
latest_sma50 = stock["SMA_50"].iloc[-1]

if latest_sma20 > latest_sma50:
    trend = "Bullish 📈"
elif latest_sma20 < latest_sma50:
    trend = "Bearish 📉"
else:
    trend = "Neutral ➡️"
# ==========================================
# HEADER
# ==========================================
st.title("🇮🇳 INDIAN STOCK MARKET | EXECUTIVE ANALYTICS")

st.caption(
    f"Power BI Style Interactive Dashboard | "
    f"Selected Stock: {selected_symbol} | "
    f"Period: {start_date.date()} → {end_date.date()}"
)


# ============================================================
# PLAIN ENGLISH → SQL
# ============================================================

st.markdown(
    '<div class="section-title">💬 Ask Your Stock Question</div>',
    unsafe_allow_html=True
)

question = st.text_input(
    "Ask a question in plain English",
    placeholder="Example: What is the average closing price?"
)

if st.button("🔎 Ask & Generate SQL"):

    q = question.lower().strip()
    
    stock_keywords = ["price", "close", "closing", "high", "highest", "low", "lowest", "volume", "average", "trend", "stock", "share", "trading"]

    if not any(word in q for word in stock_keywords):
        st.warning("I can only answer stock market related questions.")
        st.stop()  

    symbol = selected_symbol.replace("'", "''")

    start = start_date.strftime("%Y-%m-%d")
    end = end_date.strftime("%Y-%m-%d")

    sql = None
    
    if "average" in q and "close" in q:

        sql = f"""
SELECT AVG(Close) AS Average_Close
FROM stock_data
WHERE Symbol = '{symbol}'
AND Date BETWEEN '{start}' AND '{end}'
"""

    elif "highest" in q and "price" in q:

        sql = f"""
SELECT MAX(High) AS Highest_Price
FROM stock_data
WHERE Symbol = '{symbol}'
AND Date BETWEEN '{start}' AND '{end}'
"""

    elif "highest closing" in q or "highest close" in q:
     sql = f"""
SELECT MAX(Close) AS Highest_Closing_Price
FROM stock_data
WHERE Symbol = '{symbol}'
AND Date BETWEEN '{start}' AND '{end}'
  """
    elif "lowest" in q and "price" in q:

        sql = f"""
SELECT MIN(Low) AS Lowest_Price
FROM stock_data
WHERE Symbol = '{symbol}'
AND Date BETWEEN '{start}' AND '{end}'
"""

    elif "total volume" in q or ("volume" in q and "total" in q):

        sql = f"""
SELECT SUM(Volume) AS Total_Volume
FROM stock_data
WHERE Symbol = '{symbol}'
AND Date BETWEEN '{start}' AND '{end}'
"""

    elif "average volume" in q or "average trading volume" in q:
     
        sql = f"""
SELECT AVG(Volume) AS Average_Volume
FROM stock_data
WHERE Symbol = '{symbol}'
AND Date BETWEEN '{start}' AND '{end}'
"""
    elif "trend" in q:
        sql = f"""
        SELECT
            CASE
                WHEN (SELECT Close FROM stock_data
                      WHERE Symbol = '{symbol}'
                      AND Date BETWEEN '{start}' AND '{end}'
                      ORDER BY Date ASC LIMIT 1)
                     <
                     (SELECT Close FROM stock_data
                      WHERE Symbol = '{symbol}'
                      AND Date BETWEEN '{start}' AND '{end}'
                      ORDER BY Date DESC LIMIT 1)
                THEN 'UPTREND'

                WHEN (SELECT Close FROM stock_data
                      WHERE Symbol = '{symbol}'
                      AND Date BETWEEN '{start}' AND '{end}'
                      ORDER BY Date ASC LIMIT 1)
                     >
                     (SELECT Close FROM stock_data
                      WHERE Symbol = '{symbol}'
                      AND Date BETWEEN '{start}' AND '{end}'
                      ORDER BY Date DESC LIMIT 1)
                THEN 'DOWNTREND'

                ELSE 'SIDEWAYS'
            END AS Trend
        """

    elif "turnover" in q and "average" in q:
        sql = f"""
        SELECT AVG(Turnover) AS Average_Turnover
        FROM stock_data
        WHERE Symbol = '{symbol}'
        AND Date BETWEEN '{start}' AND '{end}'
        """

    elif "turnover" in q:
        sql = f"""
        SELECT SUM(Turnover) AS Total_Turnover
        FROM stock_data
        WHERE Symbol = '{symbol}'
        AND Date BETWEEN '{start}' AND '{end}'
        """

    elif "records" in q or "number of records" in q:
        sql = f"""
        SELECT COUNT(*) AS Trading_Records
        FROM stock_data
        WHERE Symbol = '{symbol}'
        AND Date BETWEEN '{start}' AND '{end}'
        """

    else:
          sql = f"""
    SELECT
        COUNT(*) AS Trading_Records,
        AVG(Close) AS Average_Close,
        MAX(High) AS Highest_Price,
        MIN(Low) AS Lowest_Price,
        AVG(Volume) AS Average_Volume
    FROM stock_data
    WHERE Symbol = '{selected_symbol}'
    AND Date BETWEEN '{start_date}' AND '{end_date}'
    """

    try:

        conn = sqlite3.connect(DB_PATH)

        result = pd.read_sql_query(
            sql,
            conn
        )

        conn.close()

        st.subheader("Your Question")
        st.info(question)

        st.subheader("Generated SQL")
        st.code(sql, language="sql")

        st.subheader("Result")
        st.dataframe(
            result,
            use_container_width=True
        )

    except Exception as e:

        st.error("SQL execution error.")
        st.code(str(e))


# ============================================================
# EXECUTIVE KPIs
# ============================================================

st.markdown(
    '<div class="section-title">📌 EXECUTIVE KPIs</div>',
    unsafe_allow_html=True
)

trading_records = len(stock)

total_volume = stock["Volume"].sum()

total_turnover = stock["Turnover"].sum()

average_close = stock["Close"].mean()

highest_price = stock["High"].max()

lowest_price = stock["Low"].min()

average_volume = stock["Volume"].mean()

average_vwap = stock["VWAP"].mean()

average_change = (
    stock["Close"] - stock["Prev Close"]
).mean()

average_change_pct = (
    (
        stock["Close"] - stock["Prev Close"]
    )
    /
    stock["Prev Close"]
    *
    100
).replace(
    [np.inf, -np.inf],
    np.nan
).mean()

volatility = stock["Close"].pct_change().std() * 100


def metric(title, value):

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">{title}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


cols = st.columns(5)

with cols[0]:
    metric(
        "Trading Records",
        f"{trading_records:,}"
    )

with cols[1]:
    metric(
        "Total Volume",
        f"{total_volume/1e9:.2f}B"
    )

with cols[2]:
    metric(
        "Total Turnover",
        f"{total_turnover/1e12:.2f}T"
    )

with cols[3]:
    metric(
        "Average Close",
        f"₹{average_close:,.2f}"
    )

with cols[4]:
    metric(
        "Highest Price",
        f"₹{highest_price:,.2f}"
    )


cols = st.columns(5)

with cols[0]:
    metric(
        "Lowest Price",
        f"₹{lowest_price:,.2f}"
    )

with cols[1]:
    metric(
        "Average Volume",
        f"{average_volume/1e6:.2f}M"
    )

with cols[2]:
    metric(
        "Average VWAP",
        f"₹{average_vwap:,.2f}"
    )

with cols[3]:
    metric(
        "Average Change",
        f"₹{average_change:,.2f}"
    )

with cols[4]:
    metric(
        "Volatility",
        f"{volatility:.2f}%"
    )


# ============================================================
# 1. CLOSING PRICE TREND
# ============================================================

st.markdown(
    '<div class="section-title">📈 PRICE INTELLIGENCE</div>',
    unsafe_allow_html=True
)

fig1 = go.Figure()

fig1.add_trace(
    go.Scatter(
        x=stock["Date"],
        y=stock["Close"],
        mode="lines",
        name="Close"
    )
)

fig1.update_layout(
    title=f"{selected_symbol} Closing Price Trend",
    xaxis_title="Date",
    yaxis_title="Closing Price",
    height=430,
    template="plotly_white"
)

st.plotly_chart(
    fig1,
    use_container_width=True
)


# ============================================================
# 2. OHLC CHART
# ============================================================

fig2 = go.Figure()

fig2.add_trace(
    go.Candlestick(
        x=stock["Date"],
        open=stock["Open"],
        high=stock["High"],
        low=stock["Low"],
        close=stock["Close"],
        name="OHLC"
    )
)

fig2.update_layout(
    title="OHLC / Candlestick Analysis",
    height=450,
    xaxis_rangeslider_visible=False
)

st.plotly_chart(
    fig2,
    use_container_width=True
)


# ============================================================
# 3. VWAP VS CLOSE
# ============================================================

fig3 = go.Figure()

fig3.add_trace(
    go.Scatter(
        x=stock["Date"],
        y=stock["Close"],
        mode="lines",
        name="Close"
    )
)

fig3.add_trace(
    go.Scatter(
        x=stock["Date"],
        y=stock["VWAP"],
        mode="lines",
        name="VWAP"
    )
)

fig3.update_layout(
    title="Closing Price vs VWAP",
    height=400,
    template="plotly_white"
)

st.plotly_chart(
    fig3,
    use_container_width=True
)


# ============================================================
# 4. DAILY CHANGE
# ============================================================

stock["Change"] = stock["Close"] - stock["Prev Close"]

fig4 = go.Figure()

fig4.add_trace(
    go.Bar(
        x=stock["Date"],
        y=stock["Change"],
        name="Daily Change"
    )
)

fig4.update_layout(
    title="Daily Price Change",
    height=400,
    template="plotly_white"
)

st.plotly_chart(
    fig4,
    use_container_width=True
)


# ============================================================
# 5. DAILY CHANGE %
# ============================================================

stock["ChangePct"] = (
    stock["Change"]
    /
    stock["Prev Close"]
    *
    100
)

fig5 = go.Figure()

fig5.add_trace(
    go.Scatter(
        x=stock["Date"],
        y=stock["ChangePct"],
        mode="lines",
        name="Change %"
    )
)

fig5.update_layout(
    title="Daily Percentage Change",
    yaxis_title="Change %",
    height=400,
    template="plotly_white"
)

st.plotly_chart(
    fig5,
    use_container_width=True
)


# ============================================================
# 6. VOLUME TREND
# ============================================================

fig6 = go.Figure()

fig6.add_trace(
    go.Bar(
        x=stock["Date"],
        y=stock["Volume"],
        name="Volume"
    )
)

fig6.update_layout(
    title="Trading Volume Trend",
    height=400,
    template="plotly_white"
)

st.plotly_chart(
    fig6,
    use_container_width=True
)


# ============================================================
# 7. TURNOVER TREND
# ============================================================

fig7 = go.Figure()

fig7.add_trace(
    go.Scatter(
        x=stock["Date"],
        y=stock["Turnover"],
        mode="lines",
        name="Turnover"
    )
)

fig7.update_layout(
    title="Turnover Trend",
    height=400,
    template="plotly_white"
)

st.plotly_chart(
    fig7,
    use_container_width=True
)


# ============================================================
# 8. HIGH VS LOW
# ============================================================

fig8 = go.Figure()

fig8.add_trace(
    go.Scatter(
        x=stock["Date"],
        y=stock["High"],
        mode="lines",
        name="High"
    )
)

fig8.add_trace(
    go.Scatter(
        x=stock["Date"],
        y=stock["Low"],
        mode="lines",
        name="Low"
    )
)

fig8.update_layout(
    title="High vs Low Price Range",
    height=400,
    template="plotly_white"
)

st.plotly_chart(
    fig8,
    use_container_width=True
)


# ============================================================
# 9. OPEN VS CLOSE
# ============================================================

fig9 = go.Figure()

fig9.add_trace(
    go.Scatter(
        x=stock["Date"],
        y=stock["Open"],
        mode="lines",
        name="Open"
    )
)

fig9.add_trace(
    go.Scatter(
        x=stock["Date"],
        y=stock["Close"],
        mode="lines",
        name="Close"
    )
)

fig9.update_layout(
    title="Opening vs Closing Price",
    height=400,
    template="plotly_white"
)

st.plotly_chart(
    fig9,
    use_container_width=True
)


# ============================================================
# 10. PRICE DISTRIBUTION
# ============================================================

fig10 = go.Figure()

fig10.add_trace(
    go.Histogram(
        x=stock["Close"],
        nbinsx=40,
        name="Closing Price"
    )
)

fig10.update_layout(
    title="Closing Price Distribution",
    height=400,
    template="plotly_white"
)

st.plotly_chart(
    fig10,
    use_container_width=True
)


# ============================================================
# 11. VOLUME DISTRIBUTION
# ============================================================

fig11 = go.Figure()

fig11.add_trace(
    go.Histogram(
        x=stock["Volume"],
        nbinsx=40,
        name="Volume"
    )
)

fig11.update_layout(
    title="Trading Volume Distribution",
    height=400,
    template="plotly_white"
)

st.plotly_chart(
    fig11,
    use_container_width=True
)


# ============================================================
# 12. VWAP DISTRIBUTION
# ============================================================

fig12 = go.Figure()

fig12.add_trace(
    go.Histogram(
        x=stock["VWAP"],
        nbinsx=40,
        name="VWAP"
    )
)

fig12.update_layout(
    title="VWAP Distribution",
    height=400,
    template="plotly_white"
)

st.plotly_chart(
    fig12,
    use_container_width=True
)


# ============================================================
# 13. PRICE RANGE
# ============================================================

stock["HighLowRange"] = (
    stock["High"] - stock["Low"]
)

fig13 = go.Figure()

fig13.add_trace(
    go.Scatter(
        x=stock["Date"],
        y=stock["HighLowRange"],
        mode="lines",
        name="High-Low Range"
    )
)

fig13.update_layout(
    title="Daily High-Low Price Range",
    height=400,
    template="plotly_white"
)

st.plotly_chart(
    fig13,
    use_container_width=True
)


# ============================================================
# 14. ROLLING VOLATILITY
# ============================================================

stock["RollingVolatility"] = (
    stock["ChangePct"]
    .rolling(20)
    .std()
)

fig14 = go.Figure()

fig14.add_trace(
    go.Scatter(
        x=stock["Date"],
        y=stock["RollingVolatility"],
        mode="lines",
        name="20-Day Volatility"
    )
)

fig14.update_layout(
    title="20-Day Rolling Volatility",
    height=400,
    template="plotly_white"
)

st.plotly_chart(
    fig14,
    use_container_width=True
)


# ============================================================
# 15. MOVING AVERAGES
# ============================================================

stock["MA20"] = stock["Close"].rolling(20).mean()
stock["MA50"] = stock["Close"].rolling(50).mean()

fig15 = go.Figure()

fig15.add_trace(
    go.Scatter(
        x=stock["Date"],
        y=stock["Close"],
        mode="lines",
        name="Close"
    )
)

fig15.add_trace(
    go.Scatter(
        x=stock["Date"],
        y=stock["MA20"],
        mode="lines",
        name="20-Day MA"
    )
)

fig15.add_trace(
    go.Scatter(
        x=stock["Date"],
        y=stock["MA50"],
        mode="lines",
        name="50-Day MA"
    )
)

fig15.update_layout(
    title="Moving Average Analysis",
    height=450,
    template="plotly_white"
)

st.plotly_chart(
    fig15,
    use_container_width=True
)


# ============================================================
# 16. TOP VOLUME DAYS
# ============================================================

top_volume = (
    stock[
        ["Date", "Volume"]
    ]
    .sort_values(
        "Volume",
        ascending=False
    )
    .head(15)
)

fig16 = go.Figure()

fig16.add_trace(
    go.Bar(
        x=top_volume["Date"].astype(str),
        y=top_volume["Volume"],
        name="Volume"
    )
)

fig16.update_layout(
    title="Top 15 Highest Volume Trading Days",
    height=450,
    template="plotly_white"
)

st.plotly_chart(
    fig16,
    use_container_width=True
)


# ============================================================
# 17. TOP TURNOVER DAYS
# ============================================================

top_turnover = (
    stock[
        ["Date", "Turnover"]
    ]
    .sort_values(
        "Turnover",
        ascending=False
    )
    .head(15)
)

fig17 = go.Figure()

fig17.add_trace(
    go.Bar(
        x=top_turnover["Date"].astype(str),
        y=top_turnover["Turnover"],
        name="Turnover"
    )
)

fig17.update_layout(
    title="Top 15 Highest Turnover Trading Days",
    height=450,
    template="plotly_white"
)

st.plotly_chart(
    fig17,
    use_container_width=True
)


# ============================================================
# 18. MONTHLY PERFORMANCE
# ============================================================

stock["Month"] = stock["Date"].dt.to_period("M").astype(str)

monthly = (
    stock.groupby("Month")
    .agg(
        Average_Close=("Close", "mean"),
        Total_Volume=("Volume", "sum"),
        Total_Turnover=("Turnover", "sum")
    )
    .reset_index()
)

fig18 = make_subplots(
    rows=2,
    cols=1,
    shared_xaxes=True,
    subplot_titles=(
        "Monthly Average Close",
        "Monthly Total Volume"
    )
)

fig18.add_trace(
    go.Bar(
        x=monthly["Month"],
        y=monthly["Average_Close"],
        name="Average Close"
    ),
    row=1,
    col=1
)

fig18.add_trace(
    go.Bar(
        x=monthly["Month"],
        y=monthly["Total_Volume"],
        name="Volume"
    ),
    row=2,
    col=1
)

fig18.update_layout(
    title="Monthly Market Performance",
    height=700,
    template="plotly_white"
)

st.plotly_chart(
    fig18,
    use_container_width=True
)


# ============================================================
# 19. QUARTERLY PERFORMANCE
# ============================================================

stock["Quarter"] = (
    stock["Date"]
    .dt.to_period("Q")
    .astype(str)
)

quarterly = (
    stock.groupby("Quarter")
    .agg(
        Average_Close=("Close", "mean"),
        Total_Volume=("Volume", "sum")
    )
    .reset_index()
)

fig19 = go.Figure()

fig19.add_trace(
    go.Bar(
        x=quarterly["Quarter"],
        y=quarterly["Average_Close"],
        name="Average Close"
    )
)

fig19.update_layout(
    title="Quarterly Average Closing Price",
    height=400,
    template="plotly_white"
)

st.plotly_chart(
    fig19,
    use_container_width=True
)


# ============================================================
# 20. YEARLY PERFORMANCE
# ============================================================

stock["Year"] = stock["Date"].dt.year

yearly = (
    stock.groupby("Year")
    .agg(
        Average_Close=("Close", "mean"),
        Total_Volume=("Volume", "sum"),
        Total_Turnover=("Turnover", "sum")
    )
    .reset_index()
)

fig20 = go.Figure()

fig20.add_trace(
    go.Bar(
        x=yearly["Year"].astype(str),
        y=yearly["Average_Close"],
        name="Average Close"
    )
)

fig20.update_layout(
    title="Yearly Average Closing Price",
    height=400,
    template="plotly_white"
)

st.plotly_chart(
    fig20,
    use_container_width=True
)


# ============================================================
# 21. PRICE VS VOLUME
# ============================================================

fig21 = go.Figure()

fig21.add_trace(
    go.Scatter(
        x=stock["Volume"],
        y=stock["Close"],
        mode="markers",
        name="Price vs Volume"
    )
)

fig21.update_layout(
    title="Price vs Trading Volume",
    xaxis_title="Volume",
    yaxis_title="Closing Price",
    height=450,
    template="plotly_white"
)

st.plotly_chart(
    fig21,
    use_container_width=True
)


# ============================================================
# 22. PRICE VS TURNOVER
# ============================================================

fig22 = go.Figure()

fig22.add_trace(
    go.Scatter(
        x=stock["Turnover"],
        y=stock["Close"],
        mode="markers",
        name="Price vs Turnover"
    )
)

fig22.update_layout(
    title="Price vs Turnover",
    xaxis_title="Turnover",
    yaxis_title="Closing Price",
    height=450,
    template="plotly_white"
)

st.plotly_chart(
    fig22,
    use_container_width=True
)


# ============================================================
# 23. OPEN-CLOSE RANGE
# ============================================================

stock["OpenCloseRange"] = (
    stock["Close"] - stock["Open"]
)

fig23 = go.Figure()

fig23.add_trace(
    go.Bar(
        x=stock["Date"],
        y=stock["OpenCloseRange"],
        name="Open-Close Range"
    )
)

fig23.update_layout(
    title="Open vs Close Difference",
    height=400,
    template="plotly_white"
)

st.plotly_chart(
    fig23,
    use_container_width=True
)


# ============================================================
# 24. PRICE MOMENTUM
# ============================================================

stock["Momentum20"] = (
    stock["Close"]
    -
    stock["Close"].shift(20)
)

fig24 = go.Figure()

fig24.add_trace(
    go.Scatter(
        x=stock["Date"],
        y=stock["Momentum20"],
        mode="lines",
        name="20-Day Momentum"
    )
)

fig24.update_layout(
    title="20-Day Price Momentum",
    height=400,
    template="plotly_white"
)

st.plotly_chart(
    fig24,
    use_container_width=True
)


# ============================================================
# 25. CORRELATION HEATMAP
# ============================================================

corr_cols = [
    "Open",
    "High",
    "Low",
    "Close",
    "VWAP",
    "Volume",
    "Turnover"
]

corr = stock[corr_cols].corr()

fig25 = go.Figure(
    data=go.Heatmap(
        z=corr.values,
        x=corr.columns,
        y=corr.columns,
        text=np.round(corr.values, 2),
        texttemplate="%{text}",
        colorscale="Blues"
    )
)

fig25.update_layout(
    title="Market Variable Correlation Matrix",
    height=550
)

st.plotly_chart(
    fig25,
    use_container_width=True
)


# ============================================================
# 26. DATA TABLE
# ============================================================

st.markdown(
    '<div class="section-title">📋 MARKET DATA</div>',
    unsafe_allow_html=True
)

display_cols = [
    "Date",
    "Symbol",
    "Open",
    "High",
    "Low",
    "Close",
    "VWAP",
    "Volume",
    "Turnover"
]

display_cols = [
    c for c in display_cols
    if c in stock.columns
]

st.dataframe(
    stock[display_cols].sort_values(
        "Date",
        ascending=False
    ),
    use_container_width=True,
    height=500
)


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    f"Indian Stock Market Executive Analytics | "
    f"{selected_symbol} | "
    f"{trading_records:,} records | "
    f"25+ analytical visuals"
)
