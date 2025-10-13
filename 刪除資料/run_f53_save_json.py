import sys, json
from CLI_modules.cli.core.compatible_data_loader import CompatibleF1DataLoader
from CLI_modules.cli.core.function_mapper import F1AnalysisFunctionMapper

year = 2023
race = "Japan"
session = "R"

loader = CompatibleF1DataLoader()
print("[SMOKE] Loading data...", year, race, session)
if not loader.load_race_data(year, race, session_type=session, force_reload=False):
    print("[SMOKE] Failed to load cached data; abort")
    sys.exit(2)

mapper = F1AnalysisFunctionMapper(data_loader=loader)
res = mapper._execute_ideal_lap_analysis(debug=False, save_json=True)
print("[SMOKE] Result success:", res.get("success"))
print("[SMOKE] Message:", res.get("message"))
print("[SMOKE] Output File:", res.get("output_file"))
