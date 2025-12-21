import json

json_file = "json/historical_flags_Las_Vegas_2023-2024.json"

with open(json_file, 'r', encoding='utf-8') as f:
    full_data = json.load(f)

print("=== Las Vegas 2023-2024 Analysis ===")
print(f"Function: {full_data['function_name']}")
print(f"Timestamp: {full_data['timestamp']}")

data = full_data['data']

print(f"\nYears analyzed: {list(data['yearly_summary'].keys())}")
print(f"Circuit: {data['metadata']['circuit_name']}")

print("\nYearly Statistics:")
for year, stats in sorted(data['yearly_summary'].items()):
    print(f"  {year}:")
    print(f"    Yellow Flags: {stats['yellow_flags']}")
    print(f"    Red Flags: {stats['red_flags']}")
    print(f"    Safety Cars: {stats['safety_cars']}")
    print(f"    Position Changes: {stats['position_changes']}")
