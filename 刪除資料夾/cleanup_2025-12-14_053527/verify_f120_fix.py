"""驗證 F120 修復效果"""
import json

# 載入數據
with open('json/fp2_corner_all_laps_analysis_2025_Abu Dhabi_FP2.json', encoding='utf-8') as f:
    data = json.load(f)

drivers = data['mode_a_unified']['drivers']

print('='*60)
print('修復驗證 - 異常車手數據檢查')
print('='*60)

# ANT T6
ant = [d for d in drivers if d['driver'] == 'ANT'][0]
print(f'\nANT T6 (低速彎):')
print(f'  最大速度: {ant["corners"]["low_speed_corner_6"]["max_speed"]} km/h')
print(f'  變異係數: {ant["corners"]["low_speed_corner_6"]["cv"]}%')
print(f'  原始速度範例: {ant["corners"]["low_speed_corner_6"]["speeds_raw"][:10]}')

# ALO T7
alo = [d for d in drivers if d['driver'] == 'ALO'][0]
print(f'\nALO T7 (中速彎):')
print(f'  最小速度: {alo["corners"]["mid_speed_corner_7"]["min_speed"]} km/h')
print(f'  變異係數: {alo["corners"]["mid_speed_corner_7"]["cv"]}%')
print(f'  原始速度範例: {alo["corners"]["mid_speed_corner_7"]["speeds_raw"][:10]}')

# ALO T8
print(f'\nALO T8 (高速彎):')
print(f'  最小速度: {alo["corners"]["high_speed_corner_8"]["min_speed"]} km/h')
print(f'  變異係數: {alo["corners"]["high_speed_corner_8"]["cv"]}%')
print(f'  原始速度範例: {alo["corners"]["high_speed_corner_8"]["speeds_raw"][:10]}')

# NOR, OCO, PIA T8
print('\n' + '='*60)
print('其他車手 T8 (高速彎) 檢查:')
print('='*60)
for driver_code in ['NOR', 'OCO', 'PIA']:
    driver = [d for d in drivers if d['driver'] == driver_code][0]
    t8 = driver["corners"]["high_speed_corner_8"]
    print(f'\n{driver_code}:')
    print(f'  最小速度: {t8["min_speed"]} km/h')
    print(f'  最大速度: {t8["max_speed"]} km/h')
    print(f'  變異係數: {t8["cv"]}%')

# 修復驗證
print('\n' + '='*60)
print('修復效果評估:')
print('='*60)

ant_t6_fixed = ant['corners']['low_speed_corner_6']['max_speed'] < 100 and ant['corners']['low_speed_corner_6']['cv'] < 15
alo_t7_fixed = alo['corners']['mid_speed_corner_7']['min_speed'] > 90 and alo['corners']['mid_speed_corner_7']['cv'] < 15
alo_t8_fixed = alo['corners']['high_speed_corner_8']['min_speed'] > 200 and alo['corners']['high_speed_corner_8']['cv'] < 15

print(f'  ANT T6: {"✅ 已修復" if ant_t6_fixed else "❌ 仍有異常"}')
print(f'  ALO T7: {"✅ 已修復" if alo_t7_fixed else "❌ 仍有異常"}')
print(f'  ALO T8: {"✅ 已修復" if alo_t8_fixed else "❌ 仍有異常"}')

if ant_t6_fixed and alo_t7_fixed and alo_t8_fixed:
    print('\n🎉 所有異常數據已成功修復！')
else:
    print('\n⚠️  部分數據仍需進一步調整')

print('='*60)
