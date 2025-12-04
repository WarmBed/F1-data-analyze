"""
單獨測試 CarData.z 是否能收到數據
使用 threading 設定超時
"""
import threading
import time
from datetime import datetime

try:
    from livef1.adapters import RealF1Client
except ImportError:
    print("請先安裝: pip install livef1")
    exit(1)

def main():
    print("=" * 60)
    print("測試 CarData.z 數據接收")
    print("=" * 60)
    
    # 只訂閱 CarData.z
    client = RealF1Client(topics=['CarData.z'])
    
    received_count = 0
    
    @client.callback('CarData.z')
    async def handle_cardata(records):
        nonlocal received_count
        received_count += 1
        now = datetime.now().strftime('%H:%M:%S')
        print(f"\n[{now}] CarData.z 收到 {len(records) if records else 0} 筆數據")
        if records:
            for i, rec in enumerate(records[:3]):
                print(f"  #{i+1}: {rec}")
        if received_count >= 3:
            raise KeyboardInterrupt()
    
    print(f"時間: {datetime.now().strftime('%H:%M:%S')}")
    print("等待 CarData.z 數據... (最多 20 秒)")
    print("如果一直沒有輸出，表示 livef1 不支援此 topic")
    print("-" * 60)
    
    # 設定超時機制
    def timeout_handler():
        time.sleep(20)
        print("\n⚠️ 超時！20秒內未收到 CarData.z 數據")
        print("結論：livef1 可能不支援 CarData.z 實時數據")
        import os
        os._exit(0)
    
    timeout_thread = threading.Thread(target=timeout_handler, daemon=True)
    timeout_thread.start()
    
    try:
        client.run()
    except KeyboardInterrupt:
        print(f"\n✅ 成功收到 CarData.z 數據")

if __name__ == "__main__":
    main()
