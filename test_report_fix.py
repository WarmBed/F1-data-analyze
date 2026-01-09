"""
测试策略报告生成器的修复

验证即使没有完整的 stints 对象，
也能从策略名称解析出基本策略细节。
"""
from strategy_simulator.gui.widgets.strategy_report_generator import StrategyReportGenerator

# 创建一个最小化的策略对象（模拟实际问题场景）
class MinimalResult:
    def __init__(self, name, win_prob=2.0):
        self.strategy_name = name
        self.win_probability = win_prob
        self.expected_position = 2
        self.stints = []  # 空！这是问题的根源

# 测试不同的策略名称格式
test_cases = [
    ("H-S", "硬胎-软胎 两停"),
    ("M-H", "中胎-硬胎 两停"),
    ("S-M-H", "软胎-中胎-硬胎 三停"),
    ("M20-H", "中胎20圈-硬胎"),
    ("Plan A", "命名策略"),
]

print("\n" + "="*80)
print("策略报告生成器修复测试")
print("="*80)

generator = StrategyReportGenerator()

for strategy_name, description in test_cases:
    print(f"\n测试策略: {strategy_name} ({description})")
    print("-" * 80)
    
    # 创建最小化结果对象
    strategy_result = MinimalResult(strategy_name)
    
    # 生成报告
    try:
        report = generator.generate_report(
            strategy_result=strategy_result,
            our_driver="NOR",
            grid_position=1,
            track_name="Yas Marina",
            race_laps=58,
        )
        
        # 提取"關鍵決策點分析"部分
        lines = report.split('\n')
        in_section = False
        section_lines = []
        
        for line in lines:
            if '關鍵決策點分析' in line:
                in_section = True
            elif in_section:
                if '第二節' in line or '第二节' in line:
                    break
                section_lines.append(line)
        
        # 检查是否有"無法取得策略細節"
        has_error = any('無法取得策略細節' in l for l in section_lines)
        has_details = any('決策點' in l for l in section_lines)
        
        if has_error:
            print("  ❌ 仍然显示'無法取得策略細節'")
        elif has_details:
            print("  ✅ 成功生成策略细节！")
            # 显示前几行
            for line in section_lines[:15]:
                if line.strip():
                    print(f"     {line}")
        else:
            print("  ⚠️  无法确定状态")
            
    except Exception as e:
        print(f"  ❌ 异常: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*80)
print("测试完成！")
print("="*80)
