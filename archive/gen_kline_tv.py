# -*- coding: utf-8 -*-
"""
用 TradingView Lightweight Charts 生成 K 线 HTML，风格更接近专业行情软件。
生成 kline_tv.html，用浏览器打开。
"""

import os
import json

DATA_DIR = "data"
SYMBOLS = [("C0", "玉米"), ("CS0", "玉米淀粉"), ("JD0", "鸡蛋")]


def load_csv(symbol: str, name: str):
    path = os.path.join(DATA_DIR, f"{symbol}_{name}_历史日K.csv")
    if not os.path.exists(path):
        return [], [], []
    dates, k_data, volumes = [], [], []
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
                o, h, l, c = float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
                vol = int(float(parts[5]))
            except (ValueError, IndexError):
                continue
            dates.append(date)
            k_data.append({"time": date, "open": round(o, 2), "high": round(h, 2), "low": round(l, 2), "close": round(c, 2)})
            volumes.append({"time": date, "value": vol})
    return dates, k_data, volumes


def main():
    all_data = {}
    for symbol, name in SYMBOLS:
        _, k_data, volumes = load_csv(symbol, name)
        if not k_data:
            continue
        all_data[name] = {"k": k_data, "vol": volumes}
    if not all_data:
        print("未找到 CSV 数据")
        return
    names = list(all_data.keys())
    default = names[0]
    all_k_js = json.dumps(all_data, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>K线 - Lightweight Charts</title>
  <script src="https://unpkg.com/lightweight-charts@4.1.0/dist/lightweight-charts.standalone.production.js"></script>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: #131722; color: #d1d4dc; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }}
    .toolbar {{ padding: 10px 16px; display: flex; align-items: center; gap: 10px; }}
    .toolbar select {{ padding: 6px 12px; background: #2a2e39; border: 1px solid #363c4e; color: #d1d4dc; border-radius: 4px; cursor: pointer; }}
    #container {{ width: 100%; height: calc(100vh - 48px); min-height: 360px; }}
  </style>
</head>
<body>
  <div class="toolbar">
    <span>品种</span>
    <select id="sym"></select>
  </div>
  <div id="container"></div>
  <script>
    var allData = {all_k_js};
    var names = {json.dumps(names, ensure_ascii=False)};
    var sel = document.getElementById("sym");
    names.forEach(function(n) {{
      var o = document.createElement("option"); o.value = n; o.textContent = n; sel.appendChild(o);
    }});
    var container = document.getElementById("container");
    var chart = LightweightCharts.createChart(container, {{
      layout: {{ background: {{ type: "solid", color: "#131722" }}, textColor: "#d1d4dc" }},
      grid: {{ vertLines: {{ color: "#2a2e39" }}, horzLines: {{ color: "#2a2e39" }} }},
      width: container.clientWidth,
      height: container.clientHeight,
      timeScale: {{ timeVisible: true, secondsVisible: false }},
      rightPriceScale: {{ borderColor: "#2a2e39" }}
    }});
    var candle = chart.addCandlestickSeries({{ upColor: "#26a69a", downColor: "#ef5350", borderVisible: false }});
    var vol = chart.addHistogramSeries({{ color: "#26a69a", priceFormat: {{ type: "volume" }}, priceScaleId: "" }});
    vol.priceScale().applyOptions({{ scaleMargins: {{ top: 0.8, bottom: 0 }} }});
    function setData(name) {{
      var d = allData[name];
      var k = d.k.map(function(r) {{ return {{ time: r.time, open: r.open, high: r.high, low: r.low, close: r.close }}; }});
      var v = d.vol.map(function(r, i) {{ return {{ time: r.time, value: r.value, color: k[i].close >= k[i].open ? "rgba(38,166,154,0.5)" : "rgba(239,83,80,0.5)" }}; }});
      candle.setData(k);
      vol.setData(v);
      chart.timeScale().fitContent();
    }}
    setData(sel.value);
    sel.addEventListener("change", function() {{ setData(sel.value); }});
    window.addEventListener("resize", function() {{ chart.applyOptions({{ width: container.clientWidth, height: container.clientHeight }}); }});
  </script>
</body>
</html>"""
    out = os.path.join(os.path.dirname(__file__), "kline_tv.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"已生成: {out}\n用浏览器打开即可（TradingView 风格）。")


if __name__ == "__main__":
    main()
