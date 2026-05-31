# Macro Recorder - 按键精灵风格自动化脚本工具

录制你的鼠标和键盘操作，自动生成可执行脚本，精确回放所有动作，支持定时自动执行。

## 功能概览

| 功能 | 说明 |
|------|------|
| **录制** | 完整记录鼠标移动、点击、滚轮以及键盘敲击，精确到毫秒级时间间隔 |
| **生成脚本** | 将录制数据自动转换为可独立运行的 Python 脚本 |
| **回放** | 按原始时间间隔精确复现所有操作，支持倍速回放 |
| **定时执行** | 通过 Windows 计划任务，每天定时自动运行生成的脚本 |

## 环境要求

- Python 3.8+
- Windows 操作系统

## 安装依赖

```bash
pip install pynput
```

如果使用阿里云镜像加速：
```bash
pip install pynput -i https://mirrors.aliyun.com/pypi/simple/
```

## 使用方法

### 1. 录制操作

```bash
python macro_recorder.py record
```

录制开始后，你的所有鼠标和键盘操作都会被记录。**按 F8 键停止录制**。

录制结束后，数据会自动保存到 `recordings/` 目录下，文件名格式为 `recording_YYYYMMDD_HHMMSS.json`。

#### 录制选项

| 选项 | 说明 |
|------|------|
| `-o, --output` | 指定输出文件名（默认自动生成） |
| `--no-mouse-move` | 不录制鼠标移动事件，只记录点击和键盘操作 |
| `--move-interval` | 鼠标移动采样间隔，单位秒（默认 0.05） |
| `-g, --generate-script` | 录制结束后自动生成可执行脚本 |

#### 示例

```bash
# 基本录制
python macro_recorder.py record

# 不录制鼠标移动（减少数据量，适合只需键盘和点击的场景）
python macro_recorder.py record --no-mouse-move

# 录制后自动生成脚本
python macro_recorder.py record -g

# 指定输出文件名
python macro_recorder.py record -o my_macro

# 调整鼠标移动采样间隔为 0.1 秒（更稀疏的移动记录）
python macro_recorder.py record --move-interval 0.1
```

---

### 2. 回放操作

```bash
python macro_recorder.py play --latest
```

回放开始前有 3 秒倒计时，方便你切换到目标窗口。回放过程中按 **Ctrl+C** 可中断。

#### 回放选项

| 选项 | 说明 |
|------|------|
| `-i, --input` | 指定录制文件路径或文件名 |
| `--latest` | 回放最近一次录制 |
| `-s, --speed` | 回放速度倍率（默认 1.0） |

#### 示例

```bash
# 回放最近一次录制
python macro_recorder.py play --latest

# 以 2 倍速回放
python macro_recorder.py play --latest --speed 2.0

# 以 0.5 倍速慢放
python macro_recorder.py play --latest --speed 0.5

# 指定录制文件回放
python macro_recorder.py play -i recording_20260531_143000.json

# 使用绝对路径指定文件
python macro_recorder.py play -i "C:\path\to\recording.json"
```

---

### 3. 生成脚本

```bash
python macro_recorder.py generate --latest
```

将录制数据转换为一个可独立运行的 Python 脚本，保存到 `scripts/` 目录下。

生成的脚本可以直接运行：

```bash
python scripts/script_20260531_143000.py
```

#### 生成选项

| 选项 | 说明 |
|------|------|
| `-i, --input` | 指定录制文件路径或文件名 |
| `--latest` | 使用最近一次录制 |
| `-o, --output` | 指定输出脚本文件名（默认自动生成） |

#### 示例

```bash
# 为最近录制生成脚本
python macro_recorder.py generate --latest

# 指定录制文件生成脚本
python macro_recorder.py generate -i recording_20260531_143000.json

# 指定输出脚本文件名
python macro_recorder.py generate --latest -o my_script
```

---

### 4. 列出录制文件

```bash
python macro_recorder.py list
```

显示 `recordings/` 目录下所有录制文件，包含事件数量和时长信息。

---

### 5. 定时执行（scheduler.py）

通过 `scheduler.py` 将生成的脚本注册为 Windows 计划任务，实现每天定时自动运行。

#### 配置任务文件 tasks.txt

在 `tasks.txt` 中添加需要定时执行的命令，每行一条，格式如下：

```
<python路径> <脚本路径> <hh:mm>
```

- `hh` 范围：00~23（小时）
- `mm` 范围：00~59（分钟）
- 以 `#` 开头的行为注释，空行会被忽略

#### tasks.txt 示例

```
# 每天早上 6 点执行脚本 A
E:\LeStoreDownload\python\python.exe E:\Project\automation\scripts\script_20260531_060000.py 06:00

# 每天下午 2 点半执行脚本 B
E:\LeStoreDownload\python\python.exe E:\Project\automation\scripts\script_20260531_143000.py 14:30
```

> 每条任务会创建一个独立的 Windows 计划任务（`MacroRecorder_Task_1`、`MacroRecorder_Task_2`...），各自按指定时间触发。

#### scheduler.py 命令

| 命令 | 说明 |
|------|------|
| `--setup` | 读取 tasks.txt，为每条任务创建 Windows 计划任务（**需管理员权限**） |
| `--remove` | 删除所有已注册的计划任务 |
| `--run` | 立即手动执行 tasks.txt 中的所有命令（用于测试） |
| `--status` | 查看已注册的计划任务状态和 tasks.txt 中的任务列表 |

#### 示例

```bash
# 第一步：编辑 tasks.txt，添加命令和执行时间

# 第二步：注册计划任务（需以管理员身份运行）
python scheduler.py --setup

# 查看计划任务状态
python scheduler.py --status

# 手动测试执行所有任务（不等待定时触发）
python scheduler.py --run

# 删除所有计划任务
python scheduler.py --remove
```

#### 完整工作流程

```
1. 录制操作并生成脚本
   python macro_recorder.py record -g

2. 编辑 tasks.txt，添加生成的脚本命令和执行时间
   E:\LeStoreDownload\python\python.exe E:\Project\automation\scripts\script_xxx.py 06:00

3. 注册计划任务（管理员权限）
   python scheduler.py --setup

4. 之后每天 06:00，Windows 会自动执行该脚本
```

#### 日志

每次执行（无论是定时触发还是手动 `--run`）都会记录日志，保存在 `logs/` 目录下，文件名格式为 `scheduler_YYYYMMDD.log`。

---

## 目录结构

```
automation/
├── macro_recorder.py          # 主程序（录制/回放/生成脚本）
├── scheduler.py               # 定时任务调度器
├── tasks.txt                  # 定时任务配置文件
├── recordings/                # 录制数据（JSON 格式）
│   └── recording_20260531_143000.json
├── scripts/                   # 生成的可执行脚本
│   └── script_20260531_143000.py
└── logs/                      # 定时任务执行日志
    └── scheduler_20260531.log
```

## 录制数据格式

录制数据保存为 JSON，每条事件包含以下字段：

```json
{
  "type": "mouse_click",
  "x": 500,
  "y": 300,
  "button": "left",
  "pressed": true,
  "time": 1.2345
}
```

支持的事件类型：

| 事件类型 | 说明 | 额外字段 |
|----------|------|----------|
| `mouse_move` | 鼠标移动 | `x`, `y` |
| `mouse_click` | 鼠标点击 | `x`, `y`, `button`（left/right/middle）, `pressed`（true按下/false释放） |
| `mouse_scroll` | 鼠标滚轮 | `x`, `y`, `dx`, `dy` |
| `key_press` | 键盘按下 | `key` |
| `key_release` | 键盘释放 | `key` |

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| **F8** | 停止录制 |
| **Ctrl+C** | 中断回放 |

## 注意事项

- 回放前有 3 秒倒计时，请在倒计时内切换到目标窗口
- 鼠标移动默认以 50ms 间隔采样，可通过 `--move-interval` 调整
- 如果只需要点击和键盘操作，建议使用 `--no-mouse-move` 减少数据量
- 生成的脚本依赖 `pynput`，运行前需确保已安装
- `scheduler.py --setup` 需要以**管理员身份**运行，否则计划任务创建会失败
- 修改 `tasks.txt` 后需重新执行 `scheduler.py --setup` 才能生效
- 定时任务执行日志保存在 `logs/` 目录下，可用于排查问题
