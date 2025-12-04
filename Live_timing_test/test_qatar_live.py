"""即時測試 - 卡達站 CarData.z + TimingData"""
from livef1.adapters import RealF1Client
import threading, time, json

# 同時訂閱多個 topics
client = RealF1Client(topics=['CarData.z', 'TimingData'])
cardata_count = 0
timing_count = 0

@client.callback('CarData.z')
async def on_cardata(records):
    global cardata_count
    cardata_count += 1
    print(f'\n*** CarData.z #{cardata_count} ***')
    print(f'Type: {type(records).__name__}')
    if isinstance(records, dict):
        print(f'Keys: {list(records.keys())}')
        for key, value in records.items():
            print(f'  {key}: {json.dumps(value, default=str)[:500]}')
    else:
        print(f'Content: {records}')
    if cardata_count >= 3:
        raise KeyboardInterrupt()

@client.callback('TimingData')
async def on_timing(records):
    global timing_count
    timing_count += 1
    if timing_count <= 2:
        print(f'\n=== TimingData #{timing_count} ===')
        print(f'Type: {type(records).__name__}')

def timeout():
    time.sleep(30)
    print(f'\n=== Timeout! CarData.z count: {cardata_count}, TimingData count: {timing_count} ===')
    import os; os._exit(0)

threading.Thread(target=timeout, daemon=True).start()
print('Connecting to F1 Live Timing (CarData.z + TimingData)...')
client.run()
