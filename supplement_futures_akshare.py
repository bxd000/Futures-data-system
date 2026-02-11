# -*- coding: utf-8 -*-
"""
用 akshare 补全 2024-07-18 之后的玉米、玉米淀粉、鸡蛋期货日K线，
与现有 data/*.csv 合并后写回，保证日期连续、去重。
"""

import os
import time

from config import DATA_DIR, SYMBOLS, CUTOFF_DATE, SUPPLEMENT_START_DATE

# SYMBOLS 为 {code: (name, note)}，此处只需 name
SYMBOLS = {k: v[0] for k, v in SYMBOLS.items()}


def load_existing_csv(symbol: str, name: str) -> list:
    """加载已有 CSV，返回 [ (日期, 开, 高, 低, 收, 量), ... ]"""
    path = os.path.join(DATA_DIR, f"{symbol}_{name}_历史日K.csv")
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, "r", encoding="utf-8-sig") as f:
        next(f)  # skip header
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if len(parts) >= 6:
                rows.append((parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]))
    return rows


def fetch_akshare_from(symbol: str, start_date: str):
    """用 akshare 拉取 start_date 起的日K，返回 list of (日期, 开, 高, 低, 收, 量)。"""
    try:
        import akshare as ak
    except ImportError:
        raise RuntimeError("请先安装 akshare: pip install akshare")
    # 格式 start_date: YYYYMMDD
    start = start_date.replace("-", "")
    df = ak.futures_main_sina(symbol=symbol, start_date=start)
    if df is None or df.empty:
        return []
    # 列名可能是 日期 开盘价 最高价 最低价 收盘价 成交量
    date_col = "日期" if "日期" in df.columns else "date"
    open_col = "开盘价" if "开盘价" in df.columns else "open"
    high_col = "最高价" if "最高价" in df.columns else "high"
    low_col = "最低价" if "最低价" in df.columns else "low"
    close_col = "收盘价" if "收盘价" in df.columns else "close"
    vol_col = "成交量" if "成交量" in df.columns else "volume"
    rows = []
    for _, r in df.iterrows():
        dt = r[date_col]
        if hasattr(dt, "strftime"):
            dt = dt.strftime("%Y-%m-%d")
        else:
            dt = str(dt).replace("/", "-")[:10]
        open_ = str(r[open_col])
        high = str(r[high_col])
        low = str(r[low_col])
        close = str(r[close_col])
        try:
            v = r[vol_col]
            vol = str(int(float(v))) if v == v else "0"
        except (TypeError, ValueError):
            vol = "0"
        rows.append((dt, open_, high, low, close, vol))
    return rows


def merge_and_save(symbol: str, name: str, existing: list, new_rows: list):
    """合并已有 + 新数据（仅日期 > CUTOFF_DATE），按日期排序去重后写回 CSV。"""
    before = len(existing)
    seen = {r[0] for r in existing}
    for r in new_rows:
        if r[0] > CUTOFF_DATE and r[0] not in seen:
            existing.append(r)
            seen.add(r[0])
    existing.sort(key=lambda x: x[0])
    path = os.path.join(DATA_DIR, f"{symbol}_{name}_历史日K.csv")
    try:
        with open(path, "w", encoding="utf-8-sig") as f:
            f.write("日期,开盘(元/吨),最高(元/吨),最低(元/吨),收盘(元/吨),成交量(手)\n")
            for r in existing:
                f.write(f"{r[0]},{r[1]},{r[2]},{r[3]},{r[4]},{r[5]}\n")
    except OSError as e:
        if e.errno == 13:  # Permission denied，可能文件被 Excel 打开
            path = os.path.join(DATA_DIR, f"{symbol}_{name}_历史日K_补全.csv")
            with open(path, "w", encoding="utf-8-sig") as f:
                f.write("日期,开盘(元/吨),最高(元/吨),最低(元/吨),收盘(元/吨),成交量(手)\n")
                for r in existing:
                    f.write(f"{r[0]},{r[1]},{r[2]},{r[3]},{r[4]},{r[5]}\n")
        else:
            raise
    return path, len(existing), len(existing) - before


def main():
    print("补全 2024-07-18 之后数据（akshare 主力连续），与现有 CSV 合并\n")
    os.makedirs(DATA_DIR, exist_ok=True)
    for symbol, name in SYMBOLS.items():
        print(f"{name} ({symbol})")
        try:
            existing = load_existing_csv(symbol, name)
            before = len(existing)
            new_rows = fetch_akshare_from(symbol, SUPPLEMENT_START_DATE)
            path, total, added = merge_and_save(symbol, name, existing, new_rows)
            print(f"  原有 {before} 条，新增 {added} 条，合计 {total} 条 -> {path}\n")
        except Exception as e:
            print(f"  失败: {e}\n")
        time.sleep(0.5)
    print("补全完成。")


if __name__ == "__main__":
    main()
