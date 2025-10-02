# Driver Race Analysis Options Integration

## 🎯 Goal
- Align the Detailed Lap Analysis workflow with the Lap Analysis option dialog experience.
- Group the detailed lap and lap time box plot modules under a unified `driver_race` package structure.

## ✅ Deliverables
- Prompt the user with a lap-analysis-style dialog before launching any driver lap related modules.
- Allow choosing between the detailed lap table and the lap time box plot views (support multi-selection).
- Relocate existing `driverLap_analysis` and `lap_box_plot_analysis` modules into a new consolidated folder.
- Update imports and GUI wiring to match the new structure.

## 🛠️ Task Checklist
- [ ] Create the `modules/gui/driver_race/` package with subpackages for detailed lap and box plot analyses.
- [ ] Move existing driver lap and box plot module files into the new structure and fix relative imports.
- [ ] Update GUI factory logic and menu handling to use the reorganised modules.
- [ ] Hook the new options dialog into the detailed lap launch flow, mirroring Lap Analysis.
- [ ] Ensure manual/automated tests import the relocated modules correctly.

## 🧪 Test Plan
- [ ] `python -m compileall f1t_gui_main.py modules/gui/driver_race tests/manual`
- [ ] Manual sanity: launch Detailed Lap Analysis from the GUI, choose each option individually and together.
- [ ] Manual sanity: verify lap time box plot still renders with data for a known session.

## 📎 Notes
- Maintain compatibility with the UniversalAnalysisMDI/UniversalDataLoader architecture.
- Follow the no-simulated-data policy; rely on existing API/JSON fallbacks.
- All terminal commands must use PowerShell syntax if executed.
