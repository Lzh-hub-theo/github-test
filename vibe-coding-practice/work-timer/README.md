# 🍅 work-timer · 桌面番茄钟

Windows 11 系统托盘常驻的番茄工作法计时器。

## 打开方式

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行
python main.py
```

启动后**无主窗口弹出**，仅在系统托盘（屏幕右下角时间旁边）出现 🍅 图标。

- **单击托盘图标** → 打开主窗口
- **关闭主窗口** → 退出进程
- **托盘菜单**「开始/暂停」「退出」也可控制

## 依赖

- **Python 3.10+**
- [pystray](https://pypi.org/project/pystray/) · 系统托盘
- [pywebview](https://pypi.org/project/pywebview/) · 主窗口（HTML/CSS/JS 渲染）
- [plyer](https://pypi.org/project/plyer/) · 跨平台系统通知
- [Pillow](https://pypi.org/project/Pillow/) · 托盘图标
- **winsound**（Windows 内置）· 阶段结束提示音

一键安装：

```bash
pip install -r requirements.txt
```

## 功能介绍

### 经典 Pomodoro 4-1 循环

| 阶段 | 时长 | 颜色 |
|---|---|---|
| 专注 | 25 分钟 | 🍅 番茄红 `#E94B3C` |
| 短休 | 5 分钟 | 🍊 橙黄 `#F5A623` |
| 长休 | 15 分钟 | 🌊 天空蓝 `#5BA8E5` |

每完成 4 个「专注」自动插入 1 个「长休」，然后重新计数。

### 主窗口

- **大字号倒计时** + **SVG 进度环**：剩余时间一目了然
- **玻璃拟态 UI**：`backdrop-filter: blur(20px)`，阶段切换时背景色 0.6s 渐变
- **末 10 秒脉冲**：倒计时数字轻微脉动提醒
- **阶段圆点指示**：底部 4 个圆点显示当前轮次进度

### 三个控制按钮

- **开始 / 暂停** · 主按钮
- **重置** · 当前阶段倒计时归零到满时长
- **跳过** · 强制进入下一阶段

### 系统集成

- **系统通知** · 阶段结束通过 `plyer` 弹 Windows 通知
- **提示音** · 阶段结束播放 C5+E5 双音提示（`winsound`）
- **状态持久化** · 关闭/崩溃后重启能恢复（`~/.work_timer/state.json`）
- **进程锁** · 防止重复启动（`~/.work_timer/state.json.lock`）
- **托盘常驻** · 不开窗口时仍可在托盘菜单控制「开始/暂停」「退出」
