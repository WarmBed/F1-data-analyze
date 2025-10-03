# Season Calendar Race Combo Fix

## Objective
Ensure the GUI race selector always populates with available events, even when no races have been completed yet, by surfacing upcoming events fetched from function 99.

## Scope & Deliverables
- Update main toolbar race/session combos to display upcoming events with clear labeling while preserving completed ones.
- Align pop-out windows and settings dialog with the new event presentation and selection behavior.
- Maintain existing provider contract (`SeasonCalendarProvider`) and verify no regression in cached data loading.

## Implementation Checklist
- [x] Partition season events into completed and upcoming groups before populating combo boxes.
- [x] Add user-facing indicators for upcoming events and ensure mapping back to canonical race keys.
- [x] Update auxiliary mappings (`_race_event_lookup`, `_display_to_race_key`) to work with annotated labels.
- [x] Mirror the updated formatting logic in pop-out windows and the settings dialog.
- [x] Prefer first completed event when available; fall back to upcoming events otherwise.
- [x] Guard against empty payloads and retain placeholder messaging only when absolutely no events are returned.

## Validation Plan
- Manually switch between years (e.g., 2024–2025) with limited completed races and confirm race combo never shows `[無已完成賽事]` when events exist.
- Verify session combo defaults gracefully for upcoming events (falls back to FP/Q/R list when no past sessions).
- [x] Run targeted unit tests: `pytest tests/test_season_calendar_provider.py -v`.
