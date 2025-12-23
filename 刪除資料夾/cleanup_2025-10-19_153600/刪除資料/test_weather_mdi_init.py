#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 WeatherTimelineMDI 的建構函式呼叫
"""

import sys
import os

# 設置 UTF-8 輸出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from PyQt5.QtWidgets import QApplication

# 清除所有 __pycache__
import os
import shutil

def clear_pycache(root_dir):
    """清除所有 Python 快取"""
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if '__pycache__' in dirnames:
            cache_dir = os.path.join(dirpath, '__pycache__')
            print(f"清除快取: {cache_dir}")
            shutil.rmtree(cache_dir, ignore_errors=True)

print("清除 Python 快取...")
clear_pycache("modules/gui/weather_timeline")
print("✅ 快取已清除\n")

# 導入模組
print("導入 WeatherTimelineMDI...")
from modules.gui.weather_timeline import WeatherTimelineMDI
print("✅ 模組導入成功\n")

# 檢查建構函式簽名
import inspect
sig = inspect.signature(WeatherTimelineMDI.__init__)
print(f"建構函式簽名: {sig}")
print(f"參數列表:")
for param_name, param in sig.parameters.items():
    if param_name != 'self':
        print(f"  - {param_name}: {param.annotation if param.annotation != inspect.Parameter.empty else 'Any'}")
print()

# 測試不同的呼叫方式
app = QApplication(sys.argv)

print("測試 1: 使用 event 參數")
try:
    mdi1 = WeatherTimelineMDI(year="2025", event="Singapore")
    print("✅ 成功: event='Singapore'")
    print(f"   mdi.year = {mdi1.year}")
    print(f"   mdi.event = {mdi1.event}\n")
except TypeError as e:
    print(f"❌ 失敗: {e}\n")

print("測試 2: 使用位置參數")
try:
    mdi2 = WeatherTimelineMDI("2025", "Japan")
    print("✅ 成功: ('2025', 'Japan')")
    print(f"   mdi.year = {mdi2.year}")
    print(f"   mdi.event = {mdi2.event}\n")
except TypeError as e:
    print(f"❌ 失敗: {e}\n")

print("測試 3: 錯誤參數 event_name")
try:
    mdi3 = WeatherTimelineMDI(year="2025", event_name="Singapore")
    print("❌ 不應該成功: event_name 參數\n")
except TypeError as e:
    print(f"✅ 正確拒絕: {e}\n")

print("測試 4: 錯誤參數 race")
try:
    mdi4 = WeatherTimelineMDI(year="2025", race="Singapore")
    print("❌ 不應該成功: race 參數\n")
except TypeError as e:
    print(f"✅ 正確拒絕: {e}\n")

print("=" * 60)
print("結論: 正確的呼叫方式是:")
print("  WeatherTimelineMDI(year='2025', event='Singapore')")
print("  或")
print("  WeatherTimelineMDI('2025', 'Singapore')")
print("=" * 60)
