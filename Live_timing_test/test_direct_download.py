"""
F1 Live Timing 靜態檔案直接下載測試
不依賴 fastf1，直接構建 URL 並下載
"""
import requests
import base64
import zlib
import json

def test_direct_download():
    """
    直接下載測試 - 2024 巴林站正賽 (最近一場完整比賽)
    """
    
    # 🔑 關鍵: URL 構建規則
    # 格式: https://livetiming.formula1.com/static/{YEAR}/{YEAR-MM-DD_Event_Name}/{YEAR-MM-DD_Session_Type}/{FILE}
    
    # 範例 1: 2024 巴林站正賽
    base_url = "https://livetiming.formula1.com/static"
    
    # API Path 格式: /YEAR/YYYY-MM-DD_Race_Name/YYYY-MM-DD_Session/
    api_path = "/2024/2024-03-02_Bahrain_Grand_Prix/2024-03-02_Race/"
    
    # 可用的檔案:
    files_to_test = [
        "CarData.z.jsonStream",      # 遙測數據 (壓縮)
        "Position.z.jsonStream",     # GPS 位置 (壓縮)
        "TimingData.jsonStream",     # 圈速數據 (未壓縮)
        "SessionInfo.jsonStream",    # 賽段資訊
    ]
    
    print("=" * 60)
    print("F1 Live Timing 靜態檔案直接下載測試")
    print("=" * 60)
    
    for filename in files_to_test:
        full_url = f"{base_url}{api_path}{filename}"
        print(f"\n📥 測試下載: {filename}")
        print(f"🔗 URL: {full_url}")
        
        try:
            response = requests.get(full_url, timeout=10)
            
            if response.status_code == 200:
                size_mb = len(response.content) / 1024 / 1024
                print(f"✅ 下載成功! 大小: {size_mb:.2f} MB")
                
                # 儲存到本地
                output_file = f"bahrain_2024_{filename}"
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                print(f"💾 已儲存: {output_file}")
                
                # 如果是 .z 檔案,嘗試解碼第一行
                if filename.endswith('.z.jsonStream'):
                    print(f"🔓 嘗試解碼第一行...")
                    try:
                        first_line = response.content.split(b'\n')[0]
                        decoded = decode_f1_packet(first_line.decode('utf-8'))
                        if decoded:
                            print(f"✅ 解碼成功! 預覽:")
                            print(json.dumps(decoded, indent=2, ensure_ascii=False)[:300] + "...")
                    except Exception as e:
                        print(f"⚠️  解碼失敗: {e}")
                        
            elif response.status_code == 404:
                print(f"❌ 404 Not Found - 檔案可能不存在或 URL 錯誤")
            else:
                print(f"❌ 下載失敗: HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"⏱️  請求超時")
        except Exception as e:
            print(f"❌ 錯誤: {e}")
    
    print("\n" + "=" * 60)
    print("測試完成!")
    print("=" * 60)


def decode_f1_packet(raw_b64_string):
    """
    解碼 F1 壓縮封包 (來自您的文檔)
    """
    try:
        # 1. Base64 Decode
        decoded_bytes = base64.b64decode(raw_b64_string)
        # 2. Zlib Decompress (wbits=-15 是關鍵!)
        decompressed_bytes = zlib.decompress(decoded_bytes, wbits=-15)
        # 3. Decode to String & Parse JSON
        return json.loads(decompressed_bytes.decode('utf-8'))
    except Exception as e:
        print(f"解碼錯誤: {e}")
        return None


def show_url_construction_guide():
    """
    顯示 URL 構建指南
    """
    print("\n" + "=" * 60)
    print("📚 F1 Live Timing URL 構建指南")
    print("=" * 60)
    
    print("\n格式:")
    print("https://livetiming.formula1.com/static/[YEAR]/[DATE_EVENT]/[DATE_SESSION]/[FILE]")
    
    print("\n範例:")
    print("https://livetiming.formula1.com/static/2024/2024-03-02_Bahrain_Grand_Prix/2024-03-02_Race/CarData.z.jsonStream")
    
    print("\n說明:")
    print("- [YEAR]: 年份 (例: 2024)")
    print("- [DATE_EVENT]: 日期_賽事名稱 (例: 2024-03-02_Bahrain_Grand_Prix)")
    print("- [DATE_SESSION]: 日期_賽段類型 (例: 2024-03-02_Race)")
    print("- [FILE]: 檔案名稱 (例: CarData.z.jsonStream)")
    
    print("\n🎯 如何找到正確的 URL?")
    print("方法 1: 使用 fastf1.get_session().api_path (您現有的方法)")
    print("方法 2: 從 F1 官網查詢賽程日期")
    print("方法 3: 爬取 https://livetiming.formula1.com/static/[YEAR]/ 列表")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    # 先顯示指南
    show_url_construction_guide()
    
    # 執行下載測試
    print("\n")
    input("按 Enter 開始下載測試...")
    test_direct_download()
