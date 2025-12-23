"""
驗證所有 20 位車手的數據完整性
"""

from CLI_modules.cli.analyzer.f125_vehicle_performance import run_vehicle_performance_analysis

result = run_vehicle_performance_analysis(year=2025, race='Abu Dhabi', session='FP2')

if result and result.get('success'):
    drivers_with_team = sum(1 for d in result['driver_results'] if d.get('team') != 'Unknown')
    drivers_with_laptime = sum(1 for d in result['driver_results'] if d.get('metrics', {}).get('best_laptime') is not None)

    print(f'Drivers with team info: {drivers_with_team}/20')
    print(f'Drivers with laptime: {drivers_with_laptime}/20')

    # Show all drivers with their data
    print('\nAll 20 drivers:')
    print('='*100)
    print(f"{'#':>2} {'Driver':3} | {'Team':20} | {'Laptime':>10} {'Rank':>4} | {'vs Expected':>11}")
    print('-'*100)

    for i, d in enumerate(result['driver_results'], 1):
        m = d['metrics']
        laptime = m.get('best_laptime', 0)
        rank = m.get('best_laptime_rank', '-')
        vs_exp = m.get('laptime_vs_expected', 0)
        team = d.get('team', 'Unknown')[:20]

        print(f'{i:2d}. {d["driver"]:3s} | {team:20s} | {laptime:8.3f}s  P{rank:>2} | {vs_exp:+5.1f}')
