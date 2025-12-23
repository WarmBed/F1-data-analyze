# Task: Implement CLI Function 53 - Ideal Lap Analysis (All Drivers)

## Objective
Implement the modular CLI function for the all-driver Ideal Lap Analysis described in the development document. Produce JSON output `ideal_lap_ranking_{year}_{race}_{session}.json` containing per-lap sector data, lap times, and ideal lap detail for each driver.

## Scope & Deliverables
- Modular analysis module under `CLI_modules/cli/analyzer/`.
- Integration with the CLI function mapper (function id 53).
- JSON serialization utilities and storage in `json/` folder.
- Unit/integration tests covering happy path and edge cases.

## Assumptions
- FastF1 session loading utilities available via existing helper modules.
- All-driver mode only; no driver filters.
- Valid FastF1 cache / network connectivity handled externally.

## Implementation Checklist
- [x] Create ideal lap analysis module with reusable classes/functions.
- [x] Load FastF1 session data using shared loader utilities.
- [x] Compute per-driver ideal lap metrics (per-lap sector times, fastest lap, gaps).
- [x] Build complete JSON structure per spec and save to `json/`.
- [x] Wire module into `F1AnalysisFunctionMapper` (function id 53).
- [x] Add CLI handling, ensuring parameters year/race/session only.
- [x] Implement logging and error handling consistent with other modules.
- [ ] Add automated tests (e.g., pytest) validating output structure and key values.

## Testing Plan
- Happy path: 2025 Japan Race, verifying JSON exists and contains driver entries with lap arrays and ideal_lap_detail.
- Alternative session: 2024 Bahrain Race to confirm robustness.
- Error handling: invalid race name yields graceful failure message.
- Performance: ensure processing completes within reasonable time for full grid data.

## Progress Notes
- Implemented `IdealLapAnalyzer` with JSON export and mapper integration.
- Pytest subset (`tests/test_api_only_mode.py -k "api_only_mode"`) currently fails at collection stage; requires further investigation before enabling automated coverage.

## Sign-off Criteria
- All checklist items completed.
- Tests pass locally (`python -m pytest tests/ -k "function_53"`).
- JSON output validated against documentation structure.
- No regression in existing CLI commands (spot-check run of a previous function).
