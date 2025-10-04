# Boxplot & Detailed Lap Filters Update

## Objectives
- Ensure Lap Time Box Plot respects global pit/yellow flag filters from System Settings.
- Apply the same filtering rules to the driver detailed lap analysis chart without altering the UI.
- Centralize caution (yellow flag / SC / VSC) detection logic for reuse across widgets.

## Progress Checklist
- [x] Audit existing widgets and settings interactions.
- [x] Catalogue available smart marker fields and track status codes.
- [x] Implement shared caution detection helpers for lap processing.
- [x] Integrate yellow flag filtering into Lap Time Box Plot data pipeline.
- [x] Integrate yellow flag filtering into detailed lap chart series generation.
- [x] Validate updates via automated tests (no test cases collected) and document manual follow-up steps.

## Test Plan
- `python -m pytest test_boxplot_dataload.py test_boxplot_mdi_full.py test_data_flow_v2.py -v`
- Manual GUI smoke: load detailed lap analysis module, toggle System Settings filters, confirm charts update.

## Notes
- Unknown `track_status_code` values containing digits {2,3,4,5,6,7} are treated as caution conditions alongside explicit incident types.
- Current pytest scripts for box plot/detailed lap are CLI drivers without assertions; automated run completes with "no tests collected".
- Shared helpers live in `modules/gui/driver_race/detailed_lap_analysis/lap_filter_utils.py` for future reuse.
