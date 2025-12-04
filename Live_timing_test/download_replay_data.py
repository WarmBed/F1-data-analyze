import fastf1
import requests
import os

def download_replay_data():
    print("正在初始化 FastF1 以獲取賽程資訊...")
    # 1. 設定賽事 (2024 日本大獎賽)
    session = fastf1.get_session(2024, 'Japan', 'R')
    
    print(f"目標賽事: {session.event['EventName']} - {session.name}")
    
    # 2. 獲取 API 路徑
    # api_path 通常格式為 /2024/2024-04-07_Japanese_Grand_Prix/2024-04-07_Race/
    api_path = session.api_path
    print(f"API Path: {api_path}")
    
    base_url = "https://livetiming.formula1.com/static"
    
    # 3. 目標檔案: CarData.z.jsonstream (包含壓縮的遙測數據)
    target_file = "CarData.z.jsonstream"
    full_url = f"{base_url}{api_path}{target_file}"
    
    output_file = "japan_2024_cardata.jsonstream"
    
    print(f"開始下載: {full_url}")
    print(f"存檔目標: {output_file}")
    
    try:
        response = requests.get(full_url, stream=True)
        
        if response.status_code == 200:
            total_size = 0
            with open(output_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    total_size += len(chunk)
            print(f"下載成功! 總大小: {total_size / 1024 / 1024:.2f} MB")
            print(f"檔案已儲存為: {os.path.abspath(output_file)}")
        else:
            print(f"下載失敗。HTTP 狀態碼: {response.status_code}")
            print("請檢查網路連線或確認該賽事數據是否存在。")
            
    except Exception as e:
        print(f"發生錯誤: {e}")

if __name__ == "__main__":
    download_replay_data()
