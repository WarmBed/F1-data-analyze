#!/usr/bin/env python3
"""
F1 所有事件詳細列表模組 (功能 4.5)
作者: F1 Analysis Team
版本: 1.0

專門處理所有事件詳細列表分析，包括：
- 完整事件時間軸
- 事件分類和統計
- 詳細事件信息表格
- 時序分析
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from prettytable import PrettyTable
import re


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


def analyze_all_incidents_data(data_loader):
    """分析所有事件數據"""
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
        
        # 提取所有賽事事件
        race_control_messages = extract_race_control_messages(loaded_data)
        all_incidents = process_all_incidents(race_control_messages)
        timeline_analysis = create_timeline_analysis(all_incidents)
        
        return {
            "session_info": session_info,
            "all_incidents": all_incidents,
            "timeline_analysis": timeline_analysis,
            "total_incidents": len(all_incidents),
            "incident_statistics": generate_incident_statistics(all_incidents)
        }
        
    except Exception as e:
        print(f"[ERROR] 分析所有事件數據時發生錯誤: {e}")
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
        
        return []
        
    except Exception as e:
        print(f"[WARNING] 提取賽事控制消息失敗: {e}")
        return []


def process_all_incidents(race_control_messages):
    """處理所有事件"""
    all_incidents = []
    
    for i, message in enumerate(race_control_messages):
        try:
            message_text = message.get('Message', '')
            lap_number = message.get('Lap', 'Unknown')
            timestamp = message.get('Time', 'Unknown')
            
            # 提取涉及的車手
            involved_drivers = extract_involved_drivers(message_text)
            
            incident = {
                "incident_id": i + 1,
                "timestamp": str(timestamp),
                "lap": lap_number,
                "message": message_text,
                "category": categorize_incident(message_text),
                "severity": assess_incident_severity(message_text),
                "involved_drivers": involved_drivers,
                "driver_count": len(involved_drivers),
                "flags": extract_flags(message_text),
                "penalties": extract_penalties(message_text),
                "track_position": extract_track_position(message_text)
            }
            
            all_incidents.append(incident)
            
        except Exception as e:
            print(f"[WARNING] 處理事件 {i+1} 時發生錯誤: {e}")
            continue
    
    return all_incidents


def extract_involved_drivers(message_text):
    """提取涉及的車手"""
    drivers = []
    
    # 標準格式: CAR 1 (VER)
    car_matches = re.findall(r'CAR \d+ \(([A-Z]{3})\)', message_text.upper())
    drivers.extend(car_matches)
    
    # 多車手格式: CARS 1 (VER) AND 44 (HAM)
    multi_car_matches = re.findall(r'\(([A-Z]{3})\)', message_text.upper())
    for driver in multi_car_matches:
        if driver not in drivers:
            drivers.append(driver)
    
    return drivers


def categorize_incident(message_text):
    """分類事件"""
    message_upper = message_text.upper()
    
    if any(keyword in message_upper for keyword in ['SAFETY CAR', 'SC DEPLOYED', 'VSC']):
        return 'SAFETY_CAR'
    elif any(keyword in message_upper for keyword in ['YELLOW FLAG', 'YELLOW']):
        return 'YELLOW_FLAG'
    elif any(keyword in message_upper for keyword in ['RED FLAG', 'SESSION STOPPED']):
        return 'RED_FLAG'
    elif any(keyword in message_upper for keyword in ['DRS', 'DRAG REDUCTION']):
        return 'DRS_EVENT'
    elif 'TRACK LIMITS' in message_upper or 'TIME DELETED' in message_upper:
        return 'TRACK_LIMITS'
    elif any(keyword in message_upper for keyword in ['PENALTY', 'TIME PENALTY', 'GRID PENALTY']):
        return 'PENALTY'
    elif any(keyword in message_upper for keyword in ['CRASH', 'COLLISION', 'INCIDENT']):
        return 'INCIDENT'
    elif any(keyword in message_upper for keyword in ['PIT', 'PITSTOP']):
        return 'PIT_EVENT'
    elif any(keyword in message_upper for keyword in ['RAIN', 'WEATHER', 'WET']):
        return 'WEATHER'
    elif any(keyword in message_upper for keyword in ['START', 'FORMATION', 'GRID']):
        return 'RACE_START'
    elif any(keyword in message_upper for keyword in ['CHEQUERED', 'FINISH']):
        return 'RACE_END'
    else:
        return 'OTHER'


def assess_incident_severity(message_text):
    """評估事件嚴重程度"""
    message_upper = message_text.upper()
    
    if any(keyword in message_upper for keyword in ['RED FLAG', 'CRASH', 'DANGEROUS', 'DISQUALIFIED']):
        return 'CRITICAL'
    elif any(keyword in message_upper for keyword in ['SAFETY CAR', 'YELLOW FLAG', 'PENALTY', 'COLLISION']):
        return 'HIGH'
    elif any(keyword in message_upper for keyword in ['INCIDENT', 'UNSAFE', 'WARNING']):
        return 'MEDIUM'
    elif any(keyword in message_upper for keyword in ['TRACK LIMITS', 'TIME DELETED', 'NOTED']):
        return 'LOW'
    else:
        return 'MINIMAL'


def extract_flags(message_text):
    """提取旗幟信息"""
    flags = []
    message_upper = message_text.upper()
    
    if 'YELLOW FLAG' in message_upper or 'YELLOW' in message_upper:
        flags.append('YELLOW')
    if 'RED FLAG' in message_upper:
        flags.append('RED')
    if 'GREEN FLAG' in message_upper or 'GREEN LIGHT' in message_upper:
        flags.append('GREEN')
    if 'BLUE FLAG' in message_upper:
        flags.append('BLUE')
    if 'CHEQUERED FLAG' in message_upper:
        flags.append('CHEQUERED')
    
    return flags


def extract_penalties(message_text):
    """提取處罰信息"""
    penalties = []
    message_upper = message_text.upper()
    
    if 'TIME PENALTY' in message_upper:
        penalties.append('TIME_PENALTY')
    if 'GRID PENALTY' in message_upper:
        penalties.append('GRID_PENALTY')
    if 'DISQUALIFIED' in message_upper:
        penalties.append('DISQUALIFIED')
    if 'WARNING' in message_upper:
        penalties.append('WARNING')
    if 'TIME DELETED' in message_upper:
        penalties.append('TIME_DELETED')
    
    return penalties


def extract_track_position(message_text):
    """提取賽道位置信息"""
    message_upper = message_text.upper()
    
    # 提取彎道信息
    turn_matches = re.findall(r'TURN (\d+)', message_upper)
    if turn_matches:
        return f"Turn {turn_matches[0]}"
    
    # 提取其他位置信息
    if 'PIT ENTRY' in message_upper:
        return 'Pit Entry'
    elif 'PIT EXIT' in message_upper:
        return 'Pit Exit'
    elif 'START/FINISH' in message_upper:
        return 'Start/Finish Line'
    
    return 'Unknown'


def create_timeline_analysis(all_incidents):
    """創建時間軸分析"""
    timeline = {
        "total_duration_laps": 0,
        "incidents_by_lap": {},
        "peak_activity_laps": [],
        "quiet_periods": [],
        "incident_frequency": {}
    }
    
    # 按圈數分組事件
    for incident in all_incidents:
        lap = incident.get('lap', 'Unknown')
        if lap != 'Unknown' and isinstance(lap, (int, float)):
            lap = int(lap)
            if lap not in timeline["incidents_by_lap"]:
                timeline["incidents_by_lap"][lap] = []
            timeline["incidents_by_lap"][lap].append(incident)
    
    # 計算總持續圈數
    if timeline["incidents_by_lap"]:
        timeline["total_duration_laps"] = max(timeline["incidents_by_lap"].keys())
    
    # 找出高活動圈數（事件數 >= 3）
    for lap, incidents in timeline["incidents_by_lap"].items():
        if len(incidents) >= 3:
            timeline["peak_activity_laps"].append({
                "lap": lap,
                "incident_count": len(incidents),
                "incidents": [inc["category"] for inc in incidents]
            })
    
    # 計算事件頻率
    category_count = {}
    for incident in all_incidents:
        category = incident.get('category', 'OTHER')
        category_count[category] = category_count.get(category, 0) + 1
    
    timeline["incident_frequency"] = category_count
    
    return timeline


def generate_incident_statistics(all_incidents):
    """生成事件統計"""
    stats = {
        "total_incidents": len(all_incidents),
        "by_category": {},
        "by_severity": {},
        "driver_involvement": {},
        "most_common_category": "",
        "most_severe_incidents": 0,
        "average_drivers_per_incident": 0
    }
    
    # 按類別統計
    for incident in all_incidents:
        category = incident.get('category', 'OTHER')
        severity = incident.get('severity', 'MINIMAL')
        involved_drivers = incident.get('involved_drivers', [])
        
        # 類別統計
        stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
        
        # 嚴重程度統計
        stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1
        
        # 車手參與統計
        for driver in involved_drivers:
            stats["driver_involvement"][driver] = stats["driver_involvement"].get(driver, 0) + 1
    
    # 找出最常見類別
    if stats["by_category"]:
        stats["most_common_category"] = max(stats["by_category"].items(), key=lambda x: x[1])[0]
    
    # 計算嚴重事件數
    stats["most_severe_incidents"] = stats["by_severity"].get("CRITICAL", 0) + stats["by_severity"].get("HIGH", 0)
    
    # 計算平均車手參與度
    total_driver_involvement = sum(len(incident.get('involved_drivers', [])) for incident in all_incidents)
    stats["average_drivers_per_incident"] = round(total_driver_involvement / len(all_incidents), 2) if all_incidents else 0
    
    return stats


def display_all_incidents_table(analysis_result):
    """顯示所有事件表格"""
    if not analysis_result:
        print("[ERROR] 無分析結果可顯示")
        return
    
    session_info = analysis_result.get("session_info", {})
    all_incidents = analysis_result.get("all_incidents", [])
    incident_statistics = analysis_result.get("incident_statistics", {})
    timeline_analysis = analysis_result.get("timeline_analysis", {})
    
    print(f"\n[LIST] 所有事件詳細列表 (功能 4.5)")
    print("=" * 80)
    print(f"📅 賽事: {session_info.get('year')} {session_info.get('track_name')}")
    print(f"[FINISH] 賽段: {session_info.get('session_type')} | 日期: {session_info.get('date')}")
    print(f"[INFO] 總事件數: {analysis_result.get('total_incidents', 0)}")
    print("=" * 80)
    
    # 事件統計摘要
    print(f"\n[INFO] 事件統計摘要:")
    print(f"🔴 嚴重事件數: {incident_statistics.get('most_severe_incidents', 0)}")
    print(f"[STATS] 最常見事件類型: {incident_statistics.get('most_common_category', 'N/A')}")
    print(f"👥 平均車手參與度: {incident_statistics.get('average_drivers_per_incident', 0)} 車手/事件")
    print(f"[FINISH] 比賽持續圈數: {timeline_analysis.get('total_duration_laps', 0)} 圈")
    
    # 類別統計表格
    if incident_statistics.get('by_category'):
        category_table = PrettyTable()
        category_table.field_names = ["事件類型", "數量", "百分比"]
        category_table.align = "l"
        
        total_incidents = incident_statistics.get('total_incidents', 1)
        sorted_categories = sorted(incident_statistics['by_category'].items(), key=lambda x: x[1], reverse=True)
        
        for category, count in sorted_categories:
            percentage = round((count / total_incidents) * 100, 1)
            category_table.add_row([
                category.replace('_', ' '),
                count,
                f"{percentage}%"
            ])
        
        print(f"\n[LIST] 事件類型統計:")
        print(category_table)
    
    # 詳細事件列表（顯示前30個）
    if all_incidents:
        detail_table = PrettyTable()
        detail_table.field_names = ["ID", "圈數", "時間", "類型", "嚴重程度", "車手", "事件描述"]
        detail_table.align = "l"
        detail_table.max_width["事件描述"] = 40
        
        incidents_to_show = all_incidents[:30]  # 只顯示前30個
        
        for incident in incidents_to_show:
            involved_drivers_str = ", ".join(incident.get('involved_drivers', []))[:15] + "..." if len(", ".join(incident.get('involved_drivers', []))) > 15 else ", ".join(incident.get('involved_drivers', []))
            
            detail_table.add_row([
                incident.get('incident_id', 'N/A'),
                incident.get('lap', 'N/A'),
                str(incident.get('timestamp', 'Unknown'))[:8] + "..." if len(str(incident.get('timestamp', 'Unknown'))) > 8 else str(incident.get('timestamp', 'Unknown')),
                incident.get('category', 'OTHER').replace('_', ' ')[:12],
                incident.get('severity', 'MINIMAL')[:8],
                involved_drivers_str,
                incident.get('message', '')[:40] + "..." if len(incident.get('message', '')) > 40 else incident.get('message', '')
            ])
        
        print(f"\n[NOTE] 詳細事件列表 (顯示前30項，共{len(all_incidents)}項):")
        print(detail_table)
        
        if len(all_incidents) > 30:
            print(f"... 還有 {len(all_incidents) - 30} 項事件 (請查看JSON文件獲取完整列表)")
    
    # 高活動圈數分析
    peak_activity_laps = timeline_analysis.get('peak_activity_laps', [])
    if peak_activity_laps:
        print(f"\n[HOT] 高活動圈數分析 (事件數 >= 3):")
        for peak in peak_activity_laps[:5]:  # 只顯示前5個
            print(f"   圈數 {peak['lap']}: {peak['incident_count']} 個事件 - {', '.join(peak['incidents'])}")


def save_all_incidents_raw_data(analysis_result, data_loader):
    """保存所有事件原始數據為JSON格式"""
    if not analysis_result:
        print("[ERROR] 無分析結果可保存")
        return
    
    try:
        session_info = analysis_result.get("session_info", {})
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        filename = f"raw_data_all_incidents_{session_info.get('year', '2025')}_{session_info.get('race', 'Unknown')}_{timestamp}.json"
        
        # 準備JSON數據
        json_data = {
            "analysis_type": "all_incidents_analysis",
            "function": "4.5",
            "timestamp": datetime.now().isoformat(),
            "session_info": clean_for_json(session_info),
            "incident_analysis": {
                "total_incidents": analysis_result.get("total_incidents", 0),
                "incident_statistics": clean_for_json(analysis_result.get("incident_statistics", {})),
                "timeline_analysis": clean_for_json(analysis_result.get("timeline_analysis", {})),
                "has_critical_incidents": analysis_result.get("incident_statistics", {}).get("most_severe_incidents", 0) > 0
            },
            "all_incidents": clean_for_json(analysis_result.get("all_incidents", [])),
            "metadata": {
                "analysis_date": datetime.now().isoformat(),
                "data_source": "FastF1 + OpenF1",
                "severity_levels": ["MINIMAL", "LOW", "MEDIUM", "HIGH", "CRITICAL"],
                "incident_categories": ["SAFETY_CAR", "YELLOW_FLAG", "RED_FLAG", "DRS_EVENT", "TRACK_LIMITS", "PENALTY", "INCIDENT", "PIT_EVENT", "WEATHER", "RACE_START", "RACE_END", "OTHER"],
                "version": "1.0"
            }
        }
        
        # 保存JSON文件
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 原始數據已保存至: {filename}")
        print(f"[INFO] JSON包含 {len(json_data.get('all_incidents', []))} 項完整事件記錄")
        
    except Exception as e:
        print(f"[ERROR] 保存JSON文件失敗: {e}")


def run_all_incidents_analysis(data_loader):
    """執行所有事件詳細列表分析的主函數"""
    try:
        print("\n[LIST] 開始所有事件詳細列表分析...")
        
        # 檢查數據載入器
        if not data_loader:
            print("[ERROR] 數據載入器未初始化")
            return False
        
        # 分析所有事件數據
        analysis_result = analyze_all_incidents_data(data_loader)
        
        if not analysis_result:
            print("[ERROR] 所有事件分析失敗")
            return False
        
        # 顯示分析結果
        display_all_incidents_table(analysis_result)
        
        # 保存原始數據
        save_all_incidents_raw_data(analysis_result, data_loader)
        
        print("\n[SUCCESS] 所有事件詳細列表分析完成")
        return True
        
    except Exception as e:
        print(f"[ERROR] 執行所有事件詳細列表分析時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("[WARNING] 此模組需要通過主程式調用")
    print("請使用 F1_Analysis_Main_Menu.bat 選擇功能 4.5")
