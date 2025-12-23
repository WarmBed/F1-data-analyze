"""測試直接導入 f1_api_downloader"""
import sys
print("Python version:", sys.version)

print("1. Testing direct import of f1_api_downloader.py...")
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "f1_api_downloader",
        r"c:\Users\mike2\OneDrive\Code\F1-data-analyze\modules\gui\live_timing\core\f1_api_downloader.py"
    )
    module = importlib.util.module_from_spec(spec)
    print("   module_from_spec OK, now loading...")
    spec.loader.exec_module(module)
    print("   exec_module OK")
    print(f"   F1APIDownloader class: {module.F1APIDownloader}")
except Exception as e:
    import traceback
    print(f"   ERROR: {e}")
    traceback.print_exc()
