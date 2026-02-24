# -*- coding: utf-8 -*-
"""
期货日K线数据系统 - Web 端
提供 K 线图、数据表、数据更新页面与 API。
"""

import json
import os
import subprocess
import sys
import time

from flask import Flask, render_template, request, jsonify, send_file

# 项目根目录加入 path，保证可 import config 及各模块
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from config import SYMBOL_LIST, CONTRACT_MULTI, csv_path

app = Flask(__name__, static_folder="static", template_folder="templates")

# get_data_meta 内存缓存，减少重复读盘
_meta_cache = None
_meta_cache_time = 0
META_CACHE_TTL = 60  # 秒


@app.context_processor
def inject_meta():
    """向所有模板注入数据元信息。异常时不注入，避免 500。"""
    try:
        meta = get_data_meta()
        return {"data_end_date": meta.get("data_end_date") or ""}
    except Exception:
        return {"data_end_date": ""}


def load_kline(symbol: str, name: str):
    """读取某品种 CSV，返回 (dates, k_data, volumes, ma20)。k_data 每项 [open, close, low, high]。"""
    path = csv_path(symbol, name)
    if not os.path.exists(path):
        return [], [], [], []
    dates, k_data, volumes, closes = [], [], [], []
    with open(path, "r", encoding="utf-8-sig") as f:
        next(f)
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if len(parts) < 6:
                continue
            try:
                date = parts[0].strip()
                open_ = float(parts[1])
                high = float(parts[2])
                low = float(parts[3])
                close = float(parts[4])
                vol = int(float(parts[5]))
            except (ValueError, TypeError):
                continue
            dates.append(date)
            k_data.append([round(open_, 2), round(close, 2), round(low, 2), round(high, 2)])
            volumes.append(vol)
            closes.append(close)
    ma20 = []
    for i in range(len(closes)):
        if i < 19:
            ma20.append(None)
        else:
            ma20.append(round(sum(closes[i - 19 : i + 1]) / 20, 2))
    return dates, k_data, volumes, ma20


def get_data_meta():
    """返回数据元信息：最新日期、各品种条数。带 60 秒内存缓存。任何异常时返回空，避免 500。"""
    global _meta_cache, _meta_cache_time
    now = time.time()
    if _meta_cache is not None and (now - _meta_cache_time) < META_CACHE_TTL:
        return _meta_cache
    try:
        latest = ""
        counts = {}
        for code, name in SYMBOL_LIST:
            path = csv_path(code, name)
            if not os.path.exists(path):
                continue
            n = 0
            last_date = ""
            with open(path, "r", encoding="utf-8-sig", errors="ignore") as f:
                next(f, None)
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(",")
                    if len(parts) >= 1:
                        last_date = parts[0].strip()
                        n += 1
            if last_date:
                counts[name] = n
                if not latest or last_date > latest:
                    latest = last_date
        _meta_cache = {"data_end_date": latest or "", "counts": counts}
        _meta_cache_time = now
        return _meta_cache
    except Exception:
        return {"data_end_date": "", "counts": {}}


def load_table(symbol: str, name: str):
    """返回表格行列表：每行 [日期, 开, 高, 低, 收, 量, MA20]。"""
    dates, k_data, volumes, ma20 = load_kline(symbol, name)
    rows = []
    for i in range(len(dates)):
        k = k_data[i]
        # k: [open, close, low, high] -> 表列：开、高、低、收
        rows.append([
            dates[i], k[0], k[3], k[2], k[1], volumes[i],
            ma20[i] if ma20[i] is not None else ""
        ])
    return rows


# ---------- API ----------

@app.route("/api/symbols")
def api_symbols():
    """品种列表：[{ code, name }, ...]"""
    return jsonify([{"code": code, "name": name} for code, name in SYMBOL_LIST])


@app.route("/api/kline/<code>")
def api_kline(code):
    """某品种 K 线数据：{ dates, k, vol, ma20 }。"""
    name_map = {c: n for c, n in SYMBOL_LIST}
    if code not in name_map:
        return jsonify({"error": "未知品种"}), 404
    name = name_map[code]
    dates, k_data, volumes, ma20 = load_kline(code, name)
    if not dates:
        return jsonify({"error": "无数据"}), 404
    resp = jsonify({
        "dates": dates,
        "k": k_data,
        "vol": volumes,
        "ma20": [v if v is not None else None for v in ma20],
    })
    resp.headers["Cache-Control"] = "public, max-age=60"
    return resp


@app.route("/api/table/<code>")
def api_table(code):
    """某品种表格数据（分页）：?page=1&size=100。"""
    name_map = {c: n for c, n in SYMBOL_LIST}
    if code not in name_map:
        return jsonify({"error": "未知品种"}), 404
    name = name_map[code]
    rows = load_table(code, name)
    page = max(1, request.args.get("page", 1, type=int))
    size = max(1, min(500, request.args.get("size", 100, type=int)))
    total = len(rows)
    start = (page - 1) * size
    chunk = rows[start : start + size]
    resp = jsonify({
        "total": total,
        "page": page,
        "size": size,
        "rows": chunk,
    })
    resp.headers["Cache-Control"] = "public, max-age=30"
    return resp


@app.route("/api/meta")
def api_meta():
    """数据元信息：最新日期等。"""
    resp = jsonify(get_data_meta())
    resp.headers["Cache-Control"] = "public, max-age=60"
    return resp


@app.route("/api/update", methods=["POST"])
def api_update():
    """执行数据更新：先 supplement，再可选 export。返回 { ok, log }。"""
    if os.environ.get("VERCEL"):
        return jsonify({
            "ok": False,
            "log": "数据更新仅在本地可用。请在本机运行 python app.py 后使用「数据更新」功能；线上环境为只读展示。"
        })
    do_export = request.json and request.json.get("export") is True
    try:
        cmd = [sys.executable, os.path.join(ROOT, "run.py"), "supplement"]
        out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=120)
        log = (out.stdout or "") + (out.stderr or "")
        if not out.returncode == 0:
            return jsonify({"ok": False, "log": log or "执行失败"})
        if do_export:
            cmd2 = [sys.executable, os.path.join(ROOT, "run.py"), "export"]
            out2 = subprocess.run(cmd2, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=60)
            log += "\n" + (out2.stdout or "") + (out2.stderr or "")
        return jsonify({"ok": True, "log": log.strip() or "完成"})
    except subprocess.TimeoutExpired:
        return jsonify({"ok": False, "log": "执行超时", "error": "执行超时"})
    except Exception as e:
        return jsonify({"ok": False, "log": str(e), "error": str(e)})


# ---------- 页面 ----------

@app.route("/")
def index():
    return render_template("index.html", symbols=SYMBOL_LIST)


@app.route("/kline")
def kline_page():
    static_dir = app.static_folder or os.path.join(ROOT, "static")
    has_local_echarts = os.path.isfile(os.path.join(static_dir, "echarts.min.js"))
    return render_template("kline.html", symbols=SYMBOL_LIST, has_local_echarts=has_local_echarts)


@app.route("/data")
def data_page():
    return render_template("data.html", symbols=SYMBOL_LIST)


@app.route("/update")
def update_page():
    return render_template("update.html")


@app.route("/backtest")
def backtest_page():
    from backtest import STRATEGIES
    strats = [{"key": k, "name": v["name"], "params": v["params"]}
              for k, v in STRATEGIES.items()]
    return render_template("backtest.html", symbols=SYMBOL_LIST, strategies=strats)


@app.route("/api/backtest", methods=["POST"])
def api_backtest():
    from backtest import BacktestEngine, STRATEGIES
    body = request.json or {}
    symbol = body.get("symbol", "C0")
    strat_key = body.get("strategy", "ma_cross")
    params = body.get("params", {})
    start_date = body.get("start_date", "")
    end_date = body.get("end_date", "")
    capital = float(body.get("capital", 100000))
    lots = int(body.get("lots", 1))
    commission = float(body.get("commission", 5))

    if strat_key not in STRATEGIES:
        return jsonify({"error": "未知策略"}), 400

    name_map = {c: n for c, n in SYMBOL_LIST}
    if symbol not in name_map:
        return jsonify({"error": "未知品种"}), 400

    dates, k_data, volumes, _ = load_kline(symbol, name_map[symbol])
    if not dates:
        return jsonify({"error": "无数据"}), 404

    if start_date:
        idx = next((i for i, d in enumerate(dates) if d >= start_date), 0)
        dates, k_data, volumes = dates[idx:], k_data[idx:], volumes[idx:]
    if end_date:
        idx = next((i for i in range(len(dates) - 1, -1, -1) if dates[i] <= end_date), len(dates) - 1)
        dates, k_data, volumes = dates[: idx + 1], k_data[: idx + 1], volumes[: idx + 1]

    if len(dates) < 30:
        return jsonify({"error": "数据不足（至少需要 30 根 K 线）"}), 400

    opens = [r[0] for r in k_data]
    closes = [r[1] for r in k_data]
    lows = [r[2] for r in k_data]
    highs = [r[3] for r in k_data]

    multi = CONTRACT_MULTI.get(symbol, 10)
    for k, v in params.items():
        try:
            params[k] = float(v)
            if params[k] == int(params[k]):
                params[k] = int(params[k])
        except (ValueError, TypeError):
            pass

    engine = BacktestEngine(dates, opens, highs, lows, closes, volumes)
    result = engine.run(strat_key, params, capital=capital, lots=lots,
                        commission=commission, multiplier=multi)

    kline_out = []
    for i in range(len(dates)):
        kline_out.append({
            "time": dates[i], "open": opens[i], "high": highs[i],
            "low": lows[i], "close": closes[i],
        })
    result["kline"] = kline_out
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
