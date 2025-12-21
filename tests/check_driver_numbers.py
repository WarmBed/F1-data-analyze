"""
檢查車手代號與車號的對應關係
"""
import fastf1
fastf1.Cache.enable_cache('cache')

session = fastf1.get_session(2025, 'Abu Dhabi', 'FP2')
session.load()

# 所有車手代號與車號
print('All drivers:')
for driver in session.laps['Driver'].unique():
    dl = session.laps[session.laps['Driver'] == driver]
    driver_num = dl.iloc[0]['DriverNumber']
    print(f'  {driver}: DriverNumber = {driver_num}')

print()
print(f'car_data keys: {list(session.car_data.keys())}')
