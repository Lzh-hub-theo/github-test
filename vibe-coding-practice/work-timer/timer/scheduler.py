"""计时器调度器：单后台线程，1Hz 轮询 + 阶段切换 + 回调。

线程模型：
    - 后台线程 _run_loop 每秒 tick 一次，更新 remaining_seconds
    - 当 remaining_seconds 归零时自动 advance_phase
    - 外部通过 start/pause/resume/reset/skip 改动状态
    - 状态读写受 self._lock 保护
    - 状态变化通过回调（on_tick / on_phase_change）通知调用方
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Callable, Optional

from .state import (
    Phase,
    TimerState,
    full_duration,
    next_phase,
)

logger = logging.getLogger(__name__)


# 回调签名：(state: TimerState) -> None
TickCallback = Callable[[TimerState], None]
# 阶段切换回调：(old_phase: Phase, new_state: TimerState) -> None
PhaseChangeCallback = Callable[[Phase, TimerState], None]


class Scheduler:
    """番茄钟调度器。

    用法：
        sched = Scheduler(initial_state, on_tick=..., on_phase_change=...)
        sched.start()       # 启动后台线程（不开始计时，仅保持 paused=False）
        sched.toggle()      # 开始/暂停
        sched.reset()
        sched.skip()
        sched.shutdown()    # 关闭后台线程
    """

    def __init__(
        self,
        initial: TimerState,
        on_tick: Optional[TickCallback] = None,
        on_phase_change: Optional[PhaseChangeCallback] = None,
        on_completed_focus: Optional[Callable[[], None]] = None,
    ) -> None:
        self._state = initial
        self._lock = threading.Lock()

        self._on_tick = on_tick
        self._on_phase_change = on_phase_change
        # 每完成一个 FOCUS 阶段时调用（用于发系统通知、累计今日完成数等）
        self._on_completed_focus = on_completed_focus

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    # ---------- 生命周期 ----------

    def start(self) -> None:
        """启动后台线程。"""
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop, name="timer-loop", daemon=True
        )
        self._thread.start()

    def shutdown(self) -> None:
        """停止后台线程。"""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    # ---------- 状态查询（供 UI / API 读取） ----------

    def snapshot(self) -> TimerState:
        """返回当前状态的副本。"""
        with self._lock:
            # TimerState 字段都是不可变类型（int, bool, Phase），可直接返回
            return TimerState(
                phase=self._state.phase,
                remaining_seconds=self._state.remaining_seconds,
                paused=self._state.paused,
                pomodoro_count=self._state.pomodoro_count,
                today_count=self._state.today_count,
            )

    # ---------- 控制指令 ----------

    def toggle(self) -> None:
        """开始/暂停切换。"""
        with self._lock:
            self._state.paused = not self._state.paused
            self._fire_tick_locked()  # 立刻推一次以更新 UI

    def reset(self) -> None:
        """重置当前阶段到满时长，不影响 pomodoro_count。"""
        with self._lock:
            self._state.remaining_seconds = full_duration(self._state.phase)
            self._fire_tick_locked()

    def skip(self) -> None:
        """强制进入下一阶段（等价于立即完成当前阶段）。"""
        with self._lock:
            self._advance_phase_locked()
            self._fire_tick_locked()

    # ---------- 内部 ----------

    def _run_loop(self) -> None:
        """后台线程：1Hz 轮询。"""
        while not self._stop_event.is_set():
            # 短睡眠 + 退出检查，便于快速响应 shutdown
            if self._stop_event.wait(timeout=1.0):
                return

            with self._lock:
                if self._state.paused:
                    continue
                self._state.remaining_seconds -= 1
                if self._state.remaining_seconds <= 0:
                    self._advance_phase_locked()
                self._fire_tick_locked()

    def _advance_phase_locked(self) -> None:
        """阶段切换（调用方需持有锁）。"""
        old_phase = self._state.phase

        # 先看是不是 FOCUS 阶段完成（决定要不要累加 today_count）
        completed_focus = old_phase == Phase.FOCUS

        new_phase, new_count = next_phase(old_phase, self._state.pomodoro_count)
        self._state.phase = new_phase
        self._state.pomodoro_count = new_count
        self._state.remaining_seconds = full_duration(new_phase)
        # 阶段切换后保持 paused 状态不变（用户偏好连续 vs 手动开始）

        if completed_focus:
            self._state.today_count += 1

        # 阶段切换通知（持锁外调用避免死锁）
        if self._on_phase_change is not None:
            try:
                self._on_phase_change(old_phase, self._state)
            except Exception:  # noqa: BLE001
                logger.exception("on_phase_change 回调异常")

        # 完成 FOCUS 通知（发系统通知 / 响铃）
        if completed_focus and self._on_completed_focus is not None:
            try:
                self._on_completed_focus()
            except Exception:  # noqa: BLE001
                logger.exception("on_completed_focus 回调异常")

    def _fire_tick_locked(self) -> None:
        """触发 tick 回调（调用方需持有锁）。回调在锁外执行。"""
        if self._on_tick is None:
            return
        snapshot = TimerState(
            phase=self._state.phase,
            remaining_seconds=self._state.remaining_seconds,
            paused=self._state.paused,
            pomodoro_count=self._state.pomodoro_count,
            today_count=self._state.today_count,
        )
        try:
            self._on_tick(snapshot)
        except Exception:  # noqa: BLE001
            logger.exception("on_tick 回调异常")
