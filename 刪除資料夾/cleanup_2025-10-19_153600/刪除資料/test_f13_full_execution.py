#!/usr/bin/env python3
"""
CLI -f13 時間序列輸出完整測試

執行 CLI -f13 並驗證 JSON 輸出包含時間數據
"""

import subprocess
import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime

def run_cli_f13_test():
    """執行完整的 CLI -f13 測試"""
    print("=" * 80)
    print("🧪 CLI -f13 時間序列輸出完整測試")
    print("=" * 80)
    
    # 測試參數
    test_params = {
        "year": "2024",
        "race": "Japan",
        "session": "R",
        "driver": "VER"
    }
    
    print(f"\n📋 測試參數:")
    for key, value in test_params.items():
        print(f"   • {key}: {value}")
    
    # 步驟 1: 執行 CLI 命令
    print(f"\n[步驟 1] 執行 CLI -f13...")
    print(f"   命令: python f1_analysis_modular_main.py -f 13 -y {test_params['year']} -r {test_params['race']} -s {test_params['session']} -d {test_params['driver']}")
    
    cmd = [
        "python",
        "f1_analysis_modular_main.py",
        "-f", "13",
        "-y", test_params['year'],
        "-r", test_params['race'],
        "-s", test_params['session'],
        "-d", test_params['driver']
    ]
    
    try:
        # 記錄開始時間
        start_time = time.time()
        
        # 執行命令
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=300  # 5分鐘超時
        )
        
        elapsed_time = time.time() - start_time
        
        print(f"\n   執行時間: {elapsed_time:.2f} 秒")
        print(f"   返回碼: {result.returncode}")
        
        if result.returncode != 0:
            print(f"\n❌ CLI 執行失敗")
            print(f"\n標準輸出:")
            print(result.stdout)
            print(f"\n標準錯誤:")
            print(result.stderr)
            return False
        
        print(f"✅ CLI 執行成功")
        
        # 顯示部分輸出（最後20行）
        output_lines = result.stdout.split('\n')
        if len(output_lines) > 20:
            print(f"\n   輸出（最後20行）:")
            for line in output_lines[-20:]:
                if line.strip():
                    print(f"      {line}")
        
    except subprocess.TimeoutExpired:
        print(f"\n❌ 執行超時（5分鐘）")
        return False
    except Exception as e:
        print(f"\n❌ 執行錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 步驟 2: 查找生成的 JSON 文件
    print(f"\n[步驟 2] 查找生成的 JSON 文件...")
    
    json_dir = Path("json")
    if not json_dir.exists():
        print(f"❌ json/ 目錄不存在")
        return False
    
    # 查找符合條件的文件
    pattern = f"driver_data_{test_params['driver']}_{test_params['year']}_{test_params['race']}_{test_params['session']}*.json"
    matching_files = list(json_dir.glob(pattern))
    
    if not matching_files:
        print(f"❌ 找不到匹配的 JSON 文件: {pattern}")
        return False
    
    # 取最新的文件
    latest_file = max(matching_files, key=lambda p: p.stat().st_mtime)
    print(f"✅ 找到 JSON 文件: {latest_file.name}")
    print(f"   文件大小: {latest_file.stat().st_size / 1024:.2f} KB")
    
    # 步驟 3: 驗證 JSON 結構
    print(f"\n[步驟 3] 驗證 JSON 結構...")
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ JSON 解析成功")
        
        # 檢查基本結構
        required_fields = ['function_id', 'data', 'timestamp']
        for field in required_fields:
            if field not in data:
                print(f"❌ 缺少必要欄位: {field}")
                return False
        
        print(f"✅ 基本結構正確")
        
        # 檢查 function_id
        if data['function_id'] != 13:
            print(f"❌ function_id 錯誤: {data['function_id']} (應為 13)")
            return False
        
        print(f"✅ function_id 正確: 13")
        
        # 檢查遙測數據
        if 'data' not in data or 'analysis_result' not in data['data']:
            print(f"❌ 缺少 analysis_result")
            return False
        
        analysis_result = data['data']['analysis_result']
        
        # 查找遙測數據區塊
        telemetry_section = None
        if 'telemetry_data' in analysis_result:
            telemetry_section = analysis_result['telemetry_data']
            section_name = 'telemetry_data'
        elif 'telemetry_comparison' in analysis_result:
            telemetry_section = analysis_result['telemetry_comparison']
            section_name = 'telemetry_comparison'
        else:
            print(f"❌ 找不到遙測數據區塊")
            return False
        
        print(f"✅ 找到遙測數據區塊: {section_name}")
        
        # 檢查時間序列數據
        if 'time_series' not in telemetry_section:
            print(f"❌ 缺少 time_series 數據")
            print(f"   可用欄位: {list(telemetry_section.keys())}")
            return False
        
        print(f"✅ 包含 time_series 數據")
        
        time_series = telemetry_section['time_series']
        
        # 驗證時間序列內容
        if 'driver' in time_series:
            # 單車手模式
            print(f"\n📊 單車手模式時間序列數據:")
            print(f"   • 車手: {time_series.get('driver')}")
            print(f"   • 數據點數: {time_series.get('data_points')}")
            print(f"   • 可用通道: {len(time_series.get('available_channels', []))}")
            
            # ✨ 關鍵驗證：時間數據
            if 'time_seconds' not in time_series:
                print(f"   ❌ 缺少 time_seconds 欄位")
                return False
            
            time_data = time_series['time_seconds']
            print(f"   ✅ 時間數據: {len(time_data)} 個數據點")
            print(f"   • 時間參考: {time_series.get('time_reference', 'N/A')}")
            
            # 檢查時間範圍
            valid_times = [t for t in time_data if t is not None]
            if valid_times:
                print(f"   • 時間範圍: {min(valid_times):.2f}s ~ {max(valid_times):.2f}s")
            
            # 檢查其他遙測通道
            telemetry_channels = {
                'distance_meters': '距離',
                'speed_kmh': '速度',
                'rpm': '轉速',
                'gear': '檔位',
                'throttle_percent': '油門',
                'brake_binary': '煞車'
            }
            
            print(f"\n   遙測通道:")
            for channel_key, channel_name in telemetry_channels.items():
                if channel_key in time_series:
                    channel_data = time_series[channel_key]
                    valid_data = [v for v in channel_data if v is not None]
                    if valid_data:
                        print(f"      ✅ {channel_name} ({channel_key}): {len(valid_data)} 個有效數據點")
                        if channel_key == 'speed_kmh':
                            print(f"         範圍: {min(valid_data):.1f} ~ {max(valid_data):.1f} km/h")
                        elif channel_key == 'rpm':
                            print(f"         範圍: {min(valid_data):.0f} ~ {max(valid_data):.0f} RPM")
                    else:
                        print(f"      ⚠️  {channel_name}: 無有效數據")
                else:
                    print(f"      ⚠️  缺少 {channel_name}")
        
        elif 'driver1' in time_series and 'driver2' in time_series:
            # 雙車手模式
            print(f"\n📊 雙車手模式時間序列數據:")
            for driver_key in ['driver1', 'driver2']:
                driver_data = time_series[driver_key]
                print(f"\n   {driver_key}: {driver_data.get('driver')}")
                print(f"      • 數據點數: {driver_data.get('data_points')}")
                
                if 'time_seconds' in driver_data:
                    print(f"      ✅ 包含時間數據")
                else:
                    print(f"      ❌ 缺少時間數據")
                    return False
        
        print(f"\n" + "=" * 80)
        print(f"✅ 所有驗證通過！")
        print(f"=" * 80)
        
        # 顯示 JSON 文件路徑
        print(f"\n📄 JSON 文件位置:")
        print(f"   {latest_file.absolute()}")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ 驗證失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print(f"\n開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    success = run_cli_f13_test()
    
    print(f"\n結束時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    if success:
        print("✅ 測試成功！CLI -f13 已正確輸出時間序列數據")
        sys.exit(0)
    else:
        print("❌ 測試失敗")
        sys.exit(1)
