# -*- coding: utf-8 -*-
"""
期货策略回测引擎
支持双均线交叉、MACD、布林带突破、KDJ 四种内置策略。
"""

import math
from datetime import datetime


# ── 技术指标计算 ──────────────────────────────────────────────

def _sma(arr, period):
    out = [None] * len(arr)
    s = 0.0
    for i, v in enumerate(arr):
        s += v
        if i >= period:
            s -= arr[i - period]
        if i >= period - 1:
            out[i] = s / period
    return out


def _ema(arr, period):
    k = 2.0 / (period + 1)
    out = [arr[0]]
    for i in range(1, len(arr)):
        out.append(arr[i] * k + out[-1] * (1 - k))
    return out


# ── 策略信号生成 ──────────────────────────────────────────────
# 每个策略返回 list[int]，长度等于 K 线数量
# 1 = 买入信号, -1 = 卖出信号, 0 = 无操作

def strategy_ma_cross(closes, short=5, long=20, **_):
    ma_s = _sma(closes, short)
    ma_l = _sma(closes, long)
    n = len(closes)
    sig = [0] * n
    for i in range(1, n):
        if ma_s[i] is None or ma_l[i] is None or ma_s[i - 1] is None or ma_l[i - 1] is None:
            continue
        if ma_s[i - 1] <= ma_l[i - 1] and ma_s[i] > ma_l[i]:
            sig[i] = 1
        elif ma_s[i - 1] >= ma_l[i - 1] and ma_s[i] < ma_l[i]:
            sig[i] = -1
    return sig


def strategy_macd(closes, fast=12, slow=26, signal=9, **_):
    ef = _ema(closes, fast)
    es = _ema(closes, slow)
    dif = [ef[i] - es[i] for i in range(len(closes))]
    dea = _ema(dif, signal)
    n = len(closes)
    sig = [0] * n
    for i in range(slow, n):
        if dif[i - 1] <= dea[i - 1] and dif[i] > dea[i]:
            sig[i] = 1
        elif dif[i - 1] >= dea[i - 1] and dif[i] < dea[i]:
            sig[i] = -1
    return sig


def strategy_boll(closes, period=20, mult=2.0, **_):
    mid = _sma(closes, period)
    n = len(closes)
    sig = [0] * n
    for i in range(1, n):
        if mid[i] is None or mid[i - 1] is None:
            continue
        sq = sum((closes[j] - mid[i]) ** 2 for j in range(i - period + 1, i + 1))
        std = math.sqrt(sq / period)
        upper = mid[i] + mult * std
        lower = mid[i] - mult * std
        prev_sq = sum((closes[j] - mid[i - 1]) ** 2 for j in range(i - period, i))
        prev_std = math.sqrt(prev_sq / period)
        prev_upper = mid[i - 1] + mult * prev_std
        prev_lower = mid[i - 1] - mult * prev_std
        if closes[i - 1] <= prev_upper and closes[i] > upper:
            sig[i] = 1
        elif closes[i - 1] >= prev_lower and closes[i] < lower:
            sig[i] = -1
    return sig


def strategy_kdj(closes, highs, lows, period=9, **_):
    n = len(closes)
    sig = [0] * n
    kv, dv = [50.0] * n, [50.0] * n
    for i in range(period - 1, n):
        hi = max(highs[i - period + 1: i + 1])
        lo = min(lows[i - period + 1: i + 1])
        rsv = 50.0 if hi == lo else (closes[i] - lo) / (hi - lo) * 100
        if i == period - 1:
            kv[i] = 50.0
            dv[i] = 50.0
        else:
            kv[i] = (2 * kv[i - 1] + rsv) / 3
            dv[i] = (2 * dv[i - 1] + kv[i]) / 3
    for i in range(period, n):
        if kv[i - 1] <= dv[i - 1] and kv[i] > dv[i] and kv[i] < 30:
            sig[i] = 1
        elif kv[i - 1] >= dv[i - 1] and kv[i] < dv[i] and kv[i] > 70:
            sig[i] = -1
    return sig


STRATEGIES = {
    "ma_cross": {
        "name": "双均线交叉",
        "fn": strategy_ma_cross,
        "params": [
            {"key": "short", "label": "短期周期", "default": 5, "min": 2, "max": 60},
            {"key": "long", "label": "长期周期", "default": 20, "min": 5, "max": 250},
        ],
        "needs_hl": False,
    },
    "macd": {
        "name": "MACD 金叉死叉",
        "fn": strategy_macd,
        "params": [
            {"key": "fast", "label": "快线", "default": 12, "min": 2, "max": 50},
            {"key": "slow", "label": "慢线", "default": 26, "min": 5, "max": 100},
            {"key": "signal", "label": "信号线", "default": 9, "min": 2, "max": 30},
        ],
        "needs_hl": False,
    },
    "boll": {
        "name": "布林带突破",
        "fn": strategy_boll,
        "params": [
            {"key": "period", "label": "周期", "default": 20, "min": 5, "max": 100},
            {"key": "mult", "label": "倍数", "default": 2.0, "min": 0.5, "max": 4.0},
        ],
        "needs_hl": False,
    },
    "kdj": {
        "name": "KDJ 金叉死叉",
        "fn": strategy_kdj,
        "params": [
            {"key": "period", "label": "周期", "default": 9, "min": 3, "max": 50},
        ],
        "needs_hl": True,
    },
}


# ── 回测引擎 ──────────────────────────────────────────────────

class BacktestEngine:
    def __init__(self, dates, opens, highs, lows, closes, volumes):
        self.dates = dates
        self.opens = opens
        self.highs = highs
        self.lows = lows
        self.closes = closes
        self.volumes = volumes
        self.n = len(dates)

    def run(self, strategy_key, params, capital=100000, lots=1,
            commission=5, multiplier=10):
        cfg = STRATEGIES[strategy_key]
        fn = cfg["fn"]
        kw = {p["key"]: params.get(p["key"], p["default"]) for p in cfg["params"]}
        if cfg["needs_hl"]:
            kw["highs"] = self.highs
            kw["lows"] = self.lows
        signals_raw = fn(self.closes, **kw)

        trades = []
        signals_out = []
        equity = []
        cash = float(capital)
        pos = 0
        entry_price = 0.0
        entry_idx = 0
        peak = cash

        for i in range(self.n):
            sig = signals_raw[i]
            price = self.opens[min(i + 1, self.n - 1)] if i + 1 < self.n else self.closes[i]

            if sig == 1 and pos == 0 and i + 1 < self.n:
                exec_price = self.opens[i + 1]
                pos = lots
                entry_price = exec_price
                entry_idx = i + 1
                cash -= commission * lots
                signals_out.append({
                    "date": self.dates[i + 1], "action": "buy",
                    "price": exec_price,
                })
            elif sig == -1 and pos > 0 and i + 1 < self.n:
                exec_price = self.opens[i + 1]
                pnl = (exec_price - entry_price) * multiplier * pos - commission * pos
                cash += pnl
                trades.append(self._trade(entry_idx, i + 1, entry_price, exec_price,
                                          pnl, capital, multiplier, pos))
                signals_out.append({
                    "date": self.dates[i + 1], "action": "sell",
                    "price": exec_price,
                })
                pos = 0

            unrealised = 0.0
            if pos > 0:
                unrealised = (self.closes[i] - entry_price) * multiplier * pos
            eq = cash + unrealised
            if eq > peak:
                peak = eq
            equity.append({"date": self.dates[i], "value": round(eq, 2)})

        if pos > 0:
            exec_price = self.closes[-1]
            pnl = (exec_price - entry_price) * multiplier * pos - commission * pos
            cash += pnl
            trades.append(self._trade(entry_idx, self.n - 1, entry_price, exec_price,
                                      pnl, capital, multiplier, pos))
            signals_out.append({
                "date": self.dates[-1], "action": "sell",
                "price": exec_price,
            })
            equity[-1]["value"] = round(cash, 2)

        metrics = self._metrics(trades, equity, capital)
        return {
            "metrics": metrics,
            "equity": equity,
            "trades": trades,
            "signals": signals_out,
        }

    def _trade(self, ei, xi, ep, xp, pnl, cap, multi, lots):
        d0 = datetime.strptime(self.dates[ei], "%Y-%m-%d")
        d1 = datetime.strptime(self.dates[xi], "%Y-%m-%d")
        return {
            "entry_date": self.dates[ei],
            "entry_price": round(ep, 2),
            "exit_date": self.dates[xi],
            "exit_price": round(xp, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl / cap * 100, 2),
            "holding_days": (d1 - d0).days,
        }

    @staticmethod
    def _metrics(trades, equity, capital):
        final = equity[-1]["value"] if equity else capital
        total_ret = (final - capital) / capital * 100
        days = len(equity)
        years = days / 252 if days > 0 else 1
        annual_ret = ((final / capital) ** (1 / years) - 1) * 100 if years > 0 and final > 0 else 0

        peak = capital
        max_dd = 0.0
        for e in equity:
            if e["value"] > peak:
                peak = e["value"]
            dd = (e["value"] - peak) / peak * 100 if peak else 0
            if dd < max_dd:
                max_dd = dd

        wins = [t for t in trades if t["pnl"] > 0]
        losses = [t for t in trades if t["pnl"] <= 0]
        win_rate = len(wins) / len(trades) * 100 if trades else 0
        gross_profit = sum(t["pnl"] for t in wins) if wins else 0
        gross_loss = abs(sum(t["pnl"] for t in losses)) if losses else 0
        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else 999.0
        avg_hold = sum(t["holding_days"] for t in trades) / len(trades) if trades else 0

        return {
            "total_return": round(total_ret, 2),
            "annual_return": round(annual_ret, 2),
            "max_drawdown": round(max_dd, 2),
            "win_rate": round(win_rate, 1),
            "total_trades": len(trades),
            "profit_factor": profit_factor,
            "avg_holding_days": round(avg_hold, 1),
        }
