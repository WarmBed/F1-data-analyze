"""
測試 Segment 加速功能改進效果
驗證所有車手是否都有 Segment 數據（目標：100% 覆蓋率）
"""

import json
from pathlib import Path
from typing import Dict, List

def analyze_segment_coverage(json_path: str) -> Dict:
    """
    分析 JSON 檔案中的 Segment 數據覆蓋率
    
    Returns:
        包含統計數據的字典
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 根據 JSON 格式提取數據
        if "data" in data:
            inner_data = data["data"]
            # 嘗試多種可能的鍵名
            driver_records = (
                inner_data.get("driver_speeds") or 
                inner_data.get("data") or 
                inner_data.get("drivers") or 
                inner_data.get("records") or
                []
            )
        else:
            driver_records = data
        
        total_drivers = len(driver_records)
        drivers_with_segment = []
        drivers_without_segment = []
        
        print("\n" + "="*80)
        print("🔍 Segment 加速數據覆蓋率分析")
        print("="*80)
        
        for record in driver_records:
            driver = record.get("driver_code", "UNKNOWN")
            segment_time = record.get("segment_accel_time_seconds")
            segment_accel = record.get("segment_avg_acceleration_ms2")
            
            if segment_time is not None and segment_accel is not None:
                drivers_with_segment.append(driver)
                print(f"✅ {driver:3s} | 時間: {segment_time:>6.3f}s | 加速度: {segment_accel:>5.2f} m/s² | ✅ 有數據")
            else:
                drivers_without_segment.append(driver)
                print(f"❌ {driver:3s} | NULL | ❌ 無數據")
        
        coverage_rate = (len(drivers_with_segment) / total_drivers * 100) if total_drivers > 0 else 0
        
        print("\n" + "="*80)
        print("📊 統計結果")
        print("="*80)
        print(f"總車手數: {total_drivers}")
        print(f"有 Segment 數據: {len(drivers_with_segment)} ({coverage_rate:.1f}%)")
        print(f"無 Segment 數據: {len(drivers_without_segment)} ({100-coverage_rate:.1f}%)")
        
        if drivers_with_segment:
            print(f"\n✅ 有數據車手: {', '.join(drivers_with_segment)}")
        
        if drivers_without_segment:
            print(f"\n❌ 無數據車手: {', '.join(drivers_without_segment)}")
        
        # 改進效果評估
        print("\n" + "="*80)
        print("🎯 改進效果評估")
        print("="*80)
        
        if coverage_rate == 100:
            print("🎉 成功！所有車手都有 Segment 加速數據！")
            print("✅ 硬編碼起點 + 動態終點模式運作正常")
        elif coverage_rate >= 80:
            print(f"⚠️  部分成功：{coverage_rate:.1f}% 車手有數據")
            print("💡 建議檢查無數據車手的遙測情況")
        else:
            print(f"❌ 改進效果不佳：僅 {coverage_rate:.1f}% 車手有數據")
            print("💡 建議檢查改進邏輯是否正確執行")
        
        return {
            "total_drivers": total_drivers,
            "with_segment": len(drivers_with_segment),
            "without_segment": len(drivers_without_segment),
            "coverage_rate": coverage_rate
        }
        
    except Exception as e:
        print(f"❌ 分析失敗: {e}")
        return {}

def find_latest_json(race: str = "Japan", year: int = 2025, session: str = "R") -> str:
    """
    找到最新的 JSON 檔案
    """
    json_dir = Path("json")
    
    # 嘗試兩種檔名格式
    # 格式 1: all_drivers_straight_line_speed_2025_Japan_R_YYYYMMDD_HHMMSS.json
    pattern1 = f"all_drivers_straight_line_speed_{year}_{race}_{session}_*.json"
    matching_files = list(json_dir.glob(pattern1))
    
    # 格式 2: all_drivers_straight_line_speed_2025_Japan_R.json
    if not matching_files:
        pattern2 = f"all_drivers_straight_line_speed_{year}_{race}_{session}.json"
        matching_files = list(json_dir.glob(pattern2))
    
    if not matching_files:
        return None
    
    # 返回最新的檔案
    latest_file = max(matching_files, key=lambda p: p.stat().st_mtime)
    return str(latest_file)

def main():
    """主函數"""
    print("\n" + "="*80)
    print("🧪 測試 Segment 加速功能改進")
    print("="*80)
    print("\n目標：驗證改進版是否讓所有車手都有 Segment 數據（100% 覆蓋率）")
    
    # 找到最新的 Japan 2025 R JSON 檔案
    json_path = find_latest_json("Japan", 2025, "R")
    
    if not json_path:
        print("\n❌ 找不到 Japan 2025 R 的 JSON 檔案")
        print("💡 請先執行: python f1_analysis_modular_main.py -f 48 -y 2025 -r Japan -s R")
        return
    
    print(f"\n📂 分析檔案: {json_path}")
    
    # 分析覆蓋率
    result = analyze_segment_coverage(json_path)
    
    if result:
        print("\n" + "="*80)
        print("✅ 測試完成")
        print("="*80)

if __name__ == "__main__":
    main()
