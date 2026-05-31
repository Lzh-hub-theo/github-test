"""
Macro Recorder - 按键精灵风格自动化脚本工具
功能：录制鼠标/键盘操作 → 生成可执行脚本 → 精确回放
"""

import json
import time
import os
import sys
import argparse
import ctypes
from datetime import datetime
from pynput import mouse, keyboard


def _enable_dpi_awareness():
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


STOP_KEY = keyboard.Key.f8
RECORDINGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recordings")
SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts")


def _ensure_dirs():
    os.makedirs(RECORDINGS_DIR, exist_ok=True)
    os.makedirs(SCRIPTS_DIR, exist_ok=True)


def _key_to_str(key):
    if isinstance(key, keyboard.Key):
        return key.name
    try:
        return key.char
    except AttributeError:
        return str(key)


def _str_to_key(s):
    try:
        return getattr(keyboard.Key, s)
    except AttributeError:
        pass
    if len(s) == 1:
        return keyboard.KeyCode.from_char(s)
    return keyboard.KeyCode.from_char(s)


def _button_to_str(btn):
    if btn == mouse.Button.left:
        return "left"
    elif btn == mouse.Button.right:
        return "right"
    elif btn == mouse.Button.middle:
        return "middle"
    return str(btn)


def _str_to_button(s):
    mapping = {"left": mouse.Button.left, "right": mouse.Button.right, "middle": mouse.Button.middle}
    return mapping.get(s, mouse.Button.left)


class EventRecorder:
    def __init__(self, record_mouse_move=True, move_interval=0.05):
        self.events = []
        self.start_time = None
        self.recording = False
        self.record_mouse_move = record_mouse_move
        self.move_interval = move_interval
        self._last_move_time = 0
        self._mouse_listener = None
        self._keyboard_listener = None

    def _add_event(self, event_type, **kwargs):
        if not self.recording:
            return
        now = time.time()
        if self.start_time is None:
            self.start_time = now
        kwargs["time"] = round(now - self.start_time, 4)
        kwargs["type"] = event_type
        self.events.append(kwargs)

    def _on_move(self, x, y):
        now = time.time()
        if not self.record_mouse_move:
            return
        if now - self._last_move_time < self.move_interval:
            return
        self._last_move_time = now
        self._add_event("mouse_move", x=x, y=y)

    def _on_click(self, x, y, button, pressed):
        self._add_event("mouse_click", x=x, y=y, button=_button_to_str(button), pressed=pressed)

    def _on_scroll(self, x, y, dx, dy):
        self._add_event("mouse_scroll", x=x, y=y, dx=dx, dy=dy)

    def _on_press(self, key):
        if key == STOP_KEY and self.recording:
            self.stop()
            return False
        self._add_event("key_press", key=_key_to_str(key))

    def _on_release(self, key):
        if key == STOP_KEY:
            return False
        self._add_event("key_release", key=_key_to_str(key))

    def start(self):
        self.events = []
        self.start_time = None
        self.recording = True
        self._last_move_time = 0

        print("\n" + "=" * 50)
        print("  录制已开始！")
        print(f"  按 F8 键停止录制")
        print("=" * 50 + "\n")

        self._mouse_listener = mouse.Listener(
            on_move=self._on_move,
            on_click=self._on_click,
            on_scroll=self._on_scroll,
        )
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._mouse_listener.start()
        self._keyboard_listener.start()
        self._keyboard_listener.join()

    def stop(self):
        self.recording = False
        if self._mouse_listener:
            self._mouse_listener.stop()
        if self._keyboard_listener:
            self._keyboard_listener.stop()
        duration = self.events[-1]["time"] if self.events else 0
        print("\n" + "=" * 50)
        print("  录制已停止！")
        print(f"  共录制 {len(self.events)} 个事件，时长 {duration:.2f} 秒")
        print("=" * 50 + "\n")

    def save(self, filename=None):
        _ensure_dirs()
        if filename is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{ts}.json"
        if not filename.endswith(".json"):
            filename += ".json"
        filepath = os.path.join(RECORDINGS_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.events, f, ensure_ascii=False, indent=2)
        print(f"  录制数据已保存至: {filepath}")
        return filepath


class EventPlayer:
    def __init__(self, speed=1.0):
        self.speed = speed

    def load(self, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            self.events = json.load(f)
        print(f"  已加载录制文件: {filepath} ({len(self.events)} 个事件)")
        return self

    def play(self):
        if not self.events:
            print("  没有可回放的事件！")
            return

        print("\n" + "=" * 50)
        print("  回放将在 3 秒后开始...")
        print("  按 Ctrl+C 可中断回放")
        print("=" * 50 + "\n")
        time.sleep(3)

        mouse_ctrl = mouse.Controller()
        keyboard_ctrl = keyboard.Controller()
        prev_time = 0

        try:
            for i, event in enumerate(self.events):
                if i > 0:
                    delay = (event["time"] - prev_time) / self.speed
                    if delay > 0:
                        time.sleep(delay)
                prev_time = event["time"]

                etype = event["type"]

                if etype == "mouse_move":
                    mouse_ctrl.position = (event["x"], event["y"])

                elif etype == "mouse_click":
                    mouse_ctrl.position = (event["x"], event["y"])
                    time.sleep(0.01)
                    btn = _str_to_button(event["button"])
                    if event["pressed"]:
                        mouse_ctrl.press(btn)
                    else:
                        mouse_ctrl.release(btn)

                elif etype == "mouse_scroll":
                    mouse_ctrl.position = (event["x"], event["y"])
                    time.sleep(0.01)
                    mouse_ctrl.scroll(event["dx"], event["dy"])

                elif etype == "key_press":
                    key_obj = _str_to_key(event["key"])
                    keyboard_ctrl.press(key_obj)

                elif etype == "key_release":
                    key_obj = _str_to_key(event["key"])
                    keyboard_ctrl.release(key_obj)

            print("\n  回放完成！")
        except KeyboardInterrupt:
            print("\n  回放已中断！")


class ScriptGenerator:
    def __init__(self):
        self.events = []

    def load(self, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            self.events = json.load(f)
        return self

    def load_from_events(self, events):
        self.events = events
        return self

    def generate(self, filename=None):
        _ensure_dirs()
        if filename is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"script_{ts}.py"
        if not filename.endswith(".py"):
            filename += ".py"
        filepath = os.path.join(SCRIPTS_DIR, filename)

        lines = []
        lines.append('"""')
        lines.append("Auto-generated macro script")
        lines.append(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append('"""')
        lines.append("")
        lines.append("import time")
        lines.append("import sys")
        lines.append("import ctypes")
        lines.append("from pynput import mouse, keyboard")
        lines.append("")
        lines.append("if sys.platform == 'win32':")
        lines.append("    try:")
        lines.append("        ctypes.windll.shcore.SetProcessDpiAwareness(2)")
        lines.append("    except Exception:")
        lines.append("        try:")
        lines.append("            ctypes.windll.user32.SetProcessDPIAware()")
        lines.append("        except Exception:")
        lines.append("            pass")
        lines.append("")
        lines.append("mouse_ctrl = mouse.Controller()")
        lines.append("keyboard_ctrl = keyboard.Controller()")
        lines.append("")
        lines.append("print('Script starting in 3 seconds...')")
        lines.append("time.sleep(3)")
        lines.append("")

        prev_time = 0
        for i, event in enumerate(self.events):
            if i > 0:
                delay = event["time"] - prev_time
                if delay > 0.005:
                    lines.append(f"time.sleep({delay:.4f})")
            prev_time = event["time"]

            etype = event["type"]

            if etype == "mouse_move":
                lines.append(f"mouse_ctrl.position = ({event['x']}, {event['y']})")

            elif etype == "mouse_click":
                btn_str = event["button"]
                lines.append(f"mouse_ctrl.position = ({event['x']}, {event['y']})")
                lines.append("time.sleep(0.01)")
                if event["pressed"]:
                    lines.append(f"mouse_ctrl.press(mouse.Button.{btn_str})")
                else:
                    lines.append(f"mouse_ctrl.release(mouse.Button.{btn_str})")

            elif etype == "mouse_scroll":
                lines.append(f"mouse_ctrl.position = ({event['x']}, {event['y']})")
                lines.append("time.sleep(0.01)")
                lines.append(f"mouse_ctrl.scroll({event['dx']}, {event['dy']})")

            elif etype == "key_press":
                key_str = event["key"]
                if len(key_str) == 1:
                    lines.append(f"keyboard_ctrl.press('{key_str}')")
                else:
                    lines.append(f"keyboard_ctrl.press(keyboard.Key.{key_str})")

            elif etype == "key_release":
                key_str = event["key"]
                if len(key_str) == 1:
                    lines.append(f"keyboard_ctrl.release('{key_str}')")
                else:
                    lines.append(f"keyboard_ctrl.release(keyboard.Key.{key_str})")

        lines.append("")
        lines.append("print('Script execution completed!')")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"  脚本已生成: {filepath}")
        return filepath


def list_recordings():
    _ensure_dirs()
    files = [f for f in os.listdir(RECORDINGS_DIR) if f.endswith(".json")]
    if not files:
        print("  暂无录制文件")
        return []
    files.sort(reverse=True)
    print("\n  可用的录制文件:")
    print("  " + "-" * 45)
    for i, f in enumerate(files, 1):
        filepath = os.path.join(RECORDINGS_DIR, f)
        with open(filepath, "r", encoding="utf-8") as fh:
            events = json.load(fh)
        duration = events[-1]["time"] if events else 0
        print(f"  {i}. {f}  ({len(events)} 事件, {duration:.1f}s)")
    print("  " + "-" * 45)
    return files


def cmd_record(args):
    recorder = EventRecorder(
        record_mouse_move=not args.no_mouse_move,
        move_interval=args.move_interval,
    )
    recorder.start()
    filepath = recorder.save(args.output)
    if args.generate_script:
        gen = ScriptGenerator()
        gen.load(filepath)
        gen.generate()


def cmd_play(args):
    _ensure_dirs()
    if args.input:
        filepath = args.input if os.path.isabs(args.input) else os.path.join(RECORDINGS_DIR, args.input)
    else:
        files = list_recordings()
        if not files:
            return
        if args.latest or len(files) == 1:
            chosen = files[0]
        else:
            try:
                idx = int(input("\n  请选择录制文件编号: ")) - 1
                chosen = files[idx]
            except (ValueError, IndexError):
                print("  无效选择")
                return
        filepath = os.path.join(RECORDINGS_DIR, chosen)

    if not os.path.exists(filepath):
        print(f"  文件不存在: {filepath}")
        return

    player = EventPlayer(speed=args.speed)
    player.load(filepath)
    player.play()


def cmd_generate(args):
    _ensure_dirs()
    if args.input:
        filepath = args.input if os.path.isabs(args.input) else os.path.join(RECORDINGS_DIR, args.input)
    else:
        files = list_recordings()
        if not files:
            return
        if args.latest or len(files) == 1:
            chosen = files[0]
        else:
            try:
                idx = int(input("\n  请选择录制文件编号: ")) - 1
                chosen = files[idx]
            except (ValueError, IndexError):
                print("  无效选择")
                return
        filepath = os.path.join(RECORDINGS_DIR, chosen)

    if not os.path.exists(filepath):
        print(f"  文件不存在: {filepath}")
        return

    gen = ScriptGenerator()
    gen.load(filepath)
    gen.generate(args.output)


def cmd_list(args):
    list_recordings()


def main():
    _enable_dpi_awareness()

    parser = argparse.ArgumentParser(
        description="Macro Recorder - 按键精灵风格自动化脚本工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python macro_recorder.py record                    开始录制（按F8停止）
  python macro_recorder.py record --no-mouse-move    录制时忽略鼠标移动
  python macro_recorder.py play --latest             回放最近一次录制
  python macro_recorder.py play --speed 2.0          以2倍速回放
  python macro_recorder.py generate --latest         为最近录制生成脚本
  python macro_recorder.py list                      列出所有录制文件
        """,
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    rec_parser = subparsers.add_parser("record", help="录制鼠标和键盘操作")
    rec_parser.add_argument("-o", "--output", help="输出文件名（默认自动生成）")
    rec_parser.add_argument("--no-mouse-move", action="store_true", help="不录制鼠标移动事件")
    rec_parser.add_argument("--move-interval", type=float, default=0.05, help="鼠标移动采样间隔（秒，默认0.05）")
    rec_parser.add_argument("-g", "--generate-script", action="store_true", help="录制后自动生成脚本")

    play_parser = subparsers.add_parser("play", help="回放录制的操作")
    play_parser.add_argument("-i", "--input", help="录制文件路径或文件名")
    play_parser.add_argument("--latest", action="store_true", help="回放最近一次录制")
    play_parser.add_argument("-s", "--speed", type=float, default=1.0, help="回放速度倍率（默认1.0）")

    gen_parser = subparsers.add_parser("generate", help="从录制数据生成可执行脚本")
    gen_parser.add_argument("-i", "--input", help="录制文件路径或文件名")
    gen_parser.add_argument("--latest", action="store_true", help="使用最近一次录制")
    gen_parser.add_argument("-o", "--output", help="输出脚本文件名（默认自动生成）")

    subparsers.add_parser("list", help="列出所有录制文件")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    commands = {
        "record": cmd_record,
        "play": cmd_play,
        "generate": cmd_generate,
        "list": cmd_list,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
