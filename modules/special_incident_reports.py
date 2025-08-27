#!/usr/bin/env python3
"""
F1 特殊事件報告模組 - Function 9
Special Incident Reports Module - Following Core Development Standards
專注於關鍵和特殊事故的深度分析，包含高影響事件、處罰決定、安全介入等
"""

import os
import json
import pickle
import pandas as pd
import re
from datetime import datetime
from prettytable import PrettyTable

def generate_cache_key(session_info):
    """生成快取鍵值"""
    return f"special_incident_reports_{session_info.get('year', 2024)}_{session_info.get('event_name', 'Unknown')}_{session_info.get('session_type', 'R')}"

def check_cache(cache_key):
    """檢查快取是否存在"""
    cache_path = os.path.join("cache", f"{cache_key}.pkl")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        except:
            return None
    return None

def save_cache(data, cache_key):
    """保存數據到快取"""
    os.makedirs("cache", exist_ok=True)
    cache_path = os.path.join("cache", f"{cache_key}.pkl")
    try:
        with open(cache_path, 'wb') as f:
            pickle.dump(data, f)
        return True
    except:
        return False

def format_time(time_obj):
    """標準時間格式化函數"""
    if hasattr(time_obj, 'total_seconds'):
        total_seconds = time_obj.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = total_seconds % 60
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:06.3f}"
        else:
            return f"{minutes}:{seconds:06.3f}"
    return str(time_obj)

def extract_driver_info(message):
    """從訊息中提取車手資訊"""
    import re
    
    # 提取車號和車手代碼
    car_pattern = r'CAR[S]?\s+(\d+)\s*\(([A-Z]{3})\)'
    cars = re.findall(car_pattern, message.upper())
    
    if cars:
        return [{'car_number': car[0], 'driver_code': car[1]} for car in cars]
    
    # 僅提取車號
    car_number_pattern = r'CAR[S]?\s+(\d+)'
    car_numbers = re.findall(car_number_pattern, message.upper())
    
    if car_numbers:
        return [{'car_number': num, 'driver_code': 'UNK'} for num in car_numbers]
    
    return []

def classify_special_incident(message):
    """分類特殊事件"""
    message = message.upper()
    
    # 高優先級特殊事件
    if 'RED FLAG' in message:
        return 'RED_FLAG_INCIDENT'
    elif 'SAFETY CAR' in message:
        if 'DEPLOYED' in message or 'FORMATION LAP' in message:
            return 'SAFETY_CAR_DEPLOYED'
        elif 'WITHDRAWN' in message or 'ENDING' in message or 'IN THIS LAP' in message:
            return 'SAFETY_CAR_WITHDRAWN'
        else:
            return 'SAFETY_CAR_INCIDENT'
    elif 'VIRTUAL SAFETY CAR' in message or 'VSC' in message:
        if 'DEPLOYED' in message:
            return 'VSC_DEPLOYED'
        elif 'ENDING' in message:
            return 'VSC_ENDING'
        else:
            return 'VSC_INCIDENT'
    elif any(word in message for word in ['COLLISION', 'CRASH', 'ACCIDENT']):
        return 'MAJOR_COLLISION'
    elif 'INCIDENT INVOLVING' in message and 'CARS' in message:
        # 進一步細分調查階段和處罰決定
        if 'FIA STEWARDS' in message:
            if any(penalty in message for penalty in ['PENALTY', 'WARNING', 'REPRIMAND']):
                return 'PENALTY_DECISION'
            else:
                return 'INVESTIGATION_INCIDENT'
        else:
            return 'CONTACT_INCIDENT'
    elif 'CONTACT' in message and any(word in message for word in ['INCIDENT', 'INVOLVING', 'CARS']):
        return 'CONTACT_INCIDENT'
    elif 'PENALTY' in message and any(word in message for word in ['DISQUALIFIED', 'STOP AND GO', 'DRIVE THROUGH']):
        return 'MAJOR_PENALTY'
    elif 'MEDICAL CAR' in message:
        return 'MEDICAL_INTERVENTION'
    elif 'UNDER INVESTIGATION' in message or ('FIA STEWARDS' in message and 'REVIEW' in message):
        return 'INVESTIGATION_INCIDENT'
    elif 'FIA STEWARDS' in message and any(word in message for word in ['PENALTY', 'SERVED', 'WARNING']):
        return 'PENALTY_DECISION'
    elif 'CHEQUERED FLAG' in message:
        return 'RACE_CONCLUSION'
    elif any(word in message for word in ['POSITION PENALTY', 'TIME PENALTY']):
        return 'PENALTY_APPLIED'
    elif 'DEBRIS' in message:
        return 'DEBRIS_INCIDENT'
    elif 'DANGEROUS DRIVING' in message:
        return 'DANGEROUS_DRIVING'
    elif 'SPIN' in message or 'OFF TRACK' in message:
        return 'TRACK_EXCURSION'
    # 新增：雨天相關事件
    elif 'RAIN' in message or 'WET' in message or 'INTERMEDIATE' in message:
        return 'WEATHER_INCIDENT'
    # 新增：處罰相關
    elif 'PENALTY' in message or 'WARNING' in message:
        return 'PENALTY_APPLIED'
    else:
        return None

def assess_special_severity(message, incident_type):
    """評估特殊事件嚴重程度"""
    message = message.upper()
    
    if incident_type == 'RED_FLAG_INCIDENT':
        return 'CRITICAL'
    elif incident_type == 'MEDICAL_INTERVENTION':
        return 'CRITICAL'
    elif incident_type == 'MAJOR_COLLISION':
        return 'HIGH'
    elif incident_type in ['SAFETY_CAR_DEPLOYED', 'SAFETY_CAR_INCIDENT']:
        return 'HIGH'
    elif incident_type == 'MAJOR_PENALTY':
        return 'HIGH'
    elif incident_type == 'PENALTY_DECISION':
        return 'HIGH'
    elif incident_type == 'CONTACT_INCIDENT':
        return 'MEDIUM'
    elif incident_type in ['VSC_DEPLOYED', 'VSC_INCIDENT']:
        return 'MEDIUM'
    elif incident_type == 'INVESTIGATION_INCIDENT':
        return 'MEDIUM'
    elif incident_type == 'DANGEROUS_DRIVING':
        return 'MEDIUM'
    elif incident_type == 'DEBRIS_INCIDENT':
        return 'MEDIUM'
    elif incident_type == 'WEATHER_INCIDENT':
        return 'MEDIUM'
    elif incident_type == 'PENALTY_APPLIED':
        return 'MEDIUM'
    elif incident_type in ['SAFETY_CAR_WITHDRAWN', 'VSC_ENDING']:
        return 'LOW'
    elif incident_type == 'TRACK_EXCURSION':
        return 'LOW'
    else:
        return 'LOW'

def calculate_impact_score(incident_type, lap, total_laps):
    """計算事件影響評分 (0-100)"""
    base_scores = {
        'RED_FLAG_INCIDENT': 95,
        'MEDICAL_INTERVENTION': 90,
        'MAJOR_COLLISION': 85,
        'SAFETY_CAR_DEPLOYED': 80,
        'SAFETY_CAR_INCIDENT': 75,
        'PENALTY_DECISION': 70,
        'VSC_DEPLOYED': 65,
        'CONTACT_INCIDENT': 60,
        'MAJOR_PENALTY': 60,
        'DANGEROUS_DRIVING': 55,
        'DEBRIS_INCIDENT': 50,
        'WEATHER_INCIDENT': 45,
        'INVESTIGATION_INCIDENT': 40,
        'PENALTY_APPLIED': 35,
        'TRACK_EXCURSION': 30,
        'VSC_ENDING': 25,
        'SAFETY_CAR_WITHDRAWN': 25,
        'RACE_CONCLUSION': 20
    }
    
    base_score = base_scores.get(incident_type, 10)
    
    # 根據發生時間調整分數
    if total_laps > 0:
        lap_factor = lap / total_laps
        if lap_factor > 0.8:  # 比賽後期
            base_score += 15
        elif lap_factor > 0.6:  # 比賽中期
            base_score += 8
        elif lap_factor < 0.2:  # 比賽前期
            base_score += 5
    
    return min(100, base_score)

def extract_penalty_details(message):
    """提取處罰詳細資訊"""
    import re
    
    penalty_info = {
        'penalty_type': None,
        'penalty_value': None,
        'reason': None
    }
    
    message_upper = message.upper()
    
    # 處罰類型
    if 'TIME PENALTY' in message_upper:
        time_match = re.search(r'(\d+)\s*SECOND[S]?\s*TIME\s*PENALTY', message_upper)
        if time_match:
            penalty_info['penalty_type'] = 'TIME_PENALTY'
            penalty_info['penalty_value'] = f"{time_match.group(1)}s"
    elif 'POSITION PENALTY' in message_upper:
        pos_match = re.search(r'(\d+)\s*POSITION[S]?\s*PENALTY', message_upper)
        if pos_match:
            penalty_info['penalty_type'] = 'POSITION_PENALTY'
            penalty_info['penalty_value'] = f"{pos_match.group(1)} positions"
    elif 'DRIVE THROUGH' in message_upper:
        penalty_info['penalty_type'] = 'DRIVE_THROUGH'
    elif 'STOP AND GO' in message_upper:
        penalty_info['penalty_type'] = 'STOP_AND_GO'
    elif 'DISQUALIFIED' in message_upper:
        penalty_info['penalty_type'] = 'DISQUALIFICATION'
    
    # 處罰原因
    if 'TRACK LIMITS' in message_upper:
        penalty_info['reason'] = 'TRACK_LIMITS_VIOLATION'
    elif 'CONTACT' in message_upper or 'COLLISION' in message_upper:
        penalty_info['reason'] = 'CONTACT_INCIDENT'
    elif 'ADVANTAGE' in message_upper:
        penalty_info['reason'] = 'GAINING_ADVANTAGE'
    elif 'PIT' in message_upper:
        penalty_info['reason'] = 'PIT_RELATED'
    elif 'DANGEROUS' in message_upper:
        penalty_info['reason'] = 'DANGEROUS_DRIVING'
    
    return penalty_info

def analyze_special_incidents(session):
    """分析特殊事件報告"""
    special_data = {
        'special_incidents': [],
        'red_flag_incidents': [],
        'safety_car_incidents': [],
        'vsc_incidents': [],
        'collision_incidents': [],
        'contact_incidents': [],
        'major_accidents': [],
        'penalty_incidents': [],
        'investigation_incidents': [],
        'medical_interventions': [],
        'debris_incidents': [],
        'weather_incidents': [],
        'summary_statistics': {
            'total_special_incidents': 0,
            'critical_incidents': 0,
            'high_severity_incidents': 0,
            'safety_car_deployments': 0,
            'vsc_deployments': 0,
            'collision_count': 0,
            'contact_incidents_count': 0,
            'weather_events': 0,
            'penalty_decisions': 0,
            'race_interruptions': 0,
            'involved_drivers_count': 0,
            'average_impact_score': 0
        },
        'safety_car_timeline': [],
        'collision_analysis': {
            'total_collisions': 0,
            'collision_locations': {},
            'collision_causes': {},
            'most_collision_prone_driver': None,
            'collision_severity_distribution': {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0},
            'collision_penalty_status': {
                'investigation_stage': 0,
                'penalty_imposed': 0,
                'no_action': 0,
                'warnings_issued': 0
            },
            'corner_incident_details': {},
            'penalty_breakdown': {
                'time_penalties': [],
                'position_penalties': [],
                'warnings': [],
                'no_penalties': []
            }
        },
        'chronological_timeline': [],
        'driver_penalty_analysis': {},
        'incident_impact_analysis': {}
    }
    
    try:
        if hasattr(session, 'race_control_messages'):
            race_control = session.race_control_messages
            
            if race_control is not None and not race_control.empty:
                special_sequence = 1
                total_impact_score = 0
                involved_drivers = []
                
                # 估算總圈數，同時用於過濾正常結束的 CHEQUERED FLAG
                total_laps = race_control['Lap'].max() if 'Lap' in race_control.columns else 50
                
                for _, message in race_control.iterrows():
                    msg_text = str(message.get('Message', ''))
                    msg_upper = msg_text.upper()
                    lap = message.get('Lap', 0)
                    time = message.get('Time', 'N/A')
                    
                    # 過濾最後一圈的正常比賽結束 CHEQUERED FLAG
                    if 'CHEQUERED FLAG' in msg_upper and lap == total_laps:
                        continue  # 跳過正常的比賽結束標誌
                    
                    # 分類特殊事件
                    incident_type = classify_special_incident(msg_text)
                    
                    if incident_type:
                        # 提取車手資訊
                        involved_drivers_info = extract_driver_info(msg_text)
                        
                        # 評估嚴重程度
                        severity = assess_special_severity(msg_text, incident_type)
                        
                        # 計算影響評分
                        impact_score = calculate_impact_score(incident_type, lap, total_laps)
                        
                        # 提取處罰詳細資訊
                        penalty_details = extract_penalty_details(msg_text) if 'PENALTY' in incident_type else None
                        
                        special_incident = {
                            'special_sequence': special_sequence,
                            'lap': lap,
                            'time': format_time(time) if time != 'N/A' else str(time),
                            'raw_time': str(time),
                            'incident_type': incident_type,
                            'severity': severity,
                            'impact_score': impact_score,
                            'message': msg_text,
                            'involved_drivers': involved_drivers_info,
                            'driver_codes': [d['driver_code'] for d in involved_drivers_info],
                            'penalty_details': penalty_details,
                            'flags_involved': extract_flags_detailed(msg_upper),
                            'safety_implications': assess_safety_implications(msg_upper, incident_type),
                            'race_impact': assess_race_impact(msg_upper, incident_type, lap, total_laps)
                        }
                        
                        special_data['special_incidents'].append(special_incident)
                        
                        # 分類存儲
                        if incident_type == 'RED_FLAG_INCIDENT':
                            special_data['red_flag_incidents'].append(special_incident)
                        elif 'SAFETY_CAR' in incident_type:
                            special_data['safety_car_incidents'].append(special_incident)
                            special_data['summary_statistics']['safety_car_deployments'] += 1
                            
                            # 安全車時間軸分析
                            special_data['safety_car_timeline'].append({
                                'sequence': special_sequence,
                                'lap': lap,
                                'time': format_time(time) if time != 'N/A' else str(time),
                                'action': incident_type,
                                'impact_score': impact_score
                            })
                        elif 'VSC' in incident_type:
                            special_data['vsc_incidents'].append(special_incident)
                            special_data['summary_statistics']['vsc_deployments'] += 1
                        elif incident_type == 'MAJOR_COLLISION':
                            special_data['collision_incidents'].append(special_incident)
                            special_data['major_accidents'].append(special_incident)  # 保持向後相容
                            special_data['summary_statistics']['collision_count'] += 1
                            
                            # 碰撞分析
                            special_data['collision_analysis']['total_collisions'] += 1
                            special_data['collision_analysis']['collision_severity_distribution'][severity] += 1
                            
                            # 提取碰撞位置（如果有）
                            location_match = re.search(r'TURN\s+(\d+)', msg_text.upper())
                            if location_match:
                                turn = f"TURN_{location_match.group(1)}"
                                special_data['collision_analysis']['collision_locations'][turn] = \
                                    special_data['collision_analysis']['collision_locations'].get(turn, 0) + 1
                                
                                # 詳細彎角事件記錄
                                corner_name = f"彎角{location_match.group(1)}"
                                if corner_name not in special_data['collision_analysis']['corner_incident_details']:
                                    special_data['collision_analysis']['corner_incident_details'][corner_name] = {
                                        'total_incidents': 0,
                                        'incidents': [],
                                        'drivers_involved': [],
                                        'penalty_outcomes': {'investigation': 0, 'penalty': 0, 'warning': 0, 'no_action': 0}
                                    }
                                
                                special_data['collision_analysis']['corner_incident_details'][corner_name]['total_incidents'] += 1
                                special_data['collision_analysis']['corner_incident_details'][corner_name]['incidents'].append({
                                    'lap': lap,
                                    'drivers': [d['driver_code'] for d in involved_drivers_info],
                                    'severity': severity,
                                    'message': msg_text
                                })
                                
                                for driver in involved_drivers_info:
                                    if driver['driver_code'] not in special_data['collision_analysis']['corner_incident_details'][corner_name]['drivers_involved']:
                                        special_data['collision_analysis']['corner_incident_details'][corner_name]['drivers_involved'].append(driver['driver_code'])
                            
                            elif 'PIT' in msg_text.upper():
                                location = "PIT_AREA"
                                special_data['collision_analysis']['collision_locations'][location] = \
                                    special_data['collision_analysis']['collision_locations'].get(location, 0) + 1
                            
                        elif incident_type == 'CONTACT_INCIDENT':
                            special_data['contact_incidents'].append(special_incident)
                            special_data['summary_statistics']['contact_incidents_count'] += 1
                        elif incident_type == 'PENALTY_DECISION':
                            special_data['penalty_incidents'].append(special_incident)
                            special_data['summary_statistics']['penalty_decisions'] += 1
                            
                            # 處罰決定詳細分析
                            special_data['collision_analysis']['collision_penalty_status']['penalty_imposed'] += 1
                            
                            # 分析處罰類型
                            if 'TIME PENALTY' in msg_text.upper():
                                special_data['collision_analysis']['penalty_breakdown']['time_penalties'].append({
                                    'driver': involved_drivers_info[0]['driver_code'] if involved_drivers_info else 'UNK',
                                    'lap': lap,
                                    'penalty': msg_text
                                })
                            elif 'POSITION' in msg_text.upper() and 'PENALTY' in msg_text.upper():
                                special_data['collision_analysis']['penalty_breakdown']['position_penalties'].append({
                                    'driver': involved_drivers_info[0]['driver_code'] if involved_drivers_info else 'UNK',
                                    'lap': lap,
                                    'penalty': msg_text
                                })
                            elif 'WARNING' in msg_text.upper():
                                special_data['collision_analysis']['penalty_breakdown']['warnings'].append({
                                    'driver': involved_drivers_info[0]['driver_code'] if involved_drivers_info else 'UNK',
                                    'lap': lap,
                                    'penalty': msg_text
                                })
                                special_data['collision_analysis']['collision_penalty_status']['warnings_issued'] += 1
                                
                        elif 'PENALTY' in incident_type:
                            special_data['penalty_incidents'].append(special_incident)
                        elif incident_type == 'INVESTIGATION_INCIDENT':
                            special_data['investigation_incidents'].append(special_incident)
                            special_data['collision_analysis']['collision_penalty_status']['investigation_stage'] += 1
                        elif incident_type == 'MEDICAL_INTERVENTION':
                            special_data['medical_interventions'].append(special_incident)
                        elif incident_type == 'DEBRIS_INCIDENT':
                            special_data['debris_incidents'].append(special_incident)
                        elif incident_type == 'WEATHER_INCIDENT':
                            special_data['weather_incidents'].append(special_incident)
                            special_data['summary_statistics']['weather_events'] += 1
                        
                        # 統計分析
                        special_data['summary_statistics']['total_special_incidents'] += 1
                        
                        if severity == 'CRITICAL':
                            special_data['summary_statistics']['critical_incidents'] += 1
                        elif severity == 'HIGH':
                            special_data['summary_statistics']['high_severity_incidents'] += 1
                        
                        if 'PENALTY' in incident_type:
                            special_data['summary_statistics']['penalty_decisions'] += 1
                        
                        if incident_type in ['RED_FLAG_INCIDENT', 'SAFETY_CAR_DEPLOYED', 'SAFETY_CAR_INCIDENT', 'VSC_DEPLOYED']:
                            special_data['summary_statistics']['race_interruptions'] += 1
                        
                        # 時間軸分析
                        special_data['chronological_timeline'].append({
                            'sequence': special_sequence,
                            'lap': lap,
                            'incident_type': incident_type,
                            'severity': severity,
                            'impact_score': impact_score
                        })
                        
                        # 車手處罰分析
                        for driver in involved_drivers_info:
                            driver_code = driver['driver_code']
                            if driver_code not in involved_drivers:
                                involved_drivers.append(driver_code)
                            
                            if driver_code not in special_data['driver_penalty_analysis']:
                                special_data['driver_penalty_analysis'][driver_code] = {
                                    'total_incidents': 0,
                                    'penalties_received': 0,
                                    'investigations': 0,
                                    'severity_breakdown': {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0, 'CRITICAL': 0},
                                    'incident_details': []
                                }
                            
                            special_data['driver_penalty_analysis'][driver_code]['total_incidents'] += 1
                            special_data['driver_penalty_analysis'][driver_code]['severity_breakdown'][severity] += 1
                            
                            if 'PENALTY' in incident_type:
                                special_data['driver_penalty_analysis'][driver_code]['penalties_received'] += 1
                            
                            if incident_type == 'INVESTIGATION_INCIDENT':
                                special_data['driver_penalty_analysis'][driver_code]['investigations'] += 1
                            
                            special_data['driver_penalty_analysis'][driver_code]['incident_details'].append({
                                'sequence': special_sequence,
                                'lap': lap,
                                'type': incident_type,
                                'severity': severity,
                                'impact_score': impact_score
                            })
                        
                        total_impact_score += impact_score
                        special_sequence += 1
                
                # 計算平均影響評分
                if special_data['summary_statistics']['total_special_incidents'] > 0:
                    special_data['summary_statistics']['average_impact_score'] = round(
                        total_impact_score / special_data['summary_statistics']['total_special_incidents'], 2
                    )
                
                special_data['summary_statistics']['involved_drivers_count'] = len(involved_drivers)
                
                # 完成碰撞分析統計
                if special_data['collision_analysis']['total_collisions'] > 0:
                    # 找出最易發生碰撞的車手
                    driver_collision_count = {}
                    for incident in special_data['collision_incidents'] + special_data['contact_incidents']:
                        for driver_code in incident['driver_codes']:
                            if driver_code != 'UNK':
                                driver_collision_count[driver_code] = driver_collision_count.get(driver_code, 0) + 1
                    
                    if driver_collision_count:
                        most_collision_driver = max(driver_collision_count.items(), key=lambda x: x[1])
                        special_data['collision_analysis']['most_collision_prone_driver'] = {
                            'driver': most_collision_driver[0],
                            'count': most_collision_driver[1]
                        }
        
        return special_data
        
    except Exception as e:
        print(f"[ERROR] 分析特殊事件報告時發生錯誤: {e}")
        return special_data

def extract_flags_detailed(message):
    """提取詳細旗幟資訊"""
    flags = []
    flag_patterns = {
        'RED FLAG': 'RED_FLAG',
        'SAFETY CAR': 'SAFETY_CAR',
        'YELLOW FLAG': 'YELLOW_FLAG',
        'CHEQUERED FLAG': 'CHEQUERED_FLAG'
    }
    
    for pattern, flag_type in flag_patterns.items():
        if pattern in message:
            flags.append(flag_type)
    
    return flags

def assess_safety_implications(message, incident_type):
    """評估安全影響"""
    implications = []
    
    if incident_type == 'RED_FLAG_INCIDENT':
        implications.append('RACE_SUSPENSION')
        implications.append('TRACK_CLEARANCE_REQUIRED')
    elif incident_type == 'MEDICAL_INTERVENTION':
        implications.append('MEDICAL_ATTENTION_REQUIRED')
        implications.append('SAFETY_PROTOCOLS_ACTIVATED')
    elif incident_type == 'SAFETY_CAR_INCIDENT':
        implications.append('SPEED_REDUCTION')
        implications.append('FIELD_NEUTRALIZATION')
    elif incident_type == 'MAJOR_ACCIDENT':
        implications.append('POTENTIAL_INJURY_RISK')
        implications.append('DEBRIS_HAZARD')
    
    return implications

def assess_race_impact(message, incident_type, lap, total_laps):
    """評估比賽影響"""
    impacts = []
    
    # 基於事件類型
    if incident_type == 'RED_FLAG_INCIDENT':
        impacts.append('RACE_STOPPAGE')
        impacts.append('GRID_RESTART_POSSIBLE')
    elif incident_type == 'SAFETY_CAR_INCIDENT':
        impacts.append('FIELD_COMPRESSION')
        impacts.append('STRATEGIC_OPPORTUNITY')
    elif 'PENALTY' in incident_type:
        impacts.append('POSITION_CHANGES')
        impacts.append('CHAMPIONSHIP_POINTS_IMPACT')
    
    # 基於發生時間
    if total_laps > 0:
        lap_percentage = lap / total_laps
        if lap_percentage > 0.8:
            impacts.append('LATE_RACE_DRAMA')
        elif lap_percentage < 0.2:
            impacts.append('EARLY_RACE_INCIDENT')
        else:
            impacts.append('MID_RACE_EVENT')
    
    return impacts

def display_penalty_summary(data):
    """顯示詳細的處罰項目清單"""
    print(f"\n⚖️ 處罰項目詳細清單 (Function 9):")
    
    # 收集所有處罰相關事件
    penalty_events = []
    served_penalties = []
    
    for incident in data['special_incidents']:
        message = incident['message'].upper()
        
        # 檢查是否為處罰決定
        if 'FIA STEWARDS' in message and any(penalty_word in message for penalty_word in ['PENALTY', 'REPRIMAND', 'WARNING']):
            if 'PENALTY SERVED' in message:
                served_penalties.append(incident)
            elif any(penalty_word in message for penalty_word in ['TIME PENALTY', 'POSITION PENALTY', 'DRIVE THROUGH', 'STOP AND GO']):
                penalty_events.append(incident)
    
    # 顯示處罰決定
    if penalty_events:
        penalty_table = PrettyTable()
        penalty_table.field_names = ["序號", "圈數", "車手", "處罰類型", "處罰原因", "詳細描述"]
        penalty_table.max_width["詳細描述"] = 50
        
        for idx, incident in enumerate(penalty_events, 1):
            # 提取車手信息
            import re
            driver_match = re.search(r'CAR\s+\d+\s*\(([A-Z]{3})\)', incident['message'])
            driver = driver_match.group(1) if driver_match else "未知"
            
            # 提取處罰類型
            penalty_type = "未知"
            if 'TIME PENALTY' in incident['message'].upper():
                time_match = re.search(r'(\d+)\s*SECOND[S]?\s*TIME\s*PENALTY', incident['message'].upper())
                penalty_type = f"{time_match.group(1)}秒時間罰" if time_match else "時間處罰"
            elif 'POSITION PENALTY' in incident['message'].upper():
                penalty_type = "位置處罰"
            elif 'DRIVE THROUGH' in incident['message'].upper():
                penalty_type = "通過維修道"
            elif 'STOP AND GO' in incident['message'].upper():
                penalty_type = "停車再出發"
            
            # 提取處罰原因
            reason = "未知"
            if 'SAFETY CAR INFRINGEMENT' in incident['message'].upper():
                reason = "安全車違規"
            elif 'CAUSING A COLLISION' in incident['message'].upper():
                reason = "造成碰撞"
            elif 'TRACK LIMITS' in incident['message'].upper():
                reason = "超出賽道界限"
            elif 'DANGEROUS DRIVING' in incident['message'].upper():
                reason = "危險駕駛"
            elif 'GAINING ADVANTAGE' in incident['message'].upper():
                reason = "獲得不當優勢"
            
            penalty_table.add_row([
                idx,
                f"第{incident['lap']}圈",
                driver,
                penalty_type,
                reason,
                incident['message'][:50] + "..." if len(incident['message']) > 50 else incident['message']
            ])
        
        print(f"\n🚨 處罰決定清單 ({len(penalty_events)}項):")
        print(penalty_table)
    else:
        print("\n✅ 本場比賽無車手被處罰")
    
    # 顯示處罰執行情況
    if served_penalties:
        served_table = PrettyTable()
        served_table.field_names = ["序號", "圈數", "車手", "已執行處罰", "詳細描述"]
        served_table.max_width["詳細描述"] = 60
        
        for idx, incident in enumerate(served_penalties, 1):
            # 提取車手信息
            import re
            driver_match = re.search(r'CAR\s+\d+\s*\(([A-Z]{3})\)', incident['message'])
            driver = driver_match.group(1) if driver_match else "未知"
            
            # 提取處罰類型
            penalty_type = "未知"
            if 'TIME PENALTY' in incident['message'].upper():
                time_match = re.search(r'(\d+)\s*SECOND[S]?\s*TIME\s*PENALTY', incident['message'].upper())
                penalty_type = f"{time_match.group(1)}秒時間罰已執行" if time_match else "時間處罰已執行"
            
            served_table.add_row([
                idx,
                f"第{incident['lap']}圈",
                driver,
                penalty_type,
                incident['message'][:60] + "..." if len(incident['message']) > 60 else incident['message']
            ])
        
        print(f"\n✅ 處罰執行確認 ({len(served_penalties)}項):")
        print(served_table)
    
    # 統計摘要
    print(f"\n📊 處罰統計摘要:")
    summary_table = PrettyTable()
    summary_table.field_names = ["統計項目", "數量", "說明"]
    summary_table.add_row(["處罰決定總數", len(penalty_events), "FIA 判罰的總數"])
    summary_table.add_row(["已執行處罰數", len(served_penalties), "確認已執行的處罰"])
    
    # 統計各種處罰類型
    time_penalties = sum(1 for p in penalty_events if 'TIME PENALTY' in p['message'].upper())
    position_penalties = sum(1 for p in penalty_events if 'POSITION PENALTY' in p['message'].upper())
    other_penalties = len(penalty_events) - time_penalties - position_penalties
    
    summary_table.add_row(["時間處罰數", time_penalties, "秒數處罰"])
    summary_table.add_row(["位置處罰數", position_penalties, "發車位置處罰"])
    summary_table.add_row(["其他處罰數", other_penalties, "其他類型處罰"])
    print(summary_table)

def display_special_incidents_report(data):
    """顯示特殊事件報告"""
    print(f"\n🚨 特殊事件報告 (Function 9):")
    
    total_special = data['summary_statistics']['total_special_incidents']
    
    if total_special == 0:
        print("✅ 本場比賽未發現特殊事件！")
        return
    
    # 特殊事件統計總覽
    overview_table = PrettyTable()
    overview_table.field_names = ["統計項目", "數值", "說明"]
    
    stats = data['summary_statistics']
    overview_table.add_row(["特殊事件總數", stats['total_special_incidents'], "需要特別關注的事件"])
    overview_table.add_row(["嚴重事件數", stats['critical_incidents'], "紅旗或醫療介入事件"])
    overview_table.add_row(["高影響事件數", stats['high_severity_incidents'], "重大事故或安全車事件"])
    overview_table.add_row(["安全車部署次數", stats['safety_car_deployments'], "實體安全車出動次數"])
    overview_table.add_row(["VSC部署次數", stats['vsc_deployments'], "虛擬安全車啟用次數"])
    overview_table.add_row(["碰撞事件數", stats['collision_count'], "重大碰撞事故"])
    overview_table.add_row(["接觸事件數", stats['contact_incidents_count'], "車輛接觸事件"])
    overview_table.add_row(["天氣事件數", stats['weather_events'], "雨天或天氣相關事件"])
    overview_table.add_row(["處罰決定數", stats['penalty_decisions'], "正式處罰決定"])
    overview_table.add_row(["比賽中斷次數", stats['race_interruptions'], "紅旗、安全車或VSC介入"])
    overview_table.add_row(["涉及車手數", stats['involved_drivers_count'], "參與特殊事件的車手"])
    overview_table.add_row(["平均影響評分", f"{stats['average_impact_score']}/100", "事件影響程度評分"])
    
    print("\n📊 特殊事件統計總覽:")
    print(overview_table)
    
    # 紅旗事件詳細報告
    if data['red_flag_incidents']:
        red_flag_table = PrettyTable()
        red_flag_table.field_names = ["序號", "圈數", "時間", "影響評分", "安全影響", "事件描述"]
        red_flag_table.max_width["事件描述"] = 50
        red_flag_table.max_width["安全影響"] = 30
        
        for incident in data['red_flag_incidents']:
            safety_str = ", ".join(incident['safety_implications'])
            description = incident['message'][:50] + "..." if len(incident['message']) > 50 else incident['message']
            
            red_flag_table.add_row([
                incident['special_sequence'],
                f"第{incident['lap']}圈",
                incident['time'],
                f"{incident['impact_score']}/100",
                safety_str,
                description
            ])
        
        print(f"\n🚩 紅旗事件詳細報告 ({len(data['red_flag_incidents'])}件):")
        print(red_flag_table)
    
    # 安全車時間軸報告
    if data['safety_car_timeline']:
        safety_car_table = PrettyTable()
        safety_car_table.field_names = ["序號", "圈數", "時間", "動作", "影響評分", "狀態"]
        
        for sc_event in data['safety_car_timeline']:
            action = sc_event['action']
            action_display = {
                'SAFETY_CAR_DEPLOYED': '🟡 安全車出動',
                'SAFETY_CAR_WITHDRAWN': '🟢 安全車撤回',
                'SAFETY_CAR_INCIDENT': '🟡 安全車事件',
                'VSC_DEPLOYED': '🟠 VSC啟用',
                'VSC_ENDING': '🟢 VSC結束'
            }.get(action, action)
            
            status = "進行中" if "DEPLOYED" in action or "INCIDENT" in action else "結束"
            
            safety_car_table.add_row([
                sc_event['sequence'],
                f"第{sc_event['lap']}圈",
                sc_event['time'],
                action_display,
                f"{sc_event['impact_score']}/100",
                status
            ])
        
        print(f"\n🚦 安全車時間軸報告 ({len(data['safety_car_timeline'])}項):")
        print(safety_car_table)
    
    # 碰撞事件分析報告
    collision_data = data['collision_analysis']
    if collision_data['total_collisions'] > 0:
        collision_table = PrettyTable()
        collision_table.field_names = ["序號", "圈數", "時間", "涉及車手", "嚴重程度", "位置", "事件描述"]
        collision_table.max_width["事件描述"] = 40
        
        for idx, incident in enumerate(data['collision_incidents'], 1):
            drivers_str = ", ".join(incident['driver_codes']) if incident['driver_codes'] else "N/A"
            description = incident['message'][:40] + "..." if len(incident['message']) > 40 else incident['message']
            
            # 提取位置信息
            location = "未知"
            location_match = re.search(r'TURN\s+(\d+)', incident['message'].upper())
            if location_match:
                location = f"彎角{location_match.group(1)}"
            elif 'PIT' in incident['message'].upper():
                location = "維修站"
            
            collision_table.add_row([
                idx,
                f"第{incident['lap']}圈",
                incident['time'],
                drivers_str,
                incident['severity'],
                location,
                description
            ])
        
        print(f"\n💥 碰撞事件分析報告 ({collision_data['total_collisions']}件):")
        print(collision_table)
        
        # 碰撞統計分析
        collision_stats_table = PrettyTable()
        collision_stats_table.field_names = ["分析項目", "結果", "說明"]
        
        collision_stats_table.add_row(["總碰撞次數", collision_data['total_collisions'], "重大碰撞事故總數"])
        
        if collision_data['collision_locations']:
            most_dangerous_corner = max(collision_data['collision_locations'].items(), key=lambda x: x[1])
            collision_stats_table.add_row(["最危險彎角", f"{most_dangerous_corner[0]} ({most_dangerous_corner[1]}次)", "發生碰撞最多的位置"])
        
        if collision_data['most_collision_prone_driver']:
            prone_driver = collision_data['most_collision_prone_driver']
            collision_stats_table.add_row(["最易碰撞車手", f"{prone_driver['driver']} ({prone_driver['count']}次)", "參與碰撞事件最多的車手"])
        
        severity_dist = collision_data['collision_severity_distribution']
        severity_str = f"高:{severity_dist['HIGH']}, 中:{severity_dist['MEDIUM']}, 低:{severity_dist['LOW']}"
        collision_stats_table.add_row(["嚴重程度分佈", severity_str, "碰撞事件嚴重程度統計"])
        
        # 處罰狀態統計
        penalty_status = collision_data['collision_penalty_status']
        status_str = f"已處罰:{penalty_status['penalty_imposed']}, 調查中:{penalty_status['investigation_stage']}, 警告:{penalty_status['warnings_issued']}"
        collision_stats_table.add_row(["處罰狀態分佈", status_str, "碰撞事件處罰結果統計"])
        
        print(f"\n📊 碰撞統計分析:")
        print(collision_stats_table)
        
        # 彎角詳細分析
        if collision_data['corner_incident_details']:
            corner_details_table = PrettyTable()
            corner_details_table.field_names = ["彎角", "事件數", "涉及車手", "主要車手", "風險等級"]
            
            for corner, details in collision_data['corner_incident_details'].items():
                drivers_list = list(details['drivers_involved'])
                drivers_str = ", ".join(drivers_list[:3])  # 顯示前3個車手
                if len(drivers_list) > 3:
                    drivers_str += f" (+{len(drivers_list)-3})"
                
                # 找出該彎角最常涉及事故的車手
                driver_count = {}
                for incident in details['incidents']:
                    for driver in incident['drivers']:
                        driver_count[driver] = driver_count.get(driver, 0) + 1
                
                main_driver = max(driver_count.items(), key=lambda x: x[1])[0] if driver_count else "N/A"
                
                # 風險等級評估
                incident_count = details['total_incidents']
                if incident_count >= 3:
                    risk_level = "🔴 高風險"
                elif incident_count >= 2:
                    risk_level = "🟡 中風險"
                else:
                    risk_level = "🟢 低風險"
                
                corner_details_table.add_row([
                    corner,
                    incident_count,
                    drivers_str,
                    f"{main_driver} ({driver_count.get(main_driver, 0)}次)",
                    risk_level
                ])
            
            print(f"\n🏁 彎角事件詳細分析:")
            print(corner_details_table)
        
        # 處罰詳細分析
        penalty_breakdown = collision_data['penalty_breakdown']
        if any(penalty_breakdown.values()):
            penalty_details_table = PrettyTable()
            penalty_details_table.field_names = ["處罰類型", "數量", "車手詳情"]
            
            if penalty_breakdown['time_penalties']:
                time_penalties_str = "; ".join([f"{p['driver']}(第{p['lap']}圈)" for p in penalty_breakdown['time_penalties']])
                penalty_details_table.add_row(["⏱️ 時間處罰", len(penalty_breakdown['time_penalties']), time_penalties_str])
            
            if penalty_breakdown['position_penalties']:
                pos_penalties_str = "; ".join([f"{p['driver']}(第{p['lap']}圈)" for p in penalty_breakdown['position_penalties']])
                penalty_details_table.add_row(["📍 位置處罰", len(penalty_breakdown['position_penalties']), pos_penalties_str])
            
            if penalty_breakdown['warnings']:
                warnings_str = "; ".join([f"{w['driver']}(第{w['lap']}圈)" for w in penalty_breakdown['warnings']])
                penalty_details_table.add_row(["⚠️ 警告", len(penalty_breakdown['warnings']), warnings_str])
            
            print(f"\n⚖️ 處罰詳細分析:")
            print(penalty_details_table)
    
    # 接觸事件報告
    if data['contact_incidents']:
        contact_table = PrettyTable()
        contact_table.field_names = ["序號", "圈數", "時間", "涉及車手", "嚴重程度", "位置", "事件描述"]
        contact_table.max_width["事件描述"] = 40
        
        for idx, incident in enumerate(data['contact_incidents'], 1):
            drivers_str = ", ".join(incident['driver_codes']) if incident['driver_codes'] else "N/A"
            description = incident['message'][:40] + "..." if len(incident['message']) > 40 else incident['message']
            
            # 提取位置信息
            location = "未知"
            location_match = re.search(r'TURN\s+(\d+)', incident['message'].upper())
            if location_match:
                location = f"彎角{location_match.group(1)}"
            elif 'PIT' in incident['message'].upper():
                location = "維修站區域"
            
            contact_table.add_row([
                idx,
                f"第{incident['lap']}圈",
                incident['time'],
                drivers_str,
                incident['severity'],
                location,
                description
            ])
        
        print(f"\n🤝 接觸事件報告 ({len(data['contact_incidents'])}件):")
        print(contact_table)
    
    # VSC事件報告
    if data['vsc_incidents']:
        vsc_table = PrettyTable()
        vsc_table.field_names = ["序號", "圈數", "時間", "VSC狀態", "影響評分", "事件描述"]
        vsc_table.max_width["事件描述"] = 45
        
        for incident in data['vsc_incidents']:
            vsc_status = {
                'VSC_DEPLOYED': '🟠 VSC啟用',
                'VSC_ENDING': '🟢 VSC結束',
                'VSC_INCIDENT': '🟠 VSC事件'
            }.get(incident['incident_type'], incident['incident_type'])
            
            description = incident['message'][:45] + "..." if len(incident['message']) > 45 else incident['message']
            
            vsc_table.add_row([
                incident['special_sequence'],
                f"第{incident['lap']}圈",
                incident['time'],
                vsc_status,
                f"{incident['impact_score']}/100",
                description
            ])
        
        print(f"\n🟠 VSC事件報告 ({len(data['vsc_incidents'])}件):")
        print(vsc_table)
    
    # 天氣事件報告
    if data['weather_incidents']:
        weather_table = PrettyTable()
        weather_table.field_names = ["序號", "圈數", "時間", "天氣類型", "影響評分", "事件描述"]
        weather_table.max_width["事件描述"] = 45
        
        for incident in data['weather_incidents']:
            weather_type = "☔ 雨天" if "RAIN" in incident['message'].upper() else "🌦️ 天氣"
            description = incident['message'][:45] + "..." if len(incident['message']) > 45 else incident['message']
            
            weather_table.add_row([
                incident['special_sequence'],
                f"第{incident['lap']}圈",
                incident['time'],
                weather_type,
                f"{incident['impact_score']}/100",
                description
            ])
        
        print(f"\n🌦️ 天氣事件報告 ({len(data['weather_incidents'])}件):")
        print(weather_table)
    
    # 重大事故報告（包含所有高影響事故）
    if data['major_accidents']:
        accident_table = PrettyTable()
        accident_table.field_names = ["序號", "圈數", "時間", "事故類型", "涉及車手", "嚴重程度", "影響評分", "事件描述"]
        accident_table.max_width["事件描述"] = 35
        
        for incident in data['major_accidents']:
            drivers_str = ", ".join(incident['driver_codes']) if incident['driver_codes'] else "N/A"
            description = incident['message'][:35] + "..." if len(incident['message']) > 35 else incident['message']
            
            incident_type_display = {
                'MAJOR_COLLISION': '💥 重大碰撞',
                'CONTACT_INCIDENT': '🤝 車輛接觸',
                'DEBRIS_INCIDENT': '🗂️ 賽道異物',
                'TRACK_EXCURSION': '🏃 賽道偏離'
            }.get(incident['incident_type'], incident['incident_type'])
            
            accident_table.add_row([
                incident['special_sequence'],
                f"第{incident['lap']}圈",
                incident['time'],
                incident_type_display,
                drivers_str,
                incident['severity'],
                f"{incident['impact_score']}/100",
                description
            ])
        
        print(f"\n💥 重大事故報告 ({len(data['major_accidents'])}件):")
        print(accident_table)
    
    # 處罰決定報告
    if data['penalty_incidents']:
        penalty_table = PrettyTable()
        penalty_table.field_names = ["序號", "圈數", "車手", "處罰類型", "處罰值", "原因", "事件描述"]
        penalty_table.max_width["事件描述"] = 35
        
        for incident in data['penalty_incidents']:
            drivers_str = ", ".join(incident['driver_codes']) if incident['driver_codes'] else "N/A"
            penalty_type = incident['penalty_details']['penalty_type'] if incident['penalty_details'] else "未知"
            penalty_value = incident['penalty_details']['penalty_value'] if incident['penalty_details'] else "N/A"
            reason = incident['penalty_details']['reason'] if incident['penalty_details'] else "未知"
            description = incident['message'][:35] + "..." if len(incident['message']) > 35 else incident['message']
            
            penalty_table.add_row([
                incident['special_sequence'],
                f"第{incident['lap']}圈",
                drivers_str,
                penalty_type,
                penalty_value,
                reason,
                description
            ])
        
        print(f"\n⚖️ 處罰決定報告 ({len(data['penalty_incidents'])}件):")
        print(penalty_table)
    
    # 車手特殊事件參與分析
    if data['driver_penalty_analysis']:
        driver_analysis_table = PrettyTable()
        driver_analysis_table.field_names = ["車手", "總事件數", "接受處罰", "調查次數", "最高嚴重程度", "總影響評分"]
        
        for driver, analysis in data['driver_penalty_analysis'].items():
            total_incidents = analysis['total_incidents']
            penalties = analysis['penalties_received']
            investigations = analysis['investigations']
            
            # 找出最高嚴重程度
            severity_order = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
            max_severity = 'LOW'
            for severity in reversed(severity_order):
                if analysis['severity_breakdown'][severity] > 0:
                    max_severity = severity
                    break
            
            # 計算總影響評分
            total_impact = sum(detail['impact_score'] for detail in analysis['incident_details'])
            
            driver_analysis_table.add_row([
                driver,
                total_incidents,
                penalties,
                investigations,
                max_severity,
                f"{total_impact}/100"
            ])
        
        print(f"\n🏎️ 車手特殊事件參與分析:")
        print(driver_analysis_table)

def save_json_results(data, session_info):
    """保存分析結果為 JSON 檔案"""
    os.makedirs("json", exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    event_name = session_info.get('event_name', 'Unknown').replace(' ', '_')
    filename = f"special_incident_reports_{session_info.get('year', 2024)}_{event_name}_{timestamp}.json"
    filepath = os.path.join("json", filename)
    
    json_result = {
        "function_id": 9,
        "function_name": "Special Incident Reports",
        "analysis_type": "special_incident_reports",
        "session_info": session_info,
        "timestamp": datetime.now().isoformat(),
        "data": data
    }
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(json_result, f, ensure_ascii=False, indent=2)
        
        abs_filepath = os.path.abspath(filepath)
        print(f"💾 JSON結果已保存到: file:///{abs_filepath}")
        return True
    except Exception as e:
        print(f"❌ JSON保存失敗: {e}")
        return False

def report_analysis_results(data, analysis_type="特殊事件報告"):
    """報告分析結果狀態"""
    if not data:
        print(f"❌ {analysis_type}失敗：無可用數據")
        return False
    
    total_special = data.get('summary_statistics', {}).get('total_special_incidents', 0)
    critical_incidents = data.get('summary_statistics', {}).get('critical_incidents', 0)
    penalty_decisions = data.get('summary_statistics', {}).get('penalty_decisions', 0)
    
    print(f"📊 {analysis_type}結果摘要：")
    print(f"   • 特殊事件總數: {total_special}")
    print(f"   • 嚴重事件數: {critical_incidents}")
    print(f"   • 處罰決定數: {penalty_decisions}")
    print(f"   • 數據完整性: {'✅ 良好' if total_special >= 0 else '❌ 異常'}")
    
    print(f"✅ {analysis_type}分析完成！")
    return True

def run_special_incident_reports(data_loader, year=None, race=None, session='R'):
    """執行特殊事件報告分析 - Function 9"""
    print("🚀 開始執行特殊事件報告分析...")
    
    # 1. 獲取賽事資訊
    session_info = {
        "event_name": race or "Unknown",
        "circuit_name": "Unknown",
        "session_type": session,
        "year": year or 2024
    }
    
    if hasattr(data_loader, 'session') and data_loader.session is not None:
        session_info.update({
            "event_name": getattr(data_loader.session, 'event', {}).get('EventName', race or 'Unknown'),
            "circuit_name": getattr(data_loader.session, 'event', {}).get('Location', 'Unknown'),
            "session_type": getattr(data_loader.session, 'session_info', {}).get('Type', session),
            "year": getattr(data_loader.session, 'event', {}).get('year', year or 2024)
        })
    
    # 2. 檢查快取
    cache_key = generate_cache_key(session_info)
    cached_data = check_cache(cache_key)
    
    if cached_data:
        print("📦 使用緩存數據")
        special_data = cached_data
    else:
        print("🔄 重新計算 - 開始數據分析...")
        
        # 3. 執行分析
        if hasattr(data_loader, 'session') and data_loader.session is not None:
            special_data = analyze_special_incidents(data_loader.session)
        else:
            print("❌ 無法獲取賽事數據")
            return None
        
        if special_data:
            # 4. 保存快取
            if save_cache(special_data, cache_key):
                print("💾 分析結果已緩存")
    
    # 5. 結果驗證和反饋
    if not report_analysis_results(special_data, "特殊事件報告"):
        return None
    
    # 6. 顯示分析結果表格
    display_special_incidents_report(special_data)
    
    # 7. 顯示詳細處罰清單
    display_penalty_summary(special_data)
    
    # 8. 保存 JSON 結果
    save_json_results(special_data, session_info)
    
    print("\n✅ 特殊事件報告分析完成！")
    return special_data

def run_special_incident_reports_json(data_loader, dynamic_team_mapping=None, f1_analysis_instance=None, enable_debug=False, show_detailed_output=True):
    """執行特殊事件報告分析並返回JSON格式結果 - API專用版本
    
    Args:
        data_loader: 數據載入器
        dynamic_team_mapping: 動態車隊映射
        f1_analysis_instance: F1分析實例
        enable_debug: 是否啟用調試模式
        show_detailed_output: 是否顯示詳細輸出（即使使用緩存也顯示完整表格）
    """
    if enable_debug:
        print(f"\n[NEW_MODULE] 執行特殊事件報告分析模組 (JSON輸出版)...")
    
    try:
        # 獲取賽事資訊
        session_info = {}
        if hasattr(data_loader, 'session') and data_loader.session is not None:
            session_info = {
                "event_name": getattr(data_loader.session, 'event', {}).get('EventName', 'Unknown'),
                "circuit_name": getattr(data_loader.session, 'event', {}).get('Location', 'Unknown'),
                "session_type": getattr(data_loader.session, 'session_info', {}).get('Type', 'Unknown'),
                "year": getattr(data_loader.session, 'event', {}).get('year', 2024)
            }
        
        # Function 15 標準 - 檢查緩存
        cache_key = generate_cache_key(session_info)
        cached_data = check_cache(cache_key)
        cache_used = cached_data is not None
        
        if cached_data and not show_detailed_output:
            if enable_debug:
                print("📦 使用緩存數據")
            return {
                "success": True,
                "message": "成功執行 特殊事件報告分析 (緩存)",
                "data": {
                    "function_id": 9,
                    "function_name": "Special Incident Reports",
                    "analysis_type": "special_incident_reports",
                    "session_info": session_info,
                    "special_incidents_analysis": cached_data
                },
                "cache_used": True,
                "cache_key": cache_key,
                "timestamp": datetime.now().isoformat()
            }
        elif cached_data and show_detailed_output:
            if enable_debug:
                print("📦 使用緩存數據 + 📊 顯示詳細分析結果")
            # 顯示詳細輸出
            _display_cached_detailed_output(cached_data, session_info)
            return {
                "success": True,
                "message": "成功執行 特殊事件報告分析 (緩存+詳細)",
                "data": {
                    "function_id": 9,
                    "function_name": "Special Incident Reports",
                    "analysis_type": "special_incident_reports",
                    "session_info": session_info,
                    "special_incidents_analysis": cached_data
                },
                "cache_used": True,
                "cache_key": cache_key,
                "timestamp": datetime.now().isoformat()
            }
        else:
            if enable_debug:
                print("🔄 重新計算 - 開始數據分析...")
        
        # 執行分析
        special_data = run_special_incident_reports(
            data_loader, 
            year=session_info.get('year'),
            race=session_info.get('event_name'),
            session=session_info.get('session_type', 'R')
        )
        
        # 保存緩存
        if special_data:
            save_cache(special_data, cache_key)
            if enable_debug:
                print("💾 分析結果已緩存")
        
        if special_data:
            return {
                "success": True,
                "message": "成功執行 特殊事件報告分析",
                "data": {
                    "function_id": 9,
                    "function_name": "Special Incident Reports",
                    "analysis_type": "special_incident_reports",
                    "session_info": session_info,
                    "special_incidents_analysis": special_data
                },
                "cache_used": cache_used,
                "cache_key": cache_key,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "message": "特殊事件報告分析執行失敗 - 無可用數據",
                "data": None,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        if enable_debug:
            print(f"[ERROR] 特殊事件報告分析模組執行錯誤: {e}")
            import traceback
            traceback.print_exc()
        return {
            "success": False,
            "message": f"特殊事件報告分析執行錯誤: {str(e)}",
            "data": None,
            "timestamp": datetime.now().isoformat()
        }

def _display_cached_detailed_output(special_data, session_info):
    """顯示緩存數據的詳細輸出 - Function 15 標準
    
    Args:
        special_data: 特殊事件報告數據
        session_info: 賽事基本信息
    """
    print("\n📊 詳細特殊事件報告 (緩存數據)")
    print("=" * 80)
    
    if not special_data:
        print("❌ 無特殊事件數據可顯示")
        return
    
    # 處理不同的數據格式
    if isinstance(special_data, list):
        incidents = special_data
    elif isinstance(special_data, dict) and 'incidents' in special_data:
        incidents = special_data['incidents']
    else:
        print("❌ 數據格式無法識別")
        return
    
    total_incidents = len(incidents)
    print(f"🚨 總特殊事件數量: {total_incidents}")
    
    # 詳細特殊事件表格
    from prettytable import PrettyTable
    incidents_table = PrettyTable()
    incidents_table.field_names = [
        "序號", "嚴重程度", "事件類型", "車手", "圈數", "描述"
    ]
    
    # 顯示前15個特殊事件
    for i, incident in enumerate(incidents[:15], 1):
        severity = incident.get('severity', 'Unknown')[:10]
        event_type = incident.get('type', 'Unknown')[:15]
        driver = incident.get('driver', 'Unknown')[:10]
        lap = str(incident.get('lap', 'N/A'))
        description = incident.get('description', 'No description')[:25]
        
        incidents_table.add_row([
            i, severity, event_type, driver, lap, description
        ])
    
    print(incidents_table)
    
    # 統計摘要
    print(f"\n📈 統計摘要:")
    print(f"   • 顯示事件數: {min(15, total_incidents)}")
    print(f"   • 總特殊事件數: {total_incidents}")
    if total_incidents > 15:
        print(f"   • 隱藏事件數: {total_incidents - 15}")
    
    # 嚴重程度統計
    if incidents:
        severity_counts = {}
        for incident in incidents:
            severity = incident.get('severity', 'Unknown')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        print(f"\n🚨 嚴重程度分佈:")
        for severity, count in severity_counts.items():
            print(f"   • {severity}: {count} 件")
    
    print("\n💾 數據來源: 緩存檔案")
    print(f"📅 賽事: {session_info.get('year', 'Unknown')} {session_info.get('event_name', 'Unknown')}")
    print(f"🏁 賽段: {session_info.get('session_type', 'Unknown')}")
    print("✅ 緩存數據詳細輸出完成")

if __name__ == "__main__":
    print("F1 特殊事件報告模組 - 獨立測試模式")
    print("此模組需要配合 F1 數據載入器使用")


def _display_cached_detailed_output(special_data, session_info):
    """顯示緩存數據的詳細輸出 - Function 15 標準
    
    Args:
        special_data: 特殊事件報告數據
        session_info: 賽事基本信息
    """
    print("\n📊 詳細特殊事件報告 (緩存數據)")
    print("=" * 80)
    
    if not special_data:
        print("❌ 無特殊事件數據")
        return
    
    total_incidents = len(special_data) if isinstance(special_data, list) else 0
    print(f"🚨 特殊事件總數: {total_incidents}")
    
    if total_incidents > 0:
        # 詳細事件表格
        detailed_table = PrettyTable()
        detailed_table.field_names = [
            "事件#", "類型", "車手", "圈數", "時間", 
            "嚴重程度", "描述", "影響"
        ]
        
        # 顯示前15個事件
        display_count = min(15, total_incidents)
        for i, incident in enumerate(special_data[:display_count], 1):
            if isinstance(incident, dict):
                detailed_table.add_row([
                    i,
                    incident.get('type', 'Unknown')[:10],
                    incident.get('driver', 'Unknown')[:8],
                    incident.get('lap', 'N/A'),
                    incident.get('time', 'N/A')[:12],
                    incident.get('severity', 'Unknown')[:8],
                    incident.get('description', '')[:20],
                    incident.get('impact', 'N/A')[:10]
                ])
            else:
                detailed_table.add_row([
                    i, "數據格式錯誤", "", "", "", "", "", ""
                ])
        
        print(detailed_table)
        
        if total_incidents > 15:
            print(f"   ... 還有 {total_incidents - 15} 個事件 (已儲存至JSON檔案)")
    
    # 統計摘要
    print("\n📈 統計摘要:")
    print(f"   • 特殊事件總數: {total_incidents}")
    print(f"   • 顯示預覽數量: {min(15, total_incidents)}")
    
    print("\n💾 數據來源: 緩存檔案")
    print(f"📅 賽事: {session_info.get('year', 'Unknown')} {session_info.get('event_name', 'Unknown')}")
    print(f"🏁 賽段: {session_info.get('session_type', 'Unknown')}")
    print("✅ 緩存數據詳細輸出完成")
