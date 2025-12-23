#!/usr/bin/env python3
"""
測試事故訊息格式 - 查看包含車手資訊的訊息
"""

import fastf1
import pandas as pd

fastf1.Cache.enable_cache('f1_analysis_cache')

print('檢查 2022 日本 GP 所有賽事控制訊息...\n')
session = fastf1.get_session(2022, 'Japan', 'R')
session.load()

messages = session.race_control_messages

print(f'總共有 {len(messages)} 條訊息\n')

# 查看所有旗幟類型
print('=== 旗幟類型統計 ===')
print(messages['Flag'].value_counts())

print('\n=== 訊息類別統計 ===')
print(messages['Category'].value_counts())

print('\n=== 包含 "SPUN" 的訊息（事故） ===')
spun_messages = messages[messages['Message'].str.contains('SPUN', na=False)]
for idx, row in spun_messages.iterrows():
    print(f'\n時間: {row["Time"]}')
    print(f'旗幟: {row["Flag"]}')
    print(f'類別: {row["Category"]}')
    print(f'訊息: {row["Message"]}')
    print('-' * 80)

print('\n=== 包含 "CAR" 數字的訊息 ===')
car_messages = messages[messages['Message'].str.contains(r'CAR \d+', regex=True, na=False)]
for idx, row in car_messages.head(20).iterrows():
    print(f'\n時間: {row["Time"]}')
    print(f'旗幟: {row["Flag"]}')
    print(f'類別: {row["Category"]}')
    print(f'訊息: {row["Message"]}')
    print('-' * 80)

print('\n=== 包含 "INVOLVING" 的訊息 ===')
involving_messages = messages[messages['Message'].str.contains('INVOLVING', na=False)]
for idx, row in involving_messages.iterrows():
    print(f'\n時間: {row["Time"]}')
    print(f'旗幟: {row["Flag"]}')
    print(f'類別: {row["Category"]}')
    print(f'訊息: {row["Message"]}')
    print('-' * 80)

print('\n=== 包含 "ACCIDENT" 的訊息 ===')
accident_messages = messages[messages['Message'].str.contains('ACCIDENT', na=False)]
for idx, row in accident_messages.iterrows():
    print(f'\n時間: {row["Time"]}')
    print(f'旗幟: {row["Flag"]}')
    print(f'類別: {row["Category"]}')
    print(f'訊息: {row["Message"]}')
    print('-' * 80)

print('\n=== 包含 "STOPPED" 的訊息 ===')
stopped_messages = messages[messages['Message'].str.contains('STOPPED', na=False)]
for idx, row in stopped_messages.iterrows():
    print(f'\n時間: {row["Time"]}')
    print(f'旗幟: {row["Flag"]}')
    print(f'類別: {row["Category"]}')
    print(f'訊息: {row["Message"]}')
    print('-' * 80)
