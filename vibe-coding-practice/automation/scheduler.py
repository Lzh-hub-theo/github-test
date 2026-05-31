"""
Scheduler - 定时任务调度器
读取 tasks.txt 中的命令和定时时间，为每条任务创建独立的 Windows 计划任务
tasks.txt 格式: <python路径> <脚本路径> <hh:mm>
"""

import os
import sys
import re
import subprocess
import argparse
from datetime import datetime


TASKS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.txt")
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
TASK_PREFIX = "MacroRecorder_Task_"


def _ensure_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)


def _log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    _ensure_log_dir()
    log_file = os.path.join(LOG_DIR, datetime.now().strftime("scheduler_%Y%m%d.log"))
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _validate_time(time_str):
    if not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', time_str):
        return False
    return True


def read_tasks():
    if not os.path.exists(TASKS_FILE):
        _log(f"任务文件不存在: {TASKS_FILE}")
        return []
    tasks = []
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.rsplit(None, 1)
            if len(parts) < 2:
                _log(f"第 {line_num} 行格式错误，缺少时间参数: {line}")
                continue
            command = parts[0]
            time_str = parts[1]
            if not _validate_time(time_str):
                _log(f"第 {line_num} 行时间格式错误（应为 hh:mm）: {time_str}")
                continue
            tasks.append({"command": command, "time": time_str, "raw": line})
    return tasks


def _get_existing_task_indices():
    result = subprocess.run(
        ["schtasks", "/query", "/fo", "csv", "/nh"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return []
    indices = []
    for row in result.stdout.strip().split("\n"):
        row = row.strip().strip('"')
        if row.startswith(TASK_PREFIX):
            name = row.split(",")[0].strip('"')
            suffix = name[len(TASK_PREFIX):]
            if suffix.isdigit():
                indices.append(int(suffix))
    return indices


def _remove_task_by_index(idx):
    task_name = f"{TASK_PREFIX}{idx}"
    subprocess.run(
        ["schtasks", "/delete", "/tn", task_name, "/f"],
        capture_output=True,
    )


def run_tasks():
    _log("=" * 50)
    _log("手动执行所有任务")
    tasks = read_tasks()
    if not tasks:
        _log("没有可执行的任务（tasks.txt 为空或无有效命令）")
        _log("=" * 50)
        return
    _log(f"共读取到 {len(tasks)} 条任务")

    for i, task in enumerate(tasks, 1):
        _log(f"执行任务 {i}/{len(tasks)}: {task['command']} (计划时间: {task['time']})")
        try:
            parts = task["command"].split()
            result = subprocess.run(
                parts,
                capture_output=True,
                text=True,
                timeout=600,
            )
            if result.stdout:
                for out_line in result.stdout.strip().split("\n"):
                    _log(f"  stdout: {out_line}")
            if result.stderr:
                for err_line in result.stderr.strip().split("\n"):
                    _log(f"  stderr: {err_line}")
            if result.returncode == 0:
                _log(f"任务 {i} 执行成功 (exit code: 0)")
            else:
                _log(f"任务 {i} 执行失败 (exit code: {result.returncode})")
        except subprocess.TimeoutExpired:
            _log(f"任务 {i} 执行超时（超过600秒），已跳过")
        except FileNotFoundError as e:
            _log(f"任务 {i} 命令未找到: {e}")
        except Exception as e:
            _log(f"任务 {i} 执行异常: {e}")

    _log("所有任务执行完毕")
    _log("=" * 50)


def setup_schedule():
    tasks = read_tasks()
    if not tasks:
        _log("tasks.txt 中没有有效任务，无法创建计划任务")
        return

    for idx in _get_existing_task_indices():
        _remove_task_by_index(idx)
        _log(f"已删除旧计划任务: {TASK_PREFIX}{idx}")

    _log(f"开始创建 {len(tasks)} 个计划任务...")

    for i, task in enumerate(tasks, 1):
        task_name = f"{TASK_PREFIX}{i}"
        command = task["command"]
        time_str = task["time"]

        _log(f"  [{i}/{len(tasks)}] 任务名: {task_name}")
        _log(f"         执行命令: {command}")
        _log(f"         触发时间: 每天 {time_str}")

        create_cmd = [
            "schtasks", "/create",
            "/tn", task_name,
            "/tr", command,
            "/sc", "daily",
            "/st", time_str,
            "/f",
        ]

        result = subprocess.run(create_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            _log(f"         创建成功")
        else:
            _log(f"         创建失败: {result.stderr.strip()}")
            _log("         提示: 请以管理员身份运行此脚本")

    _log(f"计划任务创建完毕，共 {len(tasks)} 个")


def remove_schedule():
    indices = _get_existing_task_indices()
    if not indices:
        _log("没有找到已注册的计划任务")
        return
    for idx in sorted(indices):
        task_name = f"{TASK_PREFIX}{idx}"
        result = subprocess.run(
            ["schtasks", "/delete", "/tn", task_name, "/f"],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            _log(f"已删除: {task_name}")
        else:
            _log(f"删除失败: {task_name} - {result.stderr.strip()}")
    _log(f"共删除 {len(indices)} 个计划任务")


def show_status():
    indices = _get_existing_task_indices()
    if indices:
        _log(f"已注册的计划任务 ({len(indices)} 个):")
        for idx in sorted(indices):
            task_name = f"{TASK_PREFIX}{idx}"
            result = subprocess.run(
                ["schtasks", "/query", "/tn", task_name, "/v", "/fo", "list"],
                capture_output=True, text=True,
            )
            if result.returncode == 0:
                print(result.stdout)
            else:
                _log(f"  {task_name}: 查询失败")
    else:
        _log("没有已注册的计划任务")

    _log(f"任务文件: {TASKS_FILE}")
    tasks = read_tasks()
    if tasks:
        _log(f"当前配置了 {len(tasks)} 条任务:")
        for i, t in enumerate(tasks, 1):
            _log(f"  {i}. 命令: {t['command']}  时间: {t['time']}")
    else:
        _log("当前没有配置任何任务")


def main():
    parser = argparse.ArgumentParser(
        description="Scheduler - 定时任务调度器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python scheduler.py --setup       根据 tasks.txt 为每条任务创建计划任务（需管理员权限）
  python scheduler.py --remove      删除所有已注册的计划任务
  python scheduler.py --run         立即执行 tasks.txt 中的所有命令
  python scheduler.py --status      查看计划任务状态和任务列表

tasks.txt 格式:
  <python路径> <脚本路径> <hh:mm>
  示例:
  E:\\LeStoreDownload\\python\\python.exe E:\\Project\\automation\\scripts\\script_xxx.py 06:00
        """,
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--setup", action="store_true", help="根据 tasks.txt 创建计划任务")
    group.add_argument("--remove", action="store_true", help="删除所有已注册的计划任务")
    group.add_argument("--run", action="store_true", help="立即执行 tasks.txt 中的所有命令")
    group.add_argument("--status", action="store_true", help="查看计划任务状态")

    args = parser.parse_args()

    if args.setup:
        setup_schedule()
    elif args.remove:
        remove_schedule()
    elif args.run:
        run_tasks()
    elif args.status:
        show_status()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
