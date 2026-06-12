import json

with open('json/detailed_laptime_analysis_2025_Abu Dhabi_FP2_all_drivers.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

all_drivers = data.get('all_drivers_detailed_laptime', {})

# Check GAS
print("=" * 60)
print("GAS Laps (Lap 15+):")
print("=" * 60)
gas = all_drivers.get('GAS', {})
gas_laps = gas.get('detailed_lap_data', [])
for l in gas_laps:
    if l['lap_number'] >= 15:
        pit = l.get('pit_status', '') or ''
        lap_time = l.get('lap_time_seconds') or 0
        tire_life = l.get('tire_life') or 0
        compound = l.get('tire_compound') or 'N/A'
        print(f"Lap {l['lap_number']:2d}: time={lap_time:7.3f}s  "
              f"tire_life={tire_life:4.1f}  compound={compound:8s}  "
              f"pit={'YES' if pit else ''}")

# Calculate std dev for GAS stint 3 (19-29)
gas_stint3_times = [l.get('lap_time_seconds', 0) for l in gas_laps 
                    if 19 <= l['lap_number'] <= 29 
                    and l.get('lap_time_seconds', 0) > 0
                    and not l.get('pit_status')]
if gas_stint3_times:
    import statistics
    print(f"\nGAS Stint 3 (19-29) valid times: {len(gas_stint3_times)}")
    print(f"Times: {[f'{t:.3f}' for t in gas_stint3_times]}")
    print(f"Mean: {statistics.mean(gas_stint3_times):.3f}s")
    print(f"Std Dev: {statistics.stdev(gas_stint3_times):.3f}s")

# Check ALO
print("\n" + "=" * 60)
print("ALO Laps (Lap 15+):")
print("=" * 60)
alo = all_drivers.get('ALO', {})
alo_laps = alo.get('detailed_lap_data', [])
for l in alo_laps:
    if l['lap_number'] >= 15:
        pit = l.get('pit_status', '') or ''
        lap_time = l.get('lap_time_seconds') or 0
        tire_life = l.get('tire_life') or 0
        compound = l.get('tire_compound') or 'N/A'
        print(f"Lap {l['lap_number']:2d}: time={lap_time:7.3f}s  "
              f"tire_life={tire_life:4.1f}  compound={compound:8s}  "
              f"pit={'YES' if pit else ''}")

# Check ALO lap 20-24
alo_lap20_24_times = [l.get('lap_time_seconds', 0) for l in alo_laps 
                      if 20 <= l['lap_number'] <= 24 
                      and l.get('lap_time_seconds', 0) > 0
                      and not l.get('pit_status')]
if alo_lap20_24_times:
    print(f"\nALO Lap 20-24 valid times: {len(alo_lap20_24_times)}")
    print(f"Times: {[f'{t:.3f}' for t in alo_lap20_24_times]}")
    if len(alo_lap20_24_times) >= 2:
        print(f"Mean: {statistics.mean(alo_lap20_24_times):.3f}s")
        print(f"Std Dev: {statistics.stdev(alo_lap20_24_times):.3f}s")
