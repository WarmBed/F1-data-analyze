"""
省油检测逻辑验证器
Fuel Saving Detection Logic Validator

用 2025 Abu Dhabi 真实数据验证检测准确性
"""

import json
from pathlib import Path
import statistics
from typing import Dict, List, Tuple
from collections import defaultdict


class FuelSavingValidator:
    """验证省油检测逻辑的准确性"""
    
    def __init__(self, json_file: str):
        """加载真实数据"""
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.drivers_data = data['data']['analysis']['drivers']
        self.metadata = data['data']['metadata']
        
        print(f"加载数据: {self.metadata['year']} {self.metadata['race']}")
        print(f"车手数量: {len(self.drivers_data)}")
        print()
    
    def validate_simple_baseline(
        self,
        driver_codes: List[str] = None,
        baseline_laps: int = 5,
        threshold: float = -3.0
    ):
        """
        验证简单基线方法
        
        Args:
            driver_codes: 要验证的车手列表，None 表示全部
            baseline_laps: 用于建立基线的圈数
            threshold: 省油判定阈值（百分比）
        """
        print("=" * 100)
        print(f"验证方案 1: 简单统计方法（前 {baseline_laps} 圈中位数基线 + {threshold}% 阈值）")
        print("=" * 100)
        print()
        
        if driver_codes is None:
            driver_codes = ['VER', 'NOR', 'PIA', 'LEC', 'SAI']
        
        results = {}
        
        for driver_code in driver_codes:
            driver = next((d for d in self.drivers_data if d['driver_code'] == driver_code), None)
            if not driver:
                continue
            
            print(f"\n{'='*100}")
            print(f"车手: {driver_code} ({driver['team']})")
            print(f"{'='*100}")
            
            laps = driver['laps']
            valid_laps = [
                lap for lap in laps 
                if lap['lap_time_seconds'] 
                and lap['lap_time_seconds'] < 200  # 排除进站圈
                and lap['full_throttle_ratio'] is not None
            ]
            
            if len(valid_laps) < baseline_laps + 5:
                print(f"有效圈数不足: {len(valid_laps)}")
                continue
            
            # 建立基线（前 N 圈）
            baseline_throttles = [
                lap['full_throttle_ratio'] * 100 
                for lap in valid_laps[:baseline_laps]
            ]
            baseline = statistics.median(baseline_throttles)
            
            print(f"\n基线圈 (Lap 1-{baseline_laps}):")
            print(f"  油门数据: {[f'{t:.1f}%' for t in baseline_throttles]}")
            print(f"  中位数基线: {baseline:.2f}%")
            print()
            
            # 检测后续圈
            fuel_saving_laps = []
            normal_laps = []
            
            print(f"{'Lap':<6} {'Throttle':<12} {'vs Baseline':<15} {'判定':<10}")
            print("-" * 100)
            
            for i, lap in enumerate(valid_laps, start=1):
                throttle = lap['full_throttle_ratio'] * 100
                deviation = throttle - baseline
                
                is_fuel_saving = deviation <= threshold
                status = "🔴 省油" if is_fuel_saving else "🟢 正常"
                
                if i > baseline_laps:  # 跳过基线圈
                    if is_fuel_saving:
                        fuel_saving_laps.append(i)
                    else:
                        normal_laps.append(i)
                    
                    print(f"{i:<6} {throttle:<12.2f} {deviation:>+6.2f}%{' '*8} {status}")
            
            # 统计
            total_test_laps = len(valid_laps) - baseline_laps
            fuel_saving_count = len(fuel_saving_laps)
            fuel_saving_rate = fuel_saving_count / total_test_laps * 100 if total_test_laps > 0 else 0
            
            print("\n" + "-" * 100)
            print(f"统计:")
            print(f"  测试圈数: {total_test_laps}")
            print(f"  检测到省油圈: {fuel_saving_count} ({fuel_saving_rate:.1f}%)")
            print(f"  正常圈: {len(normal_laps)} ({100-fuel_saving_rate:.1f}%)")
            
            if fuel_saving_laps:
                print(f"  省油圈号: {fuel_saving_laps[:10]}{'...' if len(fuel_saving_laps) > 10 else ''}")
            
            results[driver_code] = {
                'baseline': baseline,
                'fuel_saving_laps': fuel_saving_laps,
                'fuel_saving_rate': fuel_saving_rate,
                'total_laps': total_test_laps
            }
        
        return results
    
    def analyze_fp2_correlation(self, driver_codes: List[str] = None):
        """
        分析 FP2 与 Race 的相关性
        
        评估是否可以用 FP2 数据校正 Race 的基线
        """
        print("\n\n" + "=" * 100)
        print("验证方案 2: FP2 数据作为校正基线的可行性")
        print("=" * 100)
        print()
        
        # 需要加载 FP2 数据
        fp2_file = Path("json/driver_throttle_ratio_2025_Abu Dhabi_FP2.json")
        
        if not fp2_file.exists():
            print("❌ FP2 数据文件不存在，无法验证")
            print("需要: json/driver_throttle_ratio_2025_Abu Dhabi_FP2.json")
            return None
        
        with open(fp2_file, 'r', encoding='utf-8') as f:
            fp2_data = json.load(f)
        
        fp2_drivers = fp2_data['data']['analysis']['drivers']
        
        if driver_codes is None:
            driver_codes = ['VER', 'NOR', 'PIA']
        
        print(f"对比 FP2 vs Race 的油门使用率:")
        print()
        
        comparison = {}
        
        for driver_code in driver_codes:
            # Race 数据
            race_driver = next((d for d in self.drivers_data if d['driver_code'] == driver_code), None)
            # FP2 数据
            fp2_driver = next((d for d in fp2_drivers if d['driver_code'] == driver_code), None)
            
            if not race_driver or not fp2_driver:
                continue
            
            # 计算 Race 平均
            race_laps = [
                lap['full_throttle_ratio'] * 100 
                for lap in race_driver['laps'] 
                if lap['lap_time_seconds'] and lap['lap_time_seconds'] < 200
                and lap['full_throttle_ratio'] is not None
            ]
            
            # 计算 FP2 平均
            fp2_laps = [
                lap['full_throttle_ratio'] * 100 
                for lap in fp2_driver['laps'] 
                if lap['lap_time_seconds'] and lap['lap_time_seconds'] < 200
                and lap['full_throttle_ratio'] is not None
            ]
            
            if not race_laps or not fp2_laps:
                continue
            
            race_avg = statistics.mean(race_laps)
            fp2_avg = statistics.mean(fp2_laps)
            difference = race_avg - fp2_avg
            
            print(f"{driver_code}:")
            print(f"  FP2 平均:  {fp2_avg:.2f}%")
            print(f"  Race 平均: {race_avg:.2f}%")
            print(f"  差异:      {difference:+.2f}%")
            print()
            
            comparison[driver_code] = {
                'fp2_avg': fp2_avg,
                'race_avg': race_avg,
                'difference': difference
            }
        
        # 评估相关性
        if comparison:
            differences = [v['difference'] for v in comparison.values()]
            avg_diff = statistics.mean(differences)
            std_diff = statistics.stdev(differences) if len(differences) > 1 else 0
            
            print("-" * 100)
            print(f"FP2 vs Race 差异统计:")
            print(f"  平均差异: {avg_diff:+.2f}%")
            print(f"  标准差:   {std_diff:.2f}%")
            print()
            
            if abs(avg_diff) < 2.0 and std_diff < 3.0:
                print("✅ FP2 与 Race 相关性强，可以用于校正")
            elif abs(avg_diff) < 5.0:
                print("🟡 FP2 与 Race 有一定相关性，可谨慎使用")
            else:
                print("❌ FP2 与 Race 差异较大，不建议直接使用")
        
        return comparison
    
    def compare_baseline_strategies(self, driver_code: str = 'VER'):
        """
        对比不同基线策略的效果
        
        1. 前 3 圈
        2. 前 5 圈
        3. 前 10 圈
        4. 整场中位数
        """
        print("\n\n" + "=" * 100)
        print(f"验证方案 3: 对比不同基线策略 (车手: {driver_code})")
        print("=" * 100)
        print()
        
        driver = next((d for d in self.drivers_data if d['driver_code'] == driver_code), None)
        if not driver:
            print(f"找不到车手: {driver_code}")
            return None
        
        valid_laps = [
            lap for lap in driver['laps'] 
            if lap['lap_time_seconds'] 
            and lap['lap_time_seconds'] < 200
            and lap['full_throttle_ratio'] is not None
        ]
        
        throttle_data = [lap['full_throttle_ratio'] * 100 for lap in valid_laps]
        
        strategies = {
            '前 3 圈': statistics.median(throttle_data[:3]),
            '前 5 圈': statistics.median(throttle_data[:5]),
            '前 10 圈': statistics.median(throttle_data[:10]),
            '整场中位数': statistics.median(throttle_data),
        }
        
        print(f"{'策略':<15} {'基线':<10} {'vs 整场':<12} {'评估'}")
        print("-" * 100)
        
        full_median = strategies['整场中位数']
        
        for name, baseline in strategies.items():
            diff = baseline - full_median
            
            if abs(diff) < 1.0:
                assessment = "✅ 很准确"
            elif abs(diff) < 2.0:
                assessment = "🟡 可接受"
            else:
                assessment = "❌ 偏差大"
            
            print(f"{name:<15} {baseline:<10.2f} {diff:>+6.2f}%{' '*4} {assessment}")
        
        print()
        print("建议:")
        print("  - 前 3 圈: 最快建立，但可能受第一圈 outlap 影响")
        print("  - 前 5 圈: 平衡速度与准确性，推荐 ✅")
        print("  - 前 10 圈: 最准确，但延迟太大")
        print("  - 整场中位数: 仅用于离线分析")
        
        return strategies


def main():
    """主验证流程"""
    
    # 加载数据
    validator = FuelSavingValidator("json/driver_throttle_ratio_2025_Abu Dhabi_R.json")
    
    # 方案 1: 简单统计方法验证
    print("\n" + "🔬 开始验证".center(100, "="))
    print()
    
    results = validator.validate_simple_baseline(
        driver_codes=['VER', 'NOR', 'PIA'],
        baseline_laps=5,
        threshold=-3.0
    )
    
    # 方案 2: FP2 相关性分析
    fp2_correlation = validator.analyze_fp2_correlation(['VER', 'NOR', 'PIA'])
    
    # 方案 3: 基线策略对比
    baseline_strategies = validator.compare_baseline_strategies('VER')
    
    # 总结建议
    print("\n\n" + "=" * 100)
    print("📊 验证总结与建议")
    print("=" * 100)
    print()
    
    print("1. 简单统计方法 (当前方案)")
    print("   ✅ 优点: 实现简单，实时性强，无需训练")
    print("   ❌ 缺点: 可能误判正常波动")
    print()
    
    print("2. 机器学习方法 (XGBoost)")
    print("   ✅ 优点: 可考虑多维特征（轮胎、燃油、赛道位置等）")
    print("   ❌ 缺点: 需要标注数据、训练时间、可能过拟合")
    print()
    
    print("3. 推荐方案: 混合策略")
    print("   第一阶段: 使用简单统计方法（前 5 圈基线 + -3% 阈值）")
    print("   第二阶段: 如果检测到频繁误判，再考虑机器学习")
    print("   第三阶段: 用 FP2 数据作为参考，但不直接作为基线")
    print()
    
    print("4. FP2 校正方案:")
    if fp2_correlation:
        avg_diff = statistics.mean([v['difference'] for v in fp2_correlation.values()])
        print(f"   FP2 vs Race 平均差异: {avg_diff:+.2f}%")
        if abs(avg_diff) < 2.0:
            print("   ✅ 可以用 FP2 数据微调 Race 基线")
            print(f"   建议: Race 基线 = FP2 基线 + {avg_diff:.2f}%")
        else:
            print("   ❌ FP2 与 Race 差异较大，不建议直接使用")
    else:
        print("   ⚪ 无 FP2 数据，无法验证")
    
    print()
    print("=" * 100)
    print("✅ 验证完成")
    print("=" * 100)


if __name__ == "__main__":
    main()
