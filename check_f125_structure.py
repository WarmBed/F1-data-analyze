"""檢查 F125 車輛性能分析數據結構"""
import json

# 載入 F125 數據
with open('json/vehicle_performance_analysis_2025_Abu Dhabi_FP2.json', encoding='utf-8') as f:
    data = json.load(f)

print('=== F125 車輛性能分析 - Abu Dhabi 2025 FP2 ===\n')

# 按圈時排序
times = []
for dr in data['driver_results']:
    m = dr['metrics']
    lap = m.get('best_laptime')
    if lap:
        times.append((dr['driver'], dr['team'], lap, m.get('corner_rank_score', 0), m.get('straight_rank_score', 0)))

times.sort(key=lambda x: x[2])
fastest = times[0][2] if times else 83.0

print('車手圈時排序:')
print(f"{'#':>2} | {'Driver':4} | {'Team':15} | {'Best Lap':>10} | {'Delta':>8} | {'Corner':>7} | {'Straight':>8}")
print('-' * 80)

for i, (driver, team, lap, corner, straight) in enumerate(times, 1):
    delta = lap - fastest
    print(f"{i:2} | {driver:4} | {team[:15]:15} | {lap:10.3f}s | +{delta:7.3f}s | {corner:7.1f} | {straight:8.1f}")

print('\n' + '=' * 80)
print(f'最快圈時: {fastest:.3f}s')
print(f'最慢圈時: {times[-1][2]:.3f}s (差 {times[-1][2]-fastest:.3f}s)')
print(f'\n這 {times[-1][2]-fastest:.3f}s 的差距需要反映在速度係數中！')
print(f'目前 PositionTracker 只用 ±2% 係數，無法正確模擬這麼大的差距')
