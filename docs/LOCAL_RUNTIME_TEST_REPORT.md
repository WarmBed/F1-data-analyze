# Local Runtime Test Report

Date: 2026-04-22

## Goal

Produce a clean local desktop version where the GUI does not depend on a
running HTTP API server. The expected target is:

```text
GUI -> LocalAnalysisWorker -> LocalAnalysisExecutor -> cache / CLI modules / services
CLI -> LocalAnalysisExecutor or direct CLI entry -> cache / CLI modules / services
```

## Current Result

The project can start in local mode and the core smoke tests pass. GUI modules
no longer import the real `requests` package directly; local analysis endpoint
calls are routed through `core.local_requests`, which executes in-process via
`LocalAnalysisExecutor`.

## Tests Run

### Runtime/import smoke

Command summary:

```powershell
python -m py_compile core\runtime_mode.py core\local_analysis_executor.py windows\workers\local_task_worker.py windows\workers\api_workers.py core\api_runtime_state.py
```

Result: passed.

Runtime mode check:

```text
runtime=local local_first=True api_enabled=False
```

### GUI import smoke

Imported:

- `core.runtime_mode`
- `core.local_analysis_executor.LocalAnalysisExecutor`
- `windows.workers.local_task_worker.LocalAnalysisWorker`
- `windows.workers.api_workers.ApiHealthWorker`
- `f1t_gui_main`

Result: passed.

### GUI construction smoke

Constructed `StyleHMainWindow` five times in one Qt process, showed each window
briefly, then closed it by timer.

Result:

```text
gui_iterations=5
gui_constructs=5
gui_construct_elapsed_seconds=[5.004, 0.174, 0.274, 0.221, 0.169]
window_title=PIT WALL V0.16.0
year_count=5
current_year=2026
gui_smoke=True
```

### CLI smoke

Commands:

```powershell
python f1_analysis_modular_main.py --help
python f1_analysis_modular_main.py --version
python f1_analysis_modular_main.py --list-races
python f1_analysis_modular_main.py -f 99 -y 2026 --silent
```

Result:

- `--help`: passed.
- `--version`: passed, reports `F1 Analysis CLI v5.3`.
- `--list-races`: exit code 0, but produced no useful list output.
- `-f 99 -y 2026 --silent`: exit code 0.

### Local executor smoke

Executed F99 through `LocalAnalysisExecutor` five times.

Result:

```text
success=True
source=cache
execution_time=0.557s
has_data=True
```

### Full JSON readability

Read every JSON file under `json/`.

Result:

```text
checked=7174
read_ok=7174
total_mb=7906.46
```

Eight corrupt local JSON files were repaired before the final passing run. The
repair details are recorded in `logs/invalid_json_repair_report.json`. These
data files are local generated artifacts and are intentionally not tracked.

### Local GUI request bridge

The GUI code now imports `core.local_requests` as `requests`. This compatibility
layer intercepts calls to `/api/v2/analysis/execute` and runs:

```text
GUI loader -> core.local_requests -> LocalAnalysisExecutor -> cache / CLI
```

Direct imports of the real `requests` package in `modules/gui` and `windows`:

```text
0
```

### Focused pytest

Command:

```powershell
python -m pytest tests/test_api_base_url.py tests/test_runtime_status_resolver.py tests/test_cli_api_bridge.py -q
```

Result:

```text
14 passed
```

Tests were updated to match local-only behavior:

- localhost/private API URLs are valid in legacy/hybrid config helpers.
- F99 `year` is optional, matching the current function spec.

### GUI/module pytest attempt

Command:

```powershell
python -m pytest tests/test_gui_modules_import.py tests/test_module_imports.py tests/test_all_modules_syntax.py -q
```

Result: blocked during collection.

Reason:

- `tests/test_gui_modules_import.py` imports missing module
  `modules.gui.rain_analysis.rain_analysis_universal`.
- The test calls `sys.exit(1)` at import time, causing pytest internal error.

This test must be rewritten before it can be part of a clean CI gate.

## Remaining Blocking Risk Counts

Current source scan:

```text
requests.post              67
requests.get                8
QApplication.processEvents 21
.wait(                     59
subprocess.Popen            3
create_subprocess_exec      1
json.load                 189
pickle.load                60
fastf1.get_session         27
```

The remaining `requests.post` / `requests.get` call sites are compatibility
call sites that now use `core.local_requests` in GUI code. They should still be
gradually rewritten to explicit `LocalAnalysisWorker` usage, but they no longer
require a running HTTP API server in local mode.

## Required Clean Local Version Work

### Phase 1 - Stabilize the local runtime shell

- Keep `F1T_RUNTIME_MODE=local` as the default.
- Keep legacy API workers disabled unless `F1T_RUNTIME_MODE=hybrid` or `api`.
- Make `LocalAnalysisWorker` the only approved new GUI analysis worker.
- Keep `api/` temporarily as a compatibility namespace.

Acceptance:

- GUI smoke test passes.
- CLI smoke test passes.
- `LocalAnalysisExecutor` can execute at least F99 from cache.
- Focused tests pass.

### Phase 2 - Migrate GUI loaders off API calls

Replace per-module `requests.post()` workers with `LocalAnalysisWorker`.

Priority modules:

1. `modules/gui/shared/season_calendar_provider.py`
2. `modules/gui/themes/color_palette_provider.py`
3. `modules/gui/telemetry_analysis_mdi.py`
4. `modules/gui/all_drivers/brake/brake_all_laps_loader.py`
5. `modules/gui/all_drivers/brake/brake_chart_data_loader.py`
6. `modules/gui/all_drivers/acceleration/acceleration_chart_data_loader.py`
7. `modules/gui/lap_analysis/telemetry_data_loader_base.py`

Acceptance:

- `requests.post` count decreases every migration.
- Closing the GUI during an analysis does not hang.
- No module waits indefinitely for a blocked HTTP request.

### Phase 3 - Remove UI blocking patterns

- Replace `QApplication.processEvents()` loading patterns with signals/timers.
- Replace unsafe `worker.wait()` with short timeout + cancellation.
- Move `json.load()` / `pickle.load()` used by UI paths into background workers.
- Add request ids and cancellation states to all local jobs.

Acceptance:

- GUI construction remains under 12 seconds initially, then target under 5 seconds.
- Repeated open/close smoke test does not leave persistent QThreads.
- No UI module performs direct large disk I/O in the main thread.

### Phase 4 - Clean CLI/function registry

- Treat `api/models/function_specs.py` as the current single registry.
- Later move it to `core/analysis/function_specs.py`.
- Reduce `CLI_modules/cli/core/function_mapper.py` to implementation mapping only.
- Fix `--list-races` so it either prints useful data or returns a clear message.
- Fix stdout/log encoding mojibake in service/CLI output.

Acceptance:

- `--help`, `--version`, `--list-races`, and one cached function pass.
- CLI output is readable UTF-8.
- GUI and CLI use the same function spec metadata.

### Phase 5 - Repair tests for clean CI

- Rewrite `tests/test_gui_modules_import.py` into normal pytest tests.
- Remove imports for missing `modules.gui.rain_analysis`.
- Add tests for `LocalAnalysisWorker` and `LocalAnalysisExecutor`.
- Add a non-interactive GUI smoke test that creates and closes `StyleHMainWindow`.

Acceptance:

- Focused local runtime suite passes.
- GUI import/construction tests can be run without `sys.exit()` during collection.

## Current Recommendation

Do not delete the API package yet. First migrate the GUI modules away from
direct HTTP calls. Once `requests.post` is gone from GUI modules and tests pass,
the API package can be moved to optional legacy support or removed from the
desktop build.
