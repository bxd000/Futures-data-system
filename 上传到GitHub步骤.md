# 把代码上传到 GitHub 的步骤

## 1. 安装 Git（若尚未安装）

- 打开：https://git-scm.com/download/win  
- 下载并安装，安装时可按默认选项一路下一步。  
- 安装完成后**重新打开**终端（PowerShell 或 CMD）。

## 2. 在项目目录里初始化并提交

在终端里执行（请把路径改成你本机的项目目录，例如 `d:\vibeCoding\NO1`）：

```bash
cd d:\vibeCoding\NO1

git init
git add .
git commit -m "初始提交：期货日K线数据系统与网站"
```

说明：`.gitignore` 已配置好，不会把 `__pycache__`、`.venv`、`*.xlsx` 等提交上去；`data/` 下的 CSV 会被提交，方便 Vercel 部署。

## 3. 在 GitHub 上新建仓库

1. 打开 https://github.com 并登录。  
2. 右上角 **+** → **New repository**。  
3. **Repository name** 随便起一个，例如：`futures-kline`。  
4. 选 **Public**，不要勾选 “Add a README” 或 “Add .gitignore”（本地已有）。  
5. 点 **Create repository**。

## 4. 把本地代码推送到 GitHub

创建好仓库后，页面上会显示仓库地址，形如：  
`https://github.com/你的用户名/futures-kline.git`

在**同一个项目目录**里执行（把下面的地址换成你自己的仓库地址）：

```bash
git branch -M main
git remote add origin https://github.com/你的用户名/futures-kline.git
git push -u origin main
```

第一次推送时，可能会弹出浏览器或提示你登录 GitHub（或输入用户名/密码 / Token），按提示完成即可。

---

完成后，在 GitHub 上就能看到全部代码；之后要部署到 Vercel，在 Vercel 里 **Import** 这个仓库即可。
