#!/usr/bin/env python3
"""
診斷賽事數據不匹配問題

檢查各模組的 JSON 檔案，確認它們是否包含正確的賽事數據
"""

import json
import os
from pathlib import Path


def analyze_json_file(filepath: str) -> dict:
    """分析單個 JSON 檔案"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 提取元數據
        metadata = data.get('metadata', {})
        
        # 嘗試找出實際的賽事數據
        analysis_data = data.get('analysis', {}) or data.get('analysis_result', {})
        
        # 計算資料量
        total_drivers = 0
        total_laps = 0
        
        if 'drivers' in analysis_data:
            drivers = analysis_data['drivers']
            total_drivers = len(drivers)
            for driver in drivers:
                if 'laps' in driver:
                    total_laps += len(driver['laps'])
        
        if 'ranking' in analysis_data:
            total_drivers = len(analysis_data['ranking'])
        
        if 'driver_analysis' in data:
            for driver_code, driver_data in data['driver_analysis'].items():
                total_drivers += 1
                if 'detailed_laps' in driver_data:
                    total_laps += len(driver_data['detailed_laps'])
        
        return {
            'file': os.path.basename(filepath),
            'metadata_year': metadata.get('year'),
            'metadata_race': metadata.get('race'),
            'metadata_session': metadata.get('session'),
            'metadata_round': metadata.get('round_number'),
            'total_drivers': total_drivers,
            'total_laps': total_laps,
            'file_size_kb': os.path.getsize(filepath) / 1024,
        }
    except Exception as e:
        return {
            'file': os.path.basename(filepath),
            'error': str(e)
        }


def main():
    """主函數"""
    print("="*80)
    print("診斷賽事數據不匹配問題")
    print("="*80)
    print()
    
    json_dir = Path("json")
    
    # 檢查的檔案列表
    files_to_check = [
        # 正確的（參考）
        "ideal_lap_ranking_2025_Japan_R.json",
        
        # 可能有問題的
        "throttle_ratio_2025_united_states_R.json",
        "detailed_laptime_analysis_2025_United States_R_all_drivers.json",
    ]
    
    print("📋 檔案分析結果:\n")
    
    results = []
    for filename in files_to_check:
        filepath = json_dir / filename
        if filepath.exists():
            result = analyze_json_file(str(filepath))
            results.append(result)
        else:
            results.append({
                'file': filename,
                'error': '檔案不存在'
            })
    
    # 打印結果
    for result in results:
        print(f"📄 {result['file']}")
        print(f"   檔案大小: {result.get('file_size_kb', 0):.2f} KB")
        
        if 'error' in result:
            print(f"   ❌ 錯誤: {result['error']}")
        else:
            print(f"   年份: {result['metadata_year']}")
            print(f"   賽事: {result['metadata_race']}")
            print(f"   節次: {result['metadata_session']}")
            print(f"   輪次: {result['metadata_round']}")
            print(f"   車手數: {result['total_drivers']}")
            print(f"   總圈數: {result['total_laps']}")
        print()
    
    # 比對分析
    print("\n" + "="*80)
    print("🔍 比對分析")
    print("="*80)
    
    # 找出參考檔案（日本站）
    reference = next((r for r in results if 'Japan' in r.get('metadata_race', '')), None)
    
    if reference:
        print(f"\n✅ 參考檔案（正確）: {reference['file']}")
        print(f"   - 賽事: {reference.get('metadata_race')}")
        print(f"   - 總圈數: {reference.get('total_laps')}")
        print()
        
        # 檢查其他檔案
        for result in results:
            if result.get('file') == reference['file']:
                continue
            
            if 'error' in result:
                continue
            
            filename = result['file']
            expected_race_in_filename = "Japan" if "Japan" in filename else \
                                       "United States" if "united_states" in filename.lower() or "United States" in filename else \
                                       "Unknown"
            
            actual_race = result.get('metadata_race', 'Unknown')
            actual_laps = result.get('total_laps', 0)
            
            print(f"📄 {filename}")
            print(f"   檔名預期賽事: {expected_race_in_filename}")
            print(f"   實際元數據賽事: {actual_race}")
            print(f"   總圈數: {actual_laps}")
            
            # 判斷是否匹配
            if expected_race_in_filename in actual_race or actual_race in expected_race_in_filename:
                print(f"   ✅ 賽事名稱匹配")
            else:
                print(f"   ❌ 賽事名稱不匹配!")
            
            # 圈數比對（粗略判斷）
            if actual_laps > 50:
                print(f"   ℹ️  圈數較多 ({actual_laps})，可能是較長的賽事")
            elif actual_laps > 0:
                print(f"   ℹ️  圈數正常 ({actual_laps})")
            else:
                print(f"   ⚠️  沒有圈數數據")
            
            print()
    
    print("\n" + "="*80)
    print("建議:")
    print("="*80)
    print("1. 如果檔案名稱與實際數據不匹配，需要重新生成正確的數據")
    print("2. 檢查 GUI 模組的參數傳遞邏輯，確保 race 參數正確")
    print("3. 檢查 CLI 的賽事名稱解析邏輯，確保 FastF1 使用正確的賽事")
    print()


if __name__ == "__main__":
    main()
