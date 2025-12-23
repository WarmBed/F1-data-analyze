#!/usr/bin/env python3
"""測試彎道顏色標記 - 創建包含紅旗的測試數據"""

import json
import sys

# 讀取原始數據
with open('json/historical_flags_Japan_2022-2025_20251109_152903.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 修改 T1 和 T2 添加紅旗（用於測試）
corner_analysis = data['data']['corner_analysis']

# T1: 只有紅旗
if 'T1' in corner_analysis:
    corner_analysis['T1']['yearly_breakdown']['2022'] = {
        'yellow': 0.0,
        'double_yellow': 0.0,
        'red': 1.0
    }

# T2: 黃旗 + 紅旗（應該顯示半圓）
if 'T2' in corner_analysis:
    corner_analysis['T2']['yearly_breakdown']['2022'] = {
        'yellow': 0.5,
        'double_yellow': 0.0,
        'red': 0.5
    }

# T3: 只有黃旗（保持原樣或添加）
if 'T3' not in corner_analysis:
    corner_analysis['T3'] = {'yearly_breakdown': {}}
corner_analysis['T3']['yearly_breakdown']['2022'] = {
    'yellow': 1.0,
    'double_yellow': 0.0,
    'red': 0.0
}

# 保存測試數據
output_file = 'json/historical_flags_Japan_2022-2025_TEST.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f'✅ 測試數據已生成: {output_file}')
print('\n測試彎道配置:')
print('  T1: 🔴 只有紅旗')
print('  T2: 🔴🟡 紅旗 + 黃旗（左紅右黃）')
print('  T3: 🟡 只有黃旗')
print('  T7-T18: 🟡 黃旗/雙黃旗')
