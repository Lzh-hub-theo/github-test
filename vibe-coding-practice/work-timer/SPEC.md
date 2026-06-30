# SPEC · work-timer 番茄钟

> 项目级实现规范 · 2026-06-30

## 1. 颜色变量

```css
--color-focus: #E94B3C;        /* 番茄红 · 专注态 */
--color-short: #F5A623;        /* 橙黄   · 短休态 */
--color-long:  #5BA8E5;        /* 天空蓝 · 长休态 */
--color-text:  #2C2C2C;        /* 主文字 */
--color-text-sub: #7A7A7A;     /* 次文字 */
--color-card:  rgba(255, 255, 255, 0.65);  /* 玻璃卡片 */
--shadow-card: 0 8px 32px rgba(0, 0, 0, 0.12);
```

## 2. 字体

- 倒计时数字：`'Segoe UI', system-ui, sans-serif`，100px，font-weight 200
- 标题：`'Microsoft YaHei UI', system-ui, sans-serif`，14px，font-weight 500
- 按钮文字：14px，font-weight 500
- 副文字：12px

## 3. 间距

- 卡片内边距：32px
- 元素垂直间距：24px（主按钮到次按钮）、16px（次按钮到圆点）
- 窗口尺寸：360 × 480（不可缩放）

## 4. 组件清单

| 组件 | 类名 | 说明 |
|---|---|---|
| 顶部标题 | `.title` | "🍅 番茄钟"，小字号 |
| 倒计时 | `.timer-display` | 大字号 + SVG 进度环 |
| 主按钮 | `.btn-primary` | 圆角胶囊，开始/暂停切换 |
| 次按钮 | `.btn-secondary` | 重置、跳过，并排 |
| 阶段圆点 | `.phase-dots` | 4 个圆点指示当前轮次 |
| 底部统计 | `.stats` | "今日完成 N 个番茄" |

## 5. 动效

- 阶段切换：背景色 `transition: background 0.6s ease`
- 倒计时末 10 秒：数字 `animation: pulse 1s ease-in-out infinite`
- 主按钮悬停：`background-color` 渐变 0.2s
- 进度环：`stroke-dashoffset` 1s linear 过渡

## 6. 状态机规则

| 当前状态 | 完成条件 | 下一状态 | pomodoro_count 变化 |
|---|---|---|---|
| FOCUS | 倒计时归零 | SHORT_BREAK（除非 count=3 → LONG_BREAK） | +1 |
| SHORT_BREAK | 倒计时归零 | FOCUS | 不变 |
| LONG_BREAK | 倒计时归零 | FOCUS | 清零（同时切回 FOCUS 之前已是 4） |

跳过（skip）：等价于"立即完成当前阶段"，按上表规则走。
重置（reset）：仅重置当前阶段倒计时到满时长，pomodoro_count 不变。

## 7. pywebview ↔ JS 接口

| 方向 | 方法 | 签名 |
|---|---|---|
| JS → Python | `getState` | `() => {phase, remaining, paused, pomodoro_count, today_count}` |
| JS → Python | `toggleStartPause` | `() => void` |
| JS → Python | `resetCurrent` | `() => void` |
| JS → Python | `skipPhase` | `() => void` |
| Python → JS | `updateTimer` | `(state) => void` · 1Hz 推送 |

## 8. 错误处理

| 场景 | 处理 |
|---|---|
| 重复启动 | 文件锁冲突，提示"已有实例在运行"并退出 |
| JSON 写入失败 | log 警告，不影响主流程 |
| 托盘图标加载失败 | fallback 到 PIL 现绘红色圆 |
| 通知发送失败 | log 警告 |
| pywebview 启动失败 | 退化为 Tkinter 简易窗口 |
