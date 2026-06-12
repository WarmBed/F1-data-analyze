#!/usr/bin/env python3
"""
檢查 Function 54 (Pedal Behavior) 數據格式
==========================================

檢查項目：
1. API 返回的數據是否包含 pedal_states
2. 2025 年所有 JSON 檔案是否包含正確格式

Author: F1T Team
Date: 2026-01-12
"""

import os
import sys
import json
import requests
from pathlib import Path
from typing import Dict, List, Any, Tuple

# 確保 UTF-8 輸出
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# 設定
JSON_DIR = Path("json")
API_BASE = "http://localhost:8000"


def check_lap_has_pedal_states(lap: Dict) -> Tuple[bool, str]:
    """檢查單個 lap 是否包含 pedal_states"""
    if 'pedal_states' not in lap:
        return False, "缺少 pedal_states 欄位"
    
    pedal_states = lap['pedal_states']
    required_keys = ['throttle_only_ratio', 'brake_only_ratio', 'trail_braking_ratio', 'coasting_ratio']
    
    for key in required_keys:
        if key not in pedal_states:
            return False, f"pedal_states 缺少 {key}"
    
    return True, "OK"


def check_json_file(filepath: Path) -> Dict[str, Any]:
    """檢查單個 JSON 檔案"""
    result = {
        'file': filepath.name,
        'valid': False,
        'has_pedal_states': False,
        'driver_count': 0,
        'lap_count': 0,
        'errors': []
    }
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 檢查基本結構
        if 'analysis' not in data:
            result['errors'].append("缺少 analysis 欄位")
            return result
        
        analysis = data['analysis']
        if 'drivers' not in analysis:
            result['errors'].append("缺少 analysis.drivers 欄位")
            return result
        
        drivers = analysis['drivers']
        
        # 處理 list 格式
        if isinstance(drivers, list):
            result['driver_count'] = len(drivers)
            
            pedal_states_count = 0
            total_laps = 0
            
            for driver in drivers:
                if not isinstance(driver, dict):
                    continue
                
                laps = driver.get('laps', [])
                if not isinstance(laps, list):
                    continue
                
                for lap in laps:
                    total_laps += 1
                    has_ps, msg = check_lap_has_pedal_states(lap)
                    if has_ps:
                        pedal_states_count += 1
            
            result['lap_count'] = total_laps
            result['has_pedal_states'] = pedal_states_count > 0
            result['pedal_states_ratio'] = f"{pedal_states_count}/{total_laps}" if total_laps > 0 else "0/0"
            
            if pedal_states_count == 0 and total_laps > 0:
                result['errors'].append("沒有任何 lap 包含 pedal_states")
            elif pedal_states_count < total_laps:
                result['errors'].append(f"只有 {pedal_states_count}/{total_laps} 個 lap 包含 pedal_states")
            
            result['valid'] = pedal_states_count == total_laps and total_laps > 0
        
        # 處理 dict 格式
        elif isinstance(drivers, dict):
            result['driver_count'] = len(drivers)
            result['errors'].append("使用舊的 dict 格式（應為 list 格式）")
        
        else:
            result['errors'].append(f"drivers 格式錯誤: {type(drivers)}")
        
    except json.JSONDecodeError as e:
        result['errors'].append(f"JSON 解析錯誤: {e}")
    except Exception as e:
        result['errors'].append(f"讀取錯誤: {e}")
    
    return result


def check_api_response(year: int, race: str, session: str, force_refresh: bool = False) -> Dict[str, Any]:
    """檢查 API 返回的數據"""
    result = {
        'year': year,
        'race': race,
        'session': session,
        'api_success': False,
        'has_pedal_states': False,
        'cache_file': None,
        'errors': []
    }
    
    try:
        url = f"{API_BASE}/api/v2/analysis/execute"
        params = {
            'function_id': 54,
            'year': year,
            'race': race,
            'session': session,
            'force_refresh': 'true' if force_refresh else 'false'
        }
        
        print(f"  呼叫 API: {race} {year} {session}...", end=" ", flush=True)
        response = requests.post(url, params=params, timeout=90)
        
        if response.status_code != 200:
            result['errors'].append(f"HTTP {response.status_code}")
            print("FAILED")
            return result
        
        data = response.json()
        result['api_success'] = data.get('success', False)
        result['source'] = data.get('source', 'unknown')
        
        # 獲取緩存信息
        cache_meta = data.get('data', {}).get('_cache_metadata', {})
        result['cache_file'] = cache_meta.get('source_file')
        
        # 檢查 pedal_states
        try:
            inner_data = data['data']['data']
            drivers = inner_data['analysis']['drivers']
            
            if isinstance(drivers, list) and len(drivers) > 0:
                # 檢查第一個車手的第 5 圈（避免進站圈）
                first_driver = drivers[0]
                laps = first_driver.get('laps', [])
                
                if len(laps) > 5:
                    test_lap = laps[5]
                    has_ps, msg = check_lap_has_pedal_states(test_lap)
                    result['has_pedal_states'] = has_ps
                    if not has_ps:
                        result['errors'].append(msg)
                else:
                    result['errors'].append(f"圈數不足: {len(laps)}")
            else:
                result['errors'].append("沒有車手數據或格式錯誤")
        
        except KeyError as e:
            result['errors'].append(f"數據結構錯誤: 缺少 {e}")
        
        status = "OK" if result['has_pedal_states'] else "MISSING pedal_states"
        print(status)
        
    except requests.Timeout:
        result['errors'].append("API 超時")
        print("TIMEOUT")
    except Exception as e:
        result['errors'].append(f"請求錯誤: {e}")
        print(f"ERROR: {e}")
    
    return result


def main():
    print("=" * 70)
    print("Function 54 (Pedal Behavior) 數據格式檢查")
    print("=" * 70)
    
    # ========== 1. 檢查本地 JSON 檔案 (優先) ==========
    print("\n[1] 檢查本地 2025 年 JSON 檔案")
    print("-" * 50)
    
    # 找出所有 2025 年的 Function 54 JSON
    pattern = "driver_throttle_ratio_2025*.json"
    json_files = list(JSON_DIR.glob(pattern))
    
    print(f"找到 {len(json_files)} 個 2025 年 JSON 檔案")
    
    valid_count = 0
    invalid_count = 0
    invalid_files = []
    
    for filepath in sorted(json_files):
        result = check_json_file(filepath)
        
        if result['valid']:
            valid_count += 1
            print(f"  [OK] {result['file']}: {result['driver_count']} drivers, {result['pedal_states_ratio']} laps with pedal_states")
        else:
            invalid_count += 1
            invalid_files.append(result)
            print(f"  [X ] {result['file']}: {', '.join(result['errors'])}")
    
    # ========== 2. 檢查 API 回應 (可選) ==========
    print("\n" + "=" * 70)
    print("[2] 檢查 API 回應 (使用快取)")
    print("-" * 50)
    
    # 只測試一個賽事來確認 API 格式
    test_races = [
        (2025, "Australia", "R"),
    ]
    
    api_results = []
    for year, race, session in test_races:
        result = check_api_response(year, race, session, force_refresh=False)
        api_results.append(result)
    
    print("\nAPI 檢查結果:")
    for r in api_results:
        status = "[OK]" if r['has_pedal_states'] else "[X ]"
        print(f"  {status} {r['race']} {r['year']} {r['session']}: source={r.get('source', 'unknown')}")
        if r['errors']:
            for err in r['errors']:
                print(f"      - {err}")
    
    # ========== 總結 ==========
    print("\n" + "=" * 70)
    print("總結")
    print("=" * 70)
    
    print(f"\n本地 JSON 檔案 (2025):")
    print(f"  [OK] 有效: {valid_count}")
    print(f"  [X ] 無效: {invalid_count}")
    
    print(f"\nAPI 檢查:")
    api_ok = sum(1 for r in api_results if r['has_pedal_states'])
    api_fail = len(api_results) - api_ok
    print(f"  [OK] 通過: {api_ok}")
    print(f"  [X ] 失敗: {api_fail}")
    
    if invalid_files:
        print("\n需要重新生成的檔案:")
        for f in invalid_files:
            print(f"  - {f['file']}")
        
        print("\n建議執行以下命令重新生成:")
        for f in invalid_files:
            # 從檔名解析參數
            name = f['file'].replace('driver_throttle_ratio_', '').replace('.json', '')
            parts = name.split('_')
            if len(parts) >= 3:
                year = parts[0]
                session = parts[-1]
                race = '_'.join(parts[1:-1])
                print(f"  python f1_analysis_modular_main.py -f 54 -y {year} -r \"{race}\" -s {session}")
    
    return 0 if (api_fail == 0 and invalid_count == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
