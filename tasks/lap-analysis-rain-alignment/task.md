# Lap Analysis Rain-Style Alignment

## 🎯 Goal
- Restructure every Lap Analysis telemetry data loader so that its runtime flow mirrors the Rain Analysis module exactly.
- Enforce API-first loading with an asynchronous worker, disable implicit JSON reads/writes unless an explicit fallback flag is enabled, and remove automatic CLI invocations in normal operation.
- Provide a controlled fallback toggle matching the rain module policies and document the new behaviour for future maintainers.

## ✅ Deliverables
- `telemetry_data_loader_base.py` updated to instantiate a QThread worker (API-first), reuse rain-style progress/status emissions, and gate any JSON/CLI fallback behind the same environment flags.
- Lap analysis wrappers (speed, rpm, gear, throttle, brake, acceleration, distance diff, speed diff) continue to call into the refactored base without additional changes.
- Updated task notes and verification logs outlining the new flow and any remaining parity gaps.

## 📋 Work Items
- [x] Introduce a `TelemetryApiWorker` mirroring `RainAnalysisApiWorker` but parameterized for function 13 comparisons.
- [x] Refactor `TelemetryDataLoader.load_telemetry_data` to skip the legacy JSON-first path and reuse the new worker.
- [x] Align fallback gating (`F1T_ALLOW_TELEMETRY_JSON_FALLBACK`) with rain module semantics; add optional helper to force local load for diagnostics.
- [x] Remove or guard automatic JSON persistence so that API responses are consumed in-memory unless fallback is explicitly enabled.
- [x] Update debug/status messaging to clarify source (API vs local fallback).
- [x] Run targeted compile or unit checks to confirm no syntax regressions.

## 🧪 Test Plan
1. `python -m compileall modules/gui/lap_analysis/telemetry_data_loader_base.py`
2. (Optional) Launch `refactored_api.py`, then trigger any lap analysis GUI module to verify it pulls data via API worker without creating JSON files.
3. Toggle `F1T_ALLOW_TELEMETRY_JSON_FALLBACK=1` and confirm that disabling the API triggers controlled fallback behaviour.
