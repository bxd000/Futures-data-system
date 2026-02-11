# -*- coding: utf-8 -*-
"""
把 data/ 下三个品种的 CSV 补全为「全部日历日期」：
非交易日（周末、节假日）用前一交易日收盘价填充开高低收，成交量为 0。
"""

import os
import pandas as pd

from config import DATA_DIR, SYMBOL_LIST as SYMBOLS


def load_df(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig")
    df.columns = [c.split("(")[0].strip() for c in df.columns]
    df = df.rename(columns={"日期": "Date", "开盘": "Open", "最高": "High", "最低": "Low", "收盘": "Close", "成交量": "Volume"})
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date").sort_index()
    return df[["Open", "High", "Low", "Close", "Volume"]].astype(float)


def save_df(path: str, df: pd.DataFrame):
    df = df.reset_index()
    date_col = df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col]).dt.strftime("%Y-%m-%d")
    with open(path, "w", encoding="utf-8-sig") as f:
        f.write("日期,开盘(元/吨),最高(元/吨),最低(元/吨),收盘(元/吨),成交量(手)\n")
        for _, r in df.iterrows():
            f.write(f"{r[date_col]},{r['Open']:.3f},{r['High']:.3f},{r['Low']:.3f},{r['Close']:.3f},{int(r['Volume'])}\n")


def main():
    for symbol, name in SYMBOLS:
        path = os.path.join(DATA_DIR, f"{symbol}_{name}_历史日K.csv")
        if not os.path.exists(path):
            continue
        df = load_df(path)
        if df.empty:
            continue
        full_range = pd.date_range(df.index.min(), df.index.max(), freq="D")
        df = df.reindex(full_range)
        df["Close"] = df["Close"].ffill()
        df["Open"] = df["Open"].ffill()
        df["High"] = df["High"].ffill()
        df["Low"] = df["Low"].ffill()
        df["Volume"] = df["Volume"].fillna(0).astype(int)
        df = df.dropna(subset=["Close"])
        save_df(path, df)
        print(f"{name}: 已补全为全部日期，共 {len(df)} 行 -> {path}")
    print("日期补全完成。")


if __name__ == "__main__":
    main()
