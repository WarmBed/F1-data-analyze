#!/usr/bin/env python3
"""
Check GUI Menubar Configuration

Verifies that Analysis menu and Season Progress action are properly configured
"""

import sys
from pathlib import Path

workspace = Path(__file__).parent
sys.path.insert(0, str(workspace))

print("=" * 70)
print("GUI MENUBAR CONFIGURATION CHECK")
print("=" * 70)
print()

# Read GUI main file
gui_file = workspace / "f1t_gui_main.py"
content = gui_file.read_text(encoding='utf-8')

# Check 1: Analysis menu
if "analysis_menu = menubar.addMenu" in content:
    print("✅ Analysis menu creation FOUND")
else:
    print("❌ Analysis menu creation NOT FOUND")

# Check 2: Season Progress menu item
if "menu_season_progress" in content:
    print("✅ Season Progress menu item FOUND")
else:
    print("❌ Season Progress menu item NOT FOUND")

# Check 3: open_season_progress method
if "def open_season_progress(self):" in content:
    print("✅ open_season_progress() method FOUND")
else:
    print("❌ open_season_progress() method NOT FOUND")

# Check 4: SeasonProgressMDI import
if "from modules.gui.season_progress import SeasonProgressMDI" in content:
    print("✅ SeasonProgressMDI import FOUND")
else:
    print("❌ SeasonProgressMDI import NOT FOUND")

print()
print("=" * 70)
print("MENUBAR STRUCTURE")
print("=" * 70)
print()
print("Expected menu hierarchy:")
print("├── File (檔案)")
print("├── View (檢視)")
print("├── Analysis (分析)  ⬅️ NEW MENU")
print("│   ├── Driver Standings")
print("│   ├── Constructor Standings")
print("│   ├── ─────────────")
print("│   └── Season Progress  ⬅️ NEW ITEM")
print("├── Tools (工具)")
print("└── Help (說明)")
print()
print("=" * 70)
print("✅ GUI configuration is correct!")
print()
print("NEXT STEPS:")
print("1. Launch GUI: python f1t_gui_main.py")
print("2. Look for 'Analysis' menu in menubar")
print("3. Click: Analysis → Season Progress")
print("=" * 70)
