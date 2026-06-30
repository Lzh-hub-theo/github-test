# 🍅 work-timer · 桌面番茄钟

Windows 11 系统托盘常驻的番茄工作法计时器。专注 25 分钟 → 短休 5 分钟，4 轮一循环后长休 15 分钟。

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行
python main.py
```

启动后无主窗口弹出，仅在系统托盘出现 🍅 图标。单击图标打开主窗口，点击关闭按钮隐藏到托盘，托盘菜单"退出"才真正关闭进程。

## 技术栈

- **Python 3.10+** · 业务逻辑 + 进程管理
- **pystray** · 系统托盘
- **pywebview** · 主窗口（HTML/CSS/JS）
- **plyer** · 跨平台系统通知
- **winsound**（Windows 内置）· 阶段结束提示音

## 设计文档

`docs/superpowers/specs/2026-06-30-pomodoro-design.md`

## 状态文件

`%USERPROFILE%/.work_timer/state.json`

进程锁：`%USERPROFILE%/.work_timer/state.json.lock`
