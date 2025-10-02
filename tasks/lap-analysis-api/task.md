# Lap Analysis API Integration

## 🎯 Goal
- Rework the Lap Analysis telemetry loaders to use the REST API (Function 13) as the primary data source.
- Maintain CLI/JSON fallback for offline resilience while persisting API responses to the local cache structure.
- Extend the API stack to accept lap selection parameters required by the GUI.

## ✅ Deliverables
- Updated API request/response models, router parameters, and function specs to support `lap`, `lap1`, `lap2` for telemetry comparison.
- Telemetry loader (and dependents) updated to call the API first, with new worker, error handling, and persistence logic.
- Tasks/tests or scripts validating the API flow (syntax/build checks at minimum).

## 📋 Work Items
- [x] Update `AnalysisRequest` / FastAPI router signatures for lap arguments.
- [x] Extend `FunctionSpec` for Function 13 with lap parameter mapping.
- [x] Implement API worker + fallback orchestration in `TelemetryDataLoader`.
- [x] Persist API payloads into `json/` cache for offline reuse.
- [x] Adjust or add tests / compile checks.
- [x] Document assumptions & toggles (env vars) in task notes or final summary.

## 🧪 Test Plan
1. Run targeted syntax compilation:
   - `python -m compileall api/modules/gui/lap_analysis/telemetry_data_loader_base.py`
2. Manual API smoke test (requires running `refactored_api.py`):
   - POST `/api/v2/analysis/execute?function_id=13&year=2025&race=Japan&session=R&driver1=VER&driver2=LEC&lap1=1&lap2=1`
3. Launch GUI Lap Analysis module, confirm data arrives via API and JSON fallback works when the API is disabled.

---
Notes: Respect existing environment flags (`F1_API_BASE_URL`, etc.). Introduce new toggles if necessary for telemetry comparison fallback control.
- Telemetry loader honors `F1T_ALLOW_TELEMETRY_JSON_FALLBACK` (default `False`) for CLI/json fallback.
- API timeout remains configurable via `F1_API_TIMEOUT` and base URL via `F1_API_BASE_URL`.
