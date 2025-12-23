import pickle

data = pickle.load(open('f1_analysis_cache/f1_data_2025_Brazil_FP3.pkl', 'rb'))
meta = data['metadata']
print('Brazil 2025 FP3 Cache Metadata:')
print(f'  Event: {meta["event_name"]}')
print(f'  Session Type: {meta["session_type"]}')
print(f'  Date: {meta["date"]}')
print(f'  Laps: {len(data["laps"])}')
