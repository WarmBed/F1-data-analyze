"""測試彎道數據獲取"""
import sys
sys.path.insert(0, '.')
from PyQt5.QtWidgets import QApplication
from demo_fastf1_z_elevation import FastF1ElevationDemo
import fastf1
from pathlib import Path

# 創建 QApplication
app = QApplication(sys.argv)

# 啟用緩存
cache_dir = Path('.') / 'f1_analysis_cache'
fastf1.Cache.enable_cache(str(cache_dir))

print('載入會話...')
session = fastf1.get_session(2024, 'Japan', 'R')
session.load()

fastest_lap = session.laps.pick_fastest()

# 測試彎道數據獲取
print('\n測試 _get_official_corners 方法...')
demo = FastF1ElevationDemo()
corners = demo._get_official_corners(session, fastest_lap)

print(f'\n彎道數據結果:')
print(f'Available: {corners.get("available")}')
print(f'Count: {corners.get("count")}')

if corners.get('corners'):
    print(f'\n所有 18 個彎道:')
    for c in corners.get('corners', []):
        print(f'  T{c["number"]:<2}: distance={c["distance"]:>7.2f}m ({c["distance"]/1000:>5.3f}km), x={c["x"]:>8.1f}, y={c["y"]:>8.1f}')
