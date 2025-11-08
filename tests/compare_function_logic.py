#!/usr/bin/env python3
"""
Function 13, 28, 54 的數據載入邏輯對比
"""

print("="*80)
print("Function 13 / 28 / 54 數據載入邏輯對比")
print("="*80)

print("\n" + "="*80)
print("Function 13: 雙車手遙測比較 (✅ 正確)")
print("="*80)
print("\n📍 function_mapper.py 調用:")
print("""
def _execute_driver_comparison(self, **kwargs):
    # 從 data_loader 獲取 year/race/session (不接受參數)
    year = getattr(self.data_loader, 'year', 2025)
    race = getattr(self.data_loader, 'race_name', 'Japan')
    session = getattr(self.data_loader, 'session_type', 'R')
    
    result = run_two_driver_telemetry_comparison_analysis(
        data_loader=self.data_loader,
        year=year,    # ✅ 從 data_loader 讀取
        race=race,    # ✅ 從 data_loader 讀取
        session=session,  # ✅ 從 data_loader 讀取
        ...
    )
""")

print("\n📍 analyzer 實現:")
print("""
class TwoDriverTelemetryComparison:
    def __init__(self, data_loader, year, race, session):
        self.data_loader = data_loader
        self.year = year       # ✅ 只用於檔案命名
        self.race = race       # ✅ 只用於檔案命名
        self.session = session # ✅ 只用於檔案命名
    
    def analyze(self, driver1, driver2, lap_number1, lap_number2):
        # ✅ 直接使用 data_loader 已載入的數據
        data = self.data_loader.get_loaded_data()
        session = data['session']  # ✅ 使用已載入的 session
        laps = data['laps']        # ✅ 使用已載入的 laps
""")

print("\n✅ 正確原因:")
print("   • Function 13 不接受 year/race/session 參數")
print("   • 它從 data_loader 讀取當前狀態作為參數")
print("   • analyzer 直接使用 data_loader 已載入的數據")
print("   • year/race/session 參數只用於檔案命名和 metadata")
print("   • ✅ 數據來源與 metadata 始終一致！")

print("\n" + "="*80)
print("Function 54: 全車手油門比例分析 (✅ 正確)")
print("="*80)
print("\n📍 function_mapper.py 調用:")
print("""
def _execute_driver_throttle_ratio(self, **kwargs):
    # 不接受 year/race/session 參數
    result = run_driver_throttle_ratio_analysis(
        data_loader=self.data_loader,  # ✅ 直接傳遞 data_loader
        threshold=...,
        coast_threshold=...,
    )
""")

print("\n📍 analyzer 實現:")
print("""
def run_driver_throttle_ratio_analysis(data_loader, threshold, ...):
    # ✅ 直接從 data_loader 提取 session 資訊
    year, race, session_label = _extract_session_identifiers(data_loader)
    
    # ✅ 直接使用 data_loader 的 laps
    laps = getattr(data_loader, "laps", None)
    
    # ✅ 從 data_loader 構建 metadata
    metadata = _build_metadata(data_loader, threshold, coast_threshold)
""")

print("\n✅ 正確原因:")
print("   • Function 54 不接受 year/race/session 參數")
print("   • 它直接從 data_loader 提取當前狀態")
print("   • 直接使用 data_loader.laps (不經過 get_loaded_data())")
print("   • metadata 從 data_loader 動態生成")
print("   • ✅ 數據來源與 metadata 始終一致！")

print("\n" + "="*80)
print("Function 28: 詳細圈速分析 (❌ 錯誤)")
print("="*80)
print("\n📍 function_mapper.py 調用:")
print("""
def execute_function_by_number(self, function_id, **kwargs):
    elif function_id in [27, 28]:
        driver = kwargs.get('driver1') or kwargs.get('driver', 'VER')
        year = kwargs.get('year', 2025)      # ❌ 從參數獲取
        race = kwargs.get('race', 'Japan')   # ❌ 從參數獲取
        session = kwargs.get('session', 'R') # ❌ 從參數獲取
        
        return self.function_mapping[function_id](year, race, session, driver, ...)
        
def _execute_driver_lap_time_analysis(self, year, race, session, driver, **kwargs):
    analyzer = SingleDriverDetailedLaptimeAnalysis(
        data_loader=self.data_loader,  # ❌ data_loader 可能載入了其他賽事
        year=year,       # ❌ 參數說 United States
        race=race,       # ❌ 參數說 United States
        session=session  # ❌ 參數說 R
    )
""")

print("\n📍 analyzer 實現:")
print("""
class SingleDriverDetailedLaptimeAnalysis:
    def __init__(self, data_loader, year, race, session):
        self.data_loader = data_loader
        self.year = year       # ❌ United States (參數)
        self.race = race       # ❌ United States (參數)
        self.session = session # ❌ R (參數)
    
    def analyze_every_lap(self, driver):
        # ❌ 直接使用 data_loader 已載入的數據 (可能是 Japan)
        data = self.data_loader.get_loaded_data()
        session = data['session']  # ❌ Japan 的 session!
        laps = data['laps']        # ❌ Japan 的 laps!
        
        # ❌ 但使用 self.year/race/session 生成檔案名和 metadata
        json_filename = f"detailed_laptime_analysis_{self.year}_{self.race}_{self.session}_all_drivers.json"
        metadata = {
            "year": self.year,       # United States
            "race": self.race,       # United States
            "session": self.session  # R
        }
""")

print("\n❌ 錯誤原因:")
print("   • Function 28 接受 year/race/session 參數（來自 GUI 或 CLI）")
print("   • 但 analyzer 直接使用 data_loader.get_loaded_data()")
print("   • data_loader 可能載入了不同賽事的數據（如 Japan）")
print("   • self.year/race/session 參數只用於:")
print("     - 生成 JSON 檔案名稱")
print("     - 生成 metadata")
print("   • ❌ 結果：檔案名說 'United States'，metadata 說 'United States'")
print("   •        但實際數據是 'Japan' 的！")

print("\n" + "="*80)
print("🔍 總結對比")
print("="*80)

print("\n✅ Function 13 & 54 (正確模式):")
print("   參數來源: data_loader.year/race/session")
print("   數據來源: data_loader.get_loaded_data() 或 data_loader.laps")
print("   特點: 參數與數據來源一致（都來自 data_loader 當前狀態）")
print("   結果: ✅ metadata 與數據內容完全匹配")

print("\n❌ Function 28 (錯誤模式):")
print("   參數來源: kwargs.get('year/race/session') (外部傳入)")
print("   數據來源: data_loader.get_loaded_data() (可能是舊數據)")
print("   特點: 參數與數據來源不一致")
print("   結果: ❌ metadata 說 'United States'，數據實際是 'Japan'")

print("\n💡 修復方案:")
print("\n方案 1: 讓 Function 28 像 Function 13/54 一樣")
print("   • 不接受 year/race/session 參數")
print("   • 從 data_loader 讀取當前狀態")
print("   • 優點：邏輯統一，永遠不會出錯")
print("   • 缺點：無法在不重新載入 data_loader 的情況下分析不同賽事")

print("\n方案 2: 添加數據驗證（推薦）")
print("   • Function 28 接收參數時檢查 data_loader 狀態")
print("   • 如果不匹配，拋出錯誤或自動重新載入")
print("   • 優點：保持靈活性，防止數據錯誤")
print("   • 缺點：需要修改 analyzer 邏輯")

print("\n方案 3: 在 function_mapper 統一處理")
print("   • execute_function_by_number() 檢查參數與 data_loader 狀態")
print("   • 不匹配時自動重新載入正確的賽事數據")
print("   • 優點：所有功能受益，架構層面解決")
print("   • 缺點：需要修改核心流程")
