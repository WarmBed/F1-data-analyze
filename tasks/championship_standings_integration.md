# Championship Standings Integration Task

## Objective
- Introduce CLI function 97 to deliver driver and constructor standings with JSON freshness control.
- Mirror the architecture and data flow established by function 99, including smart reuse of cached JSON files and GUI provider wiring.
- Provide GUI access using API-only mode with local JSON fallback, ensuring multilingual readiness.

## Scope Checklist
- [x] Study existing season calendar (function 99) CLI implementation and GUI provider patterns.
- [ ] Confirm CLI standings analyzer behaviour and JSON output structure.
- [ ] Implement GUI standings provider with API fetch, JSON fallback, and caching.
- [ ] Wire provider into main window utilities for reuse across modules.
- [ ] Add automated tests covering provider behaviour and CLI freshness logic.
- [ ] Update documentation and produce comparison report between functions 97 and 99.

## Risks and Mitigations
- **API downtime**: rely on local JSON fallback and surface clear error messages via provider exceptions.
- **Data format drift**: enforce schema validation during provider transformation and expand tests with representative payloads.
- **GUI i18n compliance**: wrap new user-visible strings with `tr()` and verify no emoji usage.

## Testing Plan
1. Run targeted pytest modules:
   - `tests/test_championship_standings_analysis.py`
   - New GUI provider tests once added.
2. Manual verification steps:
   - Trigger function 97 through CLI to generate JSON and confirm timestamp handling.
   - Launch GUI in development mode to ensure provider loads standings without AttributeError.
3. Regression guard:
   - Re-run season calendar and team colour provider tests to ensure no unintended coupling.

## Progress Log
- 2025-10-09: Task file created, baseline checklist imported.
