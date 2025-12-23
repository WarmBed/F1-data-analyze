import sys, json
from CLI_modules.cli.core.compatible_data_loader import CompatibleF1DataLoader
from CLI_modules.cli.core.function_mapper import F1AnalysisFunctionMapper

year = 2025
race = "Japan"
session = "R"

loader = CompatibleF1DataLoader()
print("[RUN] Loading data...", year, race, session)
if not loader.load_race_data(year, race, session_type=session, force_reload=False):
    print("[RUN] Failed to load data (cache or network)")
    sys.exit(2)

mapper = F1AnalysisFunctionMapper(data_loader=loader)
res = mapper._execute_ideal_lap_analysis(debug=False, save_json=True)
print("[RUN] Result success:", res.get("success"))
print("[RUN] Message:", res.get("message"))
print("[RUN] Output File:", res.get("output_file"))
if res.get("success"):
    payload = res.get("data", {})
    summary = payload.get("analysis_result", {}).get("summary", {})
    print("[RUN] Summary:", summary)
