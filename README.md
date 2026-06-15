# EnglishTok — 英语短视频学习

刷 B站 + YouTube 英语学习短视频，抖音式全屏沉浸体验。

## 本地运行

双击 `start.bat`，浏览器打开 `http://localhost:8765`

> 需要安装 Python 3

## 部署到公网 (手机随时打开)

### 1. 上传到 GitHub
- 在 GitHub 新建仓库，把整个文件夹推送上去

### 2. 部署到 Vercel (免费)
- 打开 [vercel.com](https://vercel.com)，用 GitHub 登录
- 点 **New Project** → 导入你的仓库
- 直接点 **Deploy**，不需要改任何设置
- 获得 `xxx.vercel.app` 地址

### 3. 手机打开
- 手机浏览器访问 `xxx.vercel.app`
- 不依赖电脑，随时随地刷

## 功能

- 全屏竖屏，滑动切换
- 自动播放，离开停止
- 进度条 + 点击暂停 (本地)/ iframe 播放 (公网)
- 收藏夹、双击点赞
- B站内容免费使用，YouTube 需自行申请 API Key

## 注意

- 公网版 (Vercel) B站视频通过 iframe 播放，无法显示自定义进度条
- 本地版功能最全 (原生播放器 + 进度条 + 点击暂停)
