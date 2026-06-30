/* ============================================================
   番茄钟前端逻辑
   - 通过 window.pywebview.api 调用 Python
   - 监听 Python 推送的 updateTimer(state) 更新界面
   ============================================================ */

(function () {
    "use strict";

    const PHASE_LABELS = {
        FOCUS: "专注",
        SHORT_BREAK: "短休",
        LONG_BREAK: "长休",
    };

    const PHASE_DURATIONS = {
        FOCUS: 25 * 60,
        SHORT_BREAK: 5 * 60,
        LONG_BREAK: 15 * 60,
    };

    // ---- DOM 引用 ----
    const body           = document.body;
    const timerDisplay   = document.getElementById("timerDisplay");
    const phaseLabel     = document.getElementById("phaseLabel");
    const btnToggle      = document.getElementById("btnToggle");
    const btnReset       = document.getElementById("btnReset");
    const btnSkip        = document.getElementById("btnSkip");
    const phaseDots      = document.getElementById("phaseDots");
    const todayCountEl   = document.getElementById("todayCount");
    const ringProgress   = document.querySelector(".ring-progress");
    const RING_CIRCUM    = 2 * Math.PI * 90;  // 565.48

    // ---- 工具 ----
    function fmt(secs) {
        const m = Math.floor(secs / 60);
        const s = secs % 60;
        return String(m).padStart(2, "0") + ":" + String(s).padStart(2, "0");
    }

    function renderDots(pomodoroCount) {
        const dots = phaseDots.querySelectorAll(".dot");
        dots.forEach((dot, i) => {
            dot.classList.toggle("filled", i < pomodoroCount);
        });
    }

    // ---- 状态渲染 ----
    function render(state) {
        if (!state) return;
        body.setAttribute("data-phase", state.phase);

        timerDisplay.textContent = fmt(state.remaining_seconds);
        phaseLabel.textContent = PHASE_LABELS[state.phase] || "";

        // 进度环
        const total = PHASE_DURATIONS[state.phase] || 1;
        const ratio = Math.max(0, Math.min(1, state.remaining_seconds / total));
        ringProgress.setAttribute(
            "stroke-dashoffset",
            String((1 - ratio) * RING_CIRCUM)
        );

        // 主按钮文字
        btnToggle.textContent = state.paused ? "开始" : "暂停";

        // 末 10 秒脉冲
        timerDisplay.classList.toggle(
            "ending",
            !state.paused && state.remaining_seconds <= 10 && state.remaining_seconds > 0
        );

        // 阶段圆点
        renderDots(state.pomodoro_count);

        // 今日完成数
        todayCountEl.textContent = String(state.today_count);
    }

    // ---- 暴露给 Python 的入口（pywebview evaluate_js 会调用 window.updateTimer） ----
    window.updateTimer = function (state) {
        render(state);
    };

    // ---- 按钮事件 ----
    function callApi(method) {
        if (window.pywebview && window.pywebview.api) {
            return window.pywebview.api[method]();
        }
        // 浏览器直接打开时的退化（用于纯前端调试）
        console.warn("pywebview api 不可用:", method);
    }

    btnToggle.addEventListener("click", () => callApi("toggleStartPause"));
    btnReset.addEventListener("click",  () => callApi("resetCurrent"));
    btnSkip.addEventListener("click",   () => callApi("skipPhase"));

    // ---- 初始拉取一次状态 ----
    document.addEventListener("pywebviewready", () => {
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.getState().then(render);
        }
    });
    // 兜底：DOMContentLoaded 时尝试拉取
    document.addEventListener("DOMContentLoaded", () => {
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.getState().then(render);
        }
    });
})();
