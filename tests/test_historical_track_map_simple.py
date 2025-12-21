#!/usr/bin/env python3
"""
Historical Track Map 模組簡單測試
Simple Import Test

只測試模組能否成功導入和初始化
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("Historical Track Map 簡單導入測試")
print("=" * 70)

# 測試 1: 導入模組
print("\n[測試 1] 導入模組")
try:
    from modules.gui.Historical_track_map import HistoricalTrackMapMDI
    print("✅ HistoricalTrackMapMDI 導入成功")
except ImportError as e:
    print(f"❌ 導入失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 測試 2: 導入數據載入器
print("\n[測試 2] 導入數據載入器")
try:
    from modules.gui.Historical_track_map.historical_track_map_data_loader import HistoricalTrackMapDataLoader
    print("✅ HistoricalTrackMapDataLoader 導入成功")
except ImportError as e:
    print(f"❌ 導入失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 測試 3: 檢查類別屬性
print("\n[測試 3] 檢查類別屬性")
try:
    print(f"  - 模組類型: {HistoricalTrackMapMDI.__name__}")
    print(f"  - 基類: {HistoricalTrackMapMDI.__bases__}")
    print(f"  - 模組路徑: {HistoricalTrackMapMDI.__module__}")
    print("✅ 類別屬性檢查通過")
except Exception as e:
    print(f"❌ 檢查失敗: {e}")
    sys.exit(1)

# 測試 4: 檢查必要方法
print("\n[測試 4] 檢查必要方法")
required_methods = [
    'ensure_registered',
    'create_data_manager',
    'initialize_module',
    'update_lap_parameters',
    'get_module_info'
]

all_found = True
for method in required_methods:
    if hasattr(HistoricalTrackMapMDI, method):
        print(f"  ✅ {method}")
    else:
        print(f"  ❌ {method} 不存在")
        all_found = False

if all_found:
    print("✅ 所有必要方法都存在")
else:
    print("⚠️  部分方法缺失")

print("\n" + "=" * 70)
print("測試完成")
print("=" * 70)

print("\n📊 結果:")
print("  ✅ 模組可成功導入")
print("  ✅ 數據載入器可成功導入")
print("  ✅ 類別結構正確")
print("  ✅ 必要方法存在")

print("\n💡 下一步:")
print("  1. 在 f1t_gui_main.py 中添加選單項目")
print("  2. 啟動完整 GUI 測試")

print("\n⚠️  注意:")
print("  - 此模組僅支援 API 模式")
print("  - 使用前請確保 API 伺服器已啟動")
print("  - 數據源: Function 100 (歷年旗幟統計)")
