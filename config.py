# -*- coding: utf-8 -*-
"""
期货日K线数据系统 - 统一配置
所有脚本从此处读取：数据目录、品种、输出路径等。
"""

import os

# 数据目录（CSV 存放）
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# 品种：代码 -> (中文名, 可选说明，供爬虫提示用)
SYMBOLS = {
    "C0": ("玉米", "大商所，约2004年恢复上市"),
    "CS0": ("玉米淀粉", "大商所，2014年12月上市"),
    "JD0": ("鸡蛋", "大商所，2013年11月8日上市"),
}

# 品种列表 (代码, 中文名)，供需要遍历的脚本用
SYMBOL_LIST = [(code, SYMBOLS[code][0]) for code in SYMBOLS]

# 新浪接口停更后，用 akshare 补全的起始日期
CUTOFF_DATE = "2024-07-17"
SUPPLEMENT_START_DATE = "2024-07-18"

# 导出的 Excel 文件名（不含路径）
OUT_EXCEL = "期货日K线_带图.xlsx"
OUT_EXCEL_ALT = "期货日K线_带图_新.xlsx"

# CSV 表头（与各脚本读写一致）
CSV_HEADER = "日期,开盘(元/吨),最高(元/吨),最低(元/吨),收盘(元/吨),成交量(手)\n"


def csv_path(symbol: str, name: str) -> str:
    """某品种历史日K的 CSV 路径。"""
    return os.path.join(DATA_DIR, f"{symbol}_{name}_历史日K.csv")
