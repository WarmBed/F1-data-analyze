"""
直接調用 CLI 模組進行測試
"""
import sys
sys.path.insert(0, '.')

from CLI_modules.cli.core.data_loader import F1DataLoader
from CLI_modules.cli.analyzer.two_driver_telemetry_comparison_fixed import TwoDriverTelemetryComparisonAnalyzer

# 創建數據載入器
print("=" * 80)
print("🔧 初始化數據載入器...")
print("=" * 80)

data_loader = F1DataLoader(
    year=2024,
    race="Japan",
    session="R",
    enable_cache=True
)

# 載入會話數據
print("\n載入會話數據...")
data_loader.load_session_data()

# 創建分析器
print("\n創建雙車手遙測比較分析器...")
analyzer = TwoDriverTelemetryComparisonAnalyzer(
    data_loader=data_loader,
    year=2024,
    race="Japan",
    session="R",
    cache_enabled=True
)

# 執行分析
print("\n" + "=" * 80)
print("🚀 執行分析...")
print("=" * 80)

result = analyzer.analyze(
    driver1="VER",
    driver2="LEC",
    lap_number=1,
    show_detailed_output=False  # 關閉詳細輸出以減少干擾
)

if result:
    print("\n✅ 分析完成!")
    
    # 檢查是否有原始遙測數據
    if '_raw_telemetry1' in result:
        print("✅ 結果包含 _raw_telemetry1")
        print(f"   列: {list(result['_raw_telemetry1'].columns)}")
        print(f"   行數: {len(result['_raw_telemetry1'])}")
    else:
        print("❌ 結果不包含 _raw_telemetry1")
    
    if '_raw_telemetry2' in result:
        print("✅ 結果包含 _raw_telemetry2")
        print(f"   列: {list(result['_raw_telemetry2'].columns)}")
        print(f"   行數: {len(result['_raw_telemetry2'])}")
    else:
        print("❌ 結果不包含 _raw_telemetry2")
    
    # 測試時間序列提取
    print("\n" + "=" * 80)
    print("🔍 測試時間序列提取...")
    print("=" * 80)
    
    time_series = analyzer._extract_time_series_from_telemetry(result, "VER", "LEC")
    
    if time_series:
        print("\n✅ 時間序列提取成功!")
        print(f"   時間序列鍵: {list(time_series.keys())}")
        
        if 'driver1' in time_series:
            driver1_data = time_series['driver1']
            print(f"\n   driver1 鍵: {list(driver1_data.keys())}")
            if 'time_seconds' in driver1_data:
                print(f"   ✅ driver1 有 time_seconds: {len(driver1_data['time_seconds'])} 個數據點")
                print(f"   時間參考: {driver1_data.get('time_reference', 'Unknown')}")
                # 顯示前 5 個時間值
                time_data = driver1_data['time_seconds']
                sample_time = [t for t in time_data[:5] if t is not None]
                print(f"   樣本時間: {sample_time}")
            else:
                print(f"   ❌ driver1 沒有 time_seconds")
        
        if 'driver2' in time_series:
            driver2_data = time_series['driver2']
            print(f"\n   driver2 鍵: {list(driver2_data.keys())}")
            if 'time_seconds' in driver2_data:
                print(f"   ✅ driver2 有 time_seconds: {len(driver2_data['time_seconds'])} 個數據點")
                print(f"   時間參考: {driver2_data.get('time_reference', 'Unknown')}")
                # 顯示前 5 個時間值
                time_data = driver2_data['time_seconds']
                sample_time = [t for t in time_data[:5] if t is not None]
                print(f"   樣本時間: {sample_time}")
            else:
                print(f"   ❌ driver2 沒有 time_seconds")
    else:
        print("\n❌ 時間序列提取失敗（返回 None）")
else:
    print("\n❌ 分析失敗!")
