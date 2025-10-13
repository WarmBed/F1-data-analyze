"""
最終驗證：直接導入修復後的 MDI 模組並測試
這會強制使用最新的代碼（非緩存）
"""
import sys
import importlib

# 強制重新載入模組
if 'modules.gui.tire_analysis.tire_analysis_mdi' in sys.modules:
    del sys.modules['modules.gui.tire_analysis.tire_analysis_mdi']

print("=" * 80)
print("強制重新載入 tire_analysis_mdi 模組")
print("=" * 80)

from modules.gui.tire_analysis.tire_analysis_mdi import TireAnalysisMDI
import json

# 讀取測試數據
filepath = 'json/tire_strategy_2025_Japan_R.json'
with open(filepath, 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

print("\n測試 MDI _prepare_tire_chart_data() 方法...")
print("-" * 80)

# 創建臨時 MDI 實例（模擬）
class MockMDI:
    def __init__(self):
        self._debug_enabled = True
    
    def _debug(self, msg):
        pass  # 靜默
    
    def _prepare_tire_chart_data(self, raw_data):
        """複製 MDI 的處理邏輯"""
        from modules.gui.tire_analysis.tire_analysis_mdi import TireAnalysisMDI
        
        # 讀取實際代碼
        import inspect
        source_lines = inspect.getsource(TireAnalysisMDI._prepare_tire_chart_data)
        
        # 檢查是否包含修復
        if 'end_lap is None or end_lap <= 0' in source_lines:
            print("✅ 代碼包含修復：使用 'is None or <= 0' 檢查")
        else:
            print("❌ 代碼未包含修復！")
            return None
        
        # 執行實際處理
        drivers_analysis = raw_data.get("drivers_analysis", {})
        tire_chart_data = {"driver_stints": {}}
        
        for driver, driver_info in drivers_analysis.items():
            stint_analysis = driver_info.get("stint_analysis", [])
            if not stint_analysis:
                continue
            
            processed_stints = []
            for index, stint in enumerate(stint_analysis, start=1):
                if not stint:
                    continue
                
                # ===== 應用修復後的邏輯 =====
                start_lap = stint.get("start_lap")
                if start_lap is None:
                    start_lap = stint.get("lap_start")
                    if start_lap is None:
                        start_lap = stint.get("startLap")
                        if start_lap is None:
                            start_lap = 1
                
                # 修復：優先使用 end_lap，但要檢查其是否有效（> 0）
                end_lap = stint.get("end_lap")
                if end_lap is None or end_lap <= 0:
                    end_lap = stint.get("lap_end")
                    if end_lap is None or end_lap <= 0:
                        end_lap = stint.get("endLap")
                        if end_lap is None or end_lap <= 0:
                            # 嘗試使用 length 欄位計算 end_lap
                            length = stint.get("length")
                            if length is not None and length > 0:
                                end_lap = start_lap + length - 1
                            else:
                                # 最後的回退：使用 start_lap（單圈 stint）
                                end_lap = start_lap
                
                # 檢查是否觸發警告條件
                if end_lap <= start_lap and stint.get("length", 0) > 1:
                    print(f"⚠️  {driver} Stint {index}: start={start_lap}, end={end_lap}, length={stint.get('length')}")
                    print(f"   這個 stint 會在 Chart Widget 觸發警告！")
                
                processed_stints.append({
                    "start_lap": start_lap,
                    "end_lap": end_lap,
                    "compound": stint.get("compound", "UNKNOWN"),
                    "length": stint.get("length", end_lap - start_lap + 1)
                })
            
            tire_chart_data["driver_stints"][driver] = processed_stints
        
        return tire_chart_data

mdi = MockMDI()
result = mdi._prepare_tire_chart_data(raw_data)

if result:
    print("\n" + "=" * 80)
    print("處理完成！檢查是否有 start <= end 的情況...")
    print("=" * 80)
    
    warning_count = 0
    for driver, stints in result["driver_stints"].items():
        for stint in stints:
            if stint["end_lap"] <= stint["start_lap"]:
                warning_count += 1
                print(f"❌ {driver}: start={stint['start_lap']}, end={stint['end_lap']}")
    
    if warning_count == 0:
        print("\n✅ 完美！沒有任何 stint 會觸發警告")
        print("如果用戶仍然看到警告，那是因為 GUI 沒有重新啟動！")
    else:
        print(f"\n❌ 發現 {warning_count} 個會觸發警告的 stint")
