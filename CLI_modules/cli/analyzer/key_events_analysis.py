"""
F1 Analysis API - 關鍵事件摘要分析模組 (功能4.1)
專門的關鍵事件分析，包含Raw Data和JSON輸出
"""

import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

import json
import pandas as pd
from datetime import datetime
from prettytable import PrettyTable


def run_key_events_summary_analysis(data_loader):
    """主要功能：關鍵事件摘要分析 - 僅使用FastF1/OpenF1真實數據"""
    print(f"[DEBUG] F1 關鍵事件摘要分析 (功能4.1)")
    print(f"[INFO] 分析目標：關鍵事件、賽事轉折點、重要時刻")
    print("=" * 60)
    
    # 獲取賽事基本信息
    session_info = get_session_info(data_loader)
    print_session_summary(session_info)
    
    # 分析關鍵事件數據
    events_data = analyze_key_events_data(data_loader)
    
    # 顯示關鍵事件表格
    display_events_table(events_data)
    
    # 顯示事件統計
    display_events_statistics(events_data)
    
    # 保存Raw Data
    save_events_raw_data(session_info, events_data)
    
    print(f"\n[SUCCESS] 關鍵事件摘要分析完成！")


def get_session_info(data_loader):
    """獲取賽事基本信息"""
    session_info = {
        "year": getattr(data_loader, 'year', 'Unknown'),
        "race": getattr(data_loader, 'race', 'Unknown'),
        "session_type": getattr(data_loader, 'session_type', 'Unknown'),
        "track_name": "Unknown",
        "date": "Unknown"
    }
    
    if hasattr(data_loader, 'session') and data_loader.session is not None:
        try:
            session = data_loader.session
            session_info["track_name"] = getattr(session, 'event', {}).get('EventName', 'Unknown')
            session_info["date"] = str(getattr(session, 'date', 'Unknown'))
        except:
            pass
    
    return session_info


def print_session_summary(session_info):
    """顯示賽事摘要信息"""
    print(f"\n[LIST] 賽事信息摘要:")
    print(f"   📅 賽季: {session_info['year']}")
    print(f"   [FINISH] 賽事: {session_info['race']}")
    print(f"   🏎️ 賽段: {session_info['session_type']}")
    print(f"   🏟️ 賽道: {session_info['track_name']}")
    print(f"   📆 日期: {session_info['date']}")


def analyze_key_events_data(data_loader):
    """分析關鍵事件數據 - 僅使用FastF1真實數據"""
    events_data = {
        "has_events_data": False,
        "event_records": [],
        "race_control_events": [],
        "pitstop_events": [],
        "event_summary": {
            "total_events": 0,
            "yellow_flags": 0,
            "safety_cars": 0,
            "pit_stops": 0,
            "incidents": 0
        }
    }
    
    if not hasattr(data_loader, 'session') or data_loader.session is None:
        print("\n[ERROR] 無法獲取賽事數據")
        return events_data
    
    try:
        # 檢查loaded_data
        if not hasattr(data_loader, 'loaded_data') or data_loader.loaded_data is None:
            print("\n[ERROR] 沒有已載入的數據")
            return events_data
        
        loaded_data = data_loader.loaded_data
        print(f"\n[DEBUG] 檢查可用數據源:")
        
        # 1. 檢查賽事控制訊息
        race_control_messages = loaded_data.get('race_control_messages')
        if race_control_messages is not None and not race_control_messages.empty:
            print(f"   [SUCCESS] 賽事控制訊息: {len(race_control_messages)} 條")
            events_data["has_events_data"] = True
            events_data["race_control_events"] = extract_race_control_events(race_control_messages)
        else:
            print("   [ERROR] 沒有賽事控制訊息")
        
        # 2. 檢查進站數據
        pitstops_data = loaded_data.get('pitstops')
        if pitstops_data is not None and not pitstops_data.empty:
            print(f"   [SUCCESS] 進站數據: {len(pitstops_data)} 次進站")
            events_data["pitstop_events"] = extract_pitstop_events(pitstops_data)
        else:
            print("   [ERROR] 沒有進站數據")
        
        # 3. 合併所有事件
        all_events = []
        all_events.extend(events_data["race_control_events"])
        all_events.extend(events_data["pitstop_events"])
        
        # 按時間排序
        if all_events:
            all_events.sort(key=lambda x: x.get('timestamp', ''))
            events_data["event_records"] = all_events[:20]  # 最多顯示20個關鍵事件
            
            # 統計事件類型
            events_data["event_summary"]["total_events"] = len(all_events)
            events_data["event_summary"]["yellow_flags"] = len([e for e in all_events if 'YELLOW' in e.get('event_type', '')])
            events_data["event_summary"]["safety_cars"] = len([e for e in all_events if 'SAFETY' in e.get('event_type', '')])
            events_data["event_summary"]["pit_stops"] = len([e for e in all_events if e.get('event_type') == 'PIT_STOP'])
            events_data["event_summary"]["incidents"] = len([e for e in all_events if 'INCIDENT' in e.get('event_type', '')])
            
            print(f"   [INFO] 總關鍵事件: {events_data['event_summary']['total_events']} 個")
        
    except Exception as e:
        print(f"\n[ERROR] 關鍵事件數據分析失敗: {e}")
    
    return events_data


def extract_race_control_events(race_control_messages):
    """從賽事控制訊息提取關鍵事件"""
    events = []
    
    try:
        for idx, row in race_control_messages.iterrows():
            event_type = "RACE_CONTROL"
            message = str(row.get('Message', 'Unknown'))
            
            # 分類事件類型
            if 'YELLOW' in message.upper():
                event_type = "YELLOW_FLAG"
            elif 'SAFETY' in message.upper():
                event_type = "SAFETY_CAR"
            elif 'DRS' in message.upper():
                event_type = "DRS"
            elif 'INCIDENT' in message.upper():
                event_type = "INCIDENT"
            
            event = {
                "timestamp": str(row.get('Date', 'Unknown')),
                "event_type": event_type,
                "description": message,
                "lap": row.get('Lap', 'N/A'),
                "driver": row.get('Driver', 'N/A'),
                "source": "race_control"
            }
            events.append(event)
    
    except Exception as e:
        print(f"   [WARNING] 賽事控制事件提取失敗: {e}")
    
    return events


def extract_pitstop_events(pitstops_data):
    """從進站數據提取關鍵事件"""
    events = []
    
    try:
        for idx, row in pitstops_data.iterrows():
            event = {
                "timestamp": str(row.get('date', 'Unknown')),
                "event_type": "PIT_STOP",
                "description": f"進站 - 耗時 {row.get('pit_duration', 'N/A')}秒",
                "lap": row.get('lap_number', 'N/A'),
                "driver": str(row.get('driver_number', 'N/A')),
                "duration": row.get('pit_duration', 0),
                "source": "pitstops"
            }
            events.append(event)
    
    except Exception as e:
        print(f"   [WARNING] 進站事件提取失敗: {e}")
    
    return events


def display_events_table(events_data):
    """顯示關鍵事件表格"""
    if not events_data["has_events_data"] or not events_data["event_records"]:
        print("\n[ERROR] 沒有關鍵事件數據可顯示")
        return
    
    print(f"\n[INFO] 關鍵事件摘要表格:")
    
    table = PrettyTable()
    table.field_names = ["序號", "時間", "事件類型", "圈數", "車手", "描述"]
    table.align = "l"
    table.max_width["描述"] = 40
    
    for i, event in enumerate(events_data["event_records"], 1):
        # 簡化時間顯示
        timestamp = event.get('timestamp', 'Unknown')
        if 'T' in timestamp:
            time_str = timestamp.split('T')[1][:8]  # 只顯示時:分:秒
        else:
            time_str = timestamp
        
        table.add_row([
            i,
            time_str,
            event.get('event_type', 'Unknown'),
            event.get('lap', 'N/A'),
            event.get('driver', 'N/A'),
            event.get('description', 'No description')[:40]
        ])
    
    print(table)


def display_events_statistics(events_data):
    """顯示事件統計分析"""
    print(f"\n[STATS] 關鍵事件統計分析:")
    
    summary = events_data["event_summary"]
    print(f"   [INFO] 事件總數: {summary['total_events']} 個")
    print(f"   🟡 黃旗事件: {summary['yellow_flags']} 次")
    print(f"   🚗 安全車事件: {summary['safety_cars']} 次")
    print(f"   ⛽ 進站事件: {summary['pit_stops']} 次")
    print(f"   [CRITICAL] 事故事件: {summary['incidents']} 次")
    
    if events_data["event_records"]:
        print(f"   [LIST] 顯示前20個關鍵事件")


def save_events_raw_data(session_info, events_data):
    """保存關鍵事件Raw Data"""
    
    # 清理不能序列化的數據類型
    def clean_for_json(obj):
        if isinstance(obj, (list, tuple)):
            return [clean_for_json(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: clean_for_json(value) for key, value in obj.items()}
        elif isinstance(obj, bool):
            return bool(obj)
        elif obj is None or isinstance(obj, (str, int, float)):
            return obj
        else:
            return str(obj)
    
    raw_data = {
        "analysis_type": "key_events_summary_analysis",
        "function": "4.1",
        "timestamp": datetime.now().isoformat(),
        "session_info": clean_for_json(session_info),
        "events_analysis": {
            "has_events_data": bool(events_data["has_events_data"]),
            "event_summary": clean_for_json(events_data["event_summary"]),
            "total_key_events": len(events_data["event_records"])
        },
        "detailed_events": clean_for_json(events_data["event_records"]),
        "race_control_events": clean_for_json(events_data["race_control_events"]),
        "pitstop_events": clean_for_json(events_data["pitstop_events"])
    }
    
    # 確保json資料夾存在
    import os
import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

    json_dir = "json"
    os.makedirs(json_dir, exist_ok=True)
    
    raw_data_file = os.path.join(json_dir, f"raw_data_key_events_{session_info['year']}_{session_info['race']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    try:
        with open(raw_data_file, "w", encoding="utf-8") as f:
            json.dump(raw_data, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Raw Data 已保存: {raw_data_file}")
    except Exception as e:
        print(f"\n[ERROR] Raw Data 保存失敗: {e}")


if __name__ == "__main__":
    # 測試用途
    print("[DEBUG] 關鍵事件摘要分析模組 - 測試模式")
    run_key_events_summary_analysis(None)
