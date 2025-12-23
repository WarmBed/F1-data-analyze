import json

# 載入 Las Vegas 2024 JSON
with open('json/historical_flags_Las_Vegas_2024-2024.json', 'r', encoding='utf-8') as f:
    data = json.load(f)['data']

print("=== Las Vegas Official Corners Check ===")
print(f"Has official_corners: {'official_corners' in data}")

if 'official_corners' in data:
    oc = data['official_corners']
    print(f"\nOfficial Corners:")
    print(f"  Available: {oc['available']}")
    print(f"  Count: {oc['count']}")
    
    print(f"\nFirst 5 corners:")
    for corner in oc['corners'][:5]:
        print(f"  Corner {corner['number']}: X={corner['x']:.1f}, Y={corner['y']:.1f}, Angle={corner['angle']:.1f}°")
    
    print(f"\nLast corner:")
    last = oc['corners'][-1]
    print(f"  Corner {last['number']}: X={last['x']:.1f}, Y={last['y']:.1f}, Angle={last['angle']:.1f}°")
    
    # 檢查是否所有彎道都有座標
    zero_coords = [c for c in oc['corners'] if c['x'] == 0 and c['y'] == 0]
    if zero_coords:
        print(f"\n⚠️  Warning: {len(zero_coords)} corners have zero coordinates")
    else:
        print(f"\n✅ All corners have valid coordinates!")
else:
    print("❌ No official_corners data found!")
