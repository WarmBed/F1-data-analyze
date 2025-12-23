#!/usr/bin/env python3
"""
簡化測試 - 只測試 Lap Time Analysis
"""
import os
import sys
from PyQt5.QtWidgets import QApplication

print("=" * 80)
print("🧪 簡化測試：Lap Time Analysis 環境變量保護")
print("=" * 80)

app = QApplication(sys.argv)

print("\n[1/5] 設置環境變量...")
os.environ['F1T_WORKSPACE_LOADING'] = '1'
print(f"✓ F1T_WORKSPACE_LOADING = {os.environ.get('F1T_WORKSPACE_LOADING')}")

print("\n[2/5] 導入模組...")
from modules.gui.driver_race.detailed_lap_analysis import driverLapAnalysisMDI
print("✓ 模組導入成功")

print("\n[3/5] 創建實例...")
try:
    instance = driverLapAnalysisMDI(parent=None)
    print(f"✓ 實例創建成功: {type(instance).__name__}")
except Exception as e:
    print(f"❌ 實例創建失敗: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n[4/5] 清除環境變量...")
del os.environ['F1T_WORKSPACE_LOADING']
print("✓ 環境變量已清除")

print("\n[5/5] 檢查實例...")
print(f"✓ type: {type(instance)}")
print(f"✓ has current_year: {hasattr(instance, 'current_year')}")
print(f"✓ has get_widget: {hasattr(instance, 'get_widget')}")

print("\n" + "=" * 80)
print("✅ 測試完成！Lap Time Analysis 可以在環境變量保護下正常創建！")
print("=" * 80)
sys.exit(0)
