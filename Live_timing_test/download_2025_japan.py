"""
F1 Live Timing 資料下載與分析工具
測試目標: 2025 日本站 (Suzuka) 遙測資料
"""
import requests
import json
import base64
import zlib
from datetime import datetime

def decode_f1_packet(raw_b64_string):
    """
    解碼 F1 壓縮封包
    來源: F1 官方文件
    """
    try:
        # 1. Base64 Decode
        decoded_bytes = base64.b64decode(raw_b64_string)
        # 2. Zlib Decompress (wbits=-15 關鍵!)
        decompressed_bytes = zlib.decompress(decoded_bytes, wbits=-15)
        # 3. Parse JSON
        return json.loads(decompressed_bytes.decode('utf-8'))
    except Exception as e:
        print(f"❌ 解碼錯誤: {e}")
        return None


def get_2025_index():
    """取得 2025 年賽季索引"""
    url = "https://livetiming.formula1.com/static/2025/Index.json"
    print(f"[INFO] 下載 2025 年賽季索引...")
    print(f"[URL]  {url}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # 處理 UTF-8 BOM
        text = response.content.decode('utf-8-sig')
        data = json.loads(text)
        
        print(f"[OK]   成功! 找到 {len(data.get('Meetings', []))} 場比賽")
        return data
    except Exception as e:
        print(f"[ERROR] 失敗: {e}")
        return None


def find_japan_meeting(index_data):
    """從索引中找到日本站資訊"""
    meetings = index_data.get('Meetings', [])
    
    print(f"\n[SEARCH] 搜尋日本站...")
    for meeting in meetings:
        name = meeting.get('Name', '')
        location = meeting.get('Location', '')
        
        if 'Japan' in name or 'Suzuka' in location or 'japan' in name.lower():
            print(f"[FOUND] {meeting}")
            return meeting
    
    print(f"[ERROR] 未找到日本站")
    return None


def download_cardata(meeting_path, session_name='Race'):
    """
    下載 CarData.z.jsonStream
    
    meeting_path 範例: "2025-04-06_Japanese_Grand_Prix"
    """
    # 構建完整路徑
    year = "2025"
    # Session 路徑格式: YYYY-MM-DD_Session_Type
    date_prefix = meeting_path.split('_')[0]  # 取得日期部分
    session_path = f"{date_prefix}_{session_name}"
    
    url = f"https://livetiming.formula1.com/static/{year}/{meeting_path}/{session_path}/CarData.z.jsonStream"
    
    print(f"\n📥 下載遙測資料...")
    print(f"🔗 URL: {url}")
    
    try:
        response = requests.get(url, timeout=60, stream=True)
        response.raise_for_status()
        
        # 取得檔案大小
        content_length = response.headers.get('Content-Length')
        if content_length:
            size_mb = int(content_length) / 1024 / 1024
            print(f"📊 檔案大小: {size_mb:.2f} MB")
        
        # 下載內容
        content = response.content
        print(f"✅ 下載完成! 實際大小: {len(content) / 1024 / 1024:.2f} MB")
        
        return content
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP 錯誤: {e}")
        print(f"💡 提示: 檢查賽段名稱是否正確 (Race/Qualifying/Practice_1 等)")
        return None
    except Exception as e:
        print(f"❌ 下載失敗: {e}")
        return None


def parse_jsonstream(content):
    """
    解析 .jsonStream 格式
    格式: 每行 = 12字元時間戳 + JSON資料
    """
    print(f"\n🔧 解析 jsonStream 格式...")
    
    try:
        # 分割行 (使用 \r\n)
        text = content.decode('utf-8-sig')
        lines = text.split('\r\n')
        
        # 移除空行
        lines = [line for line in lines if line.strip()]
        
        print(f"📋 總行數: {len(lines)}")
        
        # 解析每一行
        records = []
        for i, line in enumerate(lines):
            if len(line) < 12:
                continue
            
            # 分割時間戳與資料
            timestamp = line[:12]
            json_data = line[12:]
            
            try:
                data = json.loads(json_data)
                records.append({
                    'timestamp': timestamp,
                    'data': data
                })
            except json.JSONDecodeError as e:
                if i < 5:  # 只顯示前幾個錯誤
                    print(f"⚠️  第 {i+1} 行解析失敗: {e}")
        
        print(f"✅ 成功解析 {len(records)} 筆記錄")
        return records
    
    except Exception as e:
        print(f"❌ 解析失敗: {e}")
        return []


def analyze_cardata_structure(records, max_samples=10):
    """分析 CarData 結構"""
    print(f"\n📊 分析資料結構...")
    print(f"=" * 60)
    
    if not records:
        print("❌ 無資料可分析")
        return
    
    # 顯示前幾筆資料
    print(f"\n前 {max_samples} 筆資料樣本:\n")
    for i, record in enumerate(records[:max_samples]):
        print(f"[{i+1}] 時間戳: {record['timestamp']}")
        
        data = record['data']
        
        # 檢查是否壓縮
        if 'A' in data and isinstance(data['A'], list) and len(data['A']) > 0:
            # SignalR 格式,可能包含壓縮資料
            print(f"    類型: SignalR 訊息")
            print(f"    內容: {str(data)[:200]}...")
            
            # 嘗試解碼壓縮資料
            for item in data['A']:
                if isinstance(item, str):
                    decoded = decode_f1_packet(item)
                    if decoded:
                        print(f"    解碼後: {str(decoded)[:200]}...")
                        break
        else:
            print(f"    類型: 直接 JSON")
            print(f"    內容: {str(data)[:200]}...")
        
        print()
    
    print(f"=" * 60)


def compare_with_fastf1():
    """說明與 fastf1 的差異"""
    print(f"\n📊 與 fastf1 的資料格式比較:\n")
    print(f"LiveTiming API (原始):")
    print(f"  - 格式: .jsonStream (逐行 JSON)")
    print(f"  - 壓縮: Base64 + Zlib (wbits=-15)")
    print(f"  - 結構: SignalR 協定封裝")
    print(f"  - 欄位: 原始遙測資料 (Speed, RPM, nGear, Throttle, Brake)")
    print()
    print(f"fastf1 (處理後):")
    print(f"  - 格式: Pandas DataFrame")
    print(f"  - 壓縮: 已解壓縮")
    print(f"  - 結構: 表格化、時間對齊")
    print(f"  - 欄位: 標準化命名 (Speed, RPM, nGear, Throttle, Brake, DRS 等)")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("F1 Live Timing - 2025 日本站遙測資料分析")
    print("=" * 60)
    
    # 步驟 1: 取得 2025 年索引
    index = get_2025_index()
    
    if index:
        # 步驟 2: 找到日本站
        japan = find_japan_meeting(index)
        
        if japan:
            meeting_path = japan.get('Path', '')
            print(f"\n📍 會議路徑: {meeting_path}")
            
            # 步驟 3: 下載 CarData
            cardata = download_cardata(meeting_path, session_name='Race')
            
            if cardata:
                # 步驟 4: 解析資料
                records = parse_jsonstream(cardata)
                
                # 步驟 5: 分析結構
                analyze_cardata_structure(records, max_samples=5)
                
                # 步驟 6: 與 fastf1 比較
                compare_with_fastf1()
                
                print(f"\n✅ 分析完成!")
            else:
                print(f"\n💡 提示: 可能比賽尚未舉行,或資料尚未發布")
                print(f"   您可以嘗試其他賽段類型:")
                print(f"   - Practice_1, Practice_2, Practice_3")
                print(f"   - Qualifying")
                print(f"   - Sprint (如果有)")
    
    print(f"\n" + "=" * 60)
