import pickle

with open('data/live_timing_cache/2025/2025_Abu_Dhabi_Race.pkl', 'rb') as f:
    data = pickle.load(f)

snapshots = data.get('snapshots', [])
print(f'Total snapshots: {len(snapshots)}')

if snapshots:
    first_snap = snapshots[0]
    drivers = first_snap.get('drivers', {})
    if drivers:
        first_driver = list(drivers.values())[0]
        print(f'\nFirst driver keys:\n{sorted(first_driver.keys())}')
        
        print(f'\nTelemetry check:')
        for field in ['speed', 'rpm', 'gear', 'throttle', 'brake', 'drs']:
            has_it = field in first_driver
            value = first_driver.get(field, 'N/A') if has_it else 'NOT FOUND'
            print(f'  {field:10s}: {"✅" if has_it else "❌"} {value}')
