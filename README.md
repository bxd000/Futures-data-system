# 期货日K线数据系统

玉米(C0)、玉米淀粉(CS0)、鸡蛋(JD0) 主力连续合约的**历史日K线**：采集、补全、导出一站式完成。

## 快速开始

```bash
pip install -r requirements.txt
python run.py all
```

## 网站（本地访问）

```bash
python app.py
```

浏览器打开 **http://127.0.0.1:5000**，可：

- **首页**：入口导航
- **K线图**：切换品种、收盘价折线 + 面积图、区间与网格、拖拽缩放，下方表格联动
- **数据表**：按品种分页查看日K表格（开/高/低/收/量/MA20）
- **数据更新**：一键从 akshare 补全到最新，可选同时导出 Excel（仅本地；线上为只读）

- 数据会写入 `data/` 下三个 CSV。
- 最后自动生成 **期货日K线_带图.xlsx**（每品种一表 + 全区间 K 线图 + MA20）。

## 数据系统入口：run.py

| 命令 | 说明 |
|------|------|
| `python run.py all` | **全流程**：新浪拉取 → akshare 补全最新 → 导出 Excel |
| `python run.py all --fill-dates` | 全流程并**补全全部日历日期**（非交易日用前收填充） |
| `python run.py fetch` | 仅从新浪拉取历史（自上市起） |
| `python run.py supplement` | 仅用 akshare 补全 2024-07-18 之后 |
| `python run.py fill-dates` | 仅将 CSV 补全为全部日历日 |
| `python run.py export` | 仅根据当前 CSV 生成带 K 线图的 Excel |

配置（品种、数据目录、导出文件名等）在 **config.py** 中统一修改。

## 部署到 Vercel

**部署前**：确保 `data/` 下三个 CSV 已存在并提交到 Git（若没有，先在本机执行 `python run.py all` 再提交）。

**步骤（无需安装 CLI）**：

1. 将本项目推送到 **GitHub**（含 `data/`、`templates/`、`app.py`、`config.py`、`vercel.json`、`requirements-vercel.txt`）。
2. 打开 [vercel.com](https://vercel.com) → 登录 → **Add New** → **Project**。
3. 选择 **Import Git Repository**，选中该仓库，点击 **Import**。
4. **Build and Output Settings** 保持默认（Vercel 会识别根目录 Flask **app.py**，并用 `requirements-vercel.txt` 安装依赖）。
5. 点击 **Deploy**，等待构建完成即可获得线上地址。

**说明**：线上为只读展示（K 线图 + 数据表），「数据更新」会提示仅在本地可用。之后若更新了本地 CSV，重新推送到 GitHub 即可触发 Vercel 自动重新部署。

本地用 CLI 预览：`npm i -g vercel` → `vercel login` → `vercel dev`。

## 输出说明

- **CSV**：`data/C0_玉米_历史日K.csv`、`data/CS0_玉米淀粉_历史日K.csv`、`data/JD0_鸡蛋_历史日K.csv`
- **表头**：日期, 开盘(元/吨), 最高(元/吨), 最低(元/吨), 收盘(元/吨), 成交量(手)
- **Excel**：`期货日K线_带图.xlsx`，每张表左侧为完整数据表（含 MA20），右侧为 K 线图 + MA20 折线图

## 数据来源与补全

- **新浪财经**：历史日K自上市/有记录起，该接口约 2024-07-17 后停更。
- **akshare**：用于补全 2024-07-18 至今，与现有 CSV 合并后写回，保证到最新交易日。

## 可选优化

- **ECharts 本地化**：运行 `python scripts/download_echarts.py` 将 ECharts 5.4.3 下载到 `static/echarts.min.js`，K 线页将优先使用本地文件，减少对 CDN 的依赖。
- **其他展示方式**：`archive/` 目录下保留有单文件 HTML、TradingView 风格、PNG 生成、Streamlit 等旧脚本，可按需使用。
- **Excel 带图**：`python run.py export` 或 `python csv_to_excel_with_chart.py` 可生成表格 + K 线 + MA20 的 Excel。
