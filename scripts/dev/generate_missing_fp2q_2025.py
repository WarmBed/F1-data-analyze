"""
批量生成2025年缺失的FP2→Q预测JSON（冲刺赛周末）

此脚本将为6场冲刺赛周末生成FP2→Q预测，
会自动使用FP1 fallback机制（因为这些赛事没有FP2）。

缺失赛事：
1. China (Round 2)
2. Miami (Round 6)
3. Belgium (Round 13)
4. United States (Round 19)
5. São Paulo (Round 21)
6. Qatar (Round 23)
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from CLI_modules.cli.core.function_mapper import F1AnalysisFunctionMapper
from CLI_modules.cli.core.compatible_data_loader import CompatibleF1DataLoader

def generate_fp2q_predictions():
    """批量生成冲刺赛周末的FP2→Q预测"""
    
    # 6场冲刺赛周末（缺失FP2→Q预测的赛事）
    sprint_races = [
        {"round": 2, "name": "China", "display": "中国"},
        {"round": 6, "name": "Miami", "display": "迈阿密"},
        {"round": 13, "name": "Belgium", "display": "比利时"},
        {"round": 19, "name": "United States", "display": "美国"},
        {"round": 21, "name": "São Paulo", "display": "圣保罗"},
        {"round": 23, "name": "Qatar", "display": "卡塔尔"},
    ]
    
    print("=" * 80)
    print(" 2025 冲刺赛周末 FP2→Q 预测批量生成工具")
    print(" (自动使用 FP1 Fallback 机制)")
    print("=" * 80)
    print()
    
    # 初始化分析器
    data_loader = CompatibleF1DataLoader()
    mapper = F1AnalysisFunctionMapper(data_loader)
    
    results = {
        "success": [],
        "failed": [],
        "total": len(sprint_races)
    }
    
    for idx, race in enumerate(sprint_races, 1):
        print(f"\n[{idx}/{results['total']}] 处理赛事: {race['display']} ({race['name']})")
        print("-" * 80)
        
        try:
            # 调用 Function 76 (FP2→Q 预测生成器)
            # 会自动检测FP2不存在并fallback到FP1
            result = mapper._execute_fp2_q_prediction_generator(
                year=2025,
                race=race['name']
            )
            
            if result.get("success"):
                results["success"].append(race['display'])
                print(f"✅ {race['display']} - 预测成功")
                print(f"   数据源: {result.get('metadata', {}).get('data_source', 'Unknown')}")
                print(f"   冲刺赛周末: {result.get('metadata', {}).get('is_sprint_weekend', False)}")
            else:
                results["failed"].append(f"{race['display']} - {result.get('message', '未知错误')}")
                print(f"❌ {race['display']} - 预测失败: {result.get('message')}")
                
        except Exception as e:
            error_msg = f"{race['display']} - Exception: {str(e)}"
            results["failed"].append(error_msg)
            print(f"❌ {race['display']} - 发生异常: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    # 生成汇总报告
    print("\n" + "=" * 80)
    print(" 批量生成完成汇总")
    print("=" * 80)
    print(f"\n总计赛事: {results['total']}")
    print(f"✅ 成功: {len(results['success'])}")
    print(f"❌ 失败: {len(results['failed'])}")
    
    if results["success"]:
        print(f"\n成功列表:")
        for race in results["success"]:
            print(f"  ✅ {race}")
    
    if results["failed"]:
        print(f"\n失败列表:")
        for error in results["failed"]:
            print(f"  ❌ {error}")
    
    print("\n" + "=" * 80)
    
    # 验证JSON文件生成
    print("\n正在验证JSON文件...")
    json_dir = Path("json")
    for race in sprint_races:
        # 查找对应的JSON文件
        pattern = f"fp2_qualifying_prediction_2025_{race['name'].replace(' ', '_')}*.json"
        json_files = list(json_dir.glob(pattern))
        
        if json_files:
            json_file = json_files[0]
            size_kb = json_file.stat().st_size / 1024
            print(f"  ✅ {race['display']:12s} - {json_file.name} ({size_kb:.1f} KB)")
        else:
            print(f"  ❌ {race['display']:12s} - JSON文件未找到")
    
    print("\n" + "=" * 80)
    print(f"所有FP2→Q预测JSON已生成至 json/ 目录")
    print("=" * 80)

if __name__ == "__main__":
    generate_fp2q_predictions()
