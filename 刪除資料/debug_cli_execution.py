"""
Debug CLI execution issues - Capture all exceptions and output
"""
import sys
import traceback

# Set command line arguments
sys.argv = ["f1_analysis_modular_main.py", "-f", "53", "-y", "2023", "-r", "Japan", "-s", "R"]

print("[DEBUG] Starting main()")
print(f"[DEBUG] sys.argv = {sys.argv}")

try:
    # Import and execute main
    print("[DEBUG] Attempting to import main...")
    from f1_analysis_modular_main import main
    print("[DEBUG] main() imported successfully")
    
    print("[DEBUG] Executing main()...")
    result = main()
    print(f"[DEBUG] main() completed, exit code: {result}")
    
except SystemExit as e:
    print(f"[DEBUG] SystemExit exception: {e.code}")
    traceback.print_exc()
    
except Exception as e:
    print(f"[DEBUG] Caught exception: {type(e).__name__}: {e}")
    traceback.print_exc()
    
except BaseException as e:
    print(f"[DEBUG] Caught BaseException: {type(e).__name__}: {e}")
    traceback.print_exc()

print("[DEBUG] Script execution complete")
