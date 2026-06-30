"""JSON 持久化 + 进程文件锁 + 60s 阈值恢复。

设计要点：
- 状态文件：~/.work_timer/state.json
- 进程锁：  ~/.work_timer/state.json.lock
  - 通过 O_CREAT|O_EXCL 原子创建实现跨平台文件锁
  - 写入 PID；启动时若锁存在但 PID 已死，视为过期锁并清理
- 60s 阈值：state.json 中的 last_update_ts 与当前时间差 < 60s 才恢复
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

from .state import TimerState

# 60s 阈值：超过 60s 的旧状态可能源自几天前的崩溃恢复，已无意义
STALE_THRESHOLD_SECONDS = 60


def _state_dir() -> Path:
    """跨平台获取状态目录。"""
    home = Path(os.path.expanduser("~"))
    return home / ".work_timer"


class StateStore:
    """状态文件读写 + 进程锁管理。

    用法：
        store = StateStore()
        store.acquire_lock()             # 启动时调用，失败抛 AlreadyRunning
        state = store.load()             # 可能返回 None（无文件 / 旧状态）
        store.save(state)                # 任意时刻保存
        store.release_lock()             # 退出时调用
    """

    def __init__(self) -> None:
        self._dir = _state_dir()
        self._state_path = self._dir / "state.json"
        self._lock_path = self._dir / "state.json.lock"
        self._lock_fd: Optional[int] = None  # type: ignore[type-arg]

    # ---------- 进程锁 ----------

    def acquire_lock(self) -> None:
        """获取进程锁。失败时抛 AlreadyRunning。"""
        self._dir.mkdir(parents=True, exist_ok=True)

        # 检查现有锁是否过期（PID 已死）
        if self._lock_path.exists():
            stale = self._is_lock_stale()
            if stale:
                # 清理过期锁
                try:
                    self._lock_path.unlink()
                except OSError:
                    pass
            else:
                raise AlreadyRunning(
                    f"已有 work-timer 实例在运行（lock: {self._lock_path}）"
                )

        # 原子创建锁文件
        try:
            self._lock_fd = os.open(
                str(self._lock_path),
                os.O_CREAT | os.O_EXCL | os.O_RDWR,
                0o644,
            )
        except FileExistsError:
            raise AlreadyRunning(
                f"已有 work-timer 实例在运行（lock: {self._lock_path}）"
            )

        # 写入 PID
        pid = os.getpid()
        os.write(self._lock_fd, f"{pid}\n".encode("utf-8"))
        os.fsync(self._lock_fd)

    def release_lock(self) -> None:
        """释放进程锁。幂等。"""
        if self._lock_fd is not None:
            try:
                os.close(self._lock_fd)
            except OSError:
                pass
            self._lock_fd = None
        try:
            self._lock_path.unlink()
        except FileNotFoundError:
            pass

    def _is_lock_stale(self) -> bool:
        """检查锁文件里的 PID 是否还活着。"""
        try:
            content = self._lock_path.read_text(encoding="utf-8").strip()
            pid = int(content.split("\n")[0])
        except (OSError, ValueError):
            # 锁文件无法读取，保守认为不是过期锁（避免误删别人的锁）
            return False

        return not self._pid_alive(pid)

    @staticmethod
    def _pid_alive(pid: int) -> bool:
        """检查 PID 是否还活着。跨平台简化版。"""
        if sys.platform == "win32":
            # Windows：使用 tasklist 命令查询（避免引入 pywin32 依赖）
            try:
                import subprocess

                out = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                    capture_output=True,
                    text=True,
                    timeout=2,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                return str(pid) in out.stdout
            except Exception:
                return True  # 查询失败时保守视为活着
        else:
            # POSIX：kill -0
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                return False

    # ---------- 状态读写 ----------

    def load(self) -> Optional[TimerState]:
        """读取状态。若无文件 / 旧状态 / JSON 损坏，返回 None。"""
        if not self._state_path.exists():
            return None

        try:
            data = json.loads(self._state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

        # 60s 阈值
        last_ts = float(data.get("last_update_ts", 0))
        if time.time() - last_ts > STALE_THRESHOLD_SECONDS:
            return None

        return TimerState.from_dict(data)

    def save(self, state: TimerState) -> None:
        """写入状态。失败时 log 警告但不抛。"""
        payload = state.to_dict()
        payload["last_update_ts"] = time.time()
        try:
            self._dir.mkdir(parents=True, exist_ok=True)
            tmp = self._state_path.with_suffix(".json.tmp")
            tmp.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            os.replace(tmp, self._state_path)  # 原子替换
        except OSError as exc:
            # 不抛：持久化失败不应中断计时
            import logging

            logging.getLogger(__name__).warning("保存 state.json 失败: %s", exc)


class AlreadyRunning(RuntimeError):
    """进程锁冲突：已有实例在运行。"""
