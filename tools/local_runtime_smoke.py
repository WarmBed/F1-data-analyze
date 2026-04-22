#!/usr/bin/env python3
"""Local runtime smoke checks.

The goal is to verify the local desktop runtime without requiring an HTTP API
server. The script writes a JSON report so CI or a human can inspect exactly
what passed, failed, or was skipped.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / "logs" / "local_runtime_smoke_report.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _run_command(cmd: List[str], timeout: int = 60) -> Dict[str, Any]:
    return _run_command_with_env(cmd, env=None, timeout=timeout)


def _run_command_with_env(cmd: List[str], env: Dict[str, str] | None, timeout: int = 60) -> Dict[str, Any]:
    started = time.perf_counter()
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
    )
    return {
        "cmd": cmd,
        "returncode": proc.returncode,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "stdout_preview": proc.stdout[-2000:],
        "stderr_preview": proc.stderr[-2000:],
        "ok": proc.returncode == 0,
    }


def check_runtime_imports() -> Dict[str, Any]:
    from core.runtime_mode import get_runtime_mode, is_api_enabled, is_local_first
    from core.local_analysis_executor import LocalAnalysisExecutor
    from windows.workers.local_task_worker import LocalAnalysisWorker

    return {
        "runtime_mode": get_runtime_mode(),
        "local_first": is_local_first(),
        "api_enabled": is_api_enabled(),
        "executor": LocalAnalysisExecutor.__name__,
        "worker": LocalAnalysisWorker.__name__,
        "ok": get_runtime_mode() == "local" and is_local_first() and not is_api_enabled(),
    }


def check_function_specs() -> Dict[str, Any]:
    from api.models.function_specs import FUNCTION_SPECS, normalize_function_id
    from api.services.simple_analysis_service import SimpleF1AnalysisService

    service = SimpleF1AnalysisService()
    failures: list[dict[str, Any]] = []
    built = 0

    sample_params = {
        "year": 2026,
        "race": "Japan",
        "session": "R",
        "driver1": "VER",
        "driver2": "LEC",
        "lap": 1,
        "lap1": 1,
        "lap2": 1,
        "corner": 1,
        "team": "Red Bull Racing",
        "colormap": "fastf1",
        "start_year": 2025,
        "end_year": 2026,
    }

    for function_id, spec in FUNCTION_SPECS.items():
        try:
            normalize_function_id(function_id)
            params = {name: sample_params[name] for name in spec.required_params if name in sample_params}
            params.update({name: sample_params[name] for name in spec.optional_params if name in sample_params})
            missing = [name for name in spec.required_params if name not in params]
            if missing:
                failures.append({"function_id": function_id, "error": f"missing sample params: {missing}"})
                continue
            prepared = service._prepare_params(spec, params)
            cmd = service._build_cli_command(spec, prepared)
            if "-f" not in cmd or str(spec.function_id) not in cmd:
                failures.append({"function_id": function_id, "error": "command missing function id"})
                continue
            built += 1
        except Exception as exc:
            failures.append({"function_id": function_id, "error": f"{type(exc).__name__}: {exc}"})

    return {
        "function_count": len(FUNCTION_SPECS),
        "commands_built": built,
        "failures": failures,
        "ok": not failures,
    }


def check_json_readability(limit: int | None = None) -> Dict[str, Any]:
    json_files = sorted((ROOT / "json").rglob("*.json"))
    if limit is not None:
        json_files = json_files[:limit]

    failures: list[dict[str, Any]] = []
    read_count = 0
    total_bytes = 0

    for path in json_files:
        try:
            total_bytes += path.stat().st_size
            with path.open("r", encoding="utf-8") as handle:
                json.load(handle)
            read_count += 1
        except Exception as exc:
            failures.append({
                "path": str(path.relative_to(ROOT)),
                "error": f"{type(exc).__name__}: {exc}",
            })
            if len(failures) >= 25:
                break

    return {
        "checked": len(json_files),
        "read_ok": read_count,
        "total_mb": round(total_bytes / 1024 / 1024, 3),
        "failures": failures,
        "ok": not failures,
    }


def run_cli_smoke(iterations: int) -> Dict[str, Any]:
    commands = [
        [sys.executable, "f1_analysis_modular_main.py", "--version"],
        [sys.executable, "f1_analysis_modular_main.py", "--help"],
        [sys.executable, "f1_analysis_modular_main.py", "-f", "99", "-y", "2026", "--silent"],
    ]
    results = []
    for iteration in range(1, iterations + 1):
        for cmd in commands:
            result = _run_command(cmd, timeout=120)
            result["iteration"] = iteration
            results.append(result)

    return {
        "iterations": iterations,
        "results": results,
        "ok": all(item["ok"] for item in results),
    }


def run_gui_smoke(iterations: int) -> Dict[str, Any]:
    from PyQt5.QtCore import QTimer
    from PyQt5.QtWidgets import QApplication
    import f1t_gui_main

    app = QApplication.instance() or QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    results: list[dict[str, Any]] = []
    state: dict[str, Any] = {"window": None, "count": 0}

    def run_one() -> None:
        progress: list[tuple[int, str]] = []

        def callback(value: int, message: str) -> None:
            progress.append((value, str(message)[:80]))

        started = time.perf_counter()
        window = f1t_gui_main.StyleHMainWindow(progress_callback=callback)
        constructed = time.perf_counter() - started
        window.show()
        results.append({
            "constructed": True,
            "construct_elapsed_seconds": round(constructed, 3),
            "window_title": window.windowTitle(),
            "progress_events": len(progress),
            "has_year_combo": hasattr(window, "year_combo"),
            "year_count": window.year_combo.count() if hasattr(window, "year_combo") and window.year_combo else None,
            "current_year": window.year_combo.currentText() if hasattr(window, "year_combo") and window.year_combo else None,
        })
        state["window"] = window
        QTimer.singleShot(350, window.close)

    def step() -> None:
        if state["count"] >= iterations:
            app.quit()
            return
        state["count"] += 1
        run_one()
        QTimer.singleShot(650, step)

    loop_started = time.perf_counter()
    QTimer.singleShot(0, step)
    QTimer.singleShot(max(10000, iterations * 25000), app.quit)
    event_result = app.exec_()

    result = {
        "iteration": "single_process",
        "returncode": 0,
        "elapsed_seconds": round(time.perf_counter() - loop_started, 3),
        "stdout_preview": "",
        "stderr_preview": "",
        "parsed": {
            "event_loop_result": event_result,
            "event_loop_elapsed_seconds": round(time.perf_counter() - loop_started, 3),
            "iterations": iterations,
            "results": results,
        },
    }
    try:
        parsed_results = result["parsed"].get("results", []) if result["parsed"] else []
        result["ok"] = len(parsed_results) == iterations and all(
            item.get("constructed") and item.get("has_year_combo") for item in parsed_results
        )
    except Exception as exc:
        result["parse_error"] = f"{type(exc).__name__}: {exc}"
        result["ok"] = False

    return {
        "iterations": iterations,
        "results": [result],
        "ok": result["ok"],
    }


def run_local_executor_smoke(iterations: int) -> Dict[str, Any]:
    snippet = r"""
import asyncio, json
from core.local_analysis_executor import LocalAnalysisExecutor
async def main():
    result = await LocalAnalysisExecutor().execute(99, year=2026)
    print(json.dumps({
        'success': result.get('success'),
        'source': result.get('source'),
        'has_data': bool(result.get('data')),
        'execution_time': result.get('execution_time'),
        'error': result.get('error'),
    }, ensure_ascii=False))
asyncio.run(main())
"""
    results = []
    for iteration in range(1, iterations + 1):
        result = _run_command([sys.executable, "-c", snippet], timeout=120)
        result["iteration"] = iteration
        try:
            lines = [line for line in result["stdout_preview"].splitlines() if line.strip()]
            result["parsed"] = json.loads(lines[-1]) if lines else None
            result["ok"] = result["ok"] and bool(
                result["parsed"]
                and result["parsed"].get("success")
                and result["parsed"].get("has_data")
            )
        except Exception as exc:
            result["parse_error"] = f"{type(exc).__name__}: {exc}"
            result["ok"] = False
        results.append(result)

    return {
        "iterations": iterations,
        "results": results,
        "ok": all(item["ok"] for item in results),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local desktop runtime smoke checks.")
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--json-limit", type=int, default=250)
    parser.add_argument("--all-json", action="store_true")
    parser.add_argument("--skip-gui", action="store_true")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    os.environ.setdefault("F1T_RUNTIME_MODE", "local")

    report: Dict[str, Any] = {
        "root": str(ROOT),
        "iterations": args.iterations,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "runtime_imports": check_runtime_imports(),
        "function_specs": check_function_specs(),
        "json_readability": check_json_readability(None if args.all_json else args.json_limit),
        "cli_smoke": run_cli_smoke(args.iterations),
        "local_executor_smoke": run_local_executor_smoke(args.iterations),
    }

    if args.skip_gui:
        report["gui_smoke"] = {"skipped": True, "ok": True}
    else:
        report["gui_smoke"] = run_gui_smoke(args.iterations)

    report["ok"] = all(
        section.get("ok", False)
        for section in (
            report["runtime_imports"],
            report["function_specs"],
            report["json_readability"],
            report["cli_smoke"],
            report["local_executor_smoke"],
            report["gui_smoke"],
        )
    )

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        print(json.dumps({"ok": report["ok"], "report": str(args.report)}, ensure_ascii=False))
    except Exception:
        pass

    # PyQt can crash in interpreter teardown on Windows after constructing the
    # full main window. The report has already been written, so exit explicitly
    # to keep the smoke-test result tied to the measured checks.
    if not args.skip_gui:
        os._exit(0 if report["ok"] else 1)

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
