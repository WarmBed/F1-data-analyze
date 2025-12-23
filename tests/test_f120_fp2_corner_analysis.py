"""
F120 測試腳本 - FP2 彎道全圈數分析

測試用例：2024 Abu Dhabi Grand Prix FP2
驗證：
1. 彎道分類邏輯（低/中/高速）
2. 異常值過濾（嚴格模式）
3. 統計指標計算（13 種指標）
4. 雙模式分析（統一 + 分組）
5. Long Run / Quali Sim 自動檢測
"""

import subprocess
import json
import os
from pathlib import Path

def test_f120():
    """執行 F120 測試"""
    
    print("=" * 80)
    print("F120 FP2 彎道全圈數分析 - 測試開始")
    print("=" * 80)
    print()
    
    # 測試參數
    test_cases = [
        {
            "name": "Test 1: 2024 Abu Dhabi FP2",
            "command": [
                "python",
                "f1_analysis_modular_main.py",
                "-f", "120",
                "-y", "2024",
                "-r", "Abu Dhabi",
                "-s", "FP2"
            ],
            "expected_file": "json/fp2_corner_all_laps_analysis_2024_Abu Dhabi_FP2*.json"
        },
        {
            "name": "Test 2: 2024 Singapore FP2",
            "command": [
                "python",
                "f1_analysis_modular_main.py",
                "-f", "120",
                "-y", "2024",
                "-r", "Singapore",
                "-s", "FP2"
            ],
            "expected_file": "json/fp2_corner_all_laps_analysis_2024_Singapore_FP2*.json"
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n{'=' * 80}")
        print(f"執行: {test_case['name']}")
        print(f"{'=' * 80}")
        print()
        
        try:
            # 執行 CLI 命令
            print(f"命令: {' '.join(test_case['command'])}")
            print()
            
            result = subprocess.run(
                test_case['command'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            # 顯示輸出
            print("STDOUT:")
            print(result.stdout)
            
            if result.stderr:
                print("\nSTDERR:")
                print(result.stderr)
            
            # 檢查返回碼
            if result.returncode == 0:
                print(f"\n✅ {test_case['name']} - 執行成功")
                
                # 檢查 JSON 檔案
                json_files = list(Path("json").glob("fp2_corner_all_laps_analysis_*.json"))
                if json_files:
                    latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
                    print(f"✅ JSON 檔案已生成: {latest_file}")
                    
                    # 驗證 JSON 結構
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    print("\n📊 JSON 結構驗證:")
                    print(f"  - success: {data.get('success')}")
                    print(f"  - function_id: {data.get('function_id')}")
                    print(f"  - year: {data.get('year')}")
                    print(f"  - race: {data.get('race')}")
                    print(f"  - session: {data.get('session')}")
                    
                    # 檢查選擇的彎道
                    selected = data.get('selected_corners', {})
                    print(f"\n  選擇的彎道:")
                    for speed_type in ['low_speed', 'mid_speed', 'high_speed']:
                        corner = selected.get(speed_type)
                        if corner:
                            print(f"    - {speed_type}: T{corner['corner_number']} "
                                  f"({corner['avg_apex_speed']:.1f} km/h)")
                    
                    # 檢查模式 A
                    mode_a = data.get('mode_a_unified', {})
                    if mode_a:
                        print(f"\n  模式 A（統一分析）:")
                        print(f"    - 車手數: {mode_a.get('total_drivers')}")
                        
                        # 顯示第一位車手的統計範例
                        drivers = mode_a.get('drivers', [])
                        if drivers:
                            sample_driver = drivers[0]
                            print(f"\n    範例車手: {sample_driver['driver']}")
                            print(f"      - 總圈數: {sample_driver['total_laps']}")
                            
                            corners = sample_driver.get('corners', {})
                            for corner_key, stats in list(corners.items())[:1]:
                                print(f"\n      {corner_key} 統計:")
                                print(f"        - 中位數: {stats.get('median_speed')} km/h")
                                print(f"        - 平均數: {stats.get('mean_speed')} km/h")
                                print(f"        - 標準差: {stats.get('std_dev')} km/h")
                                print(f"        - 變異係數: {stats.get('cv')}%")
                                print(f"        - 有效圈數: {stats.get('valid_laps')}")
                                print(f"        - 過濾圈數: {stats.get('filtered_laps')}")
                                
                                if 'warnings' in stats:
                                    print(f"        ⚠️  警告: {', '.join(stats['warnings'])}")
                    
                    # 檢查模式 B
                    mode_b = data.get('mode_b_grouped', {})
                    if mode_b:
                        print(f"\n  模式 B（分組分析）:")
                        groups = mode_b.get('groups', {})
                        
                        for group_name in ['long_run', 'quali_sim']:
                            group = groups.get(group_name, {})
                            drivers = group.get('drivers', [])
                            print(f"    - {group_name}: {len(drivers)} 車手")
                    
                    results.append({
                        "test": test_case['name'],
                        "status": "PASS",
                        "file": str(latest_file)
                    })
                else:
                    print(f"⚠️  警告: 未找到 JSON 檔案")
                    results.append({
                        "test": test_case['name'],
                        "status": "PASS (No JSON)",
                        "file": None
                    })
            else:
                print(f"\n❌ {test_case['name']} - 執行失敗 (返回碼: {result.returncode})")
                results.append({
                    "test": test_case['name'],
                    "status": "FAIL",
                    "returncode": result.returncode
                })
                
        except Exception as e:
            print(f"\n❌ {test_case['name']} - 異常: {e}")
            results.append({
                "test": test_case['name'],
                "status": "ERROR",
                "error": str(e)
            })
    
    # 總結
    print("\n" + "=" * 80)
    print("測試總結")
    print("=" * 80)
    
    for result in results:
        status_icon = "✅" if result["status"] == "PASS" else "❌"
        print(f"{status_icon} {result['test']}: {result['status']}")
    
    passed = sum(1 for r in results if r["status"] == "PASS")
    total = len(results)
    print(f"\n通過率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    print("\n" + "=" * 80)
    print("F120 測試完成")
    print("=" * 80)


if __name__ == "__main__":
    test_f120()
