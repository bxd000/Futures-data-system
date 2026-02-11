# -*- coding: utf-8 -*-
"""
Streamlit 本地 K 线应用：可选品种、日期范围，多图对比。
运行: streamlit run kline_streamlit.py
浏览器会自动打开本地页面。
"""

import os
import pandas as pd
import streamlit as st

DATA_DIR = "data"
SYMBOLS = [("C0", "玉米"), ("CS0", "玉米淀粉"), ("JD0", "鸡蛋")]


def load_df(symbol: str, name: str) -> pd.DataFrame:
    path = os.path.join(DATA_DIR, f"{symbol}_{name}_历史日K.csv")
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path, encoding="utf-8-sig")
    df.columns = [c.split("(")[0].strip() for c in df.columns]
    df = df.rename(columns={"日期": "Date", "开盘": "Open", "最高": "High", "最低": "Low", "收盘": "Close", "成交量": "Volume"})
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date")
    return df[["Open", "High", "Low", "Close", "Volume"]].astype(float)


def main():
    st.set_page_config(page_title="期货日K线", page_icon="📈", layout="wide")
    st.title("玉米 / 玉米淀粉 / 鸡蛋 日K线")
    names = [n for _, n in SYMBOLS]
    chosen = st.selectbox("选择品种", names, index=0)
    symbol = next(s for s, n in SYMBOLS if n == chosen)
    df = load_df(symbol, chosen)
    if df.empty:
        st.warning("未找到该品种数据，请先运行爬虫与补全脚本。")
        return
    col1, col2 = st.columns([1, 1])
    with col1:
        start = st.date_input("起始日期", value=df.index.min().date(), min_value=df.index.min().date(), max_value=df.index.max().date())
    with col2:
        end = st.date_input("结束日期", value=df.index.max().date(), min_value=df.index.min().date(), max_value=df.index.max().date())
    df = df.loc[pd.Timestamp(start) : pd.Timestamp(end)]
    if df.empty:
        st.warning("该日期区间无数据，请调整。")
        return
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
    except ImportError:
        st.error("请安装: pip install plotly")
        return
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], name="K线"), row=1, col=1)
    colors = ["#26a69a" if c >= o else "#ef5350" for o, c in zip(df["Open"], df["Close"])]
    fig.add_trace(go.Bar(x=df.index, y=df["Volume"], marker_color=colors, name="成交量"), row=2, col=1)
    fig.update_layout(title=f"{chosen} 日K线", template="plotly_dark", height=560, xaxis_rangeslider_visible=False)
    fig.update_yaxes(title_text="价格(元/吨)", row=1)
    fig.update_yaxes(title_text="成交量(手)", row=2)
    st.plotly_chart(fig, use_container_width=True)
    with st.expander("区间数据表"):
        st.dataframe(df.rename(columns={"Open": "开盘", "High": "最高", "Low": "最低", "Close": "收盘", "Volume": "成交量"}), use_container_width=True)


if __name__ == "__main__":
    main()
