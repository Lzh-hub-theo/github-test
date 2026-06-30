"""work-timer 入口。

启动流程：
    1. 解析命令行（暂无参数）
    2. 初始化 StateStore，加进程锁
    3. 恢复 / 初始化 TimerState
    4. 构造 Scheduler
    5. 在守护线程里跑 pystray 托盘
    6. 主线程跑 pywebview 窗口（阻塞至窗口关闭）
    7. 窗口关闭后释放锁、退出 Scheduler、停托盘
"""
from __future__ import annotations

import logging
import os
import sys
import threading
from pathlib import Path

# 解决 pywebview 在某些环境下的 DLL 加载问题
# 设 critical：pywebview 在 Windows 11 + WebView2 上的 debug 探针
# 会对 AccessibilityObject 做递归访问，触发 RecursionError，但进程不受影响
os.environ.setdefault("PYWEBVIEW_LOG", "critical")

import webview  # noqa: E402

from timer.persistence import AlreadyRunning, StateStore
from timer.scheduler import Scheduler
from timer.state import Phase, TimerState, full_duration


# ============================================================
# 路径
# ============================================================
PROJECT_ROOT = Path(__file__).resolve().parent
ASSETS_DIR = PROJECT_ROOT / "assets"
UI_DIR = PROJECT_ROOT / "ui"
ICON_PATH = ASSETS_DIR / "tomato.png"
CHIME_PATH = ASSETS_DIR / "chime.wav"

# ============================================================
# 日志
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("work-timer")


# ============================================================
# 全局单例（在 main() 中初始化）
# ============================================================
class App:
    """整个应用的状态容器。"""

    def __init__(self) -> None:
        self.store = StateStore()
        self.scheduler: Scheduler | None = None
        self.window: webview.Window | None = None
        self.tray_icon = None  # pystray.Icon
        self._tray_thread: threading.Thread | None = None

    # ---------- Python ↔ JS 桥（pywebview js_api） ----------

    def get_state(self) -> dict:
        """JS 调用：拉取当前状态。"""
        if self.scheduler is None:
            return {}
        return self.scheduler.snapshot().to_dict()

    def toggle_start_pause(self) -> None:
        """JS 调用：开始/暂停切换。"""
        if self.scheduler:
            self.scheduler.toggle()
        self._persist()

    def reset_current(self) -> None:
        """JS 调用：重置当前阶段。"""
        if self.scheduler:
            self.scheduler.reset()
        self._persist()

    def skip_phase(self) -> None:
        """JS 调用：跳到下一阶段。"""
        if self.scheduler:
            self.scheduler.skip()
        self._persist()

    # ---------- 调度器回调 ----------

    def _on_tick(self, state: TimerState) -> None:
        """1Hz tick：推到 webview UI + 定期持久化。"""
        self._push_to_ui(state)
        # 每 10 秒持久化一次（避免每次都写盘）
        if state.remaining_seconds % 10 == 0:
            self.store.save(state)

    def _on_phase_change(self, old: Phase, state: TimerState) -> None:
        """阶段切换：推 UI + 立即持久化。"""
        self._push_to_ui(state)
        self.store.save(state)

    def _on_completed_focus(self) -> None:
        """每完成一个 FOCUS 阶段：通知 + 提示音。"""
        self._notify("番茄完成！", "该休息一下啦 🍵")
        self._play_chime()

    def _push_to_ui(self, state: TimerState) -> None:
        """把状态推送到 webview 窗口的 JS。"""
        if self.window is None:
            return
        try:
            # pywebview 在子线程调用 evaluate_js 也是安全的（内部用消息队列）
            self.window.evaluate_js(
                f"window.updateTimer({self._state_to_json(state)})"
            )
        except Exception:  # noqa: BLE001
            logger.debug("evaluate_js 失败（窗口可能已关闭）", exc_info=True)

    @staticmethod
    def _state_to_json(state: TimerState) -> str:
        import json

        return json.dumps(state.to_dict(), ensure_ascii=False)

    def _persist(self) -> None:
        if self.scheduler is None:
            return
        self.store.save(self.scheduler.snapshot())

    # ---------- 通知与音效 ----------

    @staticmethod
    def _notify(title: str, message: str) -> None:
        try:
            from plyer import notification

            notification.notify(
                title=title,
                message=message,
                app_name="番茄钟",
                timeout=5,
            )
        except Exception:  # noqa: BLE001
            logger.warning("系统通知发送失败", exc_info=True)

    def _play_chime(self) -> None:
        # 用 Windows 内置 winsound 播放 wav，零依赖
        try:
            import winsound

            def _play():
                try:
                    winsound.PlaySound(
                        str(CHIME_PATH),
                        winsound.SND_FILENAME | winsound.SND_ASYNC,
                    )
                except Exception:  # noqa: BLE001
                    logger.warning("播放提示音失败", exc_info=True)

            threading.Thread(target=_play, daemon=True).start()
        except Exception:  # noqa: BLE001
            logger.warning("winsound 不可用", exc_info=True)

    # ---------- 托盘 ----------

    def _build_tray(self) -> None:
        """构造 pystray 图标与菜单，并在守护线程里启动。"""
        from pystray import Icon, Menu, MenuItem
        from PIL import Image, ImageDraw

        try:
            icon_image = Image.open(ICON_PATH)
        except Exception:  # noqa: BLE001
            # fallback：PIL 现绘一个红色圆
            icon_image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
            ImageDraw.Draw(icon_image).ellipse(
                (4, 10, 60, 60), fill=(233, 75, 60, 255)
            )

        def on_show(icon, item) -> None:
            self._show_window()

        def on_toggle(icon, item) -> None:
            if self.scheduler:
                self.scheduler.toggle()
            self._persist()

        def on_quit(icon, item) -> None:
            self._shutdown()

        menu = Menu(
            MenuItem("显示窗口", on_show, default=True),
            MenuItem("开始/暂停", on_toggle),
            MenuItem("退出", on_quit),
        )

        self.tray_icon = Icon(
            "work-timer",
            icon=icon_image,
            title="番茄钟",
            menu=menu,
        )

        def _run_icon():
            try:
                self.tray_icon.run()
            except Exception:  # noqa: BLE001
                logger.exception("托盘线程异常")

        self._tray_thread = threading.Thread(
            target=_run_icon, name="tray", daemon=True
        )
        self._tray_thread.start()

    def _show_window(self) -> None:
        if self.window is None:
            return
        try:
            self.window.show()
        except Exception:  # noqa: BLE001
            logger.debug("显示窗口失败", exc_info=True)

    def _shutdown(self) -> None:
        """应用级关闭。"""
        logger.info("收到退出信号，开始清理...")
        # 1. 停调度器
        if self.scheduler is not None:
            self.scheduler.shutdown()
        # 2. 持久化一次最终状态
        if self.scheduler is not None:
            self.store.save(self.scheduler.snapshot())
        # 3. 关窗口
        if self.window is not None:
            try:
                self.window.destroy()
            except Exception:  # noqa: BLE001
                pass
        # 4. 停托盘
        if self.tray_icon is not None:
            try:
                self.tray_icon.stop()
            except Exception:  # noqa: BLE001
                pass
        # 5. 释放进程锁
        self.store.release_lock()
        logger.info("清理完成，进程退出。")


# ============================================================
# 入口
# ============================================================
def main() -> int:
    app = App()

    # 1. 进程锁
    try:
        app.store.acquire_lock()
    except AlreadyRunning as exc:
        logger.error(str(exc))
        # 弹个简单提示（标准输出 + 短暂停）
        print(f"[work-timer] {exc}", file=sys.stderr)
        return 1

    # 2. 恢复 / 初始状态
    restored = app.store.load()
    initial_state = restored if restored is not None else TimerState()
    logger.info(
        "初始状态: phase=%s remaining=%ds paused=%s count=%d",
        initial_state.phase.value,
        initial_state.remaining_seconds,
        initial_state.paused,
        initial_state.pomodoro_count,
    )

    # 3. 调度器
    app.scheduler = Scheduler(
        initial=initial_state,
        on_tick=app._on_tick,
        on_phase_change=app._on_phase_change,
        on_completed_focus=app._on_completed_focus,
    )
    app.scheduler.start()

    # 4. 托盘（守护线程）
    try:
        app._build_tray()
    except Exception:  # noqa: BLE001
        logger.exception("托盘启动失败，进程继续（仅窗口模式）")

    # 5. pywebview 窗口（主线程）
    try:
        app.window = webview.create_window(
            title="🍅 番茄钟",
            url=str(UI_DIR / "index.html"),
            width=360,
            height=520,
            resizable=False,
            frameless=False,
            easy_drag=False,
            js_api=app,  # 暴露 app 的方法给 JS
            confirm_close=False,
        )
    except Exception:  # noqa: BLE001
        logger.exception("pywebview 启动失败")
        app._shutdown()
        return 2

    # 6. 主循环（阻塞）
    try:
        webview.start()
    finally:
        # 窗口关闭 → 清理
        app._shutdown()

    return 0


if __name__ == "__main__":
    sys.exit(main())
