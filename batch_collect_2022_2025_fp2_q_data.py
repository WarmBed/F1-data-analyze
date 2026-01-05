"""
2022-2025 FP2→Q 訓練數據收集器
收集 4 個賽季的歷史數據，為 2026 年預測做準備
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from CLI_modules.cli.prediction.fp_q_data_collector import FPQDataCollector
import json
from pathlib import Path

# 2022-2025 賽季的賽事列表
RACES_BY_YEAR = {
    2022: [
        "Bahrain", "Saudi Arabia", "Australia", "Emilia Romagna", "Miami",
        "Spain", "Monaco", "Azerbaijan", "Canada", "Great Britain",
        "Austria", "France", "Hungary", "Belgium", "Netherlands",
        "Italy", "Singapore", "Japan", "United States", "Mexico",
        "Brazil", "Abu Dhabi"
    ],
    2023: [
        "Bahrain", "Saudi Arabia", "Australia", "Azerbaijan", "Miami",
        "Monaco", "Spain", "Canada", "Austria", "Great Britain",
        "Hungary", "Belgium", "Netherlands", "Italy", "Singapore",
        "Japan", "Qatar", "United States", "Mexico", "Brazil",
        "Las Vegas", "Abu Dhabi"
    ],
    2024: [
        "Bahrain", "Saudi Arabia", "Australia", "Japan", "China",
        "Miami", "Emilia Romagna", "Monaco", "Canada", "Spain",
        "Austria", "Great Britain", "Hungary", "Belgium", "Netherlands",
        "Italy", "Azerbaijan", "Singapore", "United States", "Mexico",
        "Brazil", "Las Vegas", "Qatar", "Abu Dhabi"
    ],
    2025: [
        "Australia", "China", "Japan", "Bahrain", "Saudi Arabia",
        "Miami", "Emilia Romagna", "Monaco", "Spain", "Canada",
        "Austria", "Great Britain", "Belgium", "Hungary", "Netherlands",
        "Italy", "Azerbaijan", "Singapore", "United States", "Mexico",
        "Brazil", "Las Vegas", "Qatar", "Abu Dhabi"
    ]
}

def main():
    print("\n" + "="*70)
    print("2022-2025 FP2→Q 訓練數據收集器")
    print("="*70)
    print("目標: 收集 4 個賽季的歷史數據")
    print("用途: 訓練模型以預測 2026 年")
    
    collector = FPQDataCollector()
    all_data = []
    
    total_races = sum(len(races) for races in RACES_BY_YEAR.values())
    current_count = 0
    success_count = 0
    failed_races = []
    
    for year, races in RACES_BY_YEAR.items():
        print(f"\n{'='*70}")
        print(f"收集 {year} 賽季 ({len(races)} 場賽事)")
        print(f"{'='*70}")
        
        for race in races:
            current_count += 1
            print(f"\n[{current_count}/{total_races}] 收集: {year} {race}")
            print("-" * 60)
            
            try:
                # 收集單一賽事數據 (只收集 FP2)
                race_data = collector.collect_single_race(
                    year=year,
                    race=race,
                    include_fp1=False,
                    include_fp2=True,
                    include_fp3=False
                )
                
                if race_data:
                    all_data.append(race_data)
                    success_count += 1
                    print(f"✅ {year} {race} 數據收集成功")
                else:
                    failed_races.append(f"{year} {race}")
                    print(f"⚠️  {year} {race} 數據收集失敗（數據不可用）")
                    
            except Exception as e:
                failed_races.append(f"{year} {race}")
                print(f"❌ {year} {race} 收集異常: {str(e)}")
                continue
    
    # 保存數據
    if all_data:
        output_dir = Path("training_data")
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / "fp2_q_training_data_2022_2025.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)
        
        file_size = output_file.stat().st_size / 1024  # KB
        
        print(f"\n{'='*70}")
        print("數據收集完成！")
        print(f"{'='*70}")
        print(f"✅ 成功收集: {success_count}/{total_races} 場賽事")
        print(f"📁 輸出檔案: {output_file}")
        print(f"📊 數據大小: {file_size:.2f} KB")
        
        if failed_races:
            print(f"\n⚠️  失敗賽事 ({len(failed_races)}):")
            for race in failed_races:
                print(f"   - {race}")
        
        # 統計各賽道數據量
        track_counts = {}
        for record in all_data:
            metadata = record.get('metadata', {})
            race_name = metadata.get('race', 'Unknown')
            track_counts[race_name] = track_counts.get(race_name, 0) + 1
        
        print(f"\n📊 各賽道數據量:")
        for track, count in sorted(track_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {track}: {count} 年")
        
        print(f"\n下一步:")
        print(f"  1. 執行 Function 75 重新訓練模型")
        print(f"     python f1_analysis_modular_main.py -f 75")
        print(f"  2. 模型將基於 2022-2025 數據訓練")
        print(f"  3. 準備預測 2026 年賽事")
        
    else:
        print("\n❌ 未收集到任何數據")

if __name__ == "__main__":
    main()
