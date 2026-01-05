"""直接测试Qatar模型训练"""
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from CLI_modules.cli.core.function_mapper import F1AnalysisFunctionMapper
from CLI_modules.cli.core.compatible_data_loader import CompatibleF1DataLoader

print("="*80)
print(" 测试Qatar模型训练")
print("="*80)

loader = CompatibleF1DataLoader()
mapper = F1AnalysisFunctionMapper(loader)

print("\n调用 Function 75...")
print("参数: track='Qatar', trials=200, cv_folds=2")

result = mapper._execute_fp2_q_batch_trainer(
    track='Qatar',
    trials=200,
    cv_folds=2
)

print("\n" + "="*80)
print(" 训练结果")
print("="*80)
print(f"Success: {result.get('success')}")
print(f"Message: {result.get('message')}")

if not result.get('success'):
    print(f"\nHint: {result.get('hint', 'N/A')}")
    print(f"Expected File: {result.get('expected_file', 'N/A')}")
