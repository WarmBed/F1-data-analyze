#!/usr/bin/env python3
"""
測試黃旗訊息格式 - 確認是否包含車手、圈數和原因
"""

import fastf1
import pandas as pd

fastf1.Cache.enable_cache('f1_analysis_cache')

print('檢查 2022 日本 GP 黃旗訊息格式...\n')
session = fastf1.get_session(2022, 'Japan', 'R')
session.load()

messages = session.race_control_messages

# 過濾黃旗相關訊息
yellow_flags = messages[
    (messages['Flag'] == 'YELLOW') | 
    (messages['Flag'] == 'DOUBLE YELLOW') |
    (messages['Message'].str.contains('YELLOW', na=False))
].copy()

print(f'找到 {len(yellow_flags)} 條黃旗相關訊息\n')
print('=== 前 20 條黃旗訊息 ===')
for idx, row in yellow_flags.head(20).iterrows():
    print(f'\n時間: {row["Time"]}')
    print(f'旗幟: {row["Flag"]}')
    print(f'類別: {row["Category"]}')
    print(f'訊息: {row["Message"]}')
    print('-' * 80)

print('\n\n=== 分析黃旗訊息特徵 ===')
print(f'\n包含 "SPUN" 的訊息:')
spun_messages = yellow_flags[yellow_flags['Message'].str.contains('SPUN', na=False)]
for idx, row in spun_messages.head(10).iterrows():
    print(f'{row["Time"]} | {row["Flag"]} | {row["Message"]}')

print(f'\n包含 "CAR" 的訊息:')
car_messages = yellow_flags[yellow_flags['Message'].str.contains('CAR \d+', regex=True, na=False)]
for idx, row in car_messages.head(10).iterrows():
    print(f'{row["Time"]} | {row["Flag"]} | {row["Message"]}')

print(f'\n包含 "INVOLVING" 的訊息:')
involving_messages = yellow_flags[yellow_flags['Message'].str.contains('INVOLVING', na=False)]
for idx, row in involving_messages.head(10).iterrows():
    print(f'{row["Time"]} | {row["Flag"]} | {row["Message"]}')

print(f'\n包含 "TRACK SECTOR" 的訊息（位置訊息）:')
sector_messages = yellow_flags[yellow_flags['Message'].str.contains('TRACK SECTOR', na=False)]
for idx, row in sector_messages.head(10).iterrows():
    print(f'{row["Time"]} | {row["Flag"]} | {row["Message"]}')
