"""快速測試 LiveF1 原始數據"""
from livef1.adapters import RealF1Client
import time

print("啟動 LiveF1 測試...")
print(f"時間: {time.strftime('%H:%M:%S')}")

# 訂閱所有重要的 topics
client = RealF1Client(
    topics=[
        'CarData.z', 
        'Position.z',
        'TimingData',
        'DriverList',
    ],
    log_file_name='live_raw_output.json'
)

count = 0

@client.callback('raw_handler')
async def handle(records):
    global count
    count += 1
    
    for topic, data_list in records.items():
        print(f"\n{'='*50}")
        print(f"[{time.strftime('%H:%M:%S')}] Topic: {topic} ({len(data_list)} records)")
        print(f"{'='*50}")
        
        for i, record in enumerate(data_list[:3]):  # 只印前3筆
            print(f"  Record {i+1}: {record}")
        
        if len(data_list) > 3:
            print(f"  ... 還有 {len(data_list) - 3} 筆")
    
    if count >= 20:
        print("\n已收到足夠數據，停止...")
        raise KeyboardInterrupt()

print("開始連接 F1 Live Timing...")
client.run()
print("結束")
