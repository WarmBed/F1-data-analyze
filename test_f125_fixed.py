"""
測試 F125 最佳圈速與車隊資訊整合
"""

import sys
import json
from CLI_modules.cli.analyzer.f125_vehicle_performance import run_vehicle_performance_analysis

print('[TEST] Testing F125 with Fixed Driver Mapping')
print('='*80)

# Run analysis
result = run_vehicle_performance_analysis(year=2025, race='Abu Dhabi', session='FP2')

if result and result.get('success'):
    print('[SUCCESS] Analysis completed')

    # Check first 3 drivers for new fields
    print('\n[VERIFICATION] Checking new fields in first 3 drivers:')
    print('-'*80)

    for i, driver_result in enumerate(result['driver_results'][:3], 1):
        print(f'\n{i}. {driver_result["driver"]}')
        print(f'   Team: {driver_result.get("team", "MISSING")}')
        print(f'   Team Color: {driver_result.get("team_color", "MISSING")}')

        metrics = driver_result.get('metrics', {})
        print(f'   Best Laptime: {metrics.get("best_laptime", "MISSING")}s')
        print(f'   Laptime Rank: {metrics.get("best_laptime_rank", "MISSING")}')
        print(f'   Laptime vs Expected: {metrics.get("laptime_vs_expected", "MISSING")}')

    # Check all 20 drivers have data
    drivers_with_team = sum(1 for d in result['driver_results'] if d.get('team') != 'Unknown')
    drivers_with_laptime = sum(1 for d in result['driver_results'] if d.get('metrics', {}).get('best_laptime') is not None)

    print('\n' + '='*80)
    print(f'[INFO] Drivers with team info: {drivers_with_team}/20')
    print(f'[INFO] Drivers with laptime: {drivers_with_laptime}/20')

    # Show sample JSON structure
    print('\n[SAMPLE JSON] First driver structure:')
    print('-'*80)
    first_driver = result['driver_results'][0]
    print(json.dumps({
        'driver': first_driver['driver'],
        'team': first_driver.get('team'),
        'team_color': first_driver.get('team_color'),
        'inferred_setup': first_driver['inferred_setup'],
        'suitability_score': first_driver['suitability_score'],
        'metrics': {
            'corner_rank_score': first_driver['metrics']['corner_rank_score'],
            'straight_rank_score': first_driver['metrics']['straight_rank_score'],
            'best_laptime': first_driver['metrics'].get('best_laptime'),
            'best_laptime_rank': first_driver['metrics'].get('best_laptime_rank'),
            'laptime_vs_expected': first_driver['metrics'].get('laptime_vs_expected')
        }
    }, indent=2, ensure_ascii=False))

else:
    print('[ERROR] Analysis failed')
    if result:
        print(f'Error: {result.get("error", "Unknown")}')
