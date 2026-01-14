"""測試 import 問題"""
import sys
import os

os.chdir(r"d:\OneDrive\Code\F1-data-analyze")
sys.path.insert(0, r"d:\OneDrive\Code\F1-data-analyze")

print("Step 1: Testing os, json...", flush=True)
import os
import json
print("Step 1: OK", flush=True)

print("Step 2: Testing core.logger...", flush=True)
from core.logger import get_logger
print("Step 2: OK", flush=True)

print("Step 3: Testing PyQt5...", flush=True)
from PyQt5.QtCore import QObject, pyqtSignal, QThread
print("Step 3: OK", flush=True)

print("Step 4: Testing gui_i18n manually...", flush=True)
# 直接讀取並執行 gui_i18n 的翻譯字典部分
import core.gui_i18n as gui_i18n_module
print("Step 4: OK", flush=True)

print("All imports OK!", flush=True)
