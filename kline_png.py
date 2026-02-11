# -*- coding: utf-8 -*-
"""
用 mplfinance 生成静态 K 线图 PNG，保存到 charts/ 目录。
适合报告、打印或不需要交互时查看。
运行: python kline_png.py
"""

import os
import pandas as pd

DATA_DIR = "data"
OUT_DIR = "charts"
SYMBOLS = [("C0", "玉米"), ("CS0", "玉米淀粉"), ("JD0", "鸡蛋")]


def load_df(symbol: str, name: str) -> pd.DataFrame:
    path = os.path.join(DATA_DIR, f"{symbol}_{name}_历史日K.csv")
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path, encoding="utf-8-sig")
    # 兼容带单位的列名
    df.columns = [c.split("(")[0].strip() for c in df.columns]
    col_map = {"日期": "Date", "开盘": "Open", "最高": "High", "最低": "Low", "收盘": "Close", "成交量": "Volume"}
    df = df.rename(columns=col_map)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date")
    df = df[["Open", "High", "Low", "Close", "Volume"]].astype(float)
    return df


def main():
    try:
        import mplfinance as mpf
    except ImportError:
        print("请先安装: pip install mplfinance")
        return
    os.makedirs(OUT_DIR, exist_ok=True)
    for symbol, name in SYMBOLS:
        df = load_df(symbol, name)
        if df.empty:
            continue
        out = os.path.join(OUT_DIR, f"{name}_日K.png")
        mpf.plot(
            df,
            type="candle",
            volume=True,
            style="charles",
            title=f"{name} 主力连续 日K线",
            ylabel="价格(元/吨)",
            ylabel_lower="成交量(手)",
            savefig=out,
            figsize=(12, 6),
        )
        print(f"已保存: {out}")
    print("全部完成，图片在 charts/ 目录。")


if __name__ == "__main__":
    main()
