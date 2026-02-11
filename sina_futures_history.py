# -*- coding: utf-8 -*-
"""
新浪财经 - 玉米、玉米淀粉、鸡蛋期货历史日K线爬虫
数据从交易所上市/新浪有记录开始拉取，保存为 CSV。
"""

import json
import os
import time
import requests

# 新浪期货日K线接口（主力连续合约，返回自上市起全部日线）
API_URL = "http://stock2.finance.sina.com.cn/futures/api/json.php/IndexService.getInnerFuturesDailyKLine"
HEADERS = {
    "Referer": "http://finance.sina.com.cn",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

from config import DATA_DIR, SYMBOLS


def fetch_daily_kline(symbol: str) -> list:
    """请求单品种日K线，返回 [ [日期, 开, 高, 低, 收, 量], ... ]"""
    resp = requests.get(API_URL, params={"symbol": symbol}, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    text = resp.text.strip()
    if not text:
        return []
    data = json.loads(text)
    return data if isinstance(data, list) else []


def save_csv(symbol: str, name: str, rows: list, out_dir: str = None):
    """保存为 CSV：日期, 开盘, 最高, 最低, 收盘, 成交量"""
    out_dir = out_dir or DATA_DIR
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{symbol}_{name}_历史日K.csv")
    with open(path, "w", encoding="utf-8-sig") as f:
        f.write("日期,开盘(元/吨),最高(元/吨),最低(元/吨),收盘(元/吨),成交量(手)\n")
        for r in rows:
            if len(r) >= 6:
                line = f"{r[0]},{r[1]},{r[2]},{r[3]},{r[4]},{r[5]}\n"
                f.write(line)
    return path


def main():
    print("新浪财经 - 玉米 / 玉米淀粉 / 鸡蛋 历史日K线爬取（自上市起）\n")
    for code, (name, note) in SYMBOLS.items():
        print(f"正在拉取: {name} ({code}) - {note}")
        try:
            rows = fetch_daily_kline(code)
            if not rows:
                print(f"  -> 无数据，跳过\n")
                continue
            path = save_csv(code, name, rows)
            print(f"  -> 共 {len(rows)} 条，已保存: {path}\n")
        except Exception as e:
            print(f"  -> 失败: {e}\n")
        time.sleep(0.5)
    print("全部完成。")


if __name__ == "__main__":
    main()
