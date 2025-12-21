#!/usr/bin/env python3
"""
F1T Batch Generator GUI 啟動器
Quick launcher for Batch Data Generator GUI
"""

import sys
import subprocess
from pathlib import Path

# 獲取專案根目錄
PROJECT_ROOT = Path(__file__).parent

# 啟動 GUI
gui_script = PROJECT_ROOT / "batch_generator_gui.py"

if gui_script.exists():
    print("🚀 Launching F1T Batch Generator GUI...")
    subprocess.run([sys.executable, str(gui_script)])
else:
    print(f"❌ Error: GUI script not found at {gui_script}")
    sys.exit(1)
