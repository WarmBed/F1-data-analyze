#!/usr/bin/env python3
"""
F1 歷年旗幟統計分析模組 - Function 100
Historical Flags Analysis Module - Following Core Development Standards

掃描 2020-2025 年的賽事數據，統計特定賽道的：
1. 每年的 Yellow Flag、Double Yellow Flag、Red Flag、Safety Car 數量
2. 每個彎道在各年份的旗幟事件統計
3. 詳細的事件訊息（車手、車號、原因）
"""

import os
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

import fastf1
import pandas as pd
import numpy as np

# 全域設定
JSON_OUTPUT_DIR = os.getenv("F1_ANALYSIS_JSON_DIR", "json")
CACHE_DIR = "f1_analysis_cache"


def extract_driver_info_from_message(message: str) -> List[Dict[str, str]]:
    """
    從賽事控制訊息中提取車手資訊
    
    參考 all_incidents_summary.py 的 extract_driver_info 函數
    
    Args:
        message: 賽事控制訊息文字
        
    Returns:
        車手資訊列表，格式: [{'car_number': '1', 'driver_code': 'VER'}, ...]
    """
    # 提取車號和車手代碼
    # 模式：數字 + 空格 + (三個大寫字母)
    # 例如: "77 (BOT)", "2 (SAR)"
    car_pattern = r'(\d+)\s*\(([A-Z]{3})\)'
    matches = re.findall(car_pattern, message.upper())
    
    if matches:
        # 過濾掉可能是彎道號碼的匹配（例如 "TURN 11"）
        # 車號通常是 1-99，彎道號碼通常緊跟在 "TURN" 後面
        drivers = []
        for car_num, driver_code in matches:
            # 檢查這個數字前面是否是 "TURN"
            turn_pattern = rf'TURN\s+{car_num}\s*\('
            if not re.search(turn_pattern, message.upper()):
                drivers.append({'car_number': car_num, 'driver_code': driver_code})
        
        if drivers:
            return drivers
    
    # 僅提取車號（沒有車手代碼）- 必須有 "CAR" 關鍵字
    car_number_pattern = r'CARS?\s+(\d+)'
    car_numbers = re.findall(car_number_pattern, message.upper())
    
    if car_numbers:
        return [{'car_number': num, 'driver_code': 'UNK'} for num in car_numbers]
    
    return []


def extract_incident_reason(message: str) -> str:
    """
    從賽事控制訊息中提取事故原因
    
    Args:
        message: 賽事控制訊息文字
        
    Returns:
        事故原因的簡短描述
    """
    message_upper = message.upper()
    
    # 事故類型關鍵字
    if 'ACCIDENT' in message_upper or 'CRASH' in message_upper:
        return 'Accident'
    elif 'COLLISION' in message_upper:
        return 'Collision'
    elif 'SPIN' in message_upper:
        return 'Spin'
    elif 'OFF TRACK' in message_upper or 'OFF THE TRACK' in message_upper:
        return 'Off Track'
    elif 'DEBRIS' in message_upper:
        return 'Debris'
    elif 'STOPPED' in message_upper or 'RETIRING' in message_upper:
        return 'Stopped/Retired'
    elif 'TRACK LIMIT' in message_upper:
        return 'Track Limits'
    elif 'CONTACT' in message_upper:
        return 'Contact'
    elif 'RECOVERY' in message_upper:
        return 'Recovery Vehicle'
    elif 'SAFETY CAR' in message_upper and 'DEPLOYED' in message_upper:
        return 'Safety Car Deployed'
    else:
        return 'Other'


def _ensure_json_dir() -> Path:
    """確保 JSON 輸出目錄存在"""
    path = Path(JSON_OUTPUT_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _sanitize_token(value: Any, *, default: str = "Unknown", upper: bool = False) -> str:
    """標準化文字為檔名安全格式"""
    text = str(value).strip() if value is not None else ""
    if not text:
        text = default

    normalized = []
    for char in text:
        if char.isalnum() or char in {"_", "-"}:
            normalized.append(char)
        elif char.isspace():
            normalized.append("_")
        else:
            normalized.append("_")

    sanitized = "".join(normalized)
    while "__" in sanitized:
        sanitized = sanitized.replace("__", "_")
    sanitized = sanitized.strip("_") or default

    if upper:
        sanitized = sanitized.upper()

    return sanitized


def calculate_speed_distribution(position_data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    計算賽道速度分類統計
    
    分類標準：
    - 低速區: <120 km/h（慢速彎、髮夾彎）
    - 中速區: 120-200 km/h（中速彎、過渡區）
    - 高速區: >200 km/h（直線、高速彎）
    
    Args:
        position_data: 賽道位置數據列表，每個元素包含 speed 欄位
        
    Returns:
        速度分類統計字典，包含：
        - low_speed_count: 低速點數量
        - mid_speed_count: 中速點數量
        - high_speed_count: 高速點數量
        - low_speed_percentage: 低速區佔比
        - mid_speed_percentage: 中速區佔比
        - high_speed_percentage: 高速區佔比
        - average_speed: 平均速度
        - min_speed: 最低速度
        - max_speed: 最高速度
        - total_points: 總數據點數
    """
    if not position_data:
        return None
    
    # 提取所有速度數據
    speeds = []
    for record in position_data:
        speed = record.get('speed')
        if speed is not None and speed > 0:
            speeds.append(float(speed))
    
    if not speeds:
        return None
    
    # 分類統計（修改為 <120, 120-200, >200）
    low_speed_count = sum(1 for s in speeds if s < 120)
    mid_speed_count = sum(1 for s in speeds if 120 <= s <= 200)
    high_speed_count = sum(1 for s in speeds if s > 200)
    
    total = len(speeds)
    
    return {
        "low_speed_count": low_speed_count,
        "mid_speed_count": mid_speed_count,
        "high_speed_count": high_speed_count,
        "low_speed_percentage": (low_speed_count / total) * 100,
        "mid_speed_percentage": (mid_speed_count / total) * 100,
        "high_speed_percentage": (high_speed_count / total) * 100,
        "average_speed": sum(speeds) / total,
        "min_speed": min(speeds),
        "max_speed": max(speeds),
        "total_points": total,
        "classification": {
            "low_speed": {"threshold": "<120 km/h", "description": "Slow corners, hairpins"},
            "mid_speed": {"threshold": "120-200 km/h", "description": "Medium-speed corners, transitions"},
            "high_speed": {"threshold": ">200 km/h", "description": "Straights, high-speed corners"}
        }
    }


def extract_flag_events_from_session(session, year: int) -> Dict[str, Any]:
    """
    從單一會話中提取旗幟事件並關聯事故訊息
    
    改進策略：
    1. 先提取所有旗幟事件（黃旗、雙黃旗、安全車）
    2. 提取所有事故訊息（CarEvent、其他類別）
    3. 根據時間和位置關聯旗幟與事故訊息，補充車手資訊
    
    Args:
        session: FastF1 session 物件
        year: 年份
        
    Returns:
        字典包含旗幟事件列表和統計資料
    """
    from datetime import timedelta
    
    events = {
        'yellow_flags': [],
        'double_yellow_flags': [],
        'red_flags': [],
        'safety_cars': [],
        'statistics': {
            'yellow_count': 0,
            'double_yellow_count': 0,
            'red_count': 0,
            'safety_car_count': 0,
            'total_flags': 0
        }
    }
    
    try:
        if not hasattr(session, 'race_control_messages'):
            print(f"[WARNING] {year} 會話沒有 race_control_messages 屬性")
            return events
        
        race_control = session.race_control_messages
        
        if race_control is None or race_control.empty:
            print(f"[WARNING] {year} race_control_messages 為空")
            return events
        
        # 過濾最後一圈的 CHEQUERED FLAG（參考功能 6）
        max_lap = race_control['Lap'].max() if 'Lap' in race_control.columns else 0
        
        # 第一步：收集所有事故訊息（CarEvent 和包含車手資訊的訊息）
        incident_messages = []
        for idx, row in race_control.iterrows():
            msg_text = str(row.get('Message', ''))
            msg_upper = msg_text.upper()
            
            # 檢查是否包含事故相關資訊
            is_incident = (
                'CAR ' in msg_upper or 
                'SPUN' in msg_upper or 
                'ACCIDENT' in msg_upper or 
                'COLLISION' in msg_upper or 
                'STOPPED' in msg_upper or 
                'INVOLVING' in msg_upper or
                row.get('Category') == 'CarEvent'
            )
            
            if is_incident:
                incident_messages.append({
                    'index': idx,
                    'time': row.get('Time'),
                    'lap': row.get('Lap', 0),
                    'message': msg_text,
                    'sector': row.get('Sector'),
                    'category': row.get('Category'),
                    'track_location': extract_track_location(msg_text)
                })
        
        # 第二步：處理旗幟事件，並關聯事故訊息
        for idx, row in race_control.iterrows():
            msg_text = str(row.get('Message', '')).upper()
            lap = row.get('Lap', 0)
            time = row.get('Time', None)
            sector = row.get('Sector', None)
            
            # 跳過正常比賽結束標誌
            if 'CHEQUERED FLAG' in msg_text and lap == max_lap:
                continue
            
            # 識別旗幟類型
            event_data = {
                'lap': int(lap) if pd.notna(lap) else 0,
                'time': str(time) if pd.notna(time) else 'Unknown',
                'message': row.get('Message', ''),
                'sector': int(sector) if pd.notna(sector) else None,
                'track_location': extract_track_location(row.get('Message', '')),
                'corner': None,
                'related_incidents': []  # ✅ 新增：相關事故訊息
            }
            
            # ✅ 查找相近時間和位置的事故訊息（前後 1 分鐘）
            if time and hasattr(time, 'timestamp'):
                time_window = timedelta(minutes=1)
                for incident in incident_messages:
                    incident_time = incident['time']
                    if incident_time and hasattr(incident_time, 'timestamp'):
                        time_diff = abs(time - incident_time)
                        if time_diff <= time_window:
                            # 檢查扇區是否匹配（如果都有扇區資訊）
                            sector_match = (
                                sector is None or 
                                incident['sector'] is None or 
                                sector == incident['sector']
                            )
                            if sector_match:
                                event_data['related_incidents'].append({
                                    'message': incident['message'],
                                    'lap': incident['lap'],
                                    'time_offset_seconds': time_diff.total_seconds()
                                })
            
            # Yellow Flag 檢測
            if 'DOUBLE YELLOW' in msg_text:
                events['double_yellow_flags'].append(event_data)
                events['statistics']['double_yellow_count'] += 1
                events['statistics']['total_flags'] += 1
            elif 'YELLOW FLAG' in msg_text or 'YELLOW' in msg_text:
                if 'DOUBLE' not in msg_text:
                    events['yellow_flags'].append(event_data)
                    events['statistics']['yellow_count'] += 1
                    events['statistics']['total_flags'] += 1
            
            # Red Flag 檢測
            if 'RED FLAG' in msg_text:
                events['red_flags'].append(event_data)
                events['statistics']['red_count'] += 1
                events['statistics']['total_flags'] += 1
            
            # Safety Car 檢測
            if 'SAFETY CAR' in msg_text and 'DEPLOYED' in msg_text:
                sc_trigger_turn = extract_safety_car_trigger_turn(race_control, idx)
                if sc_trigger_turn:
                    event_data['corner'] = sc_trigger_turn
                    event_data['track_location'] = {
                        'type': 'TURN',
                        'number': sc_trigger_turn,
                        'description': f'Turn {sc_trigger_turn} (SC trigger)'
                    }
                
                events['safety_cars'].append(event_data)
                events['statistics']['safety_car_count'] += 1
        
        print(f"[INFO] {year} 事件統計: Yellow={events['statistics']['yellow_count']}, "
              f"Double Yellow={events['statistics']['double_yellow_count']}, "
              f"Red={events['statistics']['red_count']}, "
              f"Safety Car={events['statistics']['safety_car_count']}")
        print(f"[INFO] {year} 找到 {len(incident_messages)} 條事故相關訊息")
        
        return events
        
    except Exception as e:
        print(f"[ERROR] 提取 {year} 旗幟事件失敗: {e}")
        import traceback
        traceback.print_exc()
        return events


def extract_track_location(message: str) -> Optional[Dict[str, Any]]:
    """
    提取賽道位置資訊（TURN, CORNER）
    
    參考 all_incidents_summary.py 的 extract_track_location 函數
    
    Args:
        message: 事件訊息文字
        
    Returns:
        dict: {
            "type": "TURN" or "CORNER",
            "number": int,
            "description": str
        } or None if no location found
    """
    message_upper = message.upper()
    
    # 優先匹配 TURN
    turn_match = re.search(r'TURN\s+(\d+)', message_upper)
    if turn_match:
        turn_number = int(turn_match.group(1))
        return {
            "type": "TURN",
            "number": turn_number,
            "description": f"Turn {turn_number}"
        }
    
    # 次優先匹配 CORNER
    corner_match = re.search(r'CORNER\s+(\d+)', message_upper)
    if corner_match:
        corner_number = int(corner_match.group(1))
        return {
            "type": "CORNER",
            "number": corner_number,
            "description": f"Corner {corner_number}"
        }
    
    # 沒有找到賽道位置資訊
    return None


def extract_safety_car_trigger_turn(race_control: pd.DataFrame, sc_index: int) -> Optional[int]:
    """
    提取安全車觸發原因中的 TURN 資訊
    
    分析安全車部署前 3 分鐘內的事故訊息，找出包含 "AT TURN X" 的資訊
    
    Args:
        race_control: 完整的賽事控制訊息 DataFrame
        sc_index: 安全車訊息的索引
        
    Returns:
        TURN 號碼 (int) 或 None
    """
    try:
        from datetime import timedelta
        
        sc_row = race_control.iloc[sc_index]
        sc_time = sc_row.get('Time', None)
        
        if sc_time is None or not hasattr(sc_time, 'timestamp'):
            return None
        
        # 查找前 3 分鐘的訊息
        time_window = timedelta(minutes=3)
        start_time = sc_time - time_window
        
        # 過濾時間範圍內的訊息
        messages_before = race_control[
            (race_control['Time'] >= start_time) & 
            (race_control['Time'] < sc_time)
        ]
        
        # 反向掃描（最近的事件優先）
        for idx in reversed(messages_before.index):
            msg = str(race_control.loc[idx, 'Message']).upper()
            
            # 檢查是否包含 "AT TURN X" 或 "TURN X INCIDENT"
            turn_match = re.search(r'(?:AT\s+)?TURN\s+(\d+)', msg)
            if turn_match:
                turn_num = int(turn_match.group(1))
                print(f"[INFO] 安全車觸發於 Turn {turn_num}: {race_control.loc[idx, 'Message']}")
                return turn_num
            
            # 也檢查 "STOPPED AT TURN X"
            stopped_match = re.search(r'STOPPED\s+AT\s+TURN\s+(\d+)', msg)
            if stopped_match:
                turn_num = int(stopped_match.group(1))
                print(f"[INFO] 安全車觸發於 Turn {turn_num} (car stopped): {race_control.loc[idx, 'Message']}")
                return turn_num
        
        return None
        
    except Exception as e:
        print(f"[WARNING] 提取安全車觸發 TURN 失敗: {e}")
        return None


def map_event_to_corner(event: Dict[str, Any], corners_data: List[Dict]) -> Optional[int]:
    """
    將事件映射到彎道號碼
    
    參考 all_incidents_summary.py 的彎道提取邏輯
    
    優先級：
    1. 從 message 文本提取彎道號碼 (使用 extract_track_location)
    2. 基於 Sector 推斷彎道範圍
    3. 返回 None (unknown)
    
    Args:
        event: 事件字典
        corners_data: 彎道資料列表
        
    Returns:
        彎道號碼或 None
    """
    message = event.get('message', '')
    sector = event.get('sector')
    
    # 方法 1: 從 message 提取彎道號碼（使用標準函數）
    track_location = extract_track_location(message)
    if track_location:
        corner_num = track_location['number']
        # 如果沒有彎道數據，直接返回提取的號碼
        if not corners_data:
            return corner_num
        # 驗證彎道號碼是否有效
        if 1 <= corner_num <= len(corners_data):
            return corner_num
    
    # 方法 2: 基於 Sector 推斷（參考 generate_yellow_flag_statistics.py）
    if sector is not None and corners_data:
        total_corners = len(corners_data)
        corners_per_sector = total_corners // 3
        
        if sector == 1:
            # Sector 1: 前 1/3 彎道
            return list(range(1, corners_per_sector + 1))
        elif sector == 2:
            # Sector 2: 中 1/3 彎道
            return list(range(corners_per_sector + 1, 2 * corners_per_sector + 1))
        elif sector == 3:
            # Sector 3: 後 1/3 彎道
            return list(range(2 * corners_per_sector + 1, total_corners + 1))
    
    # 方法 3: 無法確定
    return None


def get_circuit_corners(session, circuit_name: str = None) -> List[Dict[str, Any]]:
    """
    獲取賽道彎道資訊
    
    參考 generate_yellow_flag_statistics.py 的彎道提取邏輯
    如果 FastF1 沒有提供，使用已知賽道的默認彎道數
    
    Args:
        session: FastF1 session 物件
        circuit_name: 賽道名稱（用於查找默認值）
        
    Returns:
        彎道資料列表
    """
    corners = []
    
    try:
        # ✅ 修正：使用 get_circuit_info() 方法（參考 track_position_analysis.py）
        circuit_info = session.get_circuit_info()
        
        if circuit_info is not None and hasattr(circuit_info, 'corners'):
            circuit_corners = circuit_info.corners
            
            if circuit_corners is not None and not circuit_corners.empty:
                for idx, corner in circuit_corners.iterrows():
                    corners.append({
                        'number': int(corner.get('Number', idx + 1)),
                        'letter': corner.get('Letter', ''),
                        'distance': float(corner.get('Distance', 0)),
                        'x': float(corner.get('X', 0)),
                        'y': float(corner.get('Y', 0)),
                        'angle': float(corner.get('Angle', 0)) if pd.notna(corner.get('Angle')) else 0
                    })
        
        # 如果沒有從 FastF1 獲取到彎道資訊，使用已知賽道的默認彎道數
        if not corners and circuit_name:
            # 已知賽道的彎道數量
            known_circuits = {
                'Suzuka': 18,
                'Monaco': 19,
                'Singapore': 23,
                'Baku': 20,
                'Spa': 19,
                'Silverstone': 18,
                'Monza': 11,
                'Interlagos': 15,
                'São Paulo': 15,  # ✅ 新增：2025 年起巴西大獎賽改名
                'Sao Paulo': 15,  # ✅ 新增：無重音版本
                'COTA': 20,  # Circuit of the Americas
                'Hungaroring': 14,
                'Red Bull Ring': 10,
                'Zandvoort': 14,
                'Melbourne': 16,
                'Bahrain': 15,
                'Jeddah': 27,
                'Shanghai': 16,
                'Imola': 19,
                'Miami': 19,
                'Barcelona': 16,
                'Las Vegas': 17,  # ✅ 新增：Las Vegas 彎道數
            }
            
            # 查找匹配的賽道（不區分大小寫，部分匹配）
            circuit_upper = circuit_name.upper()
            corner_count = None
            
            for known_name, count in known_circuits.items():
                if known_name.upper() in circuit_upper or circuit_upper in known_name.upper():
                    corner_count = count
                    print(f"[INFO] 使用已知賽道 {known_name} 的彎道數: {count}")
                    break
            
            # 如果找到默認彎道數，創建簡單的彎道列表
            if corner_count:
                for i in range(1, corner_count + 1):
                    corners.append({
                        'number': i,
                        'letter': '',
                        'distance': 0,
                        'x': 0,
                        'y': 0,
                        'angle': 0
                    })
        
        if corners:
            print(f"[INFO] 載入了 {len(corners)} 個彎道資訊")
        else:
            print(f"[WARNING] 無法獲取彎道資訊，彎道級別分析將基於 TURN/CORNER 關鍵字")
        
        return corners
        
    except Exception as e:
        print(f"[ERROR] 獲取彎道資訊失敗: {e}")
        return []


def aggregate_corner_statistics(all_events: Dict[int, Dict], corners_data: List[Dict]) -> Dict[str, Any]:
    """
    彙總每個彎道的歷年旗幟統計
    
    Args:
        all_events: {year: events_dict} 格式的所有年份事件
        corners_data: 彎道資料列表
        
    Returns:
        彎道統計字典
    """
    corner_stats = {}
    
    # 初始化每個彎道的統計
    for corner in corners_data:
        corner_num = corner['number']
        corner_key = f"T{corner_num}"
        
        corner_stats[corner_key] = {
            'corner_number': corner_num,
            'corner_letter': corner.get('letter', ''),
            'total_flags': 0,
            'yearly_breakdown': {},
            'detailed_events': []  # ✅ 新增：儲存詳細事件訊息
        }
    
    # 彙總每年的事件到彎道
    for year, events in all_events.items():
        year_str = str(year)
        
        # 處理黃旗和雙黃旗事件
        all_flag_events = (
            events.get('yellow_flags', []) +
            events.get('double_yellow_flags', [])
        )
        
        for event in all_flag_events:
            corner_result = map_event_to_corner(event, corners_data)
            
            if corner_result is None:
                # 無法確定彎道
                continue
            elif isinstance(corner_result, list):
                # Sector 範圍：分配給多個彎道
                weight = 1.0 / len(corner_result)
                for corner_num in corner_result:
                    corner_key = f"T{corner_num}"
                    if corner_key in corner_stats:
                        if year_str not in corner_stats[corner_key]['yearly_breakdown']:
                            corner_stats[corner_key]['yearly_breakdown'][year_str] = {
                                'yellow': 0.0,
                                'double_yellow': 0.0,
                                'safety_car': 0.0,
                                'messages': []  # ✅ 新增：儲存該年份的詳細訊息
                            }
                        
                        # 判斷旗幟類型
                        flag_type = None
                        if event in events.get('yellow_flags', []):
                            corner_stats[corner_key]['yearly_breakdown'][year_str]['yellow'] += weight
                            flag_type = 'yellow'
                        elif event in events.get('double_yellow_flags', []):
                            corner_stats[corner_key]['yearly_breakdown'][year_str]['double_yellow'] += weight
                            flag_type = 'double_yellow'
                        
                        # ✅ 新增：保存詳細事件訊息
                        message_text = event.get('message', '')
                        drivers = extract_driver_info_from_message(message_text)
                        reason = extract_incident_reason(message_text)
                        
                        # ✅ 如果黃旗訊息本身沒有車手資訊，從相關事故訊息中提取
                        related_incidents = event.get('related_incidents', [])
                        if not drivers and related_incidents:
                            for incident in related_incidents:
                                incident_drivers = extract_driver_info_from_message(incident['message'])
                                if incident_drivers:
                                    drivers.extend(incident_drivers)
                                    # 同時更新原因
                                    if reason == 'Other':
                                        reason = extract_incident_reason(incident['message'])
                            # 去重
                            if drivers:
                                seen = set()
                                drivers = [d for d in drivers if not (d['car_number'] in seen or seen.add(d['car_number']))]
                        
                        corner_stats[corner_key]['yearly_breakdown'][year_str]['messages'].append({
                            'year': year,
                            'lap': event.get('lap', 0),
                            'time': event.get('time', 'Unknown'),
                            'message': message_text,
                            'sector': event.get('sector'),
                            'flag_type': flag_type,
                            'weight': weight,  # Sector 範圍分配權重
                            'drivers': drivers,  # ✅ 車手資訊（從黃旗或相關事故中提取）
                            'reason': reason,  # ✅ 事故原因
                            'related_incidents': [inc['message'] for inc in related_incidents] if related_incidents else []  # ✅ 相關事故訊息
                        })
                        
                        corner_stats[corner_key]['total_flags'] += weight
            else:
                # 精確彎道號碼
                corner_key = f"T{corner_result}"
                if corner_key in corner_stats:
                    if year_str not in corner_stats[corner_key]['yearly_breakdown']:
                        corner_stats[corner_key]['yearly_breakdown'][year_str] = {
                            'yellow': 0,
                            'double_yellow': 0,
                            'safety_car': 0,
                            'messages': []  # ✅ 新增：儲存該年份的詳細訊息
                        }
                    
                    # 判斷旗幟類型
                    flag_type = None
                    if event in events.get('yellow_flags', []):
                        corner_stats[corner_key]['yearly_breakdown'][year_str]['yellow'] += 1
                        flag_type = 'yellow'
                    elif event in events.get('double_yellow_flags', []):
                        corner_stats[corner_key]['yearly_breakdown'][year_str]['double_yellow'] += 1
                        flag_type = 'double_yellow'
                    
                    # ✅ 新增：保存詳細事件訊息
                    message_text = event.get('message', '')
                    drivers = extract_driver_info_from_message(message_text)
                    reason = extract_incident_reason(message_text)
                    
                    # ✅ 如果黃旗訊息本身沒有車手資訊，從相關事故訊息中提取
                    related_incidents = event.get('related_incidents', [])
                    if not drivers and related_incidents:
                        for incident in related_incidents:
                            incident_drivers = extract_driver_info_from_message(incident['message'])
                            if incident_drivers:
                                drivers.extend(incident_drivers)
                                # 同時更新原因
                                if reason == 'Other':
                                    reason = extract_incident_reason(incident['message'])
                        # 去重
                        if drivers:
                            seen = set()
                            drivers = [d for d in drivers if not (d['car_number'] in seen or seen.add(d['car_number']))]
                    
                    corner_stats[corner_key]['yearly_breakdown'][year_str]['messages'].append({
                        'year': year,
                        'lap': event.get('lap', 0),
                        'time': event.get('time', 'Unknown'),
                        'message': message_text,
                        'sector': event.get('sector'),
                        'flag_type': flag_type,
                        'weight': 1.0,  # 精確彎道分配權重
                        'drivers': drivers,  # ✅ 車手資訊（從黃旗或相關事故中提取）
                        'reason': reason,  # ✅ 事故原因
                        'related_incidents': [inc['message'] for inc in related_incidents] if related_incidents else []  # ✅ 相關事故訊息
                    })
                    
                    corner_stats[corner_key]['total_flags'] += 1
        
        # 處理安全車事件（獨立處理，因為有 TURN 資訊）
        for sc_event in events.get('safety_cars', []):
            # 檢查是否有彎道資訊
            if sc_event.get('corner') is not None:
                corner_num = sc_event['corner']
                corner_key = f"T{corner_num}"
                
                if corner_key in corner_stats:
                    if year_str not in corner_stats[corner_key]['yearly_breakdown']:
                        corner_stats[corner_key]['yearly_breakdown'][year_str] = {
                            'yellow': 0,
                            'double_yellow': 0,
                            'safety_car': 0,
                            'messages': []  # ✅ 新增：儲存該年份的詳細訊息
                        }
                    
                    corner_stats[corner_key]['yearly_breakdown'][year_str]['safety_car'] += 1
                    
                    # ✅ 新增：保存安全車詳細事件訊息
                    message_text = sc_event.get('message', '')
                    drivers = extract_driver_info_from_message(message_text)
                    reason = extract_incident_reason(message_text)
                    
                    # ✅ 如果安全車訊息本身沒有車手資訊，從相關事故訊息中提取
                    related_incidents = sc_event.get('related_incidents', [])
                    if not drivers and related_incidents:
                        for incident in related_incidents:
                            incident_drivers = extract_driver_info_from_message(incident['message'])
                            if incident_drivers:
                                drivers.extend(incident_drivers)
                                # 同時更新原因
                                if reason == 'Other':
                                    reason = extract_incident_reason(incident['message'])
                        # 去重
                        if drivers:
                            seen = set()
                            drivers = [d for d in drivers if not (d['car_number'] in seen or seen.add(d['car_number']))]
                    
                    corner_stats[corner_key]['yearly_breakdown'][year_str]['messages'].append({
                        'year': year,
                        'lap': sc_event.get('lap', 0),
                        'time': sc_event.get('time', 'Unknown'),
                        'message': message_text,
                        'sector': sc_event.get('sector'),
                        'flag_type': 'safety_car',
                        'weight': 1.0,
                        'drivers': drivers,  # ✅ 車手資訊（從安全車或相關事故中提取）
                        'reason': reason,  # ✅ 事故原因
                        'related_incidents': [inc['message'] for inc in related_incidents] if related_incidents else []  # ✅ 相關事故訊息
                    })
                    
                    corner_stats[corner_key]['total_flags'] += 1
    
    return corner_stats


def extract_track_position_with_speed(session) -> Dict[str, Any]:
    """
    從會話中提取賽道位置和速度數據
    
    參考 demo_fastf1_z_elevation.py 和 track_position_analysis.py
    
    Args:
        session: FastF1 會話物件
        
    Returns:
        包含 position_records 的字典
    """
    try:
        print(f"   [INFO] 提取賽道位置和速度數據...")
        
        # 獲取所有圈速
        laps = session.laps
        if laps.empty:
            print(f"   [WARNING] 無圈速數據")
            return {"position_records": [], "track_bounds": None}
        
        # 選擇最快圈
        fastest_lap = laps.pick_fastest()
        if fastest_lap is None:
            print(f"   [WARNING] 無最快圈數據")
            return {"position_records": [], "track_bounds": None, "sector_boundaries": []}
        
        # 獲取遙測數據（包含 Distance, Speed 等）
        telemetry = fastest_lap.get_telemetry()
        
        if telemetry.empty:
            print(f"   [WARNING] 無遙測數據")
            return {"position_records": [], "track_bounds": None, "sector_boundaries": []}
        
        # 檢查必要欄位
        required_cols = ['Distance', 'X', 'Y']
        missing_cols = [col for col in required_cols if col not in telemetry.columns]
        if missing_cols:
            print(f"   [WARNING] 遙測數據缺少欄位: {missing_cols}")
            return {"position_records": [], "track_bounds": None, "sector_boundaries": []}
        
        # 提取數據
        distances = telemetry['Distance'].values
        x = telemetry['X'].values
        y = telemetry['Y'].values
        
        # ✅ 新增：提取 Z 軸高程數據（參考 demo_fastf1_z_elevation.py）
        z = telemetry['Z'].values if 'Z' in telemetry.columns else None
        
        # 提取速度和其他遙測數據（如果可用）
        speeds = telemetry['Speed'].values if 'Speed' in telemetry.columns else None
        throttle = telemetry['Throttle'].values if 'Throttle' in telemetry.columns else None
        brake = telemetry['Brake'].values if 'Brake' in telemetry.columns else None
        rpm = telemetry['RPM'].values if 'RPM' in telemetry.columns else None
        
        # ✅ 使用完整遙測數據（不再限制採樣數量）
        total_points = len(distances)
        
        print(f"   [INFO] 遙測數據: {total_points} 點（使用完整數據）")
        print(f"   [INFO] 距離範圍: {distances[0]:.1f}m ~ {distances[-1]:.1f}m")
        if speeds is not None:
            print(f"   [INFO] 速度範圍: {np.min(speeds):.1f} ~ {np.max(speeds):.1f} km/h")
        
        # ✅ 新增：顯示高程數據統計
        if z is not None:
            z_clean = z[~np.isnan(z)]
            if len(z_clean) > 0:
                # FastF1 Z 軸需除以 10 轉換為公尺
                min_elevation = float(np.min(z_clean) / 10.0)
                max_elevation = float(np.max(z_clean) / 10.0)
                elevation_change = float((np.max(z_clean) - np.min(z_clean)) / 10.0)
                print(f"   [INFO] 高程範圍: {min_elevation:.1f}m ~ {max_elevation:.1f}m (變化 {elevation_change:.1f}m)")
            else:
                print(f"   [WARNING] Z 軸數據全為 NaN")
        else:
            print(f"   [WARNING] 無 Z 軸高程數據")
        
        # 建立 position records（使用全部數據點）
        position_records = []
        for i in range(total_points):
            record = {
                "point_index": int(i + 1),
                "distance_m": float(distances[i]),
                "position_x": float(x[i]),
                "position_y": float(y[i])
            }
            
            # ✅ 新增：添加 Z 軸高程數據（FastF1 原始值）
            if z is not None and not np.isnan(z[i]):
                record["elevation"] = float(z[i])  # 原始值（GUI 會除以 10）
                record["z"] = float(z[i])          # 同時提供 z 欄位（兼容性）
            
            # 添加速度數據（如果可用）
            if speeds is not None:
                record["speed"] = float(speeds[i])
            if throttle is not None:
                record["throttle"] = float(throttle[i])
            if brake is not None:
                record["brake"] = float(brake[i])
            if rpm is not None:
                record["rpm"] = float(rpm[i])
            
            position_records.append(record)
        
        # 計算賽道邊界（確保沒有 None 或 NaN 值）
        x_clean = x[~np.isnan(x)]
        y_clean = y[~np.isnan(y)]
        
        if len(x_clean) == 0 or len(y_clean) == 0:
            print(f"   [WARNING] 位置數據全為 NaN，無法計算邊界")
            track_bounds = None
        else:
            track_bounds = {
                "x_min": float(np.min(x_clean)),
                "x_max": float(np.max(x_clean)),
                "y_min": float(np.min(y_clean)),
                "y_max": float(np.max(y_clean))
            }
        
        print(f"   [SUCCESS] 提取了 {len(position_records)} 個位置點（含速度數據）")
        
        # ✅ 新增：提取 Sector 邊界位置
        sector_boundaries = []
        try:
            # 獲取 Sector 時間數據
            sector1_time = fastest_lap.get('Sector1Time')
            sector2_time = fastest_lap.get('Sector2Time')
            sector3_time = fastest_lap.get('Sector3Time')
            
            # 檢查 Sector 數據是否可用
            if pd.notna(sector1_time) and pd.notna(sector2_time) and pd.notna(sector3_time):
                # 確保遙測數據有 Time 欄位
                if 'Time' in telemetry.columns:
                    # 獲取圈開始時間
                    lap_start_time = telemetry['Time'].iloc[0]
                    
                    # 計算 Sector 邊界的絕對時間
                    s1_end_time = lap_start_time + sector1_time
                    s2_end_time = lap_start_time + sector1_time + sector2_time
                    
                    # 找到最接近 Sector 邊界時間的遙測點
                    s1_idx = (telemetry['Time'] - s1_end_time).abs().idxmin()
                    s2_idx = (telemetry['Time'] - s2_end_time).abs().idxmin()
                    
                    # 提取 Sector 1 邊界位置
                    s1_distance = float(telemetry.loc[s1_idx, 'Distance'])
                    s1_x = float(telemetry.loc[s1_idx, 'X'])
                    s1_y = float(telemetry.loc[s1_idx, 'Y'])
                    s1_z = float(telemetry.loc[s1_idx, 'Z']) if 'Z' in telemetry.columns and not np.isnan(telemetry.loc[s1_idx, 'Z']) else None
                    
                    sector_boundaries.append({
                        "sector": 1,
                        "name": "S1 End",
                        "distance_m": s1_distance,
                        "position_x": s1_x,
                        "position_y": s1_y,
                        "elevation": s1_z,
                        "sector_time": float(sector1_time.total_seconds())
                    })
                    
                    # 提取 Sector 2 邊界位置
                    s2_distance = float(telemetry.loc[s2_idx, 'Distance'])
                    s2_x = float(telemetry.loc[s2_idx, 'X'])
                    s2_y = float(telemetry.loc[s2_idx, 'Y'])
                    s2_z = float(telemetry.loc[s2_idx, 'Z']) if 'Z' in telemetry.columns and not np.isnan(telemetry.loc[s2_idx, 'Z']) else None
                    
                    sector_boundaries.append({
                        "sector": 2,
                        "name": "S2 End",
                        "distance_m": s2_distance,
                        "position_x": s2_x,
                        "position_y": s2_y,
                        "elevation": s2_z,
                        "sector_time": float(sector2_time.total_seconds())
                    })
                    
                    # Sector 3 的結束就是終點線（起點）
                    s3_distance = 0.0  # 終點線距離為 0
                    s3_x = float(x[0])
                    s3_y = float(y[0])
                    s3_z = float(z[0]) if z is not None and not np.isnan(z[0]) else None
                    
                    sector_boundaries.append({
                        "sector": 3,
                        "name": "S3 End (Finish Line)",
                        "distance_m": s3_distance,
                        "position_x": s3_x,
                        "position_y": s3_y,
                        "elevation": s3_z,
                        "sector_time": float(sector3_time.total_seconds())
                    })
                    
                    print(f"   [SUCCESS] 提取了 {len(sector_boundaries)} 個 Sector 邊界")
                    print(f"   [INFO] S1 結束: {s1_distance:.1f}m")
                    print(f"   [INFO] S2 結束: {s2_distance:.1f}m")
                    print(f"   [INFO] S3 結束: {s3_distance:.1f}m (終點線)")
                else:
                    print(f"   [WARNING] 遙測數據缺少 Time 欄位，無法計算 Sector 邊界")
            else:
                print(f"   [WARNING] Sector 時間數據不完整，無法計算 Sector 邊界")
                
        except Exception as e:
            print(f"   [WARNING] 提取 Sector 邊界失敗: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"   [SUCCESS] 提取了 {len(position_records)} 個位置點（含速度數據）")
        
        # ✅ 新增：計算高程統計（如果有 Z 軸數據）
        elevation_profile = None
        if z is not None:
            z_clean = z[~np.isnan(z)]
            if len(z_clean) > 0:
                elevation_profile = {
                    "available": True,
                    "min_elevation": float(np.min(z_clean) / 10.0),
                    "max_elevation": float(np.max(z_clean) / 10.0),
                    "elevation_change": float((np.max(z_clean) - np.min(z_clean)) / 10.0),
                    "data_source": "FastF1 Z Axis (corrected /10)"
                }
                print(f"   [INFO] 高程統計: {elevation_profile['min_elevation']:.1f}m ~ {elevation_profile['max_elevation']:.1f}m")
        
        return {
            "position_records": position_records,
            "track_bounds": track_bounds,
            "elevation_profile": elevation_profile,  # ✅ 新增高程統計
            "sector_boundaries": sector_boundaries   # ✅ 新增 Sector 邊界
        }
        
    except Exception as e:
        print(f"   [ERROR] 提取位置數據失敗: {e}")
        import traceback
        traceback.print_exc()
        return {"position_records": [], "track_bounds": None, "sector_boundaries": []}


def _calculate_position_changes_for_year(year: int, race: str, session_type: str = 'R') -> int:
    """
    計算特定年份特定賽事的名次變更總次數
    
    整合 Function 15 的邏輯，但簡化為只計算 total_position_changes
    
    Args:
        year: 年份
        race: 賽道名稱
        session_type: 會話類型
        
    Returns:
        名次變更總次數 (所有車手的超車次數 + 被超次數總和)
    """
    try:
        print(f"[POSITION_CHANGES] 計算 {year} {race} 的名次變更...")
        
        # 載入會話
        session = fastf1.get_session(year, race, session_type)
        session.load(laps=True, telemetry=False)  # 只載入圈速數據，不需要遙測
        
        # 獲取所有車手
        drivers = pd.unique(session.laps['Driver'])
        
        total_position_changes = 0
        
        for driver in drivers:
            driver_laps = session.laps.pick_drivers(driver)
            
            if len(driver_laps) < 2:
                continue
            
            # 計算該車手的名次變化次數
            positions = driver_laps['Position'].tolist()
            
            # 計算連續圈速之間的名次變化（絕對值）
            for i in range(1, len(positions)):
                if pd.notna(positions[i]) and pd.notna(positions[i-1]):
                    pos_change = abs(positions[i] - positions[i-1])
                    if pos_change > 0:
                        total_position_changes += int(pos_change)
        
        print(f"[POSITION_CHANGES] {year} {race}: {total_position_changes} 次名次變更")
        return total_position_changes
        
    except Exception as e:
        print(f"[WARNING] 計算 {year} {race} 名次變更失敗: {e}")
        return 0


def _calculate_max_speed_for_year(year: int, race: str, session_type: str = 'R') -> float:
    """
    計算特定年份特定賽事的最高時速
    
    ✅ 優化版本：按車手批量載入遙測數據（而非逐圈載入）
    性能提升：從 2-3 分鐘優化至 5-10 秒（12-36 倍加速）
    
    Args:
        year: 年份
        race: 賽道名稱
        session_type: 會話類型
        
    Returns:
        最高時速 (km/h)，無數據時返回 0.0，同時返回車手和圈數
    """
    try:
        print(f"[MAX_SPEED] 計算 {year} {race} 的最高時速...")
        
        # 載入會話（必須載入 telemetry）
        session = fastf1.get_session(year, race, session_type)
        session.load(laps=True, telemetry=True)
        
        max_speed = 0.0
        max_speed_driver = None
        max_speed_lap = None
        
        # 獲取所有車手
        drivers = pd.unique(session.laps['Driver'])
        print(f"[MAX_SPEED] 使用優化方法：按車手批量載入（共 {len(drivers)} 位車手）")
        
        # ✅ 優化策略：按車手批量載入（而非逐圈載入）
        # 原本：20 車手 × 71 圈 = 1,420 次調用
        # 優化後：20 車手 = 20 次調用（減少 98.6%）
        for idx, driver in enumerate(drivers):
            try:
                driver_laps = session.laps.pick_drivers(driver)
                
                # ✅ 關鍵優化：一次性載入該車手所有圈的遙測數據
                # 而非逐圈調用 lap.get_telemetry()
                driver_telemetry = driver_laps.get_telemetry()
                
                if driver_telemetry is None or driver_telemetry.empty:
                    continue
                
                if 'Speed' not in driver_telemetry.columns:
                    continue
                
                # 找出該車手的最高速度
                driver_max_speed_idx = driver_telemetry['Speed'].idxmax()
                driver_max_speed = float(driver_telemetry.loc[driver_max_speed_idx, 'Speed'])
                
                # 透過 SessionTime 找出對應的圈數
                try:
                    session_time = driver_telemetry.loc[driver_max_speed_idx, 'SessionTime']
                    time_diff = abs(driver_laps['Time'] - session_time)
                    closest_lap_idx = time_diff.idxmin()
                    driver_max_speed_lap = driver_laps.loc[closest_lap_idx, 'LapNumber']
                except Exception:
                    driver_max_speed_lap = 'Unknown'
                
                # 更新全賽最高速度
                if driver_max_speed > max_speed:
                    max_speed = driver_max_speed
                    max_speed_driver = driver
                    max_speed_lap = driver_max_speed_lap
                
                # 每 5 位車手顯示進度
                if (idx + 1) % 5 == 0:
                    print(f"[MAX_SPEED] 進度: {idx + 1}/{len(drivers)} 車手，當前最高: {max_speed:.1f} km/h")
            
            except Exception as driver_error:
                # 單一車手失敗不影響其他車手
                continue
        
        if max_speed > 0:
            print(f"[MAX_SPEED] {year} {race}: {max_speed:.1f} km/h (車手: {max_speed_driver}, Lap {max_speed_lap})")
        else:
            print(f"[MAX_SPEED] {year} {race}: 無有效速度數據")
        
        return max_speed
        
    except Exception as e:
        print(f"[WARNING] 計算 {year} {race} 最高時速失敗: {e}")
        return 0.0


def analyze_historical_flags(
    race: str,
    start_year: int = 2022,
    end_year: int = 2025,
    session_type: str = 'R'
) -> Dict[str, Any]:
    """
    分析特定賽道的歷年旗幟統計
    
    參考功能 97 (championship_standings_analysis.py) 的多年掃描機制
    
    Args:
        race: 賽道名稱 (例如: "Japan", "Monaco")
        start_year: 起始年份 (默認 2020)
        end_year: 結束年份 (默認 2025)
        session_type: 會話類型 (默認 'R' 正賽)
        
    Returns:
        包含完整統計的字典
    """
    # ⚠️ 賽道名稱標準化映射（參考 run_rain_intensity_analysis_json.py）
    RACE_NAME_MAPPING = {
        'Bahrain': 'Bahrain Grand Prix',
        'Saudi Arabia': 'Saudi Arabian Grand Prix',
        'Australia': 'Australian Grand Prix',
        'Azerbaijan': 'Azerbaijan Grand Prix',
        'Miami': 'Miami Grand Prix',
        'Emilia Romagna': 'Emilia Romagna Grand Prix',
        'Monaco': 'Monaco Grand Prix',
        'Spain': 'Spanish Grand Prix',
        'Canada': 'Canadian Grand Prix',
        'Austria': 'Austrian Grand Prix',
        'Great Britain': 'British Grand Prix',
        'Hungary': 'Hungarian Grand Prix',
        'Belgium': 'Belgian Grand Prix',
        'Netherlands': 'Dutch Grand Prix',
        'Italy': 'Italian Grand Prix',
        'Singapore': 'Singapore Grand Prix',
        'Japan': 'Japanese Grand Prix',
        'Qatar': 'Qatar Grand Prix',
        'United States': 'United States Grand Prix',
        'Mexico': 'Mexico City Grand Prix',
        'Brazil': 'São Paulo Grand Prix',  # ✅ 修復：2025 年起改名
        'Las Vegas': 'Las Vegas Grand Prix',
        'Abu Dhabi': 'Abu Dhabi Grand Prix'
    }
    
    # 標準化賽道名稱
    original_race = race
    race = RACE_NAME_MAPPING.get(race, race)
    
    if original_race != race:
        print(f"[INFO] 賽道名稱標準化: '{original_race}' → '{race}'")
    
    print(f"[START] 開始分析 {race} 賽道的歷年旗幟統計 ({start_year}-{end_year})")
    
    # 啟用 FastF1 緩存
    fastf1.Cache.enable_cache(CACHE_DIR)
    
    # ✅ 抑制 FastF1 的日誌輸出（避免年份範圍掃描時的噪音）
    # 儲存所有年份的事件
    all_events_by_year = {}
    analyzed_years = []
    corners_data = []
    circuit_name = None
    country = None
    position_data = None  # ✅ 新增：儲存賽道位置和速度數據
    track_bounds = None   # ✅ 新增：賽道邊界
    elevation_profile = None  # ✅ 新增：高程統計
    sector_boundaries = []  # ✅ 新增：Sector 邊界
    
    # ⚠️ 優先載入 2024 年賽道資訊（統一賽道佈局）
    print(f"\n[TRACK_MAP] 🗺️  優先載入 2024 年賽道佈局資訊...")
    try:
        track_session = fastf1.get_session(2024, race, session_type)
        track_session.load()
        
        event_info = track_session.event
        circuit_name = event_info.get('Location', race) if hasattr(event_info, 'get') else race
        country = event_info.get('Country', 'Unknown') if hasattr(event_info, 'get') else 'Unknown'
        
        # 獲取彎道資訊
        corners_data = get_circuit_corners(track_session, circuit_name)
        if not corners_data:
            print(f"[WARNING] 彎道分析將基於訊息中的 TURN/CORNER 關鍵字")
        
        # 提取賽道位置和速度數據
        print(f"[TRACK_MAP] 提取 2024 年賽道位置和速度數據...")
        position_result = extract_track_position_with_speed(track_session)
        if position_result and position_result.get("position_records"):
            position_data = position_result["position_records"]
            track_bounds = position_result["track_bounds"]
            elevation_profile = position_result.get("elevation_profile")
            sector_boundaries = position_result.get("sector_boundaries", [])  # ✅ 新增
            print(f"[TRACK_MAP] ✅ 成功提取 {len(position_data)} 個賽道位置點（2024 年基準）")
            if elevation_profile and elevation_profile.get("available"):
                print(f"[TRACK_MAP] ✅ 高程數據: {elevation_profile['min_elevation']:.1f}m ~ {elevation_profile['max_elevation']:.1f}m")
            if sector_boundaries:
                print(f"[TRACK_MAP] ✅ Sector 邊界: {len(sector_boundaries)} 個")
        else:
            print(f"[TRACK_MAP] ⚠️  無法提取 2024 年賽道位置數據")
            
    except Exception as e:
        print(f"[TRACK_MAP] ⚠️  無法載入 2024 年賽道資訊: {e}")
        print(f"[TRACK_MAP] 將使用第一個可用年份的賽道資訊作為回退")
    
    # 掃描每一年
    reference_time = datetime.now(timezone.utc)
    for year in range(start_year, end_year + 1):
        print(f"\n{'='*60}")
        print(f"[YEAR] 正在處理 {year} 年 {race} 賽道...")
        
        try:
            # ✅ 檢查賽事是否存在於該年度賽程
            schedule = fastf1.get_event_schedule(year)
            
            # 檢查 race 是否在賽程中，並獲取賽事資訊
            # 改進匹配邏輯：支援 EventName、Country、Location 多種方式
            event_row = None
            for idx, event in schedule.iterrows():
                # 支援完整名稱匹配（例如 "Chinese Grand Prix"）
                if event['EventName'] == race:
                    event_row = event
                    break
                # 支援國家名稱匹配（例如 "China"）
                if event['Country'] == race:
                    event_row = event
                    break
                # 支援地點名稱匹配（例如 "Shanghai"）
                if event['Location'] == race:
                    event_row = event
                    break
            
            if event_row is None:
                print(f"[SKIP] ⏭️  {year} 年賽程中沒有 {race}（賽程中不存在）")
                continue
            
            # ✅ 檢查賽事是否已經舉辦（參考 season_calendar_analysis.py）
            race_date_utc = None
            try:
                # Session5 是正賽
                session5_date = event_row.get('Session5DateUtc')
                if session5_date is not None and not pd.isna(session5_date):
                    race_date_utc = pd.to_datetime(session5_date)
                    if race_date_utc.tzinfo is None:
                        race_date_utc = race_date_utc.replace(tzinfo=timezone.utc)
            except Exception as date_error:
                print(f"[WARNING] ⚠️  無法解析賽事日期: {date_error}")
            
            if race_date_utc and race_date_utc > reference_time:
                days_until = (race_date_utc - reference_time).days
                print(f"[FUTURE] ⏰ {year} 年 {race} 尚未舉辦")
                print(f"[INFO] 📅 賽事日期: {race_date_utc.strftime('%Y-%m-%d')} (還有 {days_until} 天)")
                print(f"[STOP] 🛑 停止掃描（不處理未來賽事）")
                break  # ✅ 提前終止，不再繼續掃描後續年份
            
            # 載入會話數據
            print(f"[LOAD] 📊 載入 {year} 年賽事數據...")
            session = fastf1.get_session(year, race, session_type)
            session.load()
            
            # ✅ 驗證數據是否成功載入
            try:
                _ = session.laps
                print(f"[OK] ✅ 數據載入成功")
            except Exception as load_check_error:
                print(f"[ERROR] ❌ 數據載入驗證失敗: {load_check_error}")
                raise
            
            # ⚠️ 如果 2024 年賽道資訊載入失敗，使用第一個可用年份作為回退
            if not circuit_name:
                event_info = session.event
                circuit_name = event_info.get('Location', race) if hasattr(event_info, 'get') else race
                country = event_info.get('Country', 'Unknown') if hasattr(event_info, 'get') else 'Unknown'
                
                corners_data = get_circuit_corners(session, circuit_name)
                if not corners_data:
                    print(f"[WARNING] 彎道分析將基於訊息中的 TURN/CORNER 關鍵字")
                
                print(f"\n[FALLBACK] 使用 {year} 年賽道佈局資訊（2024 年數據不可用）")
                position_result = extract_track_position_with_speed(session)
                if position_result and position_result.get("position_records"):
                    position_data = position_result["position_records"]
                    track_bounds = position_result["track_bounds"]
                    elevation_profile = position_result.get("elevation_profile")
                    sector_boundaries = position_result.get("sector_boundaries", [])  # ✅ 新增
                    print(f"[FALLBACK] ✅ 成功提取 {len(position_data)} 個賽道位置點（{year} 年基準）")
            
            # 提取旗幟事件
            print(f"[EXTRACT] 🏁 提取旗幟事件...")
            events = extract_flag_events_from_session(session, year)
            
            all_events_by_year[year] = events
            analyzed_years.append(year)
            
            print(f"[SUCCESS] ✅ {year} 年數據處理完成")
            
        except Exception as e:
            # ✅ 顯示錯誤訊息（已取消 Silent 模式）
            print(f"[ERROR] ❌ {year} 年 {race} 數據處理失敗: {e}")
            # 顯示詳細的錯誤堆疊（方便調試）
            import traceback
            print(f"[DEBUG] 錯誤堆疊:")
            traceback.print_exc()
            continue
    
    # ✅ 生成結果摘要
    print(f"\n{'='*60}")
    if not analyzed_years:
        print(f"[WARNING] ⚠️  {start_year}-{end_year} 年間沒有可用的數據")
        print(f"[INFO] 將生成空白 JSON（yearly_summary 為空）")
    else:
        print(f"[SUCCESS] ✅ 成功分析了 {len(analyzed_years)} 年的數據")
        print(f"[YEARS] 已處理年份: {analyzed_years}")
    
    # ✅ 彙總年度統計 - 只為已處理的年份生成條目
    yearly_summary = {}
    total_flags_all_years = 0
    
    for year in analyzed_years:
        # 有數據的年份：使用實際統計
        events = all_events_by_year[year]
        stats = events['statistics']
        
        # ✅ 計算該年度的 position changes (超車次數)
        position_changes = _calculate_position_changes_for_year(year, race, session_type)
        
        # ✅ 計算該年度的最高時速
        max_speed = _calculate_max_speed_for_year(year, race, session_type)
        
        yearly_summary[str(year)] = {
            'yellow_flags': stats['yellow_count'],
            'double_yellow_flags': stats['double_yellow_count'],
            'red_flags': stats['red_count'],
            'safety_cars': stats['safety_car_count'],
            'total_incidents': stats['total_flags'],
            'session_type': session_type,
            'position_changes': position_changes,
            'max_speed': round(max_speed, 1)  # ✅ 新增最高時速（保留1位小數）
        }
        
        total_flags_all_years += stats['total_flags']
    
    # 彙總彎道統計
    corner_analysis = {}
    if corners_data:
        corner_analysis = aggregate_corner_statistics(all_events_by_year, corners_data)
    
    # 計算趨勢
    most_dangerous_corner = None
    highest_incident_year = None
    
    if corner_analysis:
        # 找出最危險的彎道
        max_flags = 0
        for corner_key, stats in corner_analysis.items():
            if stats['total_flags'] > max_flags:
                max_flags = stats['total_flags']
                most_dangerous_corner = corner_key
    
    if yearly_summary:
        # 找出事故最多的年份
        max_incidents = 0
        for year_str, stats in yearly_summary.items():
            if stats['total_incidents'] > max_incidents:
                max_incidents = stats['total_incidents']
                highest_incident_year = int(year_str)
    
    # 組裝最終結果
    result = {
        "success": True,
        "metadata": {
            "circuit_name": circuit_name or race,
            "country": country or "Unknown",
            "years_analyzed": " ".join(map(str, analyzed_years)),  # ✅ 字串格式，只包含已處理的年份
            "years_available": len(analyzed_years),  # ✅ 實際有數據的年份數量
            "total_years": len(analyzed_years),  # ✅ 與 years_available 相同
            "corners_count": len(corners_data),
            "session_type": session_type,
            "generated_at": datetime.now().isoformat(),
            "has_position_data": position_data is not None and len(position_data) > 0,
            "has_speed_data": position_data is not None and len(position_data) > 0 and any('speed' in p for p in position_data),
            "has_elevation_data": elevation_profile is not None and elevation_profile.get("available", False)
        },
        "yearly_summary": yearly_summary,
        "corner_analysis": corner_analysis,
        "trends": {
            "most_dangerous_corner": most_dangerous_corner,
            "highest_incident_year": highest_incident_year,
            "total_flags_all_years": total_flags_all_years,
            "safety_car_deployments": sum(s.get('safety_cars', 0) for s in yearly_summary.values())
        }
    }
    
    # ✅ 新增：添加賽道位置和速度數據
    if position_data:
        result["detailed_position_records"] = position_data
        print(f"[INFO] 已添加 {len(position_data)} 個賽道位置點到結果中")
        
        # ✅ 新增：計算速度分類統計
        speed_distribution = calculate_speed_distribution(position_data)
        if speed_distribution:
            result["speed_distribution"] = speed_distribution
            print(f"[INFO] 速度分類統計:")
            print(f"  - 低速區 (<120 km/h): {speed_distribution['low_speed_percentage']:.1f}% ({speed_distribution['low_speed_count']} 點)")
            print(f"  - 中速區 (120-240 km/h): {speed_distribution['mid_speed_percentage']:.1f}% ({speed_distribution['mid_speed_count']} 點)")
            print(f"  - 高速區 (>240 km/h): {speed_distribution['high_speed_percentage']:.1f}% ({speed_distribution['high_speed_count']} 點)")
            print(f"  - 平均速度: {speed_distribution['average_speed']:.1f} km/h")
            print(f"  - 速度範圍: {speed_distribution['min_speed']:.1f} - {speed_distribution['max_speed']:.1f} km/h")
    
    if track_bounds:
        result["track_bounds"] = track_bounds
        print(f"[INFO] 賽道邊界: X({track_bounds['x_min']:.1f} ~ {track_bounds['x_max']:.1f}), Y({track_bounds['y_min']:.1f} ~ {track_bounds['y_max']:.1f})")
    
    # ✅ 新增：添加高程統計
    if elevation_profile:
        result["elevation_profile"] = elevation_profile
        print(f"[INFO] 高程統計: {elevation_profile['min_elevation']:.1f}m ~ {elevation_profile['max_elevation']:.1f}m (變化 {elevation_profile['elevation_change']:.1f}m)")
    
    # ✅ 新增：添加 Sector 邊界
    if sector_boundaries:
        result["sector_boundaries"] = sector_boundaries
        print(f"[INFO] Sector 邊界: {len(sector_boundaries)} 個")
        for boundary in sector_boundaries:
            print(f"  - {boundary['name']}: {boundary['distance_m']:.1f}m")
    
    # ✅ 新增：添加官方彎道資訊（從 corners_data 轉換為 official_corners 格式）
    print(f"\n[DEBUG] 準備構建 official_corners...")
    print(f"[DEBUG]   corners_data 類型: {type(corners_data)}, 長度: {len(corners_data) if corners_data else 0}")
    print(f"[DEBUG]   position_data 類型: {type(position_data)}, 長度: {len(position_data) if position_data else 0}")
    print(f"[DEBUG]   條件判斷: corners_data={bool(corners_data)}, position_data={bool(position_data)}")
    
    if corners_data and position_data:
        print(f"\n[INFO] 構建 official_corners 數據...")
        official_corners_list = []
        
        # ✅ 調試：打印第一個彎道數據
        if corners_data:
            first_corner = corners_data[0]
            print(f"[DEBUG] 第一個彎道數據: {first_corner}")
        
        for corner in corners_data:
            corner_num = corner.get('number', 0)
            corner_dist = corner.get('distance', 0)
            corner_x = corner.get('x', 0)
            corner_y = corner.get('y', 0)
            
            # 如果彎道有 x, y 座標（從 FastF1 獲取）
            if corner_x != 0 or corner_y != 0:
                official_corners_list.append({
                    "number": int(corner_num),
                    "x": float(corner_x),
                    "y": float(corner_y),
                    "distance": float(corner_dist),
                    "angle": float(corner.get('angle', 0)),
                    "letter": corner.get('letter', '')
                })
            # 否則從 position_data 中找到最接近的點
            elif corner_dist > 0:
                closest_point = None
                min_diff = float('inf')
                
                for point in position_data:
                    point_dist = point.get('distance_m', 0)
                    diff = abs(point_dist - corner_dist)
                    if diff < min_diff:
                        min_diff = diff
                        closest_point = point
                
                if closest_point and min_diff < 100:  # 誤差小於 100m
                    official_corners_list.append({
                        "number": int(corner_num),
                        "x": float(closest_point.get('position_x', 0)),
                        "y": float(closest_point.get('position_y', 0)),
                        "distance": float(closest_point.get('distance_m', 0)),
                        "angle": 0.0,
                        "letter": corner.get('letter', ''),
                        "mapping_error": float(min_diff)
                    })
        
        if official_corners_list:
            result["official_corners"] = {
                "available": True,
                "count": len(official_corners_list),
                "corners": official_corners_list,
                "data_source": "FastF1 circuit_info.corners" if any(c.get('x', 0) != 0 for c in corners_data) else "distance_mapping"
            }
            print(f"[SUCCESS] 已添加 {len(official_corners_list)} 個彎道位置到結果中")
        else:
            print(f"[WARNING] 無法構建 official_corners（缺少座標數據）")
    else:
        print(f"[DEBUG] ❌ 跳過 official_corners 構建（條件不滿足）")
    
    # ✅ 新增：2022-2025 賽事前三名車手最速圈統計
    print(f"\n[INFO] 開始統計 2022-2025 {race} 賽事前三名車手...")
    race_top3_stats = get_race_top3_drivers_2022_2023(race)  # 函數名稱保持不變（向後兼容）
    if race_top3_stats and race_top3_stats.get("available"):
        result["race_top3_drivers_2022_2023"] = race_top3_stats
        print(f"[SUCCESS] ✅ 成功獲取 {len(race_top3_stats.get('years_data', []))} 年的前三名數據 (2022-2025)")
    else:
        result["race_top3_drivers_2022_2023"] = {
            "available": False,
            "message": "無法獲取 2022-2025 賽事前三名數據"
        }
        print(f"[WARNING] ⚠️  無法獲取 2022-2025 賽事前三名數據")
    
    return result


def get_race_top3_drivers_2022_2023(race: str) -> Dict[str, Any]:
    """
    獲取指定賽事在 2022-2025 年的最終名次前三名車手及其最速圈
    
    註：函數名稱保留為 _2022_2023 以維持向後兼容，但實際處理 2022-2025 年數據
    
    Args:
        race: 賽道名稱（例如 "Las Vegas"）
        
    Returns:
        {
            "available": True,
            "race": "Las Vegas Grand Prix",
            "years_data": [
                {
                    "year": 2022,
                    "top3": [
                        {
                            "position": 1,
                            "driver_code": "VER",
                            "driver_name": "Max Verstappen",
                            "team": "Red Bull Racing",
                            "fastest_lap_seconds": 78.543
                        },
                        ...
                    ]
                },
                ...
            ]
        }
    """
    # 賽道名稱標準化映射（複用現有映射）
    RACE_NAME_MAPPING = {
        'Bahrain': 'Bahrain Grand Prix',
        'Saudi Arabia': 'Saudi Arabian Grand Prix',
        'Australia': 'Australian Grand Prix',
        'Azerbaijan': 'Azerbaijan Grand Prix',
        'Miami': 'Miami Grand Prix',
        'Emilia Romagna': 'Emilia Romagna Grand Prix',
        'Monaco': 'Monaco Grand Prix',
        'Spain': 'Spanish Grand Prix',
        'Canada': 'Canadian Grand Prix',
        'Austria': 'Austrian Grand Prix',
        'Great Britain': 'British Grand Prix',
        'Hungary': 'Hungarian Grand Prix',
        'Belgium': 'Belgian Grand Prix',
        'Netherlands': 'Dutch Grand Prix',
        'Italy': 'Italian Grand Prix',
        'Singapore': 'Singapore Grand Prix',
        'Japan': 'Japanese Grand Prix',
        'Qatar': 'Qatar Grand Prix',
        'United States': 'United States Grand Prix',
        'Mexico': 'Mexico City Grand Prix',
        'Brazil': 'São Paulo Grand Prix',
        'Las Vegas': 'Las Vegas Grand Prix',
        'Abu Dhabi': 'Abu Dhabi Grand Prix'
    }
    
    # 標準化賽道名稱
    original_race = race
    race = RACE_NAME_MAPPING.get(race, race)
    
    print(f"[TOP3] 🏁 正在查詢 {race} 2022-2025 年最終名次前三名...")
    
    # 啟用 FastF1 緩存
    fastf1.Cache.enable_cache(CACHE_DIR)
    
    years_data = []
    
    # ✅ 改為 2022-2025 年
    for year in [2022, 2023, 2024, 2025]:
        try:
            print(f"[TOP3] 📅 處理 {year} 年 {race}...")
            
            # 檢查賽事是否存在
            schedule = fastf1.get_event_schedule(year)
            event_row = None
            
            for idx, event in schedule.iterrows():
                if (event['EventName'] == race or 
                    event['Country'] == race or 
                    event['Location'] == race or
                    event['EventName'] == original_race):
                    event_row = event
                    break
            
            if event_row is None:
                print(f"[TOP3] ⏭️  {year} 年賽程中沒有 {race}")
                continue
            
            # ✅ 檢查賽事是否已經舉辦（避免處理未來賽事）
            race_date_utc = None
            try:
                # Session5 是正賽
                session5_date = event_row.get('Session5DateUtc')
                if session5_date is not None and not pd.isna(session5_date):
                    race_date_utc = pd.to_datetime(session5_date)
                    if race_date_utc.tzinfo is None:
                        race_date_utc = race_date_utc.replace(tzinfo=timezone.utc)
            except Exception as date_error:
                print(f"[TOP3] ⚠️  無法解析賽事日期: {date_error}")
            
            reference_time = datetime.now(timezone.utc)
            if race_date_utc and race_date_utc > reference_time:
                days_until = (race_date_utc - reference_time).days
                print(f"[TOP3] ⏰ {year} 年 {race} 尚未舉辦（還有 {days_until} 天）")
                print(f"[TOP3] 🛑 跳過未來賽事，不處理 {year} 年數據")
                continue  # ✅ 跳過未來賽事，繼續檢查其他年份
            
            # 載入正賽會話
            session = fastf1.get_session(year, race, 'R')
            session.load()
            
            # 獲取比賽結果（最終名次）
            results = session.results
            
            if results is None or results.empty:
                print(f"[TOP3] ⚠️  {year} 年 {race} 無比賽結果數據")
                continue
            
            # 按最終名次排序並取前三名
            results_sorted = results.sort_values('Position')
            top3_results = results_sorted.head(3)
            
            top3_list = []
            
            for idx, driver_result in top3_results.iterrows():
                position = int(driver_result['Position']) if pd.notna(driver_result['Position']) else 0
                driver_code = driver_result['Abbreviation'] if pd.notna(driver_result['Abbreviation']) else 'UNK'
                driver_name = f"{driver_result['FirstName']} {driver_result['LastName']}" if pd.notna(driver_result['FirstName']) else driver_code
                team_name = driver_result['TeamName'] if pd.notna(driver_result['TeamName']) else 'Unknown'
                
                # 獲取該車手的最速圈
                driver_laps = session.laps.pick_drivers(driver_code)
                
                if driver_laps is not None and not driver_laps.empty:
                    # 過濾有效圈速
                    valid_laps = driver_laps[driver_laps['LapTime'].notna()]
                    
                    if not valid_laps.empty:
                        fastest_lap_time = valid_laps['LapTime'].min()
                        fastest_lap_seconds = fastest_lap_time.total_seconds()
                    else:
                        fastest_lap_seconds = None
                else:
                    fastest_lap_seconds = None
                
                top3_list.append({
                    "position": position,
                    "driver_code": driver_code,
                    "driver_name": driver_name.strip(),
                    "team": team_name,
                    "fastest_lap_seconds": round(fastest_lap_seconds, 3) if fastest_lap_seconds else None
                })
                
                print(f"[TOP3]   P{position}: {driver_code} ({team_name}) - {fastest_lap_seconds:.3f}s" if fastest_lap_seconds else f"[TOP3]   P{position}: {driver_code} ({team_name}) - N/A")
            
            years_data.append({
                "year": year,
                "top3": top3_list
            })
            
            print(f"[TOP3] ✅ {year} 年數據獲取完成")
            
        except Exception as e:
            print(f"[TOP3] ❌ {year} 年數據獲取失敗: {e}")
            continue
    
    if not years_data:
        return {
            "available": False,
            "race": race,
            "message": "無法獲取任何年份的數據"
        }
    
    return {
        "available": True,
        "race": race,
        "years_analyzed": "2022-2025",  # ✅ 更新為 2022-2025
        "years_data": years_data
    }


def generate_json_output(data: Dict[str, Any], race: str, start_year: int, end_year: int) -> str:
    """
    生成 JSON 輸出檔案
    
    參考功能 97 的 JSON 命名規範
    
    Args:
        data: 分析結果數據
        race: 賽道名稱
        start_year: 起始年份
        end_year: 結束年份
        
    Returns:
        JSON 檔案路徑
    """
    json_dir = _ensure_json_dir()
    
    race_token = _sanitize_token(race)
    
    # ✅ 固定檔案名格式（移除 timestamp）
    filename = f"historical_flags_{race_token}_{start_year}-{end_year}.json"
    filepath = json_dir / filename
    
    json_result = {
        "function_id": 100,
        "function_name": "Historical Flags Analysis",
        "analysis_type": "historical_flags_analysis",
        "timestamp": datetime.now().isoformat(),
        "data": data
    }
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(json_result, f, ensure_ascii=False, indent=2)
        
        abs_filepath = filepath.absolute()
        print(f"\n[SUCCESS] JSON 結果已保存到: {abs_filepath}")
        return str(abs_filepath)
        
    except Exception as e:
        print(f"[ERROR] JSON 保存失敗: {e}")
        return ""


def run_historical_flags_analysis_json(
    race: str,
    start_year: int = 2022,
    end_year: int = 2025,
    session_type: str = 'R',
    **kwargs
) -> Dict[str, Any]:
    """
    執行歷年旗幟統計分析（JSON 模式）
    
    此函數被 function_mapper.py 調用
    
    Args:
        race: 賽道名稱
        start_year: 起始年份（預設 2022，跳過 COVID-19 取消年份）
        end_year: 結束年份（預設 2025）
        session_type: 會話類型
        **kwargs: 其他參數
        
    Returns:
        標準化結果字典
    """
    print(f"[FUNCTION 100] 歷年旗幟統計分析")
    print(f"[PARAMS] 賽道={race}, 年份={start_year}-{end_year}, 會話={session_type}")
    print(f"[PARAMS] 賽道={race}, 年份={start_year}-{end_year}, 會話={session_type}")
    
    # 執行分析
    result = analyze_historical_flags(race, start_year, end_year, session_type)
    
    if not result.get('success'):
        return {
            "success": False,
            "message": result.get('message', '分析失敗'),
            "function_id": "100"
        }
    
    # 生成 JSON 輸出
    json_path = generate_json_output(result, race, start_year, end_year)
    
    # 顯示摘要
    print(f"\n[SUMMARY] 歷年旗幟統計摘要:")
    print(f"  賽道: {result['metadata']['circuit_name']}")
    print(f"  分析年份: {result['metadata']['years_analyzed']}")
    print(f"  總旗幟事件: {result['trends']['total_flags_all_years']}")
    
    if result['trends']['most_dangerous_corner']:
        print(f"  最危險彎道: {result['trends']['most_dangerous_corner']}")
    
    if result['trends']['highest_incident_year']:
        print(f"  事故最多年份: {result['trends']['highest_incident_year']}")
    
    return {
        "success": True,
        "data": result,
        "json_path": json_path,
        "function_id": "100"
    }
