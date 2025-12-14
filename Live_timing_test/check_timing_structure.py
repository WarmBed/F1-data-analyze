#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""檢查 Position.json 結構 - 提取起跑和最終位置"""

import json
from core.logger import get_logger

logger = get_logger("live_timing_test.check_timing_structure", component="gui")

base = r'c:\Users\mike2\OneDrive\Code\F1-data-analyze\json\LiveF1\2023\Australian_Race'

# 檢查 Position.json
pos_path = f'{base}/Position.json'
with open(pos_path, 'r', encoding='utf-8') as f:
    pos_data = json.load(f)

logger.info('Position.json records: %s', len(pos_data.get("records", [])))

# 收集第一筆和最後一筆 Position
first_positions = None
last_positions = None

for rec in pos_data['records']:
    d = rec.get('data', {})
    if isinstance(d, dict) and 'Position' in d:
        positions = d['Position']
        if first_positions is None:
            first_positions = positions.copy()
        last_positions = positions.copy()

logger.info('起跑位置 (第一筆數據):')
if first_positions:
    for entry in first_positions[:5]:
    logger.info("  #%s: P%s", entry.get('RacingNumber'), entry.get('Position'))

logger.info('最終位置 (最後一筆數據):')
if last_positions:
    for entry in last_positions[:5]:
    logger.info("  #%s: P%s", entry.get('RacingNumber'), entry.get('Position'))
        
# 讀取 DriverList 以獲取車手名稱
driver_path = f'{base}/DriverList.json'
with open(driver_path, 'r', encoding='utf-8') as f:
    dl = json.load(f)

logger.info('車手列表:')
drivers = {}
for rec in dl.get('records', []):
    d = rec.get('data', {})
    if isinstance(d, dict):
        for num, info in d.items():
            if isinstance(info, dict) and 'Tla' in info:
                drivers[num] = info.get('Tla', '')
                
for num, tla in list(drivers.items())[:5]:
                    logger.info("  #%s: %s", num, tla)
