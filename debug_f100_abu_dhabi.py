#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test Live Timing Position Changes"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import warnings
warnings.filterwarnings('ignore')

from CLI_modules.cli.analyzer.historical_flags_analysis import _calculate_position_changes_for_year

print('=' * 60)
print('Position Changes 測試 (Live Timing Only)')
print('=' * 60)

for year in [2022, 2023, 2024, 2025]:
    print(f'\n--- {year} Abu Dhabi ---')
    result = _calculate_position_changes_for_year(year, 'Abu Dhabi Grand Prix', 'R')
    print(f'  source: {result["source"]}')
    print(f'  total: {result["total"]}')
    print(f'  on_track: {result["on_track"]}')
    print(f'  pit_related: {result["pit_related"]}')
    print(f'  lap_one: {result["lap_one"]}')
