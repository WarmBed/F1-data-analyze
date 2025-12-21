"""
比較 F48 和 F121 在 2025 Abu Dhabi 的分析結果
F48: Race (正賽最速圈分析)
F121: Race (正賽全圈數分析)
"""
import json
from typing import Dict, Any

def load_json(filepath: str) -> Dict[str, Any]:
    """載入 JSON 檔案"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def compare_driver_data(f48_data: Dict, f121_race_data: Dict):
    """比較車手數據"""
    
    print("=" * 100)
    print("F48 vs F121 分析結果比較 - 2025 Abu Dhabi Race")
    print("=" * 100)
    
    # F48 數據結構：data.driver_speeds
    f48_drivers = f48_data.get('data', {}).get('driver_speeds', [])
    
    # F121 數據（使用統一分析模式）
    f121_drivers = f121_race_data.get('mode_a_unified', {}).get('drivers', [])
    
    print(f"\n📊 數據來源比較:")
    print(f"  F48 (正賽):  {len(f48_drivers)} 位車手 - 每位使用最速圈")
    print(f"  F121 (正賽):  {len(f121_drivers)} 位車手 - 每位使用所有有效圈")
    
    # 創建車手映射
    f48_map = {d['driver']: d for d in f48_drivers}
    f121_map = {d['driver']: d for d in f121_drivers}
    
    # 找共同車手
    common_drivers = set(f48_map.keys()) & set(f121_map.keys())
    
    print(f"\n✅ 共同車手: {len(common_drivers)} 位")
    if common_drivers:
        print(f"   {', '.join(sorted(common_drivers))}")
    
    print("\n" + "=" * 100)
    print("🏎️  詳細比較（前 5 位車手）")
    print("=" * 100)
    
    # 按 F48 最高速度排序
    sorted_f48 = sorted(f48_drivers, key=lambda x: x.get('max_speed_kmh', 0), reverse=True)[:5]
    
    for i, f48_driver in enumerate(sorted_f48, 1):
        driver_code = f48_driver['driver']
        
        print(f"\n【{i}】{driver_code}")
        print("-" * 100)
        
        # F48 數據
        f48_max_speed = f48_driver.get('max_speed_kmh', 0)
        f48_accel = f48_driver.get('acceleration_100_300')
        f48_lap = f48_driver.get('lap_number', 'N/A')
        
        print(f"📍 F48 (正賽 Race - 最速圈 #{f48_lap}):")
        print(f"   最高速度: {f48_max_speed:.1f} km/h")
        
        if f48_accel:
            print(f"   加速性能 (硬編碼起點):")
            print(f"      時間: {f48_accel.get('time_seconds', 0):.3f} 秒 ({f48_accel.get('start_speed_kmh', 0):.0f}→{f48_accel.get('end_speed_kmh', 0):.0f} km/h)")
            print(f"      距離: {f48_accel.get('distance_meters', 0):.1f} m")
            print(f"      平均加速度: {f48_accel.get('avg_acceleration_ms2', 0):.2f} m/s²")
        else:
            print(f"   加速性能: ❌ 無數據")
        
        # F121 數據
        if driver_code in f121_map:
            f121_driver = f121_map[driver_code]
            f121_speed_stats = f121_driver.get('speed_stats', {})
            f121_accel_stats = f121_driver.get('acceleration_100_300_stats')
            f121_time_to_max = f121_driver.get('time_to_max_speed_stats')
            
            total_laps = f121_driver.get('total_laps', 0)
            valid_laps = f121_driver.get('valid_speed_laps', 0)
            
            print(f"\n📍 F121 (Race - 全圈數分析, {valid_laps}/{total_laps} 有效圈):")
            print(f"   最高速度統計:")
            print(f"      中位數: {f121_speed_stats.get('median', 0):.1f} km/h")
            print(f"      平均值: {f121_speed_stats.get('mean', 0):.1f} km/h")
            print(f"      範圍: {f121_speed_stats.get('min', 0):.1f} - {f121_speed_stats.get('max', 0):.1f} km/h")
            print(f"      標準差: {f121_speed_stats.get('std_dev', 0):.2f} km/h")
            
            if f121_accel_stats:
                print(f"   加速性能統計 (100→300 km/h):")
                print(f"      中位數: {f121_accel_stats.get('median', 0):.3f} 秒")
                print(f"      平均值: {f121_accel_stats.get('mean', 0):.3f} 秒")
                print(f"      最快: {f121_accel_stats.get('min', 0):.3f} 秒")
                print(f"      最慢: {f121_accel_stats.get('max', 0):.3f} 秒")
                print(f"      標準差: {f121_accel_stats.get('std_dev', 0):.3f} 秒")
            else:
                print(f"   加速性能統計: ❌ 無數據")
            
            if f121_time_to_max:
                print(f"   推算時間 (100 km/h → 最高速度，線性公式):")
                print(f"      中位數: {f121_time_to_max.get('median', 0):.3f} 秒")
                print(f"      平均值: {f121_time_to_max.get('mean', 0):.3f} 秒")
            
            # 比較差異
            print(f"\n💡 關鍵差異:")
            speed_diff = f48_max_speed - f121_speed_stats.get('median', 0)
            print(f"   速度差異: {abs(speed_diff):.1f} km/h ({'F48最速圈更快' if speed_diff > 0 else 'F121中位數更快'})")
            
            if f48_accel and f121_accel_stats:
                accel_diff = f48_accel.get('time_seconds', 0) - f121_accel_stats.get('median', 0)
                print(f"   加速時間差異: {abs(accel_diff):.3f} 秒 ({'F48最速圈更快' if accel_diff < 0 else 'F121中位數更快'})")
        else:
            print(f"\n📍 F121: ❌ 無此車手數據")
    
    print("\n" + "=" * 100)
    print("📈 整體統計比較")
    print("=" * 100)
    
    # F48 整體統計
    f48_summary = f48_data.get('data', {}).get('summary', {})
    print(f"\nF48 (正賽最速圈):")
    print(f"  車手數: {f48_summary.get('total_drivers', 0)}")
    print(f"  最高速度 - 最快: {f48_summary.get('max_speed_kmh', 0):.1f} km/h")
    print(f"  最高速度 - 平均: {f48_summary.get('mean_speed_kmh', 0):.1f} km/h")
    print(f"  最高速度 - 中位數: {f48_summary.get('median_speed_kmh', 0):.1f} km/h")
    
    # F121 整體統計（計算所有車手的中位數平均）
    if f121_drivers:
        all_medians = [d['speed_stats']['median'] for d in f121_drivers if 'speed_stats' in d]
        all_means = [d['speed_stats']['mean'] for d in f121_drivers if 'speed_stats' in d]
        
        print(f"\nF121 (FP2 全圈數):")
        print(f"  車手數: {len(f121_drivers)}")
        print(f"  各車手中位數的平均: {sum(all_medians)/len(all_medians):.1f} km/h")
        print(f"  各車手平均值的平均: {sum(all_means)/len(all_means):.1f} km/h")
    
    print("\n" + "=" * 100)
    print("🔍 分析方法差異總結")
    print("=" * 100)
    
    print("""
F48 (全車手直線速度分析 - 正賽):
  ✅ 使用每位車手的最速圈
  ✅ 硬編碼起點 (Abu Dhabi: 1454.9m)
  ✅ 高油門 (≥95%) 作為加速段
  ✅ 統一終點速度 (308.0 km/h)
  ✅ 單一數據點（最佳表現）
  ✅ 適合比較各車手的最佳性能

F121 (直線速度全圈數分析 - 正賽):
  ✅ 使用所有有效圈的數據
  ✅ 官方 API 靜態數據（避免插值）
  ✅ 100→300 km/h 固定速度範圍
  ✅ 中位數過濾異常值
  ✅ 統計分布（中位數、平均、標準差）
  ✅ 適合評估車手的穩定性和圈數變化

共同點:
  ✅ 都使用線性加速公式推算到最高速度
  ✅ 都計算 100→300 km/h 加速性能
  ✅ 都基於直線段的速度數據
  ✅ 都分析同一場正賽 (2025 Abu Dhabi Race)
    """)
    
    print("=" * 100)

if __name__ == "__main__":
    # 載入數據
    f48_file = "json/all_drivers_straight_line_speed_2025_Abu Dhabi_R.json"
    f121_file = "json/fp2_straight_line_all_laps_analysis_2025_Abu Dhabi_R.json"
    
    try:
        f48_data = load_json(f48_file)
        f121_data = load_json(f121_file)
        
        compare_driver_data(f48_data, f121_data)
        
    except FileNotFoundError as e:
        print(f"❌ 找不到檔案: {e}")
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
