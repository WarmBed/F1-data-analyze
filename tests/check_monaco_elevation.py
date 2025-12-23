import json

# 載入 GeoJSON
geo = json.load(open('json/f1-circuits-master/circuit_data/mc_1929_elevation_data.json', encoding='utf-8'))
coords = geo['coordinates']

elevs = [c['elevation'] for c in coords]
dists = [c['distance_km'] for c in coords]

print('GeoJSON 原始數據 (Monaco):')
print(f'  點數: {len(coords)}')
print(f'  距離範圍: {min(dists):.3f} ~ {max(dists):.3f} km')
print(f'  高程範圍: {min(elevs):.1f} ~ {max(elevs):.1f}m')
print(f'  高程變化: {max(elevs) - min(elevs):.1f}m')

print(f'\n前10個點:')
for i, c in enumerate(coords[:10]):
    print(f'  {i+1}. 距離: {c["distance_km"]:.3f}km, 高程: {c["elevation"]:.1f}m')

print(f'\n最高點和最低點:')
min_idx = elevs.index(min(elevs))
max_idx = elevs.index(max(elevs))
print(f'  最低: {min(elevs):.1f}m (距離 {dists[min_idx]:.3f}km)')
print(f'  最高: {max(elevs):.1f}m (距離 {dists[max_idx]:.3f}km)')

# 載入我們生成的數據
monaco = json.load(open('monaco_circuit_2024.json', encoding='utf-8'))
track_coords = monaco['track_outline']['coordinates']
track_elevs = [c.get('elevation', 0) for c in track_coords]
track_dists = [c['distance_m']/1000 for c in track_coords]

print(f'\n我們生成的數據:')
print(f'  點數: {len(track_coords)}')
print(f'  距離範圍: {min(track_dists):.3f} ~ {max(track_dists):.3f} km')
print(f'  高程範圍: {min(track_elevs):.1f} ~ {max(track_elevs):.1f}m')
print(f'  高程變化: {max(track_elevs) - min(track_elevs):.1f}m')

print(f'\nF1 官方數據: 42m 高程變化')
print(f'差異: {(max(track_elevs) - min(track_elevs)) - 42:.1f}m')
