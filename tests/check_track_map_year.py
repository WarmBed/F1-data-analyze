import json

json_file = "json/historical_flags_Las_Vegas_2023-2024.json"

with open(json_file, 'r', encoding='utf-8') as f:
    full_data = json.load(f)

data = full_data['data']
meta = data['metadata']

print("=== Track Map Information ===")
print(f"Timestamp: {full_data['timestamp']}")
print(f"Circuit: {meta['circuit_name']}")
print(f"Country: {meta['country']}")
print(f"Years analyzed: {meta['years_analyzed']}")

print(f"\nTrack Data:")
print(f"  Position records: {len(data.get('detailed_position_records', []))}")
print(f"  Track bounds: {data.get('track_bounds')}")
print(f"  Corners count: {len(data.get('corner_analysis', {}))}")

if data.get('elevation_profile'):
    elev = data['elevation_profile']
    print(f"\nElevation Profile:")
    print(f"  Available: {elev.get('available')}")
    if elev.get('available'):
        print(f"  Min: {elev.get('min_elevation')}m")
        print(f"  Max: {elev.get('max_elevation')}m")
        print(f"  Data source: {elev.get('data_source')}")

print(f"\nFirst 3 position records:")
for i, rec in enumerate(data.get('detailed_position_records', [])[:3]):
    print(f"  {i+1}. X={rec['x']:.1f}, Y={rec['y']:.1f}, Speed={rec.get('speed', 'N/A')}")
