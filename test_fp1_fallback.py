#!/usr/bin/env python3
"""測試 FP1 Fallback 機制"""

from CLI_modules.cli.core.function_mapper import F1AnalysisFunctionMapper
from CLI_modules.cli.core.compatible_data_loader import CompatibleF1DataLoader

print("="*70)
print("測試 Function 76: FP2→Q 預測生成器（FP1 Fallback 機制）")
print("="*70)

loader = CompatibleF1DataLoader()
mapper = F1AnalysisFunctionMapper(loader)

# 測試衝刺賽週末 (2024 Austria - 沒有 FP2)
print("\n測試賽事: 2024 Austria (衝刺賽週末)")
result = mapper._execute_fp2_q_prediction_generator(year=2024, race='Austria')

print("\n" + "="*70)
print("執行結果")
print("="*70)
print(f"Success: {result.get('success')}")
print(f"Message: {result.get('message')}")

if result.get('success'):
    metadata = result.get('data', {}).get('metadata', {})
    print(f"\nMetadata:")
    print(f"  - data_source: {metadata.get('data_source')}")
    print(f"  - is_sprint_weekend: {metadata.get('is_sprint_weekend')}")
    print(f"  - has_actual_results: {metadata.get('has_actual_results')}")
