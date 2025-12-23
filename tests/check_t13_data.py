import json

# 讀取 JSON 檔案
with open('json/all_drivers_cornering_analysis_2025_Mexico_R.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

drivers = data['fastest_lap_analysis']['drivers']

print(f'總車手數: {len(drivers)}')
print('\n車手列表及 T13 (low-speed corner) 數據完整性:')
print('=' * 80)

null_entry_count = 0
null_apex_count = 0
null_exit_count = 0

for i, d in enumerate(drivers):
    driver_code = d['driver']
    t13_data = d['corners']['low_speed_corner_13']
    entry = t13_data['entry_50m_speed']
    apex = t13_data['apex_speed']
    exit = t13_data['exit_50m_speed']
    
    # 標記缺失數據
    entry_str = f'{entry:6.1f}' if entry is not None else '  NULL'
    apex_str = f'{apex:6.1f}' if apex is not None else '  NULL'
    exit_str = f'{exit:6.1f}' if exit is not None else '  NULL'
    
    if entry is None:
        null_entry_count += 1
    if apex is None:
        null_apex_count += 1
    if exit is None:
        null_exit_count += 1
    
    status = '✓' if all([entry, apex, exit]) else '⚠️'
    
    print(f'{i+1:2d}. {driver_code}: {status} | Entry: {entry_str} | Apex: {apex_str} | Exit: {exit_str}')

print('=' * 80)
print(f'\n統計摘要:')
print(f'  - 完整數據車手: {len(drivers) - max(null_entry_count, null_apex_count, null_exit_count)}')
print(f'  - Entry 缺失: {null_entry_count} 位車手')
print(f'  - Apex 缺失: {null_apex_count} 位車手')
print(f'  - Exit 缺失: {null_exit_count} 位車手')
