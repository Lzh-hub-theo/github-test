# 桌面番茄钟（work-timer）设计文档

> 创建于 2026-06-30 · 状态：已获用户确认

## 一、目标与背景

用户在 Windows 11 上需要一个常驻系统托盘的番茄工作法计时器，帮助维持专注节奏。仓库 `E:\Project\TestGit` 是 Vibe Coding 实践集合，每个项目一个子目录；今日（2026-06-30）已创建空目录 `vibe-coding-practice/work-timer/` 作为本项目容器。

## 二、用户已确认的决策

| 决策项 | 选择 | 备注 |
|---|---|---|
| 产品形态 | 系统托盘常驻小程序 | 单击托盘图标开窗；点关闭按钮 = 隐藏到托盘 |
| 功能范围 | 核心计时 + 自动循环 | 专注 25min / 短休 5min / 长休 15min，4 轮一循环 |
| 技术栈 | Python + pystray + pywebview | 复用用户 HTML/CSS 技能 |
| 视觉风格 | 番茄红主题（玻璃拟态） | 主色 `#E94B3C` 番茄红，辅色橙黄 / 天空蓝 |

## 三、核心循环与状态机

经典 Pomodoro 4-1 循环：

```
[专注 25min] → [短休 5min] → [专注] → [短休] → [专注] → [短休] → [专注] → [长休 15min] → [专注] → ...
```

状态枚举：`FOCUS`, `SHORT_BREAK`, `LONG_BREAK`，每个状态可叠加 `paused: bool`。

阶段切换逻辑：当前 `pomodoro_count`（已完成的专注番茄数）达到 4 时，下一阶段为 `LONG_BREAK` 并将计数清零；否则下一阶段为 `SHORT_BREAK`。

`skip_phase()` 行为：把当前阶段标记为已完成（若是 FOCUS 则 `pomodoro_count += 1`），并按上述规则切到下一阶段。`reset_current()` 行为：仅重置当前阶段倒计时到该阶段满时长，不影响 `pomodoro_count`。

## 四、架构与模块

### 4.1 进程结构

单进程多线程：

| 线程 | 职责 |
|---|---|
| 主线程 | pywebview GUI 消息循环（`webview.start()` 阻塞） |
| 托盘线程 | `pystray.Icon` 守护线程，监听托盘点击与菜单 |
| 计时线程 | `threading.Timer` 触发阶段结束回调，1Hz 推送 tick 到主线程 |
| 通信 | 用 `threading.Lock` 保护共享状态；UI 刷新用 `webview.evaluate_js()` |

线程模式选型理由：`pystray.Icon.run()` 是阻塞调用，必须独占一个线程。在 Windows 上 `pystray` 用 Win32 消息，能稳定跑在非主线程；pywebview 则要求主线程跑其事件循环。两者解耦为：主线程跑 pywebview，pystray 跑在守护线程，由主线程 `webview.start(blocking=True)` 进入阻塞前启动 pystray。

### 4.2 模块拆分

```
vibe-coding-practice/work-timer/
├── main.py              # 入口：装配托盘 + 窗口 + 计时器
├── timer/
│   ├── __init__.py
│   ├── state.py         # 状态枚举 + 状态机逻辑
│   ├── scheduler.py     # Timer 控制器（线程安全 + 阶段切换）
│   └── persistence.py   # JSON 读写
├── ui/
│   ├── index.html       # 主窗口页面
│   ├── style.css        # 玻璃拟态 + 番茄红
│   └── app.js           # 前端逻辑，通过 pywebview bridge 调用 Python
├── assets/
│   ├── tomato.png       # 64x64 托盘图标
│   └── chime.wav        # 阶段结束提示音
├── requirements.txt
├── SPEC.md              # 项目级实现规范（沿用 reminder 风格）
└── README.md
```

### 4.3 Python ↔ JS 接口

通过 pywebview 的 `js_api` 暴露给前端：

| Python 方法 | JS 调用 | 说明 |
|---|---|---|
| `get_state()` | `window.pywebview.api.get_state()` | 返回当前阶段、剩余秒数、是否暂停、今日完成数 |
| `start_pause_toggle()` | `... .start_pause_toggle()` | 切换开始/暂停 |
| `reset_current()` | `... .reset_current()` | 重置当前阶段倒计时 |
| `skip_phase()` | `... .skip_phase()` | 跳过到下一阶段 |

Python → JS 推送（计时器 tick）：`webview.evaluate_js("updateTimer({...})")`，频率 1Hz。

## 五、数据持久化

路径：`%USERPROFILE%/.work_timer/state.json`（Windows 等价 `C:\Users\<user>\.work_timer\state.json`）。

```json
{
  "phase": "FOCUS",
  "remaining_seconds": 1234,
  "paused": false,
  "pomodoro_count": 2,
  "today_count": 5,
  "last_update_ts": 1719715200
}
```

读写时机：
- **写**：每次阶段切换、暂停/恢复、退出主窗口时
- **读**：进程启动时，若 `now - last_update_ts < 60s` 则恢复，否则丢弃（避免恢复太旧的状态）
- **60s 阈值理由**：超过 60s 的旧状态可能源自几天前的崩溃恢复，已无意义；同时给"两次启动间允许的最大间隔"一个明确值
- **并发防护**：进程启动时尝试创建 `state.json.lock`（独占文件锁 `fcntl` / Windows `msvcrt`），失败则提示"已有 work-timer 在运行"并退出

## 六、视觉设计

### 6.1 配色

| 用途 | 颜色 |
|---|---|
| 专注态主色 | `#E94B3C` 番茄红 |
| 短休态主色 | `#F5A623` 橙黄 |
| 长休态主色 | `#5BA8E5` 天空蓝 |
| 文字主色 | `#2C2C2C` |
| 文字次色 | `#7A7A7A` |
| 玻璃卡片 | `rgba(255,255,255,0.65)` + `backdrop-filter: blur(20px)` |

### 6.2 布局（主窗口 360 × 480）

```
┌────────────────────────────┐
│   🍅 番茄钟                  │  ← 顶部小标题
│                            │
│        24:38               │  ← 100px 大字号倒计时
│       [进度环]              │
│                            │
│     [ 开始 / 暂停 ]          │  ← 主按钮
│   [ 重置 ]    [ 跳过 ]       │  ← 次按钮
│                            │
│   • • • ○                  │  ← 阶段圆点指示（4 个）
│                            │
│   今日完成 5 个番茄 🍅        │  ← 底部统计
└────────────────────────────┘
```

### 6.3 交互动效

- 阶段切换：背景色 0.6s 渐变
- 倒计时数字：每秒 1Hz 更新；末 10 秒数字轻微脉冲
- 进度环：SVG `<circle>` + `stroke-dashoffset` 动画

## 七、托盘行为

- **图标**：默认 64x64 `tomato.png`，可被 PIL 缩放为 16/32/48 多尺寸
- **菜单**：
  - 开始 / 暂停
  - 重置
  - 退出
- **单击图标**：切换主窗口显示/隐藏
- **鼠标悬停 tooltip**：显示当前阶段 + 剩余时间（`pystray.Icon.notify` 或更新 `Icon.icon`）

## 八、系统通知

阶段结束触发：
1. `plyer.notification.notify(...)` 系统通知
2. 播放 `assets/chime.wav` 提示音（用 `playsound` 或 `pygame.mixer`，选用 `playsound` 更轻量）
3. 3 秒后自动开始下一阶段

## 九、错误处理

| 场景 | 处理 |
|---|---|
| 写 JSON 失败 | `try/except`，log 警告，不中断主流程 |
| 托盘图标加载失败 | fallback 到 `pystray.Icon` 默认图标 |
| 系统通知失败 | log 警告，不影响计时 |
| pywebview 启动失败 | 退化为 `tkinter` 简易窗口，提示用户 |
| 计时线程崩溃 | 主线程捕获 + 重启线程 |

## 十、范围边界（v1 不做）

- 任务列表 / 任务管理
- 统计图表（仅显示今日完成数）
- 自定义时长设置面板
- 主题切换
- 云同步 / 账号系统
- 开机自启 UI（v1 在启动文件夹放快捷方式）
- 多语言（仅中文）

## 十一、依赖清单

```
pystray>=0.19.5
pywebview>=5.0
plyer>=2.1
playsound>=1.3
Pillow>=10.0
```

## 十二、验收标准

1. 双击 `python main.py` 启动后，托盘出现番茄图标，无主窗口弹出
2. 单击托盘图标 → 主窗口淡入显示，玻璃拟态样式正确
3. 点击"开始" → 倒计时从 25:00 递减
4. 倒计时到 0:00 → 系统通知 + 提示音 + 切到短休 5:00
5. 完成 4 轮专注后 → 第 5 阶段为长休 15:00，之后计数清零
6. 点关闭按钮 → 窗口隐藏，进程不退出
7. 在第 3 分钟点暂停 → JSON 写入当前状态；杀进程重启 → 状态恢复
8. 托盘菜单"退出" → 进程干净退出
9. 主窗口在专注态显示红色背景、短休态橙色、长休态蓝色
