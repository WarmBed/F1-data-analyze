import json
import glob

files = sorted(glob.glob('json/predictionJSON/fp_q_data_2025_*.json'))
seen = set()

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        data = json.load(file)
        metadata = data.get('metadata', {})
        race_num = metadata.get('race_number', 'N/A')
        if race_num not in seen:
            seen.add(race_num)
            event_name = metadata.get('event_name', 'N/A')
            circuit_name = metadata.get('circuit_name', 'N/A')
            print(f"Race {race_num}: {event_name} ({circuit_name})")
