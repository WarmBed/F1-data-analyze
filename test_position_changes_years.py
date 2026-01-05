# -*- coding: utf-8 -*-
"""測試各年份的 position_changes"""

from CLI_modules.cli.analyzer.historical_flags_analysis import _calculate_position_changes_for_year

years = ['2022', '2023', '2024', '2025']
race = 'Abu Dhabi'

print('Abu Dhabi Position Changes (on_track only):')
print('=' * 50)
for year in years:
    try:
        result = _calculate_position_changes_for_year(int(year), race, 'R')
        if isinstance(result, dict):
            on_track = result.get('on_track', 0)
            total = result.get('total', 0)
            pit_related = result.get('pit_related', 0)
            lap_one = result.get('lap_one', 0)
            print(f'{year}: on_track={on_track:3d} | total={total:3d} | pit={pit_related:3d} | lap1={lap_one:2d}')
        else:
            print(f'{year}: {result}')
    except Exception as e:
        print(f'{year}: Error - {e}')

print('=' * 50)
print('✅ on_track 是真正的賽道超車 (排除進站+出站圈)')
