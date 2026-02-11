# -*- coding: utf-8 -*-
"""将 ECharts 5.4.3 下载到 static/echarts.min.js，K 线页将优先使用本地文件。"""
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC = os.path.join(ROOT, "static")
URL = "https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"
OUT = os.path.join(STATIC, "echarts.min.js")

def main():
    os.makedirs(STATIC, exist_ok=True)
    print("Downloading ECharts 5.4.3...")
    try:
        urllib.request.urlretrieve(URL, OUT)
        print("Saved to", OUT)
    except Exception as e:
        print("Error:", e, file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
