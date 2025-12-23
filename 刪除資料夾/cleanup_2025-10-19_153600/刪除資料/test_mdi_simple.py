# -*- coding: utf-8 -*-
import sys
import inspect
from PyQt5.QtWidgets import QApplication

app = QApplication(sys.argv)

from modules.gui.weather_timeline import WeatherTimelineMDI

# 檢查建構函式簽名
sig = inspect.signature(WeatherTimelineMDI.__init__)
print(f"WeatherTimelineMDI.__init__ signature: {sig}")
print("\nParameters:")
for name, param in sig.parameters.items():
    if name != 'self':
        print(f"  {name}: {param.annotation if param.annotation != inspect.Parameter.empty else 'any'}")

# 測試正確呼叫
print("\nTest 1: event parameter")
try:
    mdi = WeatherTimelineMDI(year="2025", event="Singapore")
    print(f"SUCCESS: year={mdi.year}, event={mdi.event}")
except Exception as e:
    print(f"FAILED: {e}")

# 測試錯誤呼叫
print("\nTest 2: event_name parameter (should fail)")
try:
    mdi = WeatherTimelineMDI(year="2025", event_name="Singapore")
    print("FAILED: Should not accept event_name")
except TypeError as e:
    print(f"SUCCESS: Correctly rejected - {e}")

print("\nCorrect usage: WeatherTimelineMDI(year='2025', event='Singapore')")
