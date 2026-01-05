#!/usr/bin/env python3
"""
批次生成所有賽事的 FP2→Q 預測 JSON

此腳本會對所有有 FP2 數據的賽事生成排位賽預測。
Sprint 周末沒有 FP2，會被自動跳過。
"""

import json
from pathlib import Path
from datetime import datetime

def main():
    from CLI_modules.cli.core.function_mapper import F1AnalysisFunctionMapper
    
    # 2025 賽季所有賽事
    races_2025 = [
        'Bahrain', 'Saudi Arabia', 'Australia', 'Japan', 'China', 
        'Miami', 'Emilia Romagna', 'Monaco', 'Spain', 'Canada',
        'Austria', 'Great Britain', 'Hungary', 'Belgium', 'Netherlands',
        'Italy', 'Azerbaijan', 'Singapore', 'United States', 'Mexico',
        'Brazil', 'Las Vegas', 'Qatar', 'Abu Dhabi'
    ]
    
    # Sprint 周末沒有 FP2 的賽事
    sprint_races = ['China', 'Miami', 'Belgium', 'United States', 'Brazil', 'Qatar']
    valid_races = [r for r in races_2025 if r not in sprint_races]
    
    print("="*70)
    print("批次生成 FP2→Q 預測 JSON")
    print("="*70)
    print(f"目標年份: 2025")
    print(f"賽事數量: {len(valid_races)}")
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    mapper = F1AnalysisFunctionMapper()
    
    success_count = 0
    failed_races = []
    results_summary = []
    
    for i, race in enumerate(valid_races, 1):
        print(f"\n[{i}/{len(valid_races)}] 生成: 2025 {race}")
        print("-"*50)
        
        try:
            result = mapper._execute_fp2_q_prediction_generator(year=2025, race=race)
            
            if result.get('success'):
                success_count += 1
                predictions = result.get('data', {}).get('predictions', [])
                if predictions:
                    top3 = [p['driver'] for p in predictions[:3]]
                    print(f"✅ 成功 - Top 3: {top3}")
                    results_summary.append({
                        'race': race,
                        'success': True,
                        'top3': top3,
                        'predictions_count': len(predictions)
                    })
                else:
                    print(f"✅ 成功（無預測數據）")
                    results_summary.append({
                        'race': race,
                        'success': True,
                        'top3': [],
                        'predictions_count': 0
                    })
            else:
                failed_races.append(race)
                error_msg = result.get('message', '未知錯誤')
                print(f"❌ 失敗: {error_msg}")
                results_summary.append({
                    'race': race,
                    'success': False,
                    'error': error_msg
                })
                
        except Exception as e:
            failed_races.append(race)
            print(f"❌ 異常: {str(e)}")
            results_summary.append({
                'race': race,
                'success': False,
                'error': str(e)
            })
    
    # 摘要報告
    print("\n" + "="*70)
    print("批次生成完成")
    print("="*70)
    print(f"成功: {success_count}/{len(valid_races)}")
    print(f"失敗: {len(failed_races)}")
    
    if failed_races:
        print(f"\n失敗賽事:")
        for race in failed_races:
            print(f"  - {race}")
    
    # 保存摘要
    summary_file = Path("json") / "fp2_q_batch_generation_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'generated_at': datetime.now().isoformat(),
            'year': 2025,
            'total_races': len(valid_races),
            'success_count': success_count,
            'failed_count': len(failed_races),
            'failed_races': failed_races,
            'results': results_summary
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 摘要已保存: {summary_file}")
    print(f"📁 JSON 檔案位置: json/fp2_qualifying_prediction_2025_*.json")

if __name__ == "__main__":
    main()
