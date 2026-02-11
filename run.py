# -*- coding: utf-8 -*-
"""
期货日K线数据系统 - 主入口
一条命令完成：拉取 → 补全最新 → 补全日历（可选）→ 导出 Excel。
"""

import argparse
import os
import sys

# 确保当前目录在 path 里，便于直接 python run.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DATA_DIR, SYMBOL_LIST


def cmd_fetch():
    """1. 从新浪拉取历史日K（自上市起）。"""
    from sina_futures_history import main
    main()


def cmd_supplement():
    """2. 用 akshare 补全 2024-07-18 之后的数据，与现有 CSV 合并。"""
    from supplement_futures_akshare import main
    main()


def cmd_fill_dates():
    """3. 将 CSV 补全为全部日历日期（非交易日用前收填充）。"""
    from fill_all_dates import main
    main()


def cmd_export():
    """4. 根据 CSV 生成带 K 线图 + MA20 的 Excel。"""
    from csv_to_excel_with_chart import main
    main()


def cmd_all(fill_calendar: bool = False):
    """全流程：fetch → supplement → [fill_dates] → export。"""
    print("======== 1/4 拉取新浪历史 ========\n")
    cmd_fetch()
    print("\n======== 2/4 补全最新（akshare） ========\n")
    cmd_supplement()
    if fill_calendar:
        print("\n======== 3/4 补全日历 ========\n")
        cmd_fill_dates()
    else:
        print("\n（跳过补全日历，仅交易日。加 --fill-dates 可补全）\n")
    print("======== 4/4 导出 Excel ========\n")
    cmd_export()
    print("\n数据系统全流程完成。")


def main():
    parser = argparse.ArgumentParser(
        description="期货日K线数据系统：拉取/补全/导出玉米、玉米淀粉、鸡蛋主力连续日K。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run.py all               # 全流程（不补全日历）
  python run.py all --fill-dates  # 全流程并补全全部日历日期
  python run.py fetch            # 仅拉取新浪
  python run.py supplement       # 仅补全 2024-07-18 后
  python run.py fill-dates       # 仅补全日历
  python run.py export          # 仅生成 Excel
        """,
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="all",
        choices=["all", "fetch", "supplement", "fill-dates", "export"],
        help="要执行的步骤（默认: all）",
    )
    parser.add_argument(
        "--fill-dates",
        action="store_true",
        help="在 all 流程中补全全部日历日期（非交易日用前收填充）",
    )
    args = parser.parse_args()

    os.makedirs(DATA_DIR, exist_ok=True)

    if args.command == "all":
        cmd_all(fill_calendar=args.fill_dates)
    elif args.command == "fetch":
        cmd_fetch()
    elif args.command == "supplement":
        cmd_supplement()
    elif args.command == "fill-dates":
        cmd_fill_dates()
    elif args.command == "export":
        cmd_export()


if __name__ == "__main__":
    main()
