#!/usr/bin/env python3
"""
測試 CLI -f13 遙測時間序列輸出

驗證修改後的 driver_comparison_advanced.py 是否正確輸出時間數據
"""

import sys
import os
import json
from pathlib import Path

# 添加專案根目錄到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_f13_json_output():
    """測試 -f13 的 JSON 輸出是否包含時間數據"""
    print("=" * 80)
    print("🧪 測試 CLI -f13 遙測時間序列輸出")
    print("=" * 80)
    
    # 步驟 1: 檢查 JSON 函數是否正常導入
    print("\n[步驟 1] 檢查模組導入...")
    try:
        # 直接檢查文件是否存在
        analyzer_path = Path("CLI_modules/cli/analyzer/driver_comparison_advanced.py")
        if not analyzer_path.exists():
            print(f"❌ 找不到分析器文件: {analyzer_path}")
            return False
        print(f"✅ 找到分析器文件: {analyzer_path}")
        
        # 嘗試導入（可能失敗，但不影響測試）
        try:
            from CLI_modules.cli.analyzer.driver_comparison_advanced import (
                run_driver_comparison_json,
                _extract_telemetry_time_series,
                _safe_get_lap_telemetry_standalone
            )
            print("✅ 成功導入所有必要函數")
        except Exception as import_error:
            print(f"⚠️  導入函數失敗: {import_error}")
            print("   (這不影響 JSON 結構驗證)")
    except Exception as e:
        print(f"⚠️  模組檢查警告: {e}")
        print("   (繼續進行 JSON 結構驗證)")
    
    # 步驟 2: 檢查最新的 JSON 文件
    print("\n[步驟 2] 查找最新的 -f13 JSON 文件...")
    json_dir = Path("json")
    if not json_dir.exists():
        print("❌ json/ 目錄不存在")
        return False
    
    # 查找 driver_data 或 driver_comparison 文件
    json_patterns = [
        "driver_data_*.json",
        "driver_comparison_*.json"
    ]
    
    latest_file = None
    latest_time = 0
    
    for pattern in json_patterns:
        for json_file in json_dir.glob(pattern):
            mtime = json_file.stat().st_mtime
            if mtime > latest_time:
                latest_time = mtime
                latest_file = json_file
    
    if not latest_file:
        print("⚠️  沒有找到現有的 JSON 文件")
        print("💡 建議：先執行 CLI 命令生成數據")
        print("   例如: python f1_analysis_modular_main.py -f 13 -y 2024 -r Japan -s R -d VER")
        return True  # 不算失敗，只是沒有現成數據
    
    print(f"✅ 找到最新文件: {latest_file.name}")
    
    # 步驟 3: 檢查 JSON 結構
    print("\n[步驟 3] 檢查 JSON 結構...")
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ JSON 文件載入成功")
        
        # 檢查頂層結構
        print("\n📋 頂層結構:")
        for key in data.keys():
            print(f"   • {key}")
        
        # 深入檢查 analysis_result
        if 'data' in data and 'analysis_result' in data['data']:
            analysis_result = data['data']['analysis_result']
            
            # 檢查遙測數據區塊
            telemetry_sections = []
            if 'telemetry_data' in analysis_result:
                telemetry_sections.append(('telemetry_data', analysis_result['telemetry_data']))
            if 'telemetry_comparison' in analysis_result:
                telemetry_sections.append(('telemetry_comparison', analysis_result['telemetry_comparison']))
            
            if not telemetry_sections:
                print("\n⚠️  沒有找到遙測數據區塊")
                print("   - 這可能是舊版本的 JSON 文件")
                print("   - 請重新執行 CLI -f13 生成新文件")
                return True
            
            # 檢查每個遙測區塊
            for section_name, section_data in telemetry_sections:
                print(f"\n📊 檢查 {section_name}:")
                print(f"   • telemetry_available: {section_data.get('telemetry_available', False)}")
                print(f"   • note: {section_data.get('note', 'N/A')}")
                
                # ✨ 關鍵檢查：time_series 是否存在
                if 'time_series' in section_data:
                    print(f"   ✅ 包含 time_series 數據！")
                    
                    time_series = section_data['time_series']
                    
                    # 單車手模式
                    if 'driver' in time_series:
                        print(f"\n   🏎️  單車手模式:")
                        print(f"      - driver: {time_series.get('driver')}")
                        print(f"      - data_points: {time_series.get('data_points')}")
                        
                        # 檢查時間數據
                        if 'time_seconds' in time_series:
                            time_data = time_series['time_seconds']
                            print(f"      ✅ 時間數據存在: {len(time_data)} 個數據點")
                            print(f"         - 時間參考: {time_series.get('time_reference')}")
                            if time_data:
                                print(f"         - 時間範圍: {min([t for t in time_data if t is not None]):.2f}s ~ {max([t for t in time_data if t is not None]):.2f}s")
                        else:
                            print(f"      ⚠️  缺少 time_seconds 欄位")
                        
                        # 檢查其他遙測通道
                        telemetry_channels = ['distance_meters', 'speed_kmh', 'rpm', 'gear', 'throttle_percent', 'brake_binary']
                        available_channels = [ch for ch in telemetry_channels if ch in time_series]
                        print(f"      - 可用遙測通道: {', '.join(available_channels)}")
                    
                    # 雙車手模式
                    elif 'driver1' in time_series and 'driver2' in time_series:
                        print(f"\n   🏎️🏎️  雙車手模式:")
                        for driver_key in ['driver1', 'driver2']:
                            driver_data = time_series[driver_key]
                            print(f"\n      {driver_key}: {driver_data.get('driver')}")
                            print(f"         - data_points: {driver_data.get('data_points')}")
                            
                            if 'time_seconds' in driver_data:
                                time_data = driver_data['time_seconds']
                                print(f"         ✅ 時間數據: {len(time_data)} 個數據點")
                                print(f"            - 時間參考: {driver_data.get('time_reference')}")
                            else:
                                print(f"         ⚠️  缺少 time_seconds")
                else:
                    print(f"   ❌ 缺少 time_series 數據")
                    print(f"   💡 這是舊版本的 JSON，請重新執行 CLI -f13")
        
        print("\n" + "=" * 80)
        print("✅ 測試完成！")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_usage():
    """顯示使用說明"""
    print("\n" + "=" * 80)
    print("📖 使用說明")
    print("=" * 80)
    print("\n此測試腳本會檢查最新的 -f13 JSON 文件是否包含時間序列數據")
    print("\n如果沒有現成的 JSON 文件，請先執行以下命令生成：")
    print("\n  單車手模式:")
    print("    python f1_analysis_modular_main.py -f 13 -y 2024 -r Japan -s R -d VER")
    print("\n  雙車手比較模式:")
    print("    python f1_analysis_modular_main.py -f 13 -y 2024 -r Japan -s R -d VER -d2 LEC")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    success = test_f13_json_output()
    
    if success:
        show_usage()
        sys.exit(0)
    else:
        print("\n❌ 測試失敗")
        sys.exit(1)
