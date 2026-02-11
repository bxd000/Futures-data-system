# -*- coding: utf-8 -*-
"""
读取 data/ 下玉米、玉米淀粉、鸡蛋的 CSV，生成带 K 线图的 HTML，用浏览器打开即可查看。
"""

import os
import json

DATA_DIR = "data"
SYMBOLS = [
    ("C0", "玉米"),
    ("CS0", "玉米淀粉"),
    ("JD0", "鸡蛋"),
]


def load_csv(symbol: str, name: str) -> tuple:
    """读取 CSV，返回 (dates, k_data, volumes, ma20)。k_data 每项为 [open, close, low, high]。"""
    path = os.path.join(DATA_DIR, f"{symbol}_{name}_历史日K.csv")
    if not os.path.exists(path):
        return [], [], [], []
    dates = []
    k_data = []
    volumes = []
    closes = []
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
            except (ValueError, IndexError):
                continue
            dates.append(date)
            k_data.append([round(open_, 2), round(close, 2), round(low, 2), round(high, 2)])
            volumes.append(vol)
            closes.append(close)
    # MA20 去杂音
    ma20 = []
    for i in range(len(closes)):
        if i < 19:
            ma20.append(None)
        else:
            ma20.append(round(sum(closes[i - 19 : i + 1]) / 20, 2))
    return dates, k_data, volumes, ma20


def main():
    all_data = {}
    for symbol, name in SYMBOLS:
        dates, k_data, volumes, ma20 = load_csv(symbol, name)
        if not dates:
            continue
        all_data[name] = {"dates": dates, "k": k_data, "vol": volumes, "ma20": ma20}

    if not all_data:
        print("未找到任何 CSV 数据，请先运行 sina_futures_history.py 与 supplement_futures_akshare.py")
        return

    # 选第一个品种做默认展示，并生成选项
    names = list(all_data.keys())
    default_name = names[0]
    options_js = json.dumps(names, ensure_ascii=False)
    default_dates = json.dumps(all_data[default_name]["dates"], ensure_ascii=False)
    default_k = json.dumps(all_data[default_name]["k"], ensure_ascii=False)
    default_vol = json.dumps(all_data[default_name]["vol"], ensure_ascii=False)

    all_dates_js = json.dumps({n: all_data[n]["dates"] for n in names}, ensure_ascii=False)
    all_k_js = json.dumps({n: all_data[n]["k"] for n in names}, ensure_ascii=False)
    all_vol_js = json.dumps({n: all_data[n]["vol"] for n in names}, ensure_ascii=False)
    all_ma20_js = json.dumps({n: all_data[n]["ma20"] for n in names}, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>玉米 / 玉米淀粉 / 鸡蛋 日K线</title>
  <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: "Microsoft YaHei", sans-serif; background: #1a1a2e; color: #eee; min-height: 100vh; }}
    .toolbar {{ padding: 12px 16px; display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }}
    .toolbar label {{ font-size: 14px; }}
    .toolbar select {{ padding: 6px 10px; font-size: 14px; border-radius: 6px; border: 1px solid #444; background: #2d2d44; color: #eee; cursor: pointer; }}
    #chart {{ width: 100%; height: 50vh; min-height: 320px; }}
    .table-wrap {{ padding: 0 16px 16px; max-height: 45vh; overflow: auto; }}
    .table-wrap table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    .table-wrap th, .table-wrap td {{ padding: 6px 10px; text-align: right; border-bottom: 1px solid #333; }}
    .table-wrap th {{ text-align: left; position: sticky; top: 0; background: #1a1a2e; }}
    .table-wrap tr.highlight {{ background: rgba(38, 166, 154, 0.25); }}
    .table-wrap tr:hover {{ background: rgba(255,255,255,0.06); }}
  </style>
</head>
<body>
  <div class="toolbar">
    <label for="symbol">品种：</label>
    <select id="symbol"></select>
    <span style="color:#888;font-size:12px;">拖拽图表选区或滑动条，下方表格会高亮对应区间</span>
  </div>
  <div id="chart"></div>
  <div class="table-wrap">
    <table><thead><tr><th>日期</th><th>开盘</th><th>最高</th><th>最低</th><th>收盘</th><th>成交量</th></tr></thead><tbody id="tb"></tbody></table>
  </div>
  <script>
    var names = {options_js};
    var allDates = {all_dates_js};
    var allK = {all_k_js};
    var allVol = {all_vol_js};
    var allMa20 = {all_ma20_js};

    var sel = document.getElementById("symbol");
    names.forEach(function(n) {{ var o = document.createElement("option"); o.value = n; o.textContent = n; sel.appendChild(o); }});

    var chart = echarts.init(document.getElementById("chart"));
    var tb = document.getElementById("tb");

    function fillTable(name, i0, i1) {{
      var dates = allDates[name];
      var k = allK[name];
      var vol = allVol[name];
      i0 = Math.max(0, Math.floor(i0));
      i1 = Math.min(dates.length, Math.ceil(i1));
      var html = "";
      for (var i = i0; i < i1; i++) {{
        var r = k[i];
        html += "<tr class='highlight' data-i='" + i + "'><td>" + dates[i] + "</td><td>" + r[0] + "</td><td>" + r[2] + "</td><td>" + r[3] + "</td><td>" + r[1] + "</td><td>" + vol[i] + "</td></tr>";
      }}
      tb.innerHTML = html;
    }}

    function update(name) {{
      var dates = allDates[name];
      var kData = allK[name];
      var volData = allVol[name];
      var ma20 = allMa20[name];
      var volBar = volData.map(function(v, i) {{
        var c = kData[i][0] <= kData[i][1] ? "#26a69a" : "#ef5350";
        return {{ value: v, itemStyle: {{ color: c }} }};
      }});
      var ma20Data = ma20.map(function(v) {{ return v == null ? "-" : v; }});
      chart.setOption({{
        animation: false,
        tooltip: {{ trigger: "axis", axisPointer: {{ type: "cross" }} }},
        legend: {{ data: ["K线", "MA20", "成交量"], top: 0 }},
        grid: [{{ left: "10%", right: "8%", top: "8%", height: "50%" }}, {{ left: "10%", right: "8%", top: "65%", height: "28%" }}],
        xAxis: [
          {{ type: "category", data: dates, gridIndex: 0, axisLabel: {{ show: true }} }},
          {{ type: "category", data: dates, gridIndex: 1, axisLabel: {{ show: false }} }}
        ],
        yAxis: [
          {{ scale: true, gridIndex: 0, splitLine: {{ lineStyle: {{ opacity: 0.2 }} }} }},
          {{ scale: true, gridIndex: 1, splitLine: {{ show: false }} }}
        ],
        dataZoom: [
          {{ type: "inside", xAxisIndex: [0, 1], start: 70, end: 100 }},
          {{ type: "slider", xAxisIndex: [0, 1], start: 70, end: 100 }}
        ],
        series: [
          {{ name: "K线", type: "candlestick", data: kData, xAxisIndex: 0, yAxisIndex: 0 }},
          {{ name: "MA20", type: "line", data: ma20Data, xAxisIndex: 0, yAxisIndex: 0, symbol: "none", lineStyle: {{ color: "#ffa726", width: 2 }}, smooth: true }},
          {{ name: "成交量", type: "bar", data: volBar, xAxisIndex: 1, yAxisIndex: 1 }}
        ]
      }}, true);
      chart.off("dataZoom");
      chart.on("dataZoom", function() {{
        var opt = chart.getOption();
        var dz = opt.dataZoom && opt.dataZoom[0];
        if (!dz || dz.start == null) return;
        var len = dates.length;
        var start = (dz.start / 100) * len;
        var end = (dz.end / 100) * len;
        fillTable(name, start, end);
      }});
      var len = dates.length;
      fillTable(name, len * 0.7, len);
    }}
    update(sel.value);
    sel.addEventListener("change", function() {{ update(sel.value); }});
    window.addEventListener("resize", function() {{ chart.resize(); }});
  </script>
</body>
</html>
"""

    out_path = os.path.join(os.path.dirname(__file__), "kline.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"已生成: {out_path}")
    print("用浏览器打开该文件即可查看 K 线（可切换品种、拖拽缩放）。")


if __name__ == "__main__":
    main()
