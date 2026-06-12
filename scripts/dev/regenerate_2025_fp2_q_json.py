#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量重新生成 2025 FP2→Q 預測 JSON（含燃油校正）

執行 Function 76 為 2025 年所有已完成的比賽重新生成 JSON
"""

import sys
from pathlib import Path

# 直接導入 function_mapper 避免 subprocess 開銷
sys.path.insert(0, str(Path(__file__).parent))

# 2025 年已完成的比賽列表
RACES_2025 = [
    "Australia",
    "Bahrain", 
    "Saudi Arabia",
    "Japan",
    "Emilia Romagna",
    "Monaco",
    "Spain",
    "Canada",
    "Austria",
    "Great Britain",
    "Hungary",
    "Netherlands",
    "Italy",
    "Azerbaijan",
    "Singapore",
    "Mexico",
    "Las Vegas",
    "Abu Dhabi"
]

def regenerate_fp2_q_predictions():
    """重新生成所有 2025 FP2→Q 預測"""
    print("=" * 60)
    print("批量重新生成 2025 FP2→Q 預測 JSON（含燃油校正）")
    print("=" * 60)
    
    # 導入 function_mapper
    from CLI_modules.cli.core.function_mapper import F1AnalysisFunctionMapper
    mapper = F1AnalysisFunctionMapper()
    
    success_count = 0
    fail_count = 0
    failed_races = []
    
    for i, race in enumerate(RACES_2025, 1):
        print(f"\n[{i}/{len(RACES_2025)}] 處理 {race}...")
        
        try:
            result = mapper.execute_function_by_number(
                function_id=76,
                year=2025,
                race=race
            )
            
            if result.get('success'):
                print(f"   ✅ {race} 完成")
                success_count += 1
            else:
                print(f"   ❌ {race} 失敗: {result.get('message', 'Unknown')}")
                fail_count += 1
                failed_races.append(race)
                
        except Exception as e:
            print(f"   ❌ {race} 異常: {e}")
            fail_count += 1
            failed_races.append(race)
    
    # 摘要
    print("\n" + "=" * 60)
    print("生成結果摘要")
    print("=" * 60)
    print(f"成功: {success_count}/{len(RACES_2025)}")
    print(f"失敗: {fail_count}/{len(RACES_2025)}")
    
    if failed_races:
        print(f"失敗的比賽: {', '.join(failed_races)}")
    
    # 驗證燃油校正欄位
    print("\n驗證燃油校正欄位...")
    import json
    json_dir = Path("json")
    verified = 0
    
    for race in RACES_2025:
        json_file = json_dir / f"fp2_qualifying_prediction_2025_{race}.json"
        if json_file.exists():
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            has_fuel_correction = data.get('metadata', {}).get('fuel_correction_enabled', False)
            if has_fuel_correction:
                verified += 1
                print(f"   ✅ {race}: fuel_correction_enabled = True")
            else:
                print(f"   ⚠️  {race}: 缺少燃油校正欄位")
    
    print(f"\n燃油校正驗證: {verified}/{len(RACES_2025)} 個檔案已更新")


if __name__ == '__main__':
    regenerate_fp2_q_predictions()
