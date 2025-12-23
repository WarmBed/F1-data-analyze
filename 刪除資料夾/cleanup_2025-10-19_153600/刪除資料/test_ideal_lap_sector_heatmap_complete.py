#!/usr/bin/env python3
"""
完整測試: Ideal Lap Sector Heatmap Widget 整合
==============================================

測試階段:
1. Import 測試
2. Widget 方法驗證
3. MDI 初始化
4. 真實數據載入
5. 功能測試
"""

from PyQt5.QtWidgets import QApplication
import sys
import json
from pathlib import Path
import pandas as pd

app = QApplication(sys.argv)

print("=" * 70)
print("Ideal Lap Sector Heatmap - 完整整合測試")
print("=" * 70)

# ------------------------------------------------------------------ #
# 階段 1: Import 測試
# ------------------------------------------------------------------ #
print("\n[測試 1/6] 檢查 Widget Import...")
try:
    from modules.gui.ideal_lap_analysis.ideal_lap_sector_heatmap.ideal_lap_sector_heatmap_widget import IdealLapSectorHeatmapWidget
    print("✅ Widget 類別導入成功")
except Exception as e:
    print(f"❌ Widget 導入失敗: {e}")
    sys.exit(1)

# ------------------------------------------------------------------ #
# 階段 2: Widget 方法驗證
# ------------------------------------------------------------------ #
print("\n[測試 2/6] 檢查 Widget 方法...")
try:
    widget = IdealLapSectorHeatmapWidget()
    required_methods = [
        'set_data',
        'render_heatmap',
        'clear_data',
        'get_current_data',
        'save_plot',
        'set_highlight_options'
    ]
    
    for method in required_methods:
        if not hasattr(widget, method):
            raise AttributeError(f"缺少方法: {method}")
        print(f"  ✅ {method}")
    
    print("✅ 所有必需方法存在")
except Exception as e:
    print(f"❌ 方法驗證失敗: {e}")
    sys.exit(1)

# ------------------------------------------------------------------ #
# 階段 3: MDI Import 測試
# ------------------------------------------------------------------ #
print("\n[測試 3/6] 檢查 MDI Import...")
try:
    from modules.gui.ideal_lap_analysis.ideal_lap_sector_heatmap.ideal_lap_sector_heatmap_mdi import IdealLapSectorHeatmapMDI
    print("✅ MDI 類別導入成功")
except Exception as e:
    print(f"❌ MDI 導入失敗: {e}")
    sys.exit(1)

# ------------------------------------------------------------------ #
# 階段 4: Data Loader 測試
# ------------------------------------------------------------------ #
print("\n[測試 4/6] 檢查 Data Loader...")
try:
    from modules.gui.ideal_lap_analysis.ideal_lap_sector_heatmap.ideal_lap_sector_heatmap_data_loader import IdealLapSectorHeatmapDataLoader
    print("✅ Data Loader 導入成功")
except Exception as e:
    print(f"❌ Data Loader 導入失敗: {e}")
    sys.exit(1)

# ------------------------------------------------------------------ #
# 階段 5: MDI 初始化測試
# ------------------------------------------------------------------ #
print("\n[測試 5/6] 測試 MDI 初始化...")
try:
    mdi = IdealLapSectorHeatmapMDI()
    print(f"  ✅ MDI 建立成功")
    print(f"  ✅ Chart Widget 類型: {type(mdi.chart_widget).__name__}")
    print(f"  ✅ Data Manager 類型: {type(mdi.data_manager).__name__}")
    print(f"  ✅ Analysis Type: {mdi.analysis_type}")
except Exception as e:
    print(f"❌ MDI 初始化失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ------------------------------------------------------------------ #
# 階段 6: 真實數據載入測試
# ------------------------------------------------------------------ #
print("\n[測試 6/6] 測試真實數據載入...")

json_path = Path("json/ideal_lap_ranking_2025_Japan_R.json")
if not json_path.exists():
    print(f"⚠️  JSON 檔案不存在: {json_path}")
    print("   跳過數據載入測試")
else:
    try:
        # 讀取 JSON
        with open(json_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        ranking = raw_data.get('analysis_result', {}).get('ranking', [])
        print(f"  ✅ JSON 載入成功: {len(ranking)} 位車手")
        
        # 模擬 Data Loader 的輸出格式
        driver_order = [entry['driver'] for entry in ranking[:20]]
        
        # 建立 DataFrame
        sector_data = {}
        for entry in ranking[:20]:
            driver = entry['driver']
            sector_breakdown = entry.get('sector_breakdown', {})
            
            s1 = sector_breakdown.get('sector_1', {}).get('time')
            s2 = sector_breakdown.get('sector_2', {}).get('time')
            s3 = sector_breakdown.get('sector_3', {}).get('time')
            
            sector_data[driver] = {
                'S1': s1 if s1 is not None else float('nan'),
                'S2': s2 if s2 is not None else float('nan'),
                'S3': s3 if s3 is not None else float('nan')
            }
        
        df = pd.DataFrame(sector_data)
        
        # 建立 payload
        payload = {
            "driver_order": driver_order,
            "sector_matrix": df,
            "sector_summary": {},
            "cell_details": {},
            "driver_best_map": {}
        }
        
        # 測試 set_data
        new_widget = IdealLapSectorHeatmapWidget()
        new_widget.set_data(payload)
        print(f"  ✅ set_data() 執行成功")
        print(f"  ✅ Widget drivers: {len(new_widget.drivers)} 位")
        print(f"  ✅ Widget sector_data: {len(new_widget.sector_data)} 筆")
        
        # 測試 render_heatmap
        new_widget.render_heatmap(driver_order)
        print(f"  ✅ render_heatmap() 執行成功")
        
        # 測試 get_current_data
        current_data = new_widget.get_current_data()
        print(f"  ✅ get_current_data() 返回: {list(current_data.keys())}")
        
    except Exception as e:
        print(f"❌ 數據載入測試失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

print("\n" + "=" * 70)
print("🎉 所有測試通過！模組整合完成")
print("=" * 70)
print("\n下一步: 啟動 GUI 測試選單功能")
print("  命令: python f1t_gui_main.py")
print("  路徑: Ideal Lap Analysis → Ideal Lap Sector Heatmap")
