#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F1 關鍵事件摘要模組 - Function 10
Key Events Summary Module - Following Core Development Standards
專注於比賽轉捩點、關鍵決策時刻和影響比賽結果的重要事件分析
"""

import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

import os
import json
import pickle
import pandas as pd
from datetime import datetime
from prettytable import PrettyTable

def generate_cache_key(session_info):
    """生成快取鍵值"""
    return f"key_events_summary_{session_info.get('year', 2025)}_{session_info.get('event_name', 'Unknown')}_{session_info.get('session_type', 'R')}"

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

def classify_key_event(message, lap, total_laps):
    """分類關鍵事件"""
    message = message.upper()
    
    # 比賽關鍵時刻
    lap_percentage = lap / total_laps if total_laps > 0 else 0
    
    if 'CHEQUERED FLAG' in message:
        return 'RACE_FINISH'
    elif 'RED FLAG' in message:
        return 'RACE_SUSPENSION'
    elif 'SAFETY CAR' in message:
        if lap_percentage > 0.8:
            return 'LATE_SAFETY_CAR'
        else:
            return 'STRATEGIC_SAFETY_CAR'
    elif any(word in message for word in ['COLLISION', 'CRASH', 'ACCIDENT']):
        if lap_percentage > 0.8:
            return 'LATE_RACE_INCIDENT'
        else:
            return 'RACE_CHANGING_INCIDENT'
    elif 'PENALTY' in message and any(word in message for word in ['DISQUALIFIED', 'POSITION']):
        return 'CHAMPIONSHIP_PENALTY'
    elif 'UNDER INVESTIGATION' in message and any(word in message for word in ['CONTACT', 'INCIDENT']):
        return 'DECISIVE_INVESTIGATION'
    elif 'MEDICAL CAR' in message:
        return 'SAFETY_INTERVENTION'
    elif 'PIT' in message and 'PENALTY' in message:
        return 'STRATEGIC_PENALTY'
    elif any(word in message for word in ['OVERTAKE', 'POSITION CHANGE']):
        if lap_percentage > 0.8:
            return 'DECISIVE_OVERTAKE'
        else:
            return 'STRATEGIC_MOVE'
    else:
        return None

def assess_championship_impact(message, incident_type, lap, total_laps):
    """評估對冠軍爭奪的影響"""
    impact_level = 'LOW'
    impact_factors = []
    
    # 基於事件類型
    if incident_type in ['RACE_SUSPENSION', 'CHAMPIONSHIP_PENALTY', 'LATE_RACE_INCIDENT']:
        impact_level = 'CRITICAL'
        impact_factors.append('POSITION_CHANGES')
    elif incident_type in ['LATE_SAFETY_CAR', 'SAFETY_INTERVENTION', 'DECISIVE_INVESTIGATION']:
        impact_level = 'HIGH'
        impact_factors.append('STRATEGIC_IMPLICATIONS')
    elif incident_type in ['STRATEGIC_SAFETY_CAR', 'RACE_CHANGING_INCIDENT']:
        impact_level = 'MEDIUM'
        impact_factors.append('TACTICAL_OPPORTUNITY')
    
    # 基於比賽時間點
    lap_percentage = lap / total_laps if total_laps > 0 else 0
    if lap_percentage > 0.9:
        if impact_level == 'HIGH':
            impact_level = 'CRITICAL'
        elif impact_level == 'MEDIUM':
            impact_level = 'HIGH'
        impact_factors.append('LATE_RACE_DRAMA')
    elif lap_percentage > 0.7:
        impact_factors.append('CRUCIAL_PHASE')
    
    # 基於訊息內容
    message_upper = message.upper()
    if any(word in message_upper for word in ['CHAMPIONSHIP', 'TITLE', 'LEADER']):
        impact_factors.append('TITLE_IMPLICATIONS')
    
    if any(word in message_upper for word in ['POINTS', 'POSITION']):
        impact_factors.append('POINTS_IMPACT')
    
    return impact_level, impact_factors

def calculate_turning_point_score(incident_type, lap, total_laps, involved_drivers_count):
    """計算轉捩點評分 (0-100)"""
    base_scores = {
        'RACE_FINISH': 100,
        'RACE_SUSPENSION': 95,
        'LATE_SAFETY_CAR': 90,
        'LATE_RACE_INCIDENT': 85,
        'CHAMPIONSHIP_PENALTY': 80,
        'SAFETY_INTERVENTION': 75,
        'DECISIVE_INVESTIGATION': 70,
        'STRATEGIC_SAFETY_CAR': 65,
        'RACE_CHANGING_INCIDENT': 60,
        'STRATEGIC_PENALTY': 50,
        'DECISIVE_OVERTAKE': 45,
        'STRATEGIC_MOVE': 30
    }
    
    base_score = base_scores.get(incident_type, 20)
    
    # 根據比賽階段調整
    if total_laps > 0:
        lap_percentage = lap / total_laps
        if lap_percentage > 0.9:  # 最後10%
            base_score += 15
        elif lap_percentage > 0.8:  # 最後20%
            base_score += 10
        elif lap_percentage > 0.7:  # 最後30%
            base_score += 5
    
    # 根據涉及車手數量調整
    if involved_drivers_count > 2:
        base_score += 10
    elif involved_drivers_count > 1:
        base_score += 5
    
    return min(100, base_score)

def analyze_strategic_window(lap, total_laps):
    """分析戰略窗口"""
    if total_laps == 0:
        return 'UNKNOWN'
    
    lap_percentage = lap / total_laps
    
    if lap_percentage <= 0.2:
        return 'RACE_START'
    elif lap_percentage <= 0.4:
        return 'EARLY_STRATEGY'
    elif lap_percentage <= 0.6:
        return 'MID_RACE_DECISIONS'
    elif lap_percentage <= 0.8:
        return 'CRITICAL_PHASE'
    else:
        return 'ENDGAME'

def extract_strategic_elements(message):
    """提取戰略要素"""
    elements = []
    message_upper = message.upper()
    
    if any(word in message_upper for word in ['PIT', 'STOP']):
        elements.append('PIT_STRATEGY')
    
    if any(word in message_upper for word in ['TYRE', 'TIRE']):
        elements.append('TYRE_STRATEGY')
    
    if 'SAFETY CAR' in message_upper:
        elements.append('SAFETY_CAR_STRATEGY')
    
    if any(word in message_upper for word in ['TRACK LIMITS', 'ADVANTAGE']):
        elements.append('TRACK_POSITION')
    
    if any(word in message_upper for word in ['WEATHER', 'RAIN', 'DRY']):
        elements.append('WEATHER_STRATEGY')
    
    if any(word in message_upper for word in ['FUEL', 'ENGINE']):
        elements.append('TECHNICAL_STRATEGY')
    
    return elements

def analyze_key_events(session):
    """分析關鍵事件摘要"""
    key_events_data = {
        'key_events': [],
        'race_turning_points': [],
        'championship_moments': [],
        'strategic_decisions': [],
        'late_race_drama': [],
        'summary_statistics': {
            'total_key_events': 0,
            'critical_moments': 0,
            'high_impact_events': 0,
            'strategic_windows': 0,
            'championship_decisive_moments': 0,
            'average_turning_point_score': 0,
            'race_phases_with_events': set()
        },
        'phase_analysis': {
            'RACE_START': [],
            'EARLY_STRATEGY': [],
            'MID_RACE_DECISIONS': [],
            'CRITICAL_PHASE': [],
            'ENDGAME': []
        },
        'driver_key_moments': {},
        'event_timeline': []
    }
    
    try:
        if hasattr(session, 'race_control_messages'):
            race_control = session.race_control_messages
            
            if race_control is not None and not race_control.empty:
                key_sequence = 1
                total_turning_point_score = 0
                
                # 估算總圈數
                total_laps = race_control['Lap'].max() if 'Lap' in race_control.columns else 50
                
                for _, message in race_control.iterrows():
                    msg_text = str(message.get('Message', ''))
                    msg_upper = msg_text.upper()
                    lap = message.get('Lap', 0)
                    time = message.get('Time', 'N/A')
                    
                    # 過濾最後一圈的正常比賽結束 CHEQUERED FLAG
                    if 'CHEQUERED FLAG' in msg_upper and lap == total_laps:
                        continue  # 跳過正常的比賽結束標誌
                    
                    # 分類關鍵事件
                    event_type = classify_key_event(msg_text, lap, total_laps)
                    
                    if event_type:
                        # 提取車手資訊
                        involved_drivers_info = extract_driver_info(msg_text)
                        
                        # 評估冠軍影響
                        championship_impact, impact_factors = assess_championship_impact(
                            msg_text, event_type, lap, total_laps
                        )
                        
                        # 計算轉捩點評分
                        turning_point_score = calculate_turning_point_score(
                            event_type, lap, total_laps, len(involved_drivers_info)
                        )
                        
                        # 分析戰略窗口
                        strategic_window = analyze_strategic_window(lap, total_laps)
                        
                        # 提取戰略要素
                        strategic_elements = extract_strategic_elements(msg_text)
                        
                        key_event = {
                            'key_sequence': key_sequence,
                            'lap': lap,
                            'time': format_time(time) if time != 'N/A' else str(time),
                            'raw_time': str(time),
                            'event_type': event_type,
                            'championship_impact': championship_impact,
                            'impact_factors': impact_factors,
                            'turning_point_score': turning_point_score,
                            'strategic_window': strategic_window,
                            'strategic_elements': strategic_elements,
                            'message': msg_text,
                            'involved_drivers': involved_drivers_info,
                            'driver_codes': [d['driver_code'] for d in involved_drivers_info],
                            'race_implications': analyze_race_implications(msg_upper, event_type),
                            'decision_impact': assess_decision_impact(msg_upper, strategic_elements)
                        }
                        
                        key_events_data['key_events'].append(key_event)
                        
                        # 分類存儲
                        if turning_point_score >= 80:
                            key_events_data['race_turning_points'].append(key_event)
                        
                        if championship_impact in ['CRITICAL', 'HIGH']:
                            key_events_data['championship_moments'].append(key_event)
                        
                        if strategic_elements:
                            key_events_data['strategic_decisions'].append(key_event)
                        
                        if strategic_window == 'ENDGAME':
                            key_events_data['late_race_drama'].append(key_event)
                        
                        # 按階段分析
                        key_events_data['phase_analysis'][strategic_window].append(key_event)
                        
                        # 統計分析
                        key_events_data['summary_statistics']['total_key_events'] += 1
                        
                        if championship_impact == 'CRITICAL':
                            key_events_data['summary_statistics']['critical_moments'] += 1
                        elif championship_impact == 'HIGH':
                            key_events_data['summary_statistics']['high_impact_events'] += 1
                        
                        if strategic_elements:
                            key_events_data['summary_statistics']['strategic_windows'] += 1
                        
                        if turning_point_score >= 85:
                            key_events_data['summary_statistics']['championship_decisive_moments'] += 1
                        
                        key_events_data['summary_statistics']['race_phases_with_events'].add(strategic_window)
                        
                        # 車手關鍵時刻分析
                        for driver in involved_drivers_info:
                            driver_code = driver['driver_code']
                            
                            if driver_code not in key_events_data['driver_key_moments']:
                                key_events_data['driver_key_moments'][driver_code] = {
                                    'total_key_moments': 0,
                                    'championship_critical': 0,
                                    'turning_points': 0,
                                    'strategic_decisions': 0,
                                    'highest_impact_score': 0,
                                    'moment_details': []
                                }
                            
                            driver_data = key_events_data['driver_key_moments'][driver_code]
                            driver_data['total_key_moments'] += 1
                            
                            if championship_impact == 'CRITICAL':
                                driver_data['championship_critical'] += 1
                            
                            if turning_point_score >= 80:
                                driver_data['turning_points'] += 1
                            
                            if strategic_elements:
                                driver_data['strategic_decisions'] += 1
                            
                            if turning_point_score > driver_data['highest_impact_score']:
                                driver_data['highest_impact_score'] = turning_point_score
                            
                            driver_data['moment_details'].append({
                                'sequence': key_sequence,
                                'lap': lap,
                                'event_type': event_type,
                                'championship_impact': championship_impact,
                                'turning_point_score': turning_point_score,
                                'strategic_window': strategic_window
                            })
                        
                        # 事件時間軸
                        key_events_data['event_timeline'].append({
                            'sequence': key_sequence,
                            'lap': lap,
                            'event_type': event_type,
                            'turning_point_score': turning_point_score,
                            'championship_impact': championship_impact
                        })
                        
                        total_turning_point_score += turning_point_score
                        key_sequence += 1
                
                # 計算平均轉捩點評分
                if key_events_data['summary_statistics']['total_key_events'] > 0:
                    key_events_data['summary_statistics']['average_turning_point_score'] = round(
                        total_turning_point_score / key_events_data['summary_statistics']['total_key_events'], 2
                    )
                
                # 轉換 set 為 list
                key_events_data['summary_statistics']['race_phases_with_events'] = list(
                    key_events_data['summary_statistics']['race_phases_with_events']
                )
        
        return key_events_data
        
    except Exception as e:
        print(f"[ERROR] 分析關鍵事件摘要時發生錯誤: {e}")
        return key_events_data

def analyze_race_implications(message, event_type):
    """分析比賽影響"""
    implications = []
    
    if event_type in ['RACE_SUSPENSION', 'LATE_SAFETY_CAR']:
        implications.append('FIELD_RESET')
        implications.append('STRATEGY_RESET')
    elif event_type in ['CHAMPIONSHIP_PENALTY', 'DECISIVE_INVESTIGATION']:
        implications.append('POSITION_SHUFFLE')
        implications.append('POINTS_REDISTRIBUTION')
    elif event_type in ['LATE_RACE_INCIDENT', 'DECISIVE_OVERTAKE']:
        implications.append('PODIUM_CHANGES')
        implications.append('CHAMPIONSHIP_IMPACT')
    
    return implications

def assess_decision_impact(message, strategic_elements):
    """評估決策影響"""
    if not strategic_elements:
        return 'MINIMAL'
    
    if len(strategic_elements) >= 3:
        return 'COMPREHENSIVE'
    elif len(strategic_elements) >= 2:
        return 'SIGNIFICANT'
    else:
        return 'MODERATE'

def display_key_events_summary(data):
    """顯示關鍵事件摘要"""
    print(f"\n🔑 關鍵事件摘要 (Function 10):")
    
    total_key_events = data['summary_statistics']['total_key_events']
    
    if total_key_events == 0:
        print("✅ 本場比賽未發現關鍵轉捩點事件！")
        return
    
    # 關鍵事件統計總覽
    overview_table = PrettyTable()
    overview_table.field_names = ["統計項目", "數值", "說明"]
    
    stats = data['summary_statistics']
    overview_table.add_row(["關鍵事件總數", stats['total_key_events'], "影響比賽走向的重要事件"])
    overview_table.add_row(["關鍵時刻數", stats['critical_moments'], "對冠軍爭奪極為重要的時刻"])
    overview_table.add_row(["高影響事件", stats['high_impact_events'], "顯著影響比賽結果的事件"])
    overview_table.add_row(["戰略決策點", stats['strategic_windows'], "重要戰略決策時機"])
    overview_table.add_row(["決定性時刻", stats['championship_decisive_moments'], "可能決定冠軍歸屬的時刻"])
    overview_table.add_row(["平均轉捩點評分", f"{stats['average_turning_point_score']}/100", "事件轉捩點重要性評分"])
    overview_table.add_row(["涉及比賽階段", len(stats['race_phases_with_events']), "有關鍵事件發生的比賽階段數"])
    
    print("\n📊 關鍵事件統計總覽:")
    print(overview_table)
    
    # 比賽轉捩點詳細報告
    if data['race_turning_points']:
        turning_points_table = PrettyTable()
        turning_points_table.field_names = ["序號", "圈數", "時間", "事件類型", "轉捩點評分", "冠軍影響", "事件描述"]
        turning_points_table.max_width["事件描述"] = 50
        
        for event in data['race_turning_points'][:10]:  # 顯示前10個最重要的轉捩點
            description = event['message'][:50] + "..." if len(event['message']) > 50 else event['message']
            
            turning_points_table.add_row([
                event['key_sequence'],
                f"第{event['lap']}圈",
                event['time'],
                event['event_type'],
                f"{event['turning_point_score']}/100",
                event['championship_impact'],
                description
            ])
        
        print(f"\n🏁 比賽轉捩點詳細報告 (顯示前10個，共{len(data['race_turning_points'])}個):")
        print(turning_points_table)
    
    # 冠軍決定性時刻
    if data['championship_moments']:
        championship_table = PrettyTable()
        championship_table.field_names = ["序號", "圈數", "戰略窗口", "涉及車手", "影響等級", "影響因素", "事件描述"]
        championship_table.max_width["事件描述"] = 40
        championship_table.max_width["影響因素"] = 30
        
        for event in data['championship_moments']:
            drivers_str = ", ".join(event['driver_codes']) if event['driver_codes'] else "N/A"
            factors_str = ", ".join(event['impact_factors'][:2])  # 顯示前2個因素
            description = event['message'][:40] + "..." if len(event['message']) > 40 else event['message']
            
            championship_table.add_row([
                event['key_sequence'],
                f"第{event['lap']}圈",
                event['strategic_window'],
                drivers_str,
                event['championship_impact'],
                factors_str,
                description
            ])
        
        print(f"\n🏆 冠軍決定性時刻 ({len(data['championship_moments'])}個):")
        print(championship_table)
    
    # 比賽階段分析
    phase_analysis_table = PrettyTable()
    phase_analysis_table.field_names = ["比賽階段", "事件數量", "最高轉捩點評分", "關鍵特徵"]
    
    phase_descriptions = {
        'RACE_START': '比賽開始階段',
        'EARLY_STRATEGY': '早期戰略階段',
        'MID_RACE_DECISIONS': '中期決策階段',
        'CRITICAL_PHASE': '關鍵階段',
        'ENDGAME': '終局階段'
    }
    
    for phase, events in data['phase_analysis'].items():
        if events:
            event_count = len(events)
            max_score = max(event['turning_point_score'] for event in events)
            
            # 分析該階段特徵
            event_types = [event['event_type'] for event in events]
            most_common_type = max(set(event_types), key=event_types.count) if event_types else "N/A"
            
            phase_analysis_table.add_row([
                phase_descriptions.get(phase, phase),
                event_count,
                f"{max_score}/100",
                most_common_type
            ])
    
    print(f"\n📈 比賽階段關鍵事件分析:")
    print(phase_analysis_table)
    
    # 車手關鍵時刻參與分析
    if data['driver_key_moments']:
        driver_moments_table = PrettyTable()
        driver_moments_table.field_names = ["車手", "關鍵時刻", "冠軍關鍵", "轉捩點數", "戰略決策", "最高影響評分"]
        
        for driver, moments in data['driver_key_moments'].items():
            driver_moments_table.add_row([
                driver,
                moments['total_key_moments'],
                moments['championship_critical'],
                moments['turning_points'],
                moments['strategic_decisions'],
                f"{moments['highest_impact_score']}/100"
            ])
        
        print(f"\n🏎️ 車手關鍵時刻參與分析:")
        print(driver_moments_table)

def save_json_results(data, session_info):
    """保存分析結果為 JSON 檔案"""
    os.makedirs("json", exist_ok=True)
    
    event_name = session_info.get('event_name', 'Unknown').replace(' ', '_')
    year = session_info.get('year', 2025)
    filename = f"key_events_summary_{year}_{event_name}.json"
    filepath = os.path.join("json", filename)
    
    json_result = {
        "function_id": 10,
        "function_name": "Key Events Summary",
        "analysis_type": "key_events_summary",
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

def report_analysis_results(data, analysis_type="關鍵事件摘要"):
    """報告分析結果狀態"""
    if not data:
        print(f"❌ {analysis_type}失敗：無可用數據")
        return False
    
    total_key_events = data.get('summary_statistics', {}).get('total_key_events', 0)
    critical_moments = data.get('summary_statistics', {}).get('critical_moments', 0)
    turning_points = len(data.get('race_turning_points', []))
    
    print(f"📊 {analysis_type}結果摘要：")
    print(f"   • 關鍵事件總數: {total_key_events}")
    print(f"   • 關鍵時刻數: {critical_moments}")
    print(f"   • 轉捩點數量: {turning_points}")
    print(f"   • 數據完整性: {'✅ 良好' if total_key_events >= 0 else '❌ 異常'}")
    
    print(f"✅ {analysis_type}分析完成！")
    return True

def run_key_events_summary(data_loader, year=None, race=None, session='R'):
    """執行關鍵事件摘要分析 - Function 10"""
    print("🚀 開始執行關鍵事件摘要分析...")
    
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
        key_events_data = cached_data
    else:
        print("🔄 重新計算 - 開始數據分析...")
        
        # 3. 執行分析
        if hasattr(data_loader, 'session') and data_loader.session is not None:
            key_events_data = analyze_key_events(data_loader.session)
        else:
            print("❌ 無法獲取賽事數據")
            return None
        
        if key_events_data:
            # 4. 保存快取
            if save_cache(key_events_data, cache_key):
                print("💾 分析結果已緩存")
    
    # 5. 結果驗證和反饋
    if not report_analysis_results(key_events_data, "關鍵事件摘要"):
        return None
    
    # 6. 顯示分析結果表格
    display_key_events_summary(key_events_data)
    
    # 7. 保存 JSON 結果
    save_json_results(key_events_data, session_info)
    
    print("\n✅ 關鍵事件摘要分析完成！")
    return key_events_data

def run_key_events_summary_json(data_loader, dynamic_team_mapping=None, f1_analysis_instance=None, enable_debug=False, show_detailed_output=True, year=None, race=None, session=None):
    """執行關鍵事件摘要分析並返回JSON格式結果 - API專用版本 (Function 15 標準)
    
    Args:
        data_loader: 數據載入器
        dynamic_team_mapping: 動態車隊映射
        f1_analysis_instance: F1分析實例
        enable_debug: 是否啟用調試模式
        show_detailed_output: 是否顯示詳細輸出（即使使用緩存也顯示完整表格）
        year: 用戶指定的年份（覆蓋data_loader中的年份）
        race: 用戶指定的賽事（覆蓋data_loader中的賽事）
        session: 用戶指定的賽段（覆蓋data_loader中的賽段）
    
    Returns:
        dict: 包含成功狀態、數據、緩存狀態和緩存鍵的標準化返回格式
    """
    if enable_debug:
        print(f"\n[NEW_MODULE] 執行關鍵事件摘要分析模組 (JSON輸出版)...")
        if year or race or session:
            print(f"[OVERRIDE] 使用者指定參數: 年份={year}, 賽事={race}, 賽段={session}")
    
    try:
        # 獲取賽事資訊 - 優先使用用戶指定的參數
        session_info = {}
        if hasattr(data_loader, 'session') and data_loader.session is not None:
            session_info = {
                "event_name": race or getattr(data_loader.session, 'event', {}).get('EventName', 'Unknown'),
                "circuit_name": getattr(data_loader.session, 'event', {}).get('Location', 'Unknown'),
                "session_type": session or getattr(data_loader.session, 'session_info', {}).get('Type', 'Unknown'),
                "year": year or getattr(data_loader.session, 'event', {}).get('year', 2025)
            }
        else:
            # 當沒有session資料時，使用用戶指定的參數
            session_info = {
                "event_name": race or 'Unknown',
                "circuit_name": 'Unknown',
                "session_type": session or 'Unknown',
                "year": year or 2025
            }
        
        # Function 15 標準 - 檢查緩存
        cache_key = generate_cache_key(session_info)
        cached_data = check_cache(cache_key)
        cache_used = cached_data is not None
        
        if cached_data and not show_detailed_output:
            if enable_debug:
                print("📦 使用緩存數據")
            # 確保即使使用緩存也保存JSON結果
            save_json_results(cached_data, session_info)
            return {
                "success": True,
                "message": "成功執行 關鍵事件摘要分析 (緩存)",
                "data": {
                    "function_id": 10,
                    "function_name": "Key Events Summary",
                    "analysis_type": "key_events_summary",
                    "session_info": session_info,
                    "key_events_analysis": cached_data
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
            # 確保即使使用緩存也保存JSON結果
            save_json_results(cached_data, session_info)
            return {
                "success": True,
                "message": "成功執行 關鍵事件摘要分析 (緩存+詳細)",
                "data": {
                    "function_id": 10,
                    "function_name": "Key Events Summary",
                    "analysis_type": "key_events_summary",
                    "session_info": session_info,
                    "key_events_analysis": cached_data
                },
                "cache_used": True,
                "cache_key": cache_key,
                "timestamp": datetime.now().isoformat()
            }
        else:
            if enable_debug:
                print("🔄 重新計算 - 開始數據分析...")
        
        # 執行分析
        key_events_data = run_key_events_summary(
            data_loader, 
            year=session_info.get('year'),
            race=session_info.get('event_name'),
            session=session_info.get('session_type', 'R')
        )
        
        # 保存緩存
        if key_events_data:
            save_cache(key_events_data, cache_key)
            if enable_debug:
                print("💾 分析結果已緩存")
        
        if key_events_data:
            return {
                "success": True,
                "message": "成功執行 關鍵事件摘要分析",
                "data": {
                    "function_id": 10,
                    "function_name": "Key Events Summary",
                    "analysis_type": "key_events_summary",
                    "session_info": session_info,
                    "key_events_analysis": key_events_data
                },
                "cache_used": cache_used,
                "cache_key": cache_key,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "message": "關鍵事件摘要分析執行失敗 - 無可用數據",
                "data": None,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        if enable_debug:
            print(f"[ERROR] 關鍵事件摘要分析模組執行錯誤: {e}")
            import traceback
import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

            traceback.print_exc()
        return {
            "success": False,
            "message": f"關鍵事件摘要分析執行錯誤: {str(e)}",
            "data": None,
            "timestamp": datetime.now().isoformat()
        }

def _display_cached_detailed_output(key_events_data, session_info):
    """顯示緩存數據的詳細輸出 - Function 15 標準
    
    Args:
        key_events_data: 關鍵事件摘要數據
        session_info: 賽事基本信息
    """
    print("\n📊 詳細關鍵事件摘要 (緩存數據)")
    print("=" * 80)
    
    if not key_events_data:
        print("❌ 無關鍵事件數據可顯示")
        return
    
    # 處理不同的數據格式
    if isinstance(key_events_data, dict):
        # 檢查是否有摘要信息
        if 'summary' in key_events_data:
            summary = key_events_data['summary']
            print(f"🎯 關鍵事件總數: {summary.get('total_events', 0)}")
            print(f"🏁 決定性事件數: {summary.get('decisive_events', 0)}")
            print(f"⚠️ 關鍵警告數: {summary.get('critical_warnings', 0)}")
        
        # 顯示事件詳細列表
        events = key_events_data.get('events', [])
        if events:
            events_table = PrettyTable()
            events_table.field_names = [
                "序號", "事件時間", "事件類型", "影響等級", "描述", "影響車手"
            ]
            
            for i, event in enumerate(events[:15], 1):  # 顯示前15個事件
                event_time = event.get('time', 'N/A')
                event_type = event.get('type', 'Unknown')[:12]
                impact_level = event.get('impact_level', 'Unknown')[:8]
                description = event.get('description', 'No description')[:25]
                affected_drivers = ', '.join(event.get('affected_drivers', []))[:15]
                
                events_table.add_row([
                    i, event_time, event_type, impact_level, description, affected_drivers
                ])
            
            print(f"\n📋 關鍵事件詳細列表 (前 {min(15, len(events))} 項):")
            print(events_table)
            
            if len(events) > 15:
                print(f"   ⋯ 還有 {len(events) - 15} 個事件 (已保存至完整數據)")
        
        # 統計摘要
        print(f"\n📈 統計摘要:")
        print(f"   • 總事件數: {len(events)}")
        print(f"   • 高影響事件: {sum(1 for e in events if e.get('impact_level') == 'HIGH')}")
        print(f"   • 中等影響事件: {sum(1 for e in events if e.get('impact_level') == 'MEDIUM')}")
        print(f"   • 低影響事件: {sum(1 for e in events if e.get('impact_level') == 'LOW')}")
        
    elif isinstance(key_events_data, list):
        # 舊格式處理
        print(f"🎯 關鍵事件總數: {len(key_events_data)}")
        
        events_table = PrettyTable()
        events_table.field_names = ["序號", "事件", "描述"]
        
        for i, event in enumerate(key_events_data[:15], 1):
            if isinstance(event, dict):
                event_desc = event.get('description', str(event))[:40]
            else:
                event_desc = str(event)[:40]
            
            events_table.add_row([i, f"事件{i}", event_desc])
        
        print(f"\n📋 關鍵事件列表 (前 {min(15, len(key_events_data))} 項):")
        print(events_table)
    
    print("\n💾 數據來源: 緩存檔案")
    print(f"📅 賽事: {session_info.get('year', 'Unknown')} {session_info.get('event_name', 'Unknown')}")
    print(f"🏁 賽段: {session_info.get('session_type', 'Unknown')}")
    print("✅ 緩存數據詳細輸出完成")

if __name__ == "__main__":
    print("F1 關鍵事件摘要模組 - 獨立測試模式")
    print("此模組需要配合 F1 數據載入器使用")
