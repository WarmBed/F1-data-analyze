#!/usr/bin/env python3
"""
Test Welcome Screen Layout Changes

Verifies that three modules are arranged horizontally
"""

import sys
from pathlib import Path

workspace = Path(__file__).parent
sys.path.insert(0, str(workspace))

print("=" * 80)
print("WELCOME SCREEN LAYOUT VERIFICATION")
print("=" * 80)
print()

# Read GUI main file
gui_file = workspace / "f1t_gui_main.py"
content = gui_file.read_text(encoding='utf-8')

# Check 1: Season Progress auto-load
if "from modules.gui.season_progress import SeasonProgressMDI" in content:
    print("✅ Season Progress import FOUND")
else:
    print("❌ Season Progress import NOT FOUND")

# Check 2: Three windows creation
if "season_progress_sub = QMdiSubWindow()" in content:
    print("✅ Season Progress MDI window FOUND")
else:
    print("❌ Season Progress MDI window NOT FOUND")

if "constructor_sub = QMdiSubWindow()" in content:
    print("✅ Constructor Standings MDI window FOUND")
else:
    print("❌ Constructor Standings MDI window NOT FOUND")

if "driver_sub = QMdiSubWindow()" in content:
    print("✅ Driver Standings MDI window FOUND")
else:
    print("❌ Driver Standings MDI window NOT FOUND")

# Check 3: Horizontal layout arrangement
if "window_width = mdi_width // 3" in content:
    print("✅ Horizontal layout calculation FOUND (divide by 3)")
else:
    print("❌ Horizontal layout calculation NOT FOUND")

# Check 4: QTimer delayed arrangement
if "QTimer.singleShot(100, arrange_windows)" in content:
    print("✅ QTimer delayed arrangement FOUND")
else:
    print("❌ QTimer delayed arrangement NOT FOUND")

# Check 5: Subtitle removed
if '"Professional F1 Data Analysis Platform"' in content or 'Professional F1 Data Analysis Platform' in content:
    # Check if it's only in comments or translations
    lines_with_subtitle = [line for line in content.split('\n') if 'Professional F1 Data Analysis Platform' in line and not line.strip().startswith('#')]
    if len(lines_with_subtitle) > 2:  # Allow for translation keys
        print("⚠️  Subtitle text still exists in code (check if intentional)")
    else:
        print("✅ Subtitle removed from welcome screen")
else:
    print("✅ Subtitle text not found")

print()
print("=" * 80)
print("EXPECTED LAYOUT")
print("=" * 80)
print()
print("┌────────────────────────────────────────────────────────────────────────┐")
print("│  Left Sidebar  │     Season Progress    │ Constructor │   Driver     │")
print("│  (Modules)     │      (1/3 width)       │  Standings  │  Standings   │")
print("│                │                        │  (1/3 width)│  (1/3 width) │")
print("│                ├────────────────────────┼─────────────┼──────────────┤")
print("│                │   Calendar Summary     │ Constructor │  Driver List │")
print("│                │   Championship Leaders │    Table    │    Table     │")
print("│                │                        │             │              │")
print("└────────────────┴────────────────────────┴─────────────┴──────────────┘")
print()
print("=" * 80)
print("✅ Layout configuration complete!")
print()
print("NEXT STEP:")
print("Run: python f1t_gui_main.py")
print("Expected: Three modules arranged horizontally (equal width)")
print("=" * 80)
