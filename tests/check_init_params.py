#!/usr/bin/env python3
"""快速檢查 StyleHMainWindow 參數"""
import inspect
from f1t_gui_main import StyleHMainWindow

sig = inspect.signature(StyleHMainWindow.__init__)
params = list(sig.parameters.keys())

print("StyleHMainWindow.__init__ 參數:")
for param in params:
    print(f"  - {param}")

if 'progress_callback' in params:
    print("\n✅ progress_callback 參數存在")
else:
    print("\n❌ progress_callback 參數缺失")
