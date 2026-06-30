"""番茄钟状态机：阶段枚举、时长配置、阶段切换规则。

经典的 Pomodoro 4-1 循环：
    FOCUS × 4 → LONG_BREAK → 重新计数 → FOCUS × 4 → ...
    FOCUS × 1 → SHORT_BREAK → FOCUS × 1 → SHORT_BREAK → ...
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Phase(str, Enum):
    """计时阶段。继承 str 便于 JSON 序列化。"""

    FOCUS = "FOCUS"
    SHORT_BREAK = "SHORT_BREAK"
    LONG_BREAK = "LONG_BREAK"


# 每个阶段的满时长（秒）。这是 v1 的硬编码配置，YAGNI 不做设置面板。
PHASE_DURATIONS: dict[Phase, int] = {
    Phase.FOCUS: 25 * 60,
    Phase.SHORT_BREAK: 5 * 60,
    Phase.LONG_BREAK: 15 * 60,
}

# 一个完整循环里包含的 FOCUS 阶段数；达到该数后下一阶段为 LONG_BREAK。
POMODOROS_PER_CYCLE = 4


def full_duration(phase: Phase) -> int:
    """返回阶段对应的满时长（秒）。"""
    return PHASE_DURATIONS[phase]


@dataclass
class TimerState:
    """计时器运行时状态。线程间通过锁访问。"""

    phase: Phase = Phase.FOCUS
    remaining_seconds: int = PHASE_DURATIONS[Phase.FOCUS]
    paused: bool = True
    pomodoro_count: int = 0  # 当前 cycle 内已完成的 FOCUS 数
    today_count: int = 0     # 跨进程持久化的"今日完成数"

    def to_dict(self) -> dict:
        return {
            "phase": self.phase.value,
            "remaining_seconds": self.remaining_seconds,
            "paused": self.paused,
            "pomodoro_count": self.pomodoro_count,
            "today_count": self.today_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TimerState":
        return cls(
            phase=Phase(data.get("phase", Phase.FOCUS.value)),
            remaining_seconds=int(data.get("remaining_seconds", PHASE_DURATIONS[Phase.FOCUS])),
            paused=bool(data.get("paused", True)),
            pomodoro_count=int(data.get("pomodoro_count", 0)),
            today_count=int(data.get("today_count", 0)),
        )


def next_phase(current: Phase, pomodoro_count: int) -> tuple[Phase, int]:
    """根据当前阶段和已完成 FOCUS 数，计算下一阶段与新的 count。

    规则（与 SPEC.md §6 一致）：
        - FOCUS 完成 → SHORT_BREAK；若 count 在递增前为 3（即本轮是第 4 个 FOCUS），
          则下一阶段为 LONG_BREAK，并清零。
        - SHORT_BREAK 完成 → FOCUS
        - LONG_BREAK 完成 → FOCUS（此时 count 早已清零）

    返回：(next_phase, new_pomodoro_count)
    """
    if current == Phase.FOCUS:
        # 即将完成一个 FOCUS，count 先 +1 再判断
        will_be_count = pomodoro_count + 1
        if will_be_count >= POMODOROS_PER_CYCLE:
            return Phase.LONG_BREAK, 0
        return Phase.SHORT_BREAK, will_be_count
    # 休息阶段结束都回 FOCUS
    return Phase.FOCUS, pomodoro_count
