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
    """分析所有事件數據 - 增強版包含詳細旗幟信息"""
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
    """處理所有事件 - 增強版本保留所有原始數據"""
    all_incidents = []
    
    for i, message in enumerate(race_control_messages):
        try:
            # 提取所有原始欄位
            message_text = message.get('Message', '')
            lap_number = message.get('Lap', 'Unknown')
            timestamp = message.get('Time', 'Unknown')
            
            # 保留所有 FastF1 原始欄位
            raw_category = message.get('Category', 'Unknown')
            raw_status = message.get('Status', 'Unknown')
            raw_flag = message.get('Flag', 'Unknown')
            raw_scope = message.get('Scope', 'Unknown')
            raw_sector = message.get('Sector', 'Unknown')
            raw_racing_number = message.get('RacingNumber', 'Unknown')
            
            # 提取涉及的車手
            involved_drivers = extract_involved_drivers(message_text)
            
            incident = {
                "incident_id": i + 1,
                "timestamp": str(timestamp),
                "lap": lap_number,
                "message": message_text,
                
                # 原始 FastF1 欄位
                "original_fastf1_data": {
                    "Category": raw_category,
                    "Status": raw_status,
                    "Flag": raw_flag,
                    "Scope": raw_scope,
                    "Sector": raw_sector,
                    "RacingNumber": raw_racing_number
                },
                
                # 分析後的分類
                "enhanced_category": categorize_incident(message_text),
                "severity": assess_incident_severity(message_text),
                "involved_drivers": involved_drivers,
                "driver_count": len(involved_drivers),
                "flags": extract_flags(message_text),
                "penalties": extract_penalties(message_text),
                "track_position": extract_track_position(message_text),
                
                # 新增分析欄位
                "is_safety_related": any(keyword in message_text.upper() for keyword in 
                                       ['SAFETY CAR', 'VSC', 'YELLOW', 'RED FLAG', 'DOUBLE YELLOW']),
                "involves_penalty": any(keyword in message_text.upper() for keyword in 
                                      ['PENALTY', 'TIME DELETED', 'INVESTIGATION', 'WARNING']),
                "track_position_details": {
                    "sector": raw_sector if raw_sector != 'Unknown' and str(raw_sector) != 'nan' else extract_sector_from_message(message_text),
                    "scope": raw_scope if raw_scope != 'Unknown' else None,
                    "racing_number": raw_racing_number if raw_racing_number != 'Unknown' and str(raw_racing_number) != 'nan' else None
                }
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


def extract_sector_from_message(message_text):
    """從消息文本中提取扇區信息"""
    message_upper = message_text.upper()
    sector_match = re.search(r'SECTOR (\d+)', message_upper)
    if sector_match:
        return int(sector_match.group(1))
    return None


def categorize_incident(message_text):
    """分類事件 - 增強版本包含更詳細的旗幟分類"""
    message_upper = message_text.upper()
    
    # 安全車相關
    if 'VIRTUAL SAFETY CAR' in message_upper or 'VSC' in message_upper:
        return 'VIRTUAL_SAFETY_CAR'
    elif any(keyword in message_upper for keyword in ['SAFETY CAR', 'SC DEPLOYED']):
        return 'SAFETY_CAR'
    
    # 旗幟相關 - 詳細分類
    elif 'DOUBLE YELLOW' in message_upper:
        return 'DOUBLE_YELLOW_FLAG'
    elif 'YELLOW FLAG' in message_upper or ('YELLOW' in message_upper and ('SECTOR' in message_upper or 'TRACK' in message_upper)):
        return 'YELLOW_FLAG'
    elif 'BLUE FLAG' in message_upper or 'WAVED BLUE' in message_upper:
        return 'BLUE_FLAG'
    elif 'RED FLAG' in message_upper or 'SESSION STOPPED' in message_upper:
        return 'RED_FLAG'
    elif 'GREEN FLAG' in message_upper or 'GREEN LIGHT' in message_upper:
        return 'GREEN_FLAG'
    elif 'CHEQUERED FLAG' in message_upper:
        return 'CHEQUERED_FLAG'
    elif 'CLEAR' in message_upper and ('SECTOR' in message_upper or 'TRACK' in message_upper):
        return 'FLAG_CLEAR'
    
    # DRS 相關
    elif 'DRS ENABLED' in message_upper:
        return 'DRS_ENABLED'
    elif 'DRS DISABLED' in message_upper:
        return 'DRS_DISABLED'
    elif any(keyword in message_upper for keyword in ['DRS', 'DRAG REDUCTION']):
        return 'DRS_EVENT'
    
    # 處罰相關
    elif 'TIME PENALTY' in message_upper:
        return 'TIME_PENALTY'
    elif 'GRID PENALTY' in message_upper:
        return 'GRID_PENALTY'
    elif 'DISQUALIFIED' in message_upper:
        return 'DISQUALIFICATION'
    elif 'WARNING' in message_upper:
        return 'WARNING'
    elif 'PENALTY' in message_upper:
        return 'PENALTY'
    
    # 賽道相關
    elif 'TRACK LIMITS' in message_upper:
        return 'TRACK_LIMITS'
    elif 'TIME DELETED' in message_upper or 'LAP DELETED' in message_upper:
        return 'TIME_DELETED'
    elif 'TRACK SURFACE SLIPPERY' in message_upper:
        return 'TRACK_CONDITIONS'
    
    # 事故和調查
    elif 'UNDER INVESTIGATION' in message_upper:
        return 'INVESTIGATION'
    elif 'NO FURTHER ACTION' in message_upper:
        return 'NO_ACTION'
    elif any(keyword in message_upper for keyword in ['CRASH', 'COLLISION', 'CONTACT']):
        return 'INCIDENT'
    elif 'UNSAFE RELEASE' in message_upper:
        return 'UNSAFE_RELEASE'
    elif 'NOTED' in message_upper and 'INVOLVING' in message_upper:
        return 'INCIDENT_NOTED'
    
    # 進站相關
    elif 'PIT EXIT OPEN' in message_upper:
        return 'PIT_EXIT_OPEN'
    elif 'PIT EXIT CLOSED' in message_upper:
        return 'PIT_EXIT_CLOSED'
    elif any(keyword in message_upper for keyword in ['PIT', 'PITSTOP']):
        return 'PIT_EVENT'
    
    # 天氣相關
    elif 'RISK OF RAIN' in message_upper:
        return 'WEATHER_FORECAST'
    elif any(keyword in message_upper for keyword in ['RAIN', 'WEATHER', 'WET']):
        return 'WEATHER'
    elif 'LOW GRIP CONDITIONS' in message_upper:
        return 'TRACK_CONDITIONS'
    
    # 比賽狀態
    elif 'ABORTED START' in message_upper:
        return 'ABORTED_START'
    elif 'FORMATION LAP' in message_upper:
        return 'FORMATION_LAP'
    elif any(keyword in message_upper for keyword in ['START', 'FORMATION', 'GRID']):
        return 'RACE_START'
    elif 'CHEQUERED' in message_upper or 'FINISH' in message_upper:
        return 'RACE_END'
    
    # 車輛和恢復
    elif 'RECOVERY VEHICLE' in message_upper:
        return 'RECOVERY_VEHICLE'
    elif 'LAPPED CAR' in message_upper:
        return 'LAPPED_CAR_OVERTAKE'
    
    # 其他
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
    """提取旗幟信息 - 增強版本包含詳細信息"""
    flags = []
    message_upper = message_text.upper()
    
    # Yellow Flag 詳細分析
    if 'YELLOW FLAG' in message_upper or 'YELLOW' in message_upper:
        flag_info = {
            "type": "YELLOW",
            "reason": "",
            "location": "",
            "duration": ""
        }
        
        # 分析黃旗原因
        if any(keyword in message_upper for keyword in ['ACCIDENT', 'CRASH', 'COLLISION']):
            flag_info["reason"] = "ACCIDENT"
        elif any(keyword in message_upper for keyword in ['DEBRIS', 'OBJECT']):
            flag_info["reason"] = "DEBRIS"
        elif any(keyword in message_upper for keyword in ['SPIN', 'STOPPED']):
            flag_info["reason"] = "VEHICLE_INCIDENT"
        elif any(keyword in message_upper for keyword in ['MARSHAL', 'RECOVERY']):
            flag_info["reason"] = "TRACK_OPERATIONS"
        else:
            flag_info["reason"] = "GENERAL"
        
        # 提取位置信息
        import re
        sector_match = re.search(r'SECTOR (\d+)', message_upper)
        turn_match = re.search(r'TURN (\d+)', message_upper)
        corner_match = re.search(r'CORNER (\d+)', message_upper)
        
        if sector_match:
            flag_info["location"] = f"SECTOR_{sector_match.group(1)}"
        elif turn_match:
            flag_info["location"] = f"TURN_{turn_match.group(1)}"
        elif corner_match:
            flag_info["location"] = f"CORNER_{corner_match.group(1)}"
        else:
            flag_info["location"] = "UNKNOWN"
        
        flags.append(flag_info)
    
    # Red Flag 詳細分析
    if 'RED FLAG' in message_upper:
        flag_info = {
            "type": "RED",
            "reason": "",
            "session_status": "STOPPED"
        }
        
        # 分析紅旗原因
        if any(keyword in message_upper for keyword in ['SERIOUS ACCIDENT', 'MAJOR INCIDENT', 'SAFETY']):
            flag_info["reason"] = "SAFETY_CONCERN"
        elif any(keyword in message_upper for keyword in ['WEATHER', 'RAIN', 'CONDITIONS']):
            flag_info["reason"] = "WEATHER_CONDITIONS"
        elif any(keyword in message_upper for keyword in ['BARRIER', 'DAMAGE', 'TRACK']):
            flag_info["reason"] = "TRACK_DAMAGE"
        elif 'SESSION STOPPED' in message_upper:
            flag_info["reason"] = "SESSION_SUSPENSION"
        else:
            flag_info["reason"] = "GENERAL"
        
        flags.append(flag_info)
    
    # 其他旗幟
    if 'GREEN FLAG' in message_upper or 'GREEN LIGHT' in message_upper:
        flags.append({"type": "GREEN", "status": "SESSION_RESUMED"})
    if 'BLUE FLAG' in message_upper:
        flags.append({"type": "BLUE", "instruction": "MOVE_ASIDE"})
    if 'CHEQUERED FLAG' in message_upper:
        flags.append({"type": "CHEQUERED", "status": "SESSION_END"})
    
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
                "enhanced_categories": [inc.get("enhanced_category", "OTHER") for inc in incidents],
                "original_categories": [inc.get("original_fastf1_data", {}).get("Category", "Unknown") for inc in incidents]
            })
    
    # 計算事件頻率 - 雙重分類
    enhanced_category_count = {}
    original_category_count = {}
    for incident in all_incidents:
        enhanced_cat = incident.get('enhanced_category', 'OTHER')
        original_cat = incident.get('original_fastf1_data', {}).get('Category', 'Unknown')
        
        enhanced_category_count[enhanced_cat] = enhanced_category_count.get(enhanced_cat, 0) + 1
        original_category_count[original_cat] = original_category_count.get(original_cat, 0) + 1
    
    timeline["enhanced_incident_frequency"] = enhanced_category_count
    timeline["original_incident_frequency"] = original_category_count
    
    return timeline


def generate_incident_statistics(all_incidents):
    """生成事件統計 - 增強版本包含詳細旗幟統計和原始分類"""
    stats = {
        "total_incidents": len(all_incidents),
        "by_enhanced_category": {},
        "by_original_category": {},
        "by_severity": {},
        "driver_involvement": {},
        "flag_statistics": {
            "yellow_flags": {
                "total_count": 0,
                "by_reason": {},
                "by_location": {},
                "details": []
            },
            "red_flags": {
                "total_count": 0,
                "by_reason": {},
                "details": []
            },
            "other_flags": {
                "green_flags": 0,
                "blue_flags": 0,
                "chequered_flags": 0,
                "double_yellow_flags": 0,
                "clear_flags": 0
            }
        },
        "safety_related_count": 0,
        "penalty_related_count": 0,
        "most_common_enhanced_category": "",
        "most_common_original_category": "",
        "most_severe_incidents": 0,
        "average_drivers_per_incident": 0
    }
    
    # 按類別統計
    for incident in all_incidents:
        enhanced_category = incident.get('enhanced_category', 'OTHER')
        original_category = incident.get('original_fastf1_data', {}).get('Category', 'Unknown')
        severity = incident.get('severity', 'MINIMAL')
        involved_drivers = incident.get('involved_drivers', [])
        flags = incident.get('flags', [])
        
        # 增強分類統計
        stats["by_enhanced_category"][enhanced_category] = stats["by_enhanced_category"].get(enhanced_category, 0) + 1
        
        # 原始分類統計
        stats["by_original_category"][original_category] = stats["by_original_category"].get(original_category, 0) + 1
        
        # 嚴重程度統計
        stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1
        
        # 安全和處罰相關統計
        if incident.get('is_safety_related', False):
            stats["safety_related_count"] += 1
        if incident.get('involves_penalty', False):
            stats["penalty_related_count"] += 1
        
        # 車手參與統計
        for driver in involved_drivers:
            stats["driver_involvement"][driver] = stats["driver_involvement"].get(driver, 0) + 1
        severity = incident.get('severity', 'MINIMAL')
        involved_drivers = incident.get('involved_drivers', [])
        flags = incident.get('flags', [])
        
        # 旗幟統計 - 增強版本
        enhanced_cat = enhanced_category.upper()
        if 'YELLOW_FLAG' in enhanced_cat:
            stats["flag_statistics"]["other_flags"]["yellow_flags"] = stats["flag_statistics"]["other_flags"].get("yellow_flags", 0) + 1
        elif 'DOUBLE_YELLOW_FLAG' in enhanced_cat:
            stats["flag_statistics"]["other_flags"]["double_yellow_flags"] += 1
        elif 'BLUE_FLAG' in enhanced_cat:
            stats["flag_statistics"]["other_flags"]["blue_flags"] += 1
        elif 'GREEN_FLAG' in enhanced_cat:
            stats["flag_statistics"]["other_flags"]["green_flags"] += 1
        elif 'CHEQUERED_FLAG' in enhanced_cat:
            stats["flag_statistics"]["other_flags"]["chequered_flags"] += 1
        elif 'FLAG_CLEAR' in enhanced_cat:
            stats["flag_statistics"]["other_flags"]["clear_flags"] += 1
        
        # 傳統旗幟統計
        for flag in flags:
            if isinstance(flag, dict):
                flag_type = flag.get('type', '').upper()
                
                if flag_type == 'YELLOW':
                    stats["flag_statistics"]["yellow_flags"]["total_count"] += 1
                    
                    # 黃旗原因統計
                    reason = flag.get('reason', 'UNKNOWN')
                    yellow_reasons = stats["flag_statistics"]["yellow_flags"]["by_reason"]
                    yellow_reasons[reason] = yellow_reasons.get(reason, 0) + 1
                    
                    # 黃旗位置統計
                    location = flag.get('location', 'UNKNOWN')
                    yellow_locations = stats["flag_statistics"]["yellow_flags"]["by_location"]
                    yellow_locations[location] = yellow_locations.get(location, 0) + 1
                    
                    # 詳細信息
                    stats["flag_statistics"]["yellow_flags"]["details"].append({
                        "incident_id": incident.get('incident_id'),
                        "lap": incident.get('lap'),
                        "timestamp": incident.get('timestamp'),
                        "reason": reason,
                        "location": location,
                        "message": incident.get('message', '')[:100] + "..." if len(incident.get('message', '')) > 100 else incident.get('message', '')
                    })
                
                elif flag_type == 'RED':
                    stats["flag_statistics"]["red_flags"]["total_count"] += 1
                    
                    # 紅旗原因統計
                    reason = flag.get('reason', 'UNKNOWN')
                    red_reasons = stats["flag_statistics"]["red_flags"]["by_reason"]
                    red_reasons[reason] = red_reasons.get(reason, 0) + 1
                    
                    # 詳細信息
                    stats["flag_statistics"]["red_flags"]["details"].append({
                        "incident_id": incident.get('incident_id'),
                        "lap": incident.get('lap'),
                        "timestamp": incident.get('timestamp'),
                        "reason": reason,
                        "session_status": flag.get('session_status', 'STOPPED'),
                        "message": incident.get('message', '')[:100] + "..." if len(incident.get('message', '')) > 100 else incident.get('message', '')
                    })
    
    # 找出最常見類別
    if stats["by_enhanced_category"]:
        stats["most_common_enhanced_category"] = max(stats["by_enhanced_category"].items(), key=lambda x: x[1])[0]
    
    if stats["by_original_category"]:
        stats["most_common_original_category"] = max(stats["by_original_category"].items(), key=lambda x: x[1])[0]
    
    # 計算嚴重事件數
    stats["most_severe_incidents"] = stats["by_severity"].get("CRITICAL", 0) + stats["by_severity"].get("HIGH", 0)
    
    # 計算平均車手參與度
    total_driver_involvement = sum(len(incident.get('involved_drivers', [])) for incident in all_incidents)
    stats["average_drivers_per_incident"] = round(total_driver_involvement / len(all_incidents), 2) if all_incidents else 0
    
    return stats


def display_all_incidents_table(analysis_result):
    """顯示所有事件表格 - 增強版本包含旗幟統計"""
    if not analysis_result:
        print("[ERROR] 無分析結果可顯示")
        return
    
    session_info = analysis_result.get("session_info", {})
    all_incidents = analysis_result.get("all_incidents", [])
    incident_statistics = analysis_result.get("incident_statistics", {})
    timeline_analysis = analysis_result.get("timeline_analysis", {})
    flag_stats = incident_statistics.get("flag_statistics", {})
    
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
    
    # 旗幟統計摘要
    print(f"\n🏁 旗幟統計摘要:")
    yellow_flags = flag_stats.get("yellow_flags", {})
    red_flags = flag_stats.get("red_flags", {})
    other_flags = flag_stats.get("other_flags", {})
    
    print(f"🟡 黃旗事件: {yellow_flags.get('total_count', 0)} 次")
    if yellow_flags.get('by_reason'):
        print("   黃旗原因分布:")
        for reason, count in yellow_flags['by_reason'].items():
            print(f"     • {reason}: {count} 次")
    
    print(f"🔴 紅旗事件: {red_flags.get('total_count', 0)} 次")
    if red_flags.get('by_reason'):
        print("   紅旗原因分布:")
        for reason, count in red_flags['by_reason'].items():
            print(f"     • {reason}: {count} 次")
    
    print(f"🟢 綠旗事件: {other_flags.get('green_flags', 0)} 次")
    print(f"🔵 藍旗事件: {other_flags.get('blue_flags', 0)} 次")
    print(f"🏁 方格旗事件: {other_flags.get('chequered_flags', 0)} 次")
    
    # 旗幟統計詳細信息
    flag_stats = incident_statistics.get('flag_statistics', {})
    if flag_stats:
        print(f"\n[FLAG] 旗幟事件統計詳情:")
        print("=" * 60)
        
        # 黃旗統計
        yellow_flags = flag_stats.get('yellow_flags', {})
        print(f"🟨 黃旗事件: {yellow_flags.get('total_count', 0)} 次")
        
        if yellow_flags.get('by_reason'):
            print(f"   黃旗原因分佈:")
            for reason, count in yellow_flags['by_reason'].items():
                print(f"      • {reason.replace('_', ' ')}: {count} 次")
        
        if yellow_flags.get('by_location'):
            print(f"   黃旗位置分佈:")
            for location, count in yellow_flags['by_location'].items():
                if location != 'UNKNOWN':
                    print(f"      • {location.replace('_', ' ')}: {count} 次")
        
        # 紅旗統計
        red_flags = flag_stats.get('red_flags', {})
        print(f"\n🟥 紅旗事件: {red_flags.get('total_count', 0)} 次")
        
        if red_flags.get('by_reason'):
            print(f"   紅旗原因分佈:")
            for reason, count in red_flags['by_reason'].items():
                print(f"      • {reason.replace('_', ' ')}: {count} 次")
        
        # 其他旗幟
        other_flags = flag_stats.get('other_flags', {})
        if any(other_flags.values()):
            print(f"\n🏁 其他旗幟:")
            if other_flags.get('green_flags', 0) > 0:
                print(f"   • 綠旗: {other_flags['green_flags']} 次")
            if other_flags.get('blue_flags', 0) > 0:
                print(f"   • 藍旗: {other_flags['blue_flags']} 次")
            if other_flags.get('chequered_flags', 0) > 0:
                print(f"   • 方格旗: {other_flags['chequered_flags']} 次")
        
        print("=" * 60)

    # 增強分類統計表格
    if incident_statistics.get('by_enhanced_category'):
        category_table = PrettyTable()
        category_table.field_names = ["增強事件類型", "數量", "百分比"]
        category_table.align = "l"
        
        total_incidents = incident_statistics.get('total_incidents', 1)
        sorted_categories = sorted(incident_statistics['by_enhanced_category'].items(), key=lambda x: x[1], reverse=True)
        
        for category, count in sorted_categories:
            percentage = round((count / total_incidents) * 100, 1)
            category_table.add_row([
                category.replace('_', ' '),
                count,
                f"{percentage}%"
            ])
        
        print(f"\n[LIST] 增強事件類型統計:")
        print(category_table)
    
    # 原始 FastF1 分類統計表格
    if incident_statistics.get('by_original_category'):
        original_table = PrettyTable()
        original_table.field_names = ["原始類型", "數量", "百分比"]
        original_table.align = "l"
        
        total_incidents = incident_statistics.get('total_incidents', 1)
        sorted_original = sorted(incident_statistics['by_original_category'].items(), key=lambda x: x[1], reverse=True)
        
        for category, count in sorted_original:
            percentage = round((count / total_incidents) * 100, 1)
            original_table.add_row([
                str(category),
                count,
                f"{percentage}%"
            ])
        
        print(f"\n[LIST] FastF1 原始類型統計:")
        print(original_table)
    
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
                incident.get('enhanced_category', 'OTHER').replace('_', ' ')[:12],
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
            enhanced_cats = peak.get('enhanced_categories', [])
            original_cats = peak.get('original_categories', [])
            if enhanced_cats:
                categories_str = ', '.join(enhanced_cats[:3]) + ('...' if len(enhanced_cats) > 3 else '')
            else:
                categories_str = ', '.join(original_cats[:3]) + ('...' if len(original_cats) > 3 else '')
            print(f"   圈數 {peak['lap']}: {peak['incident_count']} 個事件 - {categories_str}")


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
                "enhanced_categories": [
                    "VIRTUAL_SAFETY_CAR", "SAFETY_CAR", "DOUBLE_YELLOW_FLAG", "YELLOW_FLAG", 
                    "BLUE_FLAG", "RED_FLAG", "GREEN_FLAG", "CHEQUERED_FLAG", "FLAG_CLEAR",
                    "DRS_ENABLED", "DRS_DISABLED", "DRS_EVENT", "TIME_PENALTY", "GRID_PENALTY", 
                    "DISQUALIFICATION", "WARNING", "PENALTY", "TRACK_LIMITS", "TIME_DELETED", 
                    "TRACK_CONDITIONS", "INVESTIGATION", "NO_ACTION", "INCIDENT", "UNSAFE_RELEASE", 
                    "INCIDENT_NOTED", "PIT_EXIT_OPEN", "PIT_EXIT_CLOSED", "PIT_EVENT", 
                    "WEATHER_FORECAST", "WEATHER", "ABORTED_START", "FORMATION_LAP", "RACE_START", 
                    "RACE_END", "RECOVERY_VEHICLE", "LAPPED_CAR_OVERTAKE", "OTHER"
                ],
                "original_fastf1_categories": ["Flag", "Other", "SafetyCar", "Drs"],
                "data_completeness": {
                    "preserves_all_race_control_messages": True,
                    "includes_original_fastf1_fields": True,
                    "enhanced_categorization": True,
                    "detailed_flag_analysis": True
                },
                "version": "2.0_enhanced"
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
