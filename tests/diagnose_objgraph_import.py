#!/usr/bin/env python3
"""
快速診斷 objgraph_window 導入問題
Quick diagnosis for objgraph_window import issue
"""

import sys
import os
from pathlib import Path

workspace = Path(__file__).parent
sys.path.insert(0, str(workspace))

print("=" * 80)
print("診斷 objgraph_window 導入問題")
print("=" * 80)
print()

print("[步驟 1] 測試基本模組導入...")
try:
    import objgraph
    print("[OK] objgraph 導入成功")
except Exception as e:
    print(f"[ERROR] objgraph 導入失敗: {e}")
    sys.exit(1)

print()
print("[步驟 2] 測試 PyQt5 導入...")
try:
    from PyQt5.QtWidgets import QWidget, QApplication
    from PyQt5.QtCore import QThread, pyqtSignal
    print("[OK] PyQt5 導入成功")
except Exception as e:
    print(f"[ERROR] PyQt5 導入失敗: {e}")
    sys.exit(1)

print()
print("[步驟 3] 測試 core 模組導入...")
try:
    from core.gui_i18n import tr
    print("[OK] core.gui_i18n 導入成功")
except Exception as e:
    print(f"[ERROR] core.gui_i18n 導入失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("[步驟 4] 測試 logger 導入...")
try:
    from core.logger import get_logger
    logger = get_logger("test", component="gui")
    print("[OK] core.logger 導入成功")
except Exception as e:
    print(f"[ERROR] core.logger 導入失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("[步驟 5] 讀取 objgraph_window.py 檔案內容...")
try:
    window_file = workspace / "modules" / "gui" / "diagnostics" / "objgraph_window.py"
    content = window_file.read_text(encoding='utf-8')
    print(f"[OK] 檔案大小: {len(content)} 字元")
    print(f"[OK] 檔案行數: {content.count(chr(10))} 行")
except Exception as e:
    print(f"[ERROR] 讀取檔案失敗: {e}")
    sys.exit(1)

print()
print("[步驟 6] 嘗試導入 objgraph_window 模組...")
print("   (這一步可能會卡住...)")
try:
    import modules.gui.diagnostics.objgraph_window as objgraph_window_module
    print("[OK] objgraph_window 模組導入成功")
    print(f"   模組路徑: {objgraph_window_module.__file__}")
except Exception as e:
    print(f"[ERROR] 模組導入失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("[步驟 7] 檢查類別是否存在...")
try:
    if hasattr(objgraph_window_module, 'ObjgraphDiagnosticWindow'):
        print("[OK] ObjgraphDiagnosticWindow 類別存在")
    else:
        print("[ERROR] ObjgraphDiagnosticWindow 類別不存在")
        print(f"   可用的類別: {[name for name in dir(objgraph_window_module) if not name.startswith('_')]}")
except Exception as e:
    print(f"[ERROR] 檢查失敗: {e}")
    sys.exit(1)

print()
print("=" * 80)
print("診斷完成")
print("=" * 80)
