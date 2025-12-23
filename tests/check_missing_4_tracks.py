#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查 4 個未訓練賽道的數據缺失情況
"""
from pathlib import Path

tracks = ['China', 'Austria', 'Brazil', 'Qatar']
years = [2022, 2023, 2024]

print('檢查缺失數據:')
print('=' * 70)

for track in tracks:
    print(f'\n【{track}】')
    for year in years:
        fp_q = list(Path('json/predictionJSON').glob(f'fp_q_data_{year}_{track}_*.json'))
        corner = list(Path('json').glob(f'all_drivers_cornering_analysis_{year}_{track}_FP3.json'))
        
        status_fp_q = '✅' if fp_q else '❌'
        status_corner = '✅' if corner else '❌'
        
        print(f'  {year}: FP-Q {status_fp_q} ({len(fp_q)})  |  Corner {status_corner} ({len(corner)})')
