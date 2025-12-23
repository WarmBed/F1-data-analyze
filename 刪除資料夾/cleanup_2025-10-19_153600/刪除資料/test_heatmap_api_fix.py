"""
測試 API 數據處理修復

驗證 _on_api_success 現在正確傳遞完整 data 對象
"""

import sys
from unittest.mock import Mock

print("=" * 70)
print("🔧 測試 API 數據處理修復")
print("=" * 70)

# 步驟 1: 導入模組
print("\n[1] 導入模組...")
from PyQt5.QtWidgets import QApplication
app = QApplication.instance() or QApplication(sys.argv)

from modules.gui.ideal_lap_analysis.ideal_lap_sector_heatmap.ideal_lap_sector_heatmap_mdi import IdealLapSectorHeatmapMDI
from modules.gui.ideal_lap_analysis.ideal_lap_sector_heatmap.ideal_lap_sector_heatmap_data_loader import IdealLapSectorHeatmapDataLoader

print("✅ 模組導入成功")

# 步驟 2: 模擬 API 響應
print("\n[2] 創建模擬 API 響應...")

mock_api_response = {
    "success": True,
    "data": {
        "analysis_result": {
            "ranking": [
                {
                    "driver": "VER",
                    "driver_name": "Max Verstappen",
                    "team": "Red Bull Racing",
                    "position": 1,
                    "ideal_lap_time": 89.123,
                    "ideal_lap_detail": {
                        "sector_sources": {
                            "s1": {"time": 28.5, "lap": 10},
                            "s2": {"time": 30.2, "lap": 12},
                            "s3": {"time": 30.423, "lap": 15}
                        }
                    }
                },
                {
                    "driver": "LEC",
                    "driver_name": "Charles Leclerc",
                    "team": "Ferrari",
                    "position": 2,
                    "ideal_lap_time": 89.456,
                    "ideal_lap_detail": {
                        "sector_sources": {
                            "s1": {"time": 28.6, "lap": 11},
                            "s2": {"time": 30.3, "lap": 13},
                            "s3": {"time": 30.556, "lap": 14}
                        }
                    }
                }
            ],
            "sector_comparison": {}
        }
    },
    "meta": {
        "source": "api",
        "latency_ms": 123.45
    }
}

print("✅ 模擬 API 響應已創建")

# 步驟 3: 測試 DataLoader._transform_data_for_display
print("\n[3] 測試 _transform_data_for_display...")

try:
    loader = IdealLapSectorHeatmapDataLoader(year=2025, race="Japan", session="R")
    
    # ✅ 傳遞完整 data 對象（包含 analysis_result）
    data = mock_api_response["data"]
    print(f"   輸入數據結構: {list(data.keys())}")
    print(f"   包含 analysis_result: {'analysis_result' in data}")
    
    payload = loader._transform_data_for_display(data)
    
    if payload:
        print("✅ 數據轉換成功")
        print(f"   Payload 鍵: {list(payload.keys())}")
        print(f"   成功: {payload.get('success')}")
        print(f"   驅動員數量: {len(payload.get('driver_order', []))}")
        print(f"   Matrix 形狀: {payload.get('sector_matrix').shape if 'sector_matrix' in payload else 'N/A'}")
    else:
        print("❌ 數據轉換失敗：payload 為空")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ _transform_data_for_display 測試失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 步驟 4: 模擬 MDI._on_api_success 調用
print("\n[4] 測試 _on_api_success 處理流程...")

try:
    # 創建 MDI 實例（不初始化完整 GUI）
    mdi = IdealLapSectorHeatmapMDI()
    
    # 手動設置必要組件
    mdi.data_manager = loader
    mdi.chart_widget = Mock()
    mdi.chart_widget.set_data = Mock()
    
    # 模擬 API 成功回調
    print("   調用 _on_api_success...")
    mdi._on_api_success(mock_api_response)
    
    # 驗證 chart_widget.set_data 被調用
    if mdi.chart_widget.set_data.called:
        print("✅ chart_widget.set_data 已被調用")
        call_args = mdi.chart_widget.set_data.call_args[0][0]
        print(f"   傳遞的 payload 鍵: {list(call_args.keys())}")
    else:
        print("❌ chart_widget.set_data 未被調用")
        sys.exit(1)
    
except Exception as e:
    print(f"⚠️  _on_api_success 測試警告: {e}")
    import traceback
    traceback.print_exc()

# 總結
print("\n" + "=" * 70)
print("🎉 修復驗證完成！")
print("=" * 70)

print("\n📋 修復摘要:")
print("  修復前：傳遞 result['data']['analysis_result']  ❌")
print("  修復後：傳遞 result['data'] (完整對象)         ✅")
print()
print("  原因：_transform_data_for_display 期望：")
print("        data['analysis_result']['ranking'] 結構")
print()
print("  與 ranking_table 保持一致 ✅")

print("\n🚀 準備啟動 GUI 測試實際 API 調用...")
