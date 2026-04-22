# Local-Only Refactor Plan

## Decision

The application should move to a local-first runtime. The GUI should not depend
on an always-running HTTP API server. The API package should be treated as a
legacy optional adapter until all GUI modules are migrated.

Target runtime:

```text
GUI -> Local task runner -> LocalAnalysisExecutor -> cache / CLI modules / services
CLI -> LocalAnalysisExecutor -> cache / CLI modules / services
API -> optional legacy adapter -> LocalAnalysisExecutor
```

## Current Risk Points

- GUI modules still contain many per-page `QThread` workers and direct
  `requests.post()` calls.
- Some UI paths still use blocking `json.load()`, `pickle.load()`, glob scans,
  and synchronous worker cleanup.
- `windows/workers/cli_workers.py` contains disabled CLI worker code followed by
  unreachable subprocess code.
- `windows/workers/api_workers.py` is now legacy. It should only run in
  `hybrid` or `api` runtime mode.
- `api/routers/analysis.py` contains heavy telemetry merge logic. That should
  move to service/core code before the API layer is removed.
- `api/models/function_specs.py` is the cleanest function registry and should
  become the single source of truth for GUI, CLI, and optional API adapters.

## Dead-Code Policy

Do not delete large blocks immediately. Mark them with:

```python
# LOCAL_ONLY_REFACTOR: legacy/dead path. Keep temporarily until replacement.
```

Deletion can happen only after:

1. The replacement local path exists.
2. At least one GUI module is migrated and verified.
3. CLI execution still works through the same function registry.
4. No imports reference the legacy worker/service.

## Migration Order

1. Introduce a shared local execution facade.
   - Current file: `core/local_analysis_executor.py`
   - Future target: move `api/services/simple_analysis_service.py` into
     `core/analysis/`.
2. Add runtime mode control.
   - Current file: `core/runtime_mode.py`
   - Default: `local`
   - Optional values: `hybrid`, `api`
3. Stop new API dependencies in GUI modules.
   - New GUI work should call a local task runner.
   - Existing API workers stay marked as legacy until migrated.
4. Replace per-module workers with one local task runner.
   - Current file: `windows/workers/local_task_worker.py`
   - Required signals: started, progress, result, error, cancelled, finished.
   - No UI thread disk I/O, network I/O, FastF1 calls, or heavy pandas work.
5. Consolidate function mapping.
   - Use `api/models/function_specs.py` as the registry for now.
   - Later move it to `core/analysis/function_specs.py`.
   - `CLI_modules/cli/core/function_mapper.py` should become an implementation
     adapter, not the public registry.
6. Move heavy API router logic.
   - Move `_merge_cross_event_telemetry()` out of `api/routers/analysis.py`.
   - Put analysis/data transforms in core service modules.
7. Cache/data performance work.
   - Avoid repeated glob scans.
   - Avoid loading large JSON/pickle files on the UI thread.
   - Add downsampling for chart data before it reaches the UI.

## Blocking/Hang Rules

- No `requests.*` in GUI modules after migration.
- No `QApplication.processEvents()` as a loading strategy.
- No `worker.wait()` without a short timeout and cancellation state.
- No unbounded `while True` loops without a stop flag and sleep/timeout.
- All local long-running jobs need a request id, state, timeout, and cancel path.

## First Modules To Migrate

Start with high-risk modules that currently do blocking API-style work:

- `modules/gui/all_drivers/brake/brake_all_laps_loader.py`
- `modules/gui/all_drivers/brake/brake_chart_data_loader.py`
- `modules/gui/all_drivers/acceleration/acceleration_chart_data_loader.py`
- `modules/gui/telemetry_analysis_mdi.py`

## API Status

The API is not needed for the final local desktop flow. Keep it temporarily as
an optional compatibility adapter while the GUI still imports API health/runtime
workers. After migration, the `api/` package can either be removed or moved into
an optional plugin/server package.
