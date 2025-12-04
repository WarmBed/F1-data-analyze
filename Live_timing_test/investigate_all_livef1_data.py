"""
全面調查 Live F1 API 提供的所有資料類型

目標：列出所有可用的 jsonStream 檔案及其內容結構
"""

import json
import requests
from typing import Dict, Any, List


def fetch_stream(base_url: str, file_name: str) -> List[Dict]:
    """下載並解析 jsonStream 檔案"""
    url = f"{base_url}/{file_name}"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        content = response.content.decode('utf-8-sig')
        lines = [l for l in content.splitlines() if l.strip() and len(l) > 12]
        
        records = []
        for line in lines[:10]:  # 只取前 10 筆作為樣本
            timestamp = line[:12]
            payload = line[12:]
            try:
                data = json.loads(payload)
                records.append({'timestamp': timestamp, 'data': data})
            except:
                pass
        return records
    except Exception as e:
        return []


def analyze_structure(data: Any, prefix: str = "", depth: int = 0) -> List[str]:
    """分析資料結構，返回所有欄位路徑"""
    fields = []
    if depth > 4:  # 限制深度
        return [f"{prefix}: ..."]
    
    if isinstance(data, dict):
        for key, value in list(data.items())[:10]:  # 限制數量
            field_path = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                fields.extend(analyze_structure(value, field_path, depth + 1))
            elif isinstance(value, list):
                if value and isinstance(value[0], dict):
                    fields.append(f"{field_path}: List[Dict]")
                    fields.extend(analyze_structure(value[0], f"{field_path}[0]", depth + 1))
                else:
                    fields.append(f"{field_path}: List")
            else:
                fields.append(f"{field_path}: {type(value).__name__} = {repr(value)[:50]}")
    elif isinstance(data, list):
        if data and isinstance(data[0], dict):
            fields.extend(analyze_structure(data[0], f"{prefix}[0]", depth + 1))
    
    return fields


def main():
    base_url = 'https://livetiming.formula1.com/static/2025/2025-04-06_Japanese_Grand_Prix/2025-04-06_Race'
    
    # 所有已知的 Live F1 資料流
    streams = [
        # 核心計時資料
        ("TimingData.jsonStream", "計時資料 - 圈時、差距、位置等"),
        ("TimingAppData.jsonStream", "計時 App 資料 - 輪胎策略、Stint"),
        ("TimingStats.jsonStream", "計時統計 - 最快圈、速度陷阱等"),
        
        # 位置與遙測
        ("Position.z.jsonStream", "位置資料 (壓縮) - X/Y 座標"),
        ("CarData.z.jsonStream", "車輛資料 (壓縮) - 速度、RPM、檔位、DRS"),
        
        # 車手與車隊
        ("DriverList.jsonStream", "車手列表 - 車手資訊"),
        ("TeamRadio.jsonStream", "車隊無線電"),
        
        # 賽道與天氣
        ("TrackStatus.jsonStream", "賽道狀態 - 黃旗、紅旗、SC 等"),
        ("WeatherData.jsonStream", "天氣資料 - 溫度、濕度、風速"),
        ("WeatherDataSeries.jsonStream", "天氣資料序列"),
        
        # 比賽控制
        ("RaceControlMessages.jsonStream", "比賽控制訊息 - 處罰、調查等"),
        ("SessionStatus.jsonStream", "賽段狀態"),
        ("SessionInfo.jsonStream", "賽段資訊"),
        ("SessionData.jsonStream", "賽段資料"),
        
        # 其他
        ("LapCount.jsonStream", "圈數計數"),
        ("LapSeries.jsonStream", "圈數序列"),
        ("ExtrapolatedClock.jsonStream", "推算時鐘"),
        ("DriverRaceInfo.jsonStream", "車手比賽資訊"),
        ("CurrentTyres.jsonStream", "當前輪胎"),
        ("TyreStintSeries.jsonStream", "輪胎 Stint 序列"),
        ("PitLaneTimeCollection.jsonStream", "維修站時間"),
        ("ChampionshipPrediction.jsonStream", "積分預測"),
        ("OvertakeSeries.jsonStream", "超車序列"),
        ("TopThree.jsonStream", "前三名"),
        ("RcmSeries.jsonStream", "RCM 序列"),
        ("DriverScore.jsonStream", "車手得分"),
        ("SPFeed.jsonStream", "SP Feed"),
        ("PitStopSeries.jsonStream", "進站序列"),
        ("TlaRcm.jsonStream", "TLA RCM"),
    ]
    
    print("=" * 100)
    print("Live F1 API 資料流調查報告")
    print("=" * 100)
    print(f"賽事: 2025 Japanese Grand Prix - Race")
    print(f"來源: {base_url}")
    print("=" * 100)
    
    available_streams = []
    unavailable_streams = []
    
    for stream_name, description in streams:
        print(f"\n{'='*80}")
        print(f"[{stream_name}] {description}")
        print("-" * 80)
        
        records = fetch_stream(base_url, stream_name)
        
        if not records:
            print("  ❌ 無法取得資料")
            unavailable_streams.append(stream_name)
            continue
        
        available_streams.append(stream_name)
        print(f"  ✅ 可用 - 取得 {len(records)} 筆樣本")
        
        # 分析第一筆資料的結構
        if records:
            sample = records[0]['data']
            print(f"  時間戳範例: {records[0]['timestamp']}")
            print(f"  資料結構:")
            
            fields = analyze_structure(sample)
            for field in fields[:20]:  # 限制顯示數量
                print(f"    - {field}")
            
            if len(fields) > 20:
                print(f"    ... 還有 {len(fields) - 20} 個欄位")
    
    # 總結
    print("\n" + "=" * 100)
    print("總結")
    print("=" * 100)
    print(f"\n✅ 可用資料流 ({len(available_streams)} 個):")
    for s in available_streams:
        print(f"   - {s}")
    
    print(f"\n❌ 不可用資料流 ({len(unavailable_streams)} 個):")
    for s in unavailable_streams:
        print(f"   - {s}")


if __name__ == '__main__':
    main()
