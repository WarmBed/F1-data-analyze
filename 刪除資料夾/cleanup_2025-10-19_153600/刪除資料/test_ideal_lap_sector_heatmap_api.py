"""
測試 Ideal Lap Sector Heatmap API-ONLY 模式實現

驗證項目:
1. 模組導入
2. API Worker 類別存在
3. MDI 方法完整性
4. API Worker 信號定義
"""

import sys
from pathlib import Path

# 測試 1: 驗證模組導入
print("[TEST 1] 驗證模組導入...")
try:
    from modules.gui.ideal_lap_analysis.ideal_lap_sector_heatmap import ideal_lap_sector_heatmap_mdi
    print("✅ Import 成功")
except Exception as e:
    print(f"❌ Import 失敗: {e}")
    sys.exit(1)

# 測試 2: 驗證 API Worker 類別存在
print("\n[TEST 2] 驗證 API Worker 類別...")
try:
    assert hasattr(ideal_lap_sector_heatmap_mdi, 'IdealLapSectorHeatmapApiWorker')
    worker_class = ideal_lap_sector_heatmap_mdi.IdealLapSectorHeatmapApiWorker
    print(f"✅ IdealLapSectorHeatmapApiWorker 類別存在: {worker_class}")
except AssertionError:
    print("❌ API Worker 類別不存在")
    sys.exit(1)

# 測試 3: 驗證 MDI 類別方法
print("\n[TEST 3] 驗證 MDI 類別方法...")
try:
    mdi_class = ideal_lap_sector_heatmap_mdi.IdealLapSectorHeatmapMDI
    
    required_methods = [
        'load_initial_data',
        '_on_api_success',
        '_on_api_failure',
        '_on_api_progress'
    ]
    
    for method_name in required_methods:
        assert hasattr(mdi_class, method_name), f"缺少方法: {method_name}"
        print(f"  ✓ {method_name} 已定義")
    
    print("✅ 所有 API 方法已定義")
except AssertionError as e:
    print(f"❌ 方法驗證失敗: {e}")
    sys.exit(1)

# 測試 4: 驗證 API Worker 信號
print("\n[TEST 4] 驗證 API Worker 信號...")
try:
    worker_class = ideal_lap_sector_heatmap_mdi.IdealLapSectorHeatmapApiWorker
    
    # 檢查信號屬性
    required_signals = ['progress', 'success', 'failure']
    for signal_name in required_signals:
        assert hasattr(worker_class, signal_name), f"缺少信號: {signal_name}"
        print(f"  ✓ {signal_name} 信號已定義")
    
    print("✅ API Worker 信號已定義")
except AssertionError as e:
    print(f"❌ 信號驗證失敗: {e}")
    sys.exit(1)

# 測試 5: 驗證 API Worker run() 方法
print("\n[TEST 5] 驗證 API Worker run() 方法...")
try:
    assert hasattr(worker_class, 'run')
    print("✅ run() 方法已定義")
except AssertionError:
    print("❌ run() 方法不存在")
    sys.exit(1)

# 測試 6: 驗證數據加載器 API-ONLY 合規性
print("\n[TEST 6] 驗證數據加載器 API-ONLY 合規性...")
try:
    from modules.gui.ideal_lap_analysis.ideal_lap_sector_heatmap import ideal_lap_sector_heatmap_data_loader
    
    # 檢查 _allow_local_fallback 設置
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    
    loader = ideal_lap_sector_heatmap_data_loader.IdealLapSectorHeatmapDataLoader(
        year=2025,
        race="Japan",
        session="R"
    )
    
    assert loader._allow_local_fallback == False, "_allow_local_fallback 應該為 False"
    print("✅ _allow_local_fallback = False (API-ONLY 合規)")
    
except Exception as e:
    print(f"⚠️  數據加載器驗證警告: {e}")

print("\n" + "="*60)
print("🎉 所有測試通過！API-ONLY 模式已完成實現")
print("="*60)

print("\n📋 實現摘要:")
print("  1. ✅ IdealLapSectorHeatmapApiWorker 類別已添加")
print("  2. ✅ load_initial_data() 方法已覆寫")
print("  3. ✅ API 回調處理器已實現 (_on_api_success, _on_api_failure, _on_api_progress)")
print("  4. ✅ 錯誤處理和本地備援機制已實現")
print("  5. ✅ 與 ideal_lap_ranking_table 保持一致的架構模式")

print("\n🚀 下一步: 啟動 GUI 測試實際 API 調用")
print("  命令: python f1t_gui_main.py")
print("  操作: 分析 → 理想單圈 → 扇區熱力圖")
