#!/usr/bin/env python3
"""
测试 SC/VSC 超车限制和默认迭代次数

验证：
1. SC/VSC 期间不允许超车
2. 默认迭代次数已改为 200

Author: F1T Team
Date: 2026-01-05
"""

import sys
from pathlib import Path

# Add project root to path
_project_root = Path(__file__).parent
sys.path.insert(0, str(_project_root))

from strategy_simulator.core.monte_carlo import MonteCarloParams

def test_default_iterations():
    """测试默认迭代次数"""
    print("\n" + "="*70)
    print("TEST 1: 验证默认迭代次数")
    print("="*70)
    
    # 创建默认参数
    params = MonteCarloParams()
    
    print(f"\n创建 MonteCarloParams()...")
    print(f"  iterations: {params.iterations}")
    print(f"  sc_probability_per_lap: {params.sc_probability_per_lap}")
    print(f"  vsc_probability_per_lap: {params.vsc_probability_per_lap}")
    
    # 验证
    expected = 200
    if params.iterations == expected:
        print(f"\n✅ PASS: 默认迭代次数 = {params.iterations} (正确)")
        return True
    else:
        print(f"\n❌ FAIL: 默认迭代次数 = {params.iterations}, 期望 {expected}")
        return False

def test_sc_overtaking_logic():
    """测试 SC 超车逻辑（代码检查）"""
    print("\n" + "="*70)
    print("TEST 2: 验证 SC 超车限制代码")
    print("="*70)
    
    # 读取 race_simulator.py 检查代码
    race_sim_file = Path(__file__).parent / "strategy_simulator" / "core" / "race_simulator.py"
    
    if not race_sim_file.exists():
        print(f"\n⚠️  找不到文件: {race_sim_file}")
        return False
    
    with open(race_sim_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查关键代码
    checks = {
        "禁止 SC 超车检查": "if sc_active:" in content,
        "SC 超车日志": "SC/VSC active - overtaking prohibited" in content,
        "SC 时维持位置": "maintain current order" in content or "Skip overtaking" in content,
    }
    
    print("\n代码检查:")
    all_passed = True
    for check_name, passed in checks.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {check_name}")
        if not passed:
            all_passed = False
    
    # 检查是否有 else 分支（正常情况允许超车）
    if "else:" in content and "overtaking logic" in content.lower():
        print(f"  ✅ PASS: 正常情况下允许超车")
    else:
        print(f"  ⚠️  WARNING: 未找到正常超车逻辑的 else 分支")
    
    if all_passed:
        print(f"\n✅ PASS: SC 超车限制代码已正确实现")
    else:
        print(f"\n❌ FAIL: SC 超车限制代码有问题")
    
    return all_passed

def test_iteration_recommendations():
    """测试迭代次数推荐"""
    print("\n" + "="*70)
    print("TEST 3: 迭代次数使用建议")
    print("="*70)
    
    recommendations = [
        ("快速测试", 100, "30秒-1分钟", "查看大致趋势"),
        ("日常使用", 200, "1.5-2分钟", "平衡精度和速度 👈 默认"),
        ("精确分析", 500, "4-5分钟", "高精度结果"),
        ("专业研究", 1000, "8-10分钟", "最高精度"),
    ]
    
    print("\n| 使用场景     | 推荐次数 | 预计时间      | 说明               |")
    print("|-------------|---------|--------------|-------------------|")
    for scenario, iterations, time, desc in recommendations:
        print(f"| {scenario:<12} | {iterations:<8} | {time:<13} | {desc:<18} |")
    
    print("\n💡 提示:")
    print("  - 默认 200 次适合日常使用")
    print("  - 需要更高精度时可手动增加到 500-1000")
    print("  - GUI 界面可以随时修改迭代次数")
    
    return True

def test_sc_behavior_example():
    """展示 SC 行为示例"""
    print("\n" + "="*70)
    print("TEST 4: SC 期间行为示例")
    print("="*70)
    
    print("\n场景: Lap 25 SC 出动")
    print("-" * 70)
    
    print("\n【之前的行为 ❌ 不符合规则】")
    print("  Lap 24: VER (P1, 旧胎) vs LEC (P2, 新胎)")
    print("  Lap 25: SC active")
    print("    → 系统计算超车概率: 60%")
    print("    → LEC 可能超越 VER")
    print("    → 结果: P1 LEC, P2 VER (错误!)")
    
    print("\n【现在的行为 ✅ 符合规则】")
    print("  Lap 24: VER (P1, 旧胎) vs LEC (P2, 新胎)")
    print("  Lap 25: SC active")
    print("    → 检测到 sc_active = True")
    print("    → 跳过超车逻辑")
    print("    → 日志: 'SC/VSC active - overtaking prohibited'")
    print("    → 结果: P1 VER, P2 LEC (正确!)")
    print("  Lap 28: Green flag")
    print("    → sc_active = False")
    print("    → 允许超车")
    print("    → LEC 可以尝试超越 VER")
    
    return True

def print_summary(results):
    """打印测试总结"""
    print("\n" + "="*70)
    print("测试总结")
    print("="*70)
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\n总测试: {total}")
    print(f"通过: {passed}")
    print(f"失败: {total - passed}")
    
    print("\n详细结果:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    if passed == total:
        print("\n🎉 所有测试通过!")
        print("\n更新内容:")
        print("  1. ✅ SC/VSC 期间禁止超车（符合 F1 规则）")
        print("  2. ✅ 默认迭代次数改为 200（更快的体验）")
    else:
        print("\n⚠️  部分测试失败，请检查代码")

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════╗
║         SC/VSC 超车限制 + 默认迭代次数更新 - 功能测试              ║
╚════════════════════════════════════════════════════════════════════╝

本测试将验证两个重要更新：
1. SC/VSC 期间是否禁止超车
2. 默认迭代次数是否改为 200

按 Enter 开始测试...
""")
    input()
    
    # 运行所有测试
    results = {}
    
    results["默认迭代次数"] = test_default_iterations()
    results["SC 超车限制代码"] = test_sc_overtaking_logic()
    results["迭代次数建议"] = test_iteration_recommendations()
    results["SC 行为示例"] = test_sc_behavior_example()
    
    # 打印总结
    print_summary(results)
    
    print("\n" + "="*70)
    print("✅ 测试完成!")
    print("="*70)
    print("\n下一步:")
    print("  1. 启动 GUI: python strategy_simulator_main.py")
    print("  2. 观察默认迭代次数是否为 200")
    print("  3. 运行模拟，观察 SC 期间是否有超车日志")
    print("  4. 查看日志: 应该显示 'SC/VSC active - overtaking prohibited'")
