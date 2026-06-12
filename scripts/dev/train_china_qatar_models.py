"""
为China和Qatar训练FP2→Q预测模型

这两场赛事在2022-2025训练数据集中缺失，需要单独收集数据并训练：
- China: 2024年回归（冲刺赛周末）
- Qatar: 2023-2024年有数据（冲刺赛周末）

策略：收集可用年份的数据，然后训练专属模型
"""

import sys
import json
from pathlib import Path
import fastf1

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from CLI_modules.cli.core.function_mapper import F1AnalysisFunctionMapper
from CLI_modules.cli.core.compatible_data_loader import CompatibleF1DataLoader

def check_available_data():
    """检查China和Qatar在2023-2025年的可用数据"""
    
    print("="*80)
    print(" 检查 China 和 Qatar 可用数据")
    print("="*80)
    
    races_info = {
        'Qatar': {
            'years_to_check': [2023, 2024, 2025],
            'available': []
        },
        'China': {
            'years_to_check': [2024, 2025],  # 2024年才回归
            'available': []
        }
    }
    
    for race_name, info in races_info.items():
        print(f"\n{race_name}:")
        print("-" * 40)
        
        for year in info['years_to_check']:
            try:
                schedule = fastf1.get_event_schedule(year)
                event = schedule[schedule['EventName'].str.contains(race_name, case=False)]
                
                if not event.empty:
                    event_name = event['EventName'].iloc[0]
                    event_format = event['EventFormat'].iloc[0]
                    round_num = event['RoundNumber'].iloc[0]
                    
                    print(f"  ✅ {year}: Round {round_num:2d} - {event_name:30s} - {event_format}")
                    info['available'].append(year)
                else:
                    print(f"  ❌ {year}: 无赛事")
            except Exception as e:
                print(f"  ❌ {year}: Error - {e}")
        
        print(f"\n  可用年份: {info['available']}")
    
    return races_info

def collect_race_data(race_name, years):
    """收集指定赛事的FP2→Q数据"""
    
    print(f"\n{'='*80}")
    print(f" 收集 {race_name} 的 FP2→Q 数据")
    print(f"{'='*80}")
    
    data_loader = CompatibleF1DataLoader()
    collected_data = []
    
    for year in years:
        print(f"\n[{race_name} {year}]")
        print("-" * 40)
        
        try:
            # 载入FP2数据（如果不存在会自动fallback到FP1）
            print(f"  正在载入 FP2 数据...")
            fp2_loaded = data_loader.load_race_data(year, race_name, 'FP2')
            
            if not fp2_loaded:
                print(f"  ⚠️  FP2不存在，尝试载入FP1...")
                fp1_loaded = data_loader.load_race_data(year, race_name, 'FP1')
                if not fp1_loaded:
                    print(f"  ❌ FP1也不存在，跳过此年份")
                    continue
                session_type = 'FP1'
            else:
                session_type = 'FP2'
            
            practice_session = data_loader.session
            print(f"  ✅ {session_type}数据载入成功")
            
            # 载入Q数据
            print(f"  正在载入 Q 数据...")
            q_loaded = data_loader.load_race_data(year, race_name, 'Q')
            
            if not q_loaded:
                print(f"  ❌ Q数据载入失败，跳过此年份")
                continue
            
            q_session = data_loader.session
            print(f"  ✅ Q数据载入成功")
            
            # 提取练习赛和排位赛数据
            practice_laps = practice_session.laps
            q_laps = q_session.laps
            
            if practice_laps.empty or q_laps.empty:
                print(f"  ❌ 圈速数据为空，跳过此年份")
                continue
            
            print(f"  {session_type}圈速: {len(practice_laps)} | Q圈速: {len(q_laps)}")
            
            # 这里应该实现完整的特征提取逻辑
            # 为简化示例，我们只记录基本信息
            race_data = {
                "year": year,
                "track": race_name,
                "session_type": session_type,
                "practice_laps_count": len(practice_laps),
                "q_laps_count": len(q_laps),
                "metadata": {
                    "race": race_name,
                    "year": year,
                    "session": "R",
                    "is_sprint_weekend": True
                }
            }
            
            collected_data.append(race_data)
            print(f"  ✅ 数据收集成功")
            
        except Exception as e:
            print(f"  ❌ 异常: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{race_name} 共收集 {len(collected_data)} 个年份的数据")
    return collected_data

def train_models(race_name):
    """为指定赛事训练XGBoost模型"""
    
    print(f"\n{'='*80}")
    print(f" 训练 {race_name} FP2→Q 模型")
    print(f"{'='*80}")
    
    data_loader = CompatibleF1DataLoader()
    mapper = F1AnalysisFunctionMapper(data_loader)
    
    try:
        # 调用Function 75，指定单一赛道训练
        result = mapper._execute_fp2_q_batch_trainer(
            track=race_name,
            trials=300,  # 减少试验次数以加快训练
            cv_folds=2,   # 减少CV folds（因为数据量少）
            start_year=2023,  # 从2023开始
            end_year=2025
        )
        
        if result.get("success"):
            print(f"✅ {race_name} 模型训练成功")
            return True
        else:
            print(f"❌ {race_name} 模型训练失败: {result.get('message')}")
            return False
            
    except Exception as e:
        print(f"❌ {race_name} 训练异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主流程"""
    
    print("\n" + "="*80)
    print(" China & Qatar FP2→Q 模型训练工具")
    print(" 使用 2023-2025 年数据")
    print("="*80)
    
    # 步骤1: 检查可用数据
    races_info = check_available_data()
    
    # 步骤2: 收集数据（可选，如果需要重新收集）
    print("\n" + "="*80)
    print(" 注意：当前版本直接使用Function 75训练")
    print(" Function 75会自动载入training_data/fp2_q_training_data_2022_2025.json")
    print(" 如果该文件缺少China/Qatar数据，需要先运行数据收集脚本")
    print("="*80)
    
    # 步骤3: 训练模型
    results = {}
    
    for race_name in ['Qatar', 'China']:
        available_years = races_info[race_name]['available']
        
        if not available_years:
            print(f"\n⚠️  {race_name} 没有可用数据，跳过训练")
            results[race_name] = False
            continue
        
        print(f"\n{race_name} 可用年份: {available_years}")
        
        # 尝试训练模型
        success = train_models(race_name)
        results[race_name] = success
    
    # 步骤4: 汇总结果
    print("\n" + "="*80)
    print(" 训练结果汇总")
    print("="*80)
    
    for race_name, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"  {race_name:15s}: {status}")
    
    # 步骤5: 验证模型文件
    print("\n" + "="*80)
    print(" 验证模型文件")
    print("="*80)
    
    model_dir = Path("models/fp2_q_specific_v3.10")
    for race_name in ['Qatar', 'China']:
        model_file = model_dir / f"{race_name}.pkl"
        
        if model_file.exists():
            size_kb = model_file.stat().st_size / 1024
            print(f"  ✅ {race_name:15s}: {model_file.name} ({size_kb:.1f} KB)")
        else:
            print(f"  ❌ {race_name:15s}: 模型文件不存在")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()
