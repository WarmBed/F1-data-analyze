#!/usr/bin/env python3
"""
批次收集 2025 賽季 FP2→Q 訓練數據

此腳本將：
1. 收集所有 2025 賽事的 FP2 和 Q 數據
2. 使用新的 Quali Sim 過濾邏輯
3. 輸出到 training_data/fp2_q_training_data.json

使用方式:
    python batch_collect_2025_fp2_q_data.py
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from CLI_modules.cli.prediction.fp_q_data_collector import FPQDataCollector

# 2025 賽季賽事列表（按照賽曆順序）
RACES_2025 = [
    "Australia",      # 1. Melbourne
    "China",          # 2. Shanghai
    "Japan",          # 3. Suzuka
    "Bahrain",        # 4. Sakhir
    "Saudi Arabia",   # 5. Jeddah
    "Miami",          # 6. Miami
    "Emilia Romagna", # 7. Imola
    "Monaco",         # 8. Monaco
    "Spain",          # 9. Barcelona
    "Canada",         # 10. Montreal
    "Austria",        # 11. Spielberg
    "Great Britain",  # 12. Silverstone
    "Belgium",        # 13. Spa
    "Hungary",        # 14. Budapest
    "Netherlands",    # 15. Zandvoort
    "Italy",          # 16. Monza
    "Azerbaijan",     # 17. Baku
    "Singapore",      # 18. Singapore
    "United States",  # 19. Austin
    "Mexico",         # 20. Mexico City
    "Brazil",         # 21. São Paulo
    "Las Vegas",      # 22. Las Vegas
    "Qatar",          # 23. Losail
    "Abu Dhabi"       # 24. Yas Marina
]

def main():
    """主執行流程"""
    print("="*80)
    print("批次收集 2025 賽季 FP2→Q 訓練數據")
    print("="*80)
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"賽事數量: {len(RACES_2025)}")
    print("\n⚠️  注意: 使用新的 Quali Sim 過濾邏輯（SOFT 胎優先）")
    print("-"*80)
    
    # 初始化收集器
    collector = FPQDataCollector()
    
    # 收集所有賽事數據
    all_data = []
    success_count = 0
    failed_races = []
    
    for idx, race in enumerate(RACES_2025, 1):
        print(f"\n[{idx}/{len(RACES_2025)}] 收集: {race}")
        print("-"*60)
        
        try:
            # 只收集 FP2（用於訓練 FP2→Q 模型）
            data = collector.collect_single_race(
                year=2025,
                race=race,
                include_fp1=False,
                include_fp2=True,
                include_fp3=False
            )
            
            if data:
                all_data.append(data)
                success_count += 1
                print(f"✅ {race} 數據收集成功")
            else:
                failed_races.append(race)
                print(f"⚠️  {race} 數據不可用")
                
        except Exception as e:
            failed_races.append(race)
            print(f"❌ {race} 收集失敗: {str(e)[:100]}")
    
    # 保存訓練數據
    if all_data:
        output_dir = project_root / "training_data"
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / "fp2_q_training_data.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)
        
        print("\n" + "="*80)
        print("數據收集完成！")
        print("="*80)
        print(f"✅ 成功收集: {success_count}/{len(RACES_2025)} 場賽事")
        print(f"📁 輸出檔案: {output_file}")
        print(f"📊 數據大小: {output_file.stat().st_size / 1024:.2f} KB")
        
        if failed_races:
            print(f"\n⚠️  失敗賽事 ({len(failed_races)}):")
            for race in failed_races:
                print(f"   - {race}")
        
        print("\n下一步:")
        print("  1. 執行 Function 75 重新訓練模型")
        print("     python f1_analysis_modular_main.py -f 75")
        print("  2. 批次生成預測")
        print("     python batch_generate_fp2_q_predictions.py")
        
    else:
        print("\n❌ 錯誤: 沒有成功收集任何數據")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
