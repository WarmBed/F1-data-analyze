# Detailed Lap Analysis Reorganization Task

## 🎯 Objective
- Relocate the legacy `modules/gui/driverLap_analysis/` package into `modules/gui/driver_race/detailed_lap_analysis/` so every GUI module under the driver race namespace follows the API-ONLY architecture.
- Ensure all imports, tests, and runtime hooks reference the new package path while keeping backwards compatibility for existing feature flags.

## ✅ Scope
- Migrate `driverlap_analysis_module.py`, `driverlap_analysis_mdi.py`, dialog helpers, and related widgets into `driver_race/detailed_lap_analysis`.
- Remove the deprecated `modules/gui/driverLap_analysis/` folder once consumers point to the new namespace.
- Update GUI entrypoints, manual test harnesses, and regression scripts to target the new module path.
- Verify API-ONLY behaviour remains intact (no CLI auto-trigger) after the move.

## 🛠️ Task Checklist
- [x] Copy or merge any missing files from `driverLap_analysis` into `driver_race/detailed_lap_analysis`.
- [x] Adjust relative imports to use the driver_race namespace (e.g., `from ...interfaces.analysis_module import IAnalysisModule`).
- [x] Update all references (`f1t_gui_main.py`, tests, docs) from `modules.gui.driverLap_analysis` to `modules.gui.driver_race.detailed_lap_analysis`.
- [x] Retire the old `modules/gui/driverLap_analysis/` directory by converting files into ImportError sentinels that direct consumers to the new path.
- [x] Run targeted validations (py_compile + smoke PyTests) to confirm the GUI module still loads under API-ONLY mode.

## 🔍 Validation Plan
- `python -m py_compile modules/gui/driver_race/detailed_lap_analysis/driverlap_analysis_module.py`
- `python -m py_compile modules/gui/driver_race/detailed_lap_analysis/driverlap_analysis_mdi.py`
- `python -m pytest tests/manual -k detailed_lap --maxfail=1` *(manual harness should import the new path without ImportError)*
- Optional: Launch GUI via task `🎯 執行 F1T GUI 主程式` and open "Detailed Lap Analysis" window to confirm the module renders correctly.

## 📎 Notes
- Preserve API-ONLY messaging inside the data loader; do not re-enable CLI generation hooks.
- Keep translated labels and GUI strings unchanged; this task focuses solely on module placement and wiring.
- Legacy `modules/gui/driverLap_analysis/` now raises `ImportError` immediately to prevent accidental usage and to point developers to the driver_race namespace.
