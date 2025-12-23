# Task: Enable linkage toggle support for Track Analysis module

## Summary
- implement full support for the per-window linkage toggle in the Track Analysis MDI module
- ensure `TrackMapWidget` can be disabled/enabled for linkage without unregistering from the linkage manager
- sync control panel UI states with linkage toggle and clear markers when linkage is turned off

## Acceptance Criteria
- toggling the 🔗 button on a Track Analysis window disables linkage markers and stops responding to incoming linkage signals
- re-enabling linkage restores marker visibility and linkage signal handling
- control panel checkboxes for "同步游標"/"固定游標" are disabled when linkage is off and restored when on
- all affected modules continue to load track data successfully

## Implementation Notes
- add a local linkage-enabled state to `TrackAnalysisUniversal` and propagate to `TrackMapWidget`
- extend `TrackMapWidget` with `set_linkage_enabled` and guard incoming linkage callbacks accordingly
- persist marker visibility preferences while linkage is off

## Test Plan
- manual: open Track Analysis window, toggle 🔗 off, verify markers disappear and do not reappear on external linkage events
- manual: toggle 🔗 on, confirm markers return and linkage resumes
- automated: run `pytest tests/test_gui_modules_import.py`
