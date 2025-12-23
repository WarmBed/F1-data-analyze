#!/usr/bin/env python3
"""性能分析 - Function 54 執行時間"""
import time
import warnings
import sys

warnings.filterwarnings('ignore')

# 設置路徑
sys.path.insert(0, '.')

# 計時裝飾器
def timer(name):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            print(f"⏱️  {name}: {elapsed:.3f}秒")
            return result
        return wrapper
    return decorator

# 開始總計時
total_start = time.time()

print("\n" + "="*80)
print("🔍 Function 54 性能分析 - 2025 Australia R")
print("="*80 + "\n")

# 步驟 1: 導入模組
@timer("1️⃣ 導入模組")
def import_modules():
    from CLI_modules.cli.core.compatible_data_loader import CompatibleF1DataLoader
    from CLI_modules.cli.analyzer.driver_throttle_ratio import run_driver_throttle_ratio_analysis
    return CompatibleF1DataLoader, run_driver_throttle_ratio_analysis

DataLoader, analyze_func = import_modules()

# 步驟 2: 初始化數據載入器
@timer("2️⃣ 初始化數據載入器")
def init_loader():
    return DataLoader()

loader = init_loader()

# 步驟 3: 載入賽事數據
@timer("3️⃣ 載入賽事數據 (FastF1)")
def load_race_data():
    return loader.load_race_data(2025, "Australia", "R")

success = load_race_data()
if not success:
    print("❌ 數據載入失敗")
    sys.exit(1)

print(f"\n📊 已載入數據:")
print(f"   車手數量: {len(loader.laps['Driver'].unique()) if hasattr(loader, 'laps') else '?'}")
print(f"   總圈數: {len(loader.laps) if hasattr(loader, 'laps') else '?'}")

# 步驟 4: 執行油門分析
print("\n開始執行 Function 54 分析...")
analysis_start = time.time()

# 修改分析函數以添加內部計時
import CLI_modules.cli.analyzer.driver_throttle_ratio as throttle_module

# Monkey patch 關鍵函數來測量時間
original_safe_get_telemetry = throttle_module._safe_get_telemetry
original_calculate_metrics = throttle_module._calculate_lap_metrics_from_telemetry

telemetry_times = []
calculation_times = []

def timed_get_telemetry(lap):
    start = time.time()
    result = original_safe_get_telemetry(lap)
    elapsed = time.time() - start
    telemetry_times.append(elapsed)
    return result

def timed_calculate_metrics(telemetry, lap_time, threshold, coast_threshold):
    start = time.time()
    result = original_calculate_metrics(telemetry, lap_time, threshold, coast_threshold)
    elapsed = time.time() - start
    calculation_times.append(elapsed)
    return result

throttle_module._safe_get_telemetry = timed_get_telemetry
throttle_module._calculate_lap_metrics_from_telemetry = timed_calculate_metrics

# 執行分析
result = analyze_func(
    data_loader=loader,
    threshold=0.9,
    coast_threshold=0.2,
    show_summary=False,
    save_json=False
)

analysis_elapsed = time.time() - analysis_start

# 恢復原始函數
throttle_module._safe_get_telemetry = original_safe_get_telemetry
throttle_module._calculate_lap_metrics_from_telemetry = original_calculate_metrics

print(f"\n⏱️  4️⃣ 執行油門分析: {analysis_elapsed:.3f}秒")

# 分析時間分布
if telemetry_times:
    import numpy as np
    print(f"\n📈 性能分析:")
    print(f"   get_telemetry() 調用次數: {len(telemetry_times)}")
    print(f"   總耗時: {sum(telemetry_times):.3f}秒 ({sum(telemetry_times)/analysis_elapsed*100:.1f}%)")
    print(f"   平均每次: {np.mean(telemetry_times)*1000:.1f}ms")
    print(f"   最慢一次: {max(telemetry_times)*1000:.1f}ms")
    print(f"   最快一次: {min(telemetry_times)*1000:.1f}ms")

if calculation_times:
    print(f"\n   calculate_metrics() 調用次數: {len(calculation_times)}")
    print(f"   總耗時: {sum(calculation_times):.3f}秒 ({sum(calculation_times)/analysis_elapsed*100:.1f}%)")
    print(f"   平均每次: {np.mean(calculation_times)*1000:.1f}ms")

total_elapsed = time.time() - total_start
print(f"\n{'='*80}")
print(f"⏱️  總執行時間: {total_elapsed:.3f}秒 ({total_elapsed/60:.2f}分鐘)")
print(f"{'='*80}\n")

# 瓶頸分析
print("🎯 性能瓶頸分析:")
if sum(telemetry_times) / analysis_elapsed > 0.7:
    print("   ⚠️  主要瓶頸: get_telemetry() 佔用 >70% 時間")
    print("   💡 建議: 使用批次載入遙測數據而非逐圈載入")
else:
    print("   ✅ 未發現明顯瓶頸")
