"""
专门为 China 和 Qatar 收集 FP2→Q 训练数据

这两场赛事在现有训练数据集中缺失，需要单独收集：
- Qatar: 2023, 2024 年（冲刺赛周末）
- China: 2024 年（冲刺赛周末，2025年未举办）
"""
import sys
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from CLI_modules.cli.prediction.fp_q_data_collector import FPQDataCollector

def main():
    print("\n" + "="*80)
    print(" China & Qatar FP2→Q 数据收集工具")
    print("="*80)
    
    collector = FPQDataCollector()
    
    # 定义要收集的赛事
    races_to_collect = [
        {"year": 2023, "race": "Qatar"},
        {"year": 2024, "race": "Qatar"},
        {"year": 2024, "race": "China"},
    ]
    
    collected_data = []
    success_count = 0
    failed_races = []
    
    for idx, race_info in enumerate(races_to_collect, 1):
        year = race_info["year"]
        race = race_info["race"]
        
        print(f"\n[{idx}/{len(races_to_collect)}] 收集: {year} {race}")
        print("-" * 80)
        
        try:
            # 收集 FP2→Q 数据（冲刺赛周末会自动fallback到FP1）
            race_data = collector.collect_single_race(
                year=year,
                race=race,
                include_fp1=False,  # 主要收集FP2
                include_fp2=True,
                include_fp3=False
            )
            
            if race_data:
                collected_data.append(race_data)
                success_count += 1
                print(f"✅ {year} {race} 数据收集成功")
                
                # 显示数据统计
                if 'drivers' in race_data:
                    driver_count = len(race_data['drivers'])
                    print(f"   收集到 {driver_count} 位车手的数据")
            else:
                failed_races.append(f"{year} {race}")
                print(f"⚠️  {year} {race} 数据收集失败（数据不可用）")
                
        except Exception as e:
            failed_races.append(f"{year} {race}")
            print(f"❌ {year} {race} 收集异常: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # 合并到现有训练数据
    if collected_data:
        print("\n" + "="*80)
        print(" 合并到现有训练数据集")
        print("="*80)
        
        training_data_dir = Path("training_data")
        training_data_dir.mkdir(exist_ok=True)
        
        # 载入现有数据
        existing_data_file = training_data_dir / "fp2_q_training_data_2022_2025.json"
        
        if existing_data_file.exists():
            print(f"\n载入现有数据: {existing_data_file}")
            with open(existing_data_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            print(f"✅ 现有数据: {len(existing_data)} 笔赛事记录")
        else:
            print(f"\n⚠️  现有数据文件不存在，将创建新文件")
            existing_data = []
        
        # 合并新数据
        all_data = existing_data + collected_data
        
        # 保存合并后的数据
        with open(existing_data_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ 数据已保存: {existing_data_file}")
        print(f"   总计: {len(all_data)} 笔赛事记录")
        print(f"   新增: {len(collected_data)} 笔")
        
        # 验证赛道覆盖
        tracks = set()
        for record in all_data:
            track = record.get('track') or record.get('metadata', {}).get('race', 'Unknown')
            tracks.add(track)
        
        print(f"\n✅ 赛道覆盖: {len(tracks)} 个")
        if 'Qatar' in tracks:
            print("   ✅ Qatar 已包含")
        if 'China' in tracks:
            print("   ✅ China 已包含")
    
    # 汇总结果
    print("\n" + "="*80)
    print(" 收集结果汇总")
    print("="*80)
    print(f"总计尝试: {len(races_to_collect)} 场")
    print(f"✅ 成功: {success_count}")
    print(f"❌ 失败: {len(failed_races)}")
    
    if failed_races:
        print(f"\n失败列表:")
        for race in failed_races:
            print(f"  - {race}")
    
    print("\n" + "="*80)
    print(" 下一步：训练模型")
    print("="*80)
    print("执行以下命令为这两场赛事训练模型：")
    print("  python f1_analysis_modular_main.py -f 75 --track Qatar --trials 200")
    print("  python f1_analysis_modular_main.py -f 75 --track China --trials 200")
    print("="*80)

if __name__ == "__main__":
    main()
