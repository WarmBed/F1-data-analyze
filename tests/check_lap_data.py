import pickle

data = pickle.load(open('data/live_timing_cache/2025/Abu_Dhabi_Race.pkl', 'rb'))

for lap in [15, 16, 17, 18, 19, 20]:
    snaps = [s for s in data['snapshots'] if s.get('current_lap') == lap]
    if not snaps:
        print(f"Lap {lap}: 無數據")
        continue
    
    snap = snaps[0]
    tsu = [d for d in snap['drivers'].values() if d['driver_tla'] == 'TSU']
    nor = [d for d in snap['drivers'].values() if d['driver_tla'] == 'NOR']
    
    if not tsu or not nor:
        print(f"Lap {lap}: 找不到車手")
        continue
    
    tsu = tsu[0]
    nor = nor[0]
    
    print(f"\nLap {lap}:")
    print(f"  TSU: P{tsu['position']}, Gap to leader: {tsu.get('gap_to_leader')}")
    print(f"  NOR: P{nor['position']}, Gap to leader: {nor.get('gap_to_leader')}")
    print(f"  NOR Gap ahead: {nor.get('gap_to_ahead_display')}")
    
    # 計算 Gap
    if tsu['position'] < nor['position']:
        # TSU 在前
        gap = float(nor.get('gap_to_leader', 0) or 0) - float(tsu.get('gap_to_leader', 0) or 0)
        print(f"  計算 Gap (NOR 落後 TSU): {gap:.3f}s")
    else:
        # NOR 在前
        gap = float(tsu.get('gap_to_leader', 0) or 0) - float(nor.get('gap_to_leader', 0) or 0)
        print(f"  計算 Gap (TSU 落後 NOR): {gap:.3f}s")

# 檢查輪胎數據
print("\n\n輪胎 Stint 數據:")
if 'driver_stints' in data:
    for driver in ['TSU', 'NOR']:
        print(f"\n{driver}:")
        stints = data['driver_stints'].get(driver, [])
        for stint in stints:
            print(f"  Lap {stint.get('start_lap')}-{stint.get('end_lap')}: {stint.get('compound')}")
