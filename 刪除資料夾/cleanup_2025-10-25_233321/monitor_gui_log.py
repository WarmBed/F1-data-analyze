#!/usr/bin/env python3
"""Monitor GUI log for Season Progress debug output"""
import time
from pathlib import Path

log_file = Path("logs/f1_gui_2025-10-25.log")

print("Monitoring GUI log for Season Progress activity...")
print("Please start GUI and open Season Progress window")
print("-" * 80)

# Get current position
if log_file.exists():
    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
        f.seek(0, 2)  # Go to end
        current_pos = f.tell()
else:
    current_pos = 0
    print("Waiting for log file to be created...")

try:
    while True:
        if log_file.exists():
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(current_pos)
                new_lines = f.readlines()
                current_pos = f.tell()
                
                for line in new_lines:
                    if any(keyword in line for keyword in [
                        "SEASON_PROGRESS",
                        "season_progress",
                        "Calendar:",
                        "calendar",
                        "populate_data"
                    ]):
                        print(line.rstrip())
        
        time.sleep(0.5)
        
except KeyboardInterrupt:
    print("\n\nMonitoring stopped")
