"""更詳細的導入測試"""
import sys
print("Python version:", sys.version)

print("1. Testing Path...")
from pathlib import Path
print("   OK")

print("2. Testing project_root...")
project_root = Path(__file__).resolve().parent
print(f"   project_root = {project_root}")

print("3. Testing core.logger...")
from core.logger import get_logger
print("   OK")

print("4. Testing _get_downloader import...")
try:
    from modules.gui.live_timing.core.f1_api_downloader import F1APIDownloader
    print("   F1APIDownloader import OK")
except Exception as e:
    print(f"   F1APIDownloader import ERROR: {e}")

print("5. Reading file directly...")
try:
    file_path = r"c:\Users\mike2\OneDrive\Code\F1-data-analyze\CLI_modules\cli\analyzer\live_timing_traffic_distance_analysis.py"
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # 檢查語法錯誤
    compile(content, file_path, 'exec')
    print("   Syntax OK")
except SyntaxError as e:
    print(f"   Syntax ERROR: {e}")
except Exception as e:
    print(f"   Error: {e}")

print("6. Attempting import with exec...")
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "live_timing_traffic_distance_analysis",
        r"c:\Users\mike2\OneDrive\Code\F1-data-analyze\CLI_modules\cli\analyzer\live_timing_traffic_distance_analysis.py"
    )
    module = importlib.util.module_from_spec(spec)
    print("   module_from_spec OK, now loading...")
    spec.loader.exec_module(module)
    print("   exec_module OK")
except Exception as e:
    import traceback
    print(f"   ERROR: {e}")
    traceback.print_exc()
