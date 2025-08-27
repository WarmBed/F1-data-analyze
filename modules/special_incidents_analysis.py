#!/usr/bin/env python3
"""
F1 特殊事件報告分析模組 (功能 4.2)
作者: F1 Analysis Team
版本: 1.0

專門處理特殊事件報告分析，包括：
- 安全車事件
- 黃旗事件
- 紅旗事件
- DRS 禁用事件
- 賽道限制違規
- 車手處罰
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from prettytable import PrettyTable


def clean_for_json(obj):
    """清理數據以便JSON序列化"""
    if obj is None:
        return None
    elif isinstance(obj, (str, int, float, bool)):
        return obj
    elif hasattr(obj, 'isoformat'):  # datetime objects
        return obj.isoformat()
    elif isinstance(obj, (list, tuple)):
        return [clean_for_json(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: clean_for_json(value) for key, value in obj.items()}
    else:
        return str(obj)


def analyze_special_incidents_data(data_loader):
    """分析特殊事件數據"""
    try:
        if not data_loader or not hasattr(data_loader, 'loaded_data') or not data_loader.loaded_data:
            print("[ERROR] 無法獲取已載入的數據")
            return None
            
        loaded_data = data_loader.loaded_data
        
        # 提取基本會話信息
        session_info = {
            "year": getattr(loaded_data.get('session'), 'year', 'Unknown'),
            "race": getattr(loaded_data.get('session'), 'event_name', 'Unknown'),
            "session_type": getattr(loaded_data.get('session'), 'session_type', 'R'),
            "track_name": getattr(loaded_data.get('session'), 'event', {}).get('EventName', 'Unknown'),
            "date": str(getattr(loaded_data.get('session'), 'date', 'Unknown'))
        }
        
        # 提取賽事控制消息
        race_control_messages = extract_race_control_messages(loaded_data)
        special_incidents = categorize_special_incidents(race_control_messages)
        
        return {
            "session_info": session_info,
            "special_incidents": special_incidents,
            "total_incidents": len(special_incidents.get('all_incidents', [])),
            "incident_summary": generate_incident_summary(special_incidents)
        }
        
    except Exception as e:
        print(f"[ERROR] 分析特殊事件數據時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return None


def extract_race_control_messages(loaded_data):
    """提取賽事控制消息"""
    try:
        session = loaded_data.get('session')
        if not session:
            return []
            
        # 嘗試獲取賽事控制消息
        if hasattr(session, 'race_control_messages'):
            messages_df = session.race_control_messages
            if messages_df is not None and not messages_df.empty:
                return messages_df.to_dict('records')
        
        # 後備方案：從其他數據源提取
        return []
        
    except Exception as e:
        print(f"[WARNING] 提取賽事控制消息失敗: {e}")
        return []


def categorize_special_incidents(race_control_messages):
    """分類特殊事件"""
    categories = {
        "safety_car": [],
        "yellow_flags": [],
        "red_flags": [],
        "drs_events": [],
        "track_limits": [],
        "penalties": [],
        "weather_alerts": [],
        "other_incidents": [],
        "all_incidents": []
    }
    
    for message in race_control_messages:
        try:
            message_text = message.get('Message', '').upper()
            lap_number = message.get('Lap', 'Unknown')
            timestamp = message.get('Time', 'Unknown')
            
            incident = {
                "timestamp": str(timestamp),
                "lap": lap_number,
                "message": message.get('Message', ''),
                "category": "OTHER"
            }
            
            # 分類邏輯
            if any(keyword in message_text for keyword in ['SAFETY CAR', 'SC DEPLOYED', 'VSC']):
                incident["category"] = "SAFETY_CAR"
                categories["safety_car"].append(incident)
                
            elif any(keyword in message_text for keyword in ['YELLOW FLAG', 'YELLOW']):
                incident["category"] = "YELLOW_FLAG"
                categories["yellow_flags"].append(incident)
                
            elif any(keyword in message_text for keyword in ['RED FLAG', 'SESSION STOPPED']):
                incident["category"] = "RED_FLAG"
                categories["red_flags"].append(incident)
                
            elif any(keyword in message_text for keyword in ['DRS', 'DRAG REDUCTION']):
                incident["category"] = "DRS_EVENT"
                categories["drs_events"].append(incident)
                
            elif any(keyword in message_text for keyword in ['TRACK LIMITS', 'TIME DELETED']):
                incident["category"] = "TRACK_LIMITS"
                categories["track_limits"].append(incident)
                
            elif any(keyword in message_text for keyword in ['PENALTY', 'TIME PENALTY', 'GRID PENALTY']):
                incident["category"] = "PENALTY"
                categories["penalties"].append(incident)
                
            elif any(keyword in message_text for keyword in ['RAIN', 'WEATHER', 'WET']):
                incident["category"] = "WEATHER"
                categories["weather_alerts"].append(incident)
                
            else:
                incident["category"] = "OTHER"
                categories["other_incidents"].append(incident)
            
            categories["all_incidents"].append(incident)
            
        except Exception as e:
            print(f"[WARNING] 處理消息時發生錯誤: {e}")
            continue
    
    return categories


def generate_incident_summary(special_incidents):
    """生成事件摘要統計"""
    return {
        "safety_car_events": len(special_incidents.get("safety_car", [])),
        "yellow_flag_events": len(special_incidents.get("yellow_flags", [])),
        "red_flag_events": len(special_incidents.get("red_flags", [])),
        "drs_events": len(special_incidents.get("drs_events", [])),
        "track_limit_violations": len(special_incidents.get("track_limits", [])),
        "penalties_issued": len(special_incidents.get("penalties", [])),
        "weather_alerts": len(special_incidents.get("weather_alerts", [])),
        "other_incidents": len(special_incidents.get("other_incidents", []))
    }


def display_special_incidents_table(analysis_result):
    """顯示特殊事件表格"""
    if not analysis_result:
        print("[ERROR] 無分析結果可顯示")
        return
    
    session_info = analysis_result.get("session_info", {})
    special_incidents = analysis_result.get("special_incidents", {})
    incident_summary = analysis_result.get("incident_summary", {})
    
    print(f"\n[CRITICAL] 特殊事件報告分析 (功能 4.2)")
    print("=" * 80)
    print(f"📅 賽事: {session_info.get('year')} {session_info.get('track_name')}")
    print(f"[FINISH] 賽段: {session_info.get('session_type')} | 日期: {session_info.get('date')}")
    print(f"[INFO] 總特殊事件數: {analysis_result.get('total_incidents', 0)}")
    print("=" * 80)
    
    # 事件摘要表格
    summary_table = PrettyTable()
    summary_table.field_names = ["事件類型", "數量", "描述"]
    summary_table.align = "l"
    
    summary_data = [
        ("安全車事件", incident_summary.get("safety_car_events", 0), "Safety Car/VSC 部署"),
        ("黃旗事件", incident_summary.get("yellow_flag_events", 0), "黃旗警示事件"),
        ("紅旗事件", incident_summary.get("red_flag_events", 0), "比賽中止事件"),
        ("DRS事件", incident_summary.get("drs_events", 0), "DRS 啟用/禁用"),
        ("賽道限制", incident_summary.get("track_limit_violations", 0), "賽道限制違規"),
        ("處罰事件", incident_summary.get("penalties_issued", 0), "車手處罰"),
        ("天氣警報", incident_summary.get("weather_alerts", 0), "天氣相關警報"),
        ("其他事件", incident_summary.get("other_incidents", 0), "其他特殊事件")
    ]
    
    for event_type, count, description in summary_data:
        summary_table.add_row([event_type, count, description])
    
    print("\n[LIST] 特殊事件摘要:")
    print(summary_table)
    
    # 詳細事件列表
    if special_incidents.get("all_incidents"):
        detail_table = PrettyTable()
        detail_table.field_names = ["圈數", "時間", "類型", "事件描述"]
        detail_table.align = "l"
        detail_table.max_width["事件描述"] = 50
        
        # 顯示前20個事件
        incidents_to_show = special_incidents["all_incidents"][:20]
        for incident in incidents_to_show:
            detail_table.add_row([
                incident.get("lap", "N/A"),
                incident.get("timestamp", "Unknown"),
                incident.get("category", "OTHER"),
                incident.get("message", "")[:50] + "..." if len(incident.get("message", "")) > 50 else incident.get("message", "")
            ])
        
        print(f"\n[NOTE] 詳細事件列表 (顯示前20項，共{len(special_incidents['all_incidents'])}項):")
        print(detail_table)
        
        if len(special_incidents["all_incidents"]) > 20:
            print(f"... 還有 {len(special_incidents['all_incidents']) - 20} 項事件 (請查看JSON文件獲取完整列表)")


def save_special_incidents_raw_data(analysis_result, data_loader):
    """保存特殊事件原始數據為JSON格式"""
    if not analysis_result:
        print("[ERROR] 無分析結果可保存")
        return
    
    try:
        session_info = analysis_result.get("session_info", {})
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 確保json資料夾存在
        import os
        json_dir = "json"
        os.makedirs(json_dir, exist_ok=True)
        
        filename = os.path.join(json_dir, f"raw_data_special_incidents_{session_info.get('year', '2025')}_{session_info.get('race', 'Unknown')}_{timestamp}.json")
        
        # 準備JSON數據
        json_data = {
            "analysis_type": "special_incidents_analysis",
            "function": "4.2",
            "timestamp": datetime.now().isoformat(),
            "session_info": clean_for_json(session_info),
            "incident_analysis": {
                "total_incidents": analysis_result.get("total_incidents", 0),
                "incident_summary": clean_for_json(analysis_result.get("incident_summary", {})),
                "has_incidents": analysis_result.get("total_incidents", 0) > 0
            },
            "detailed_incidents": clean_for_json(analysis_result.get("special_incidents", {})),
            "metadata": {
                "analysis_date": datetime.now().isoformat(),
                "data_source": "FastF1 + OpenF1",
                "total_categories": 8,
                "version": "1.0"
            }
        }
        
        # 保存JSON文件
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 原始數據已保存至: {filename}")
        print(f"[INFO] JSON包含 {len(json_data.get('detailed_incidents', {}).get('all_incidents', []))} 項詳細事件記錄")
        
    except Exception as e:
        print(f"[ERROR] 保存JSON文件失敗: {e}")


def run_special_incidents_analysis(data_loader):
    """執行特殊事件報告分析的主函數"""
    try:
        print("\n[CRITICAL] 開始特殊事件報告分析...")
        
        # 檢查數據載入器
        if not data_loader:
            print("[ERROR] 數據載入器未初始化")
            return False
        
        # 分析特殊事件數據
        analysis_result = analyze_special_incidents_data(data_loader)
        
        if not analysis_result:
            print("[ERROR] 特殊事件分析失敗")
            return False
        
        # 顯示分析結果
        display_special_incidents_table(analysis_result)
        
        # 保存原始數據
        save_special_incidents_raw_data(analysis_result, data_loader)
        
        print("\n[SUCCESS] 特殊事件報告分析完成")
        return True
        
    except Exception as e:
        print(f"[ERROR] 執行特殊事件報告分析時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("[WARNING] 此模組需要通過主程式調用")
    print("請使用 F1_Analysis_Main_Menu.bat 選擇功能 4.2")
