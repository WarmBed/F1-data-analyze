import json

json_file = "json/historical_flags_Japan_2024-2024.json"

with open(json_file, 'r', encoding='utf-8') as f:
    full_data = json.load(f)

data = full_data['data']

print("=== Official Corners Check ===")
print(f"official_corners exists: {'official_corners' in data}")

if 'official_corners' in data:
    oc = data['official_corners']
    print(f"available: {oc.get('available')}")
    print(f"count: {oc.get('count')}")
    print(f"data_source: {oc.get('data_source')}")
    
    if oc.get('corners'):
        corners = oc['corners']
        print(f"\nFirst 3 corners:")
        for i, corner in enumerate(corners[:3]):
            print(f"  T{corner['number']}: x={corner['x']:.1f}, y={corner['y']:.1f}, dist={corner.get('distance', 0):.1f}m")
        
        print(f"\nLast corner:")
        last = corners[-1]
        print(f"  T{last['number']}: x={last['x']:.1f}, y={last['y']:.1f}, dist={last.get('distance', 0):.1f}m")
else:
    print("❌ NO official_corners field found!")
