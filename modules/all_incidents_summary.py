#!/usr/bin/env python3
"""
F1 所有事件詳細列表模組 - Function 8
All Incidents Summary Module - Following Core Development Standards
提供完整的事故事件詳細列表，包含時間、圈數、車手、詳細描述等
"""

import os
import json
import pickle
import pandas as pd
from datetime import datetime
from prettytable import PrettyTable

def generate_cache_key(session_info):
    """生成快取鍵值"""
    return f"all_incidents_summary_{session_info.get('year', 2024)}_{session_info.get('event_name', 'Unknown')}_{session_info.get('session_type', 'R')}"

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

def categorize_incident_detailed(message):
    """詳細事故分類"""
    message = message.upper()
    
    if 'CHEQUERED FLAG' in message:
        return 'RACE_END'
    elif any(word in message for word in ['ACCIDENT', 'COLLISION', 'CRASH']):
        return 'ACCIDENT'
    elif 'SAFETY CAR' in message:
        return 'SAFETY_CAR'
    elif 'RED FLAG' in message:
        return 'RED_FLAG'
    elif 'YELLOW FLAG' in message:
        return 'YELLOW_FLAG'
    elif 'INVESTIGATION' in message:
        return 'INVESTIGATION'
    elif 'PENALTY' in message:
        return 'PENALTY'
    elif any(word in message for word in ['CONTACT', 'INCIDENT']):
        return 'CONTACT'
    elif 'PIT' in message:
        return 'PIT_RELATED'
    elif any(word in message for word in ['TRACK', 'LIMIT', 'ADVANTAGE']):
        return 'TRACK_LIMITS'
    else:
        return 'OTHER'

def assess_incident_impact(message, category):
    """評估事故影響程度"""
    message = message.upper()
    
    if category == 'RED_FLAG':
        return 'RACE_STOPPED'
    elif category == 'SAFETY_CAR':
        return 'SAFETY_INTERVENTION'
    elif 'NO FURTHER INVESTIGATION' in message or 'NO ACTION' in message:
        return 'NO_ACTION'
    elif 'TIME PENALTY' in message or 'POSITION PENALTY' in message:
        return 'PENALTY_APPLIED'
    elif 'UNDER INVESTIGATION' in message or 'NOTED' in message:
        return 'UNDER_REVIEW'
    else:
        return 'MONITORING'

def analyze_all_incidents(session):
    """分析所有事故事件詳細資訊"""
    incidents_data = {
        'all_incidents': [],
        'incident_summary': {
            'total_count': 0,
            'by_category': {},
            'by_impact': {},
            'by_lap_range': {},
            'involved_drivers': set(),
            'timeline_analysis': {}
        },
        'chronological_sequence': [],
        'driver_involvement': {},
        'lap_analysis': {}
    }
    
    try:
        if hasattr(session, 'race_control_messages'):
            race_control = session.race_control_messages
            
            if race_control is not None and not race_control.empty:
                # 找出最後一圈圈數，用於過濾正常結束的 CHEQUERED FLAG
                max_lap = race_control['Lap'].max() if 'Lap' in race_control.columns else 0
                incident_sequence = 1
                
                for _, message in race_control.iterrows():
                    msg_text = str(message.get('Message', ''))
                    msg_upper = msg_text.upper()
                    lap = message.get('Lap', 0)
                    time = message.get('Time', 'N/A')
                    
                    # 過濾最後一圈的正常比賽結束 CHEQUERED FLAG
                    if 'CHEQUERED FLAG' in msg_upper and lap == max_lap:
                        continue  # 跳過正常的比賽結束標誌
                    
                    # 識別事故相關關鍵字
                    if any(keyword in msg_upper for keyword in [
                        'ACCIDENT', 'COLLISION', 'CRASH', 'INCIDENT', 
                        'SAFETY CAR', 'RED FLAG', 'YELLOW FLAG',
                        'INVESTIGATION', 'PENALTY', 'CONTACT', 'CHEQUERED FLAG',
                        'PIT EXIT', 'TRACK LIMITS', 'ADVANTAGE'
                    ]):
                        # 提取車手資訊
                        involved_drivers = extract_driver_info(msg_text)
                        
                        # 分類事故
                        category = categorize_incident_detailed(msg_text)
                        
                        # 評估影響
                        impact = assess_incident_impact(msg_text, category)
                        
                        # 評估嚴重程度
                        severity = assess_severity_detailed(msg_upper)
                        
                        incident_detail = {
                            'sequence_number': incident_sequence,
                            'lap': lap,
                            'time': format_time(time) if time != 'N/A' else str(time),
                            'raw_time': str(time),
                            'message': msg_text,
                            'category': category,
                            'severity': severity,
                            'impact': impact,
                            'involved_drivers': involved_drivers,
                            'driver_codes': [d['driver_code'] for d in involved_drivers],
                            'car_numbers': [d['car_number'] for d in involved_drivers],
                            'keywords': extract_keywords(msg_upper),
                            'flags_mentioned': extract_flags(msg_upper)
                        }
                        
                        incidents_data['all_incidents'].append(incident_detail)
                        incidents_data['chronological_sequence'].append({
                            'sequence': incident_sequence,
                            'lap': lap,
                            'category': category,
                            'severity': severity
                        })
                        
                        # 統計分析
                        incidents_data['incident_summary']['total_count'] += 1
                        
                        # 按類別統計
                        if category not in incidents_data['incident_summary']['by_category']:
                            incidents_data['incident_summary']['by_category'][category] = 0
                        incidents_data['incident_summary']['by_category'][category] += 1
                        
                        # 按影響統計
                        if impact not in incidents_data['incident_summary']['by_impact']:
                            incidents_data['incident_summary']['by_impact'][impact] = 0
                        incidents_data['incident_summary']['by_impact'][impact] += 1
                        
                        # 記錄涉及的車手
                        for driver in involved_drivers:
                            driver_code = driver['driver_code']
                            incidents_data['incident_summary']['involved_drivers'].add(driver_code)
                            
                            if driver_code not in incidents_data['driver_involvement']:
                                incidents_data['driver_involvement'][driver_code] = []
                            incidents_data['driver_involvement'][driver_code].append({
                                'sequence': incident_sequence,
                                'lap': lap,
                                'category': category,
                                'severity': severity
                            })
                        
                        # 按圈數分析
                        lap_range = f"{(lap//10)*10}-{(lap//10)*10+9}"
                        if lap_range not in incidents_data['incident_summary']['by_lap_range']:
                            incidents_data['incident_summary']['by_lap_range'][lap_range] = 0
                        incidents_data['incident_summary']['by_lap_range'][lap_range] += 1
                        
                        if lap not in incidents_data['lap_analysis']:
                            incidents_data['lap_analysis'][lap] = []
                        incidents_data['lap_analysis'][lap].append(incident_detail)
                        
                        incident_sequence += 1
                
                # 轉換 set 為 list 以便 JSON 序列化
                incidents_data['incident_summary']['involved_drivers'] = list(incidents_data['incident_summary']['involved_drivers'])
        
        return incidents_data
        
    except Exception as e:
        print(f"[ERROR] 分析所有事件詳細列表時發生錯誤: {e}")
        return incidents_data

def assess_severity_detailed(message):
    """詳細評估事故嚴重程度"""
    if any(word in message for word in ['RED FLAG', 'RACE SUSPENSION', 'MEDICAL CAR']):
        return 'CRITICAL'
    elif any(word in message for word in ['SAFETY CAR', 'YELLOW FLAG', 'COLLISION', 'CRASH']):
        return 'HIGH'
    elif any(word in message for word in ['INVESTIGATION', 'CONTACT', 'PENALTY']):
        return 'MEDIUM'
    else:
        return 'LOW'

def extract_keywords(message):
    """提取關鍵字"""
    keywords = []
    keyword_list = ['ACCIDENT', 'COLLISION', 'CRASH', 'SAFETY CAR', 'RED FLAG', 'YELLOW FLAG',
                   'INVESTIGATION', 'PENALTY', 'CONTACT', 'PIT EXIT', 'TRACK LIMITS', 'ADVANTAGE']
    
    for keyword in keyword_list:
        if keyword in message:
            keywords.append(keyword)
    
    return keywords

def extract_flags(message):
    """提取旗幟相關資訊"""
    flags = []
    flag_types = ['RED FLAG', 'YELLOW FLAG', 'CHEQUERED FLAG', 'SAFETY CAR']
    
    for flag in flag_types:
        if flag in message:
            flags.append(flag)
    
    return flags

def display_all_incidents_summary(data):
    """顯示所有事件詳細列表"""
    print(f"\n📋 所有事件詳細列表 (Function 8):")
    
    total_incidents = data['incident_summary']['total_count']
    
    if total_incidents == 0:
        print("✅ 本場比賽未發現任何事故記錄！")
        return
    
    # 總覽統計表格
    overview_table = PrettyTable()
    overview_table.field_names = ["統計項目", "數值", "說明"]
    
    overview_table.add_row(["總事件數量", total_incidents, "所有記錄的事故事件"])
    overview_table.add_row(["涉及車手數量", len(data['incident_summary']['involved_drivers']), "受事故影響的車手總數"])
    overview_table.add_row(["事件類型數量", len(data['incident_summary']['by_category']), "不同類型的事故分類"])
    overview_table.add_row(["影響等級數量", len(data['incident_summary']['by_impact']), "不同影響程度的分類"])
    
    print("\n📊 事件總覽統計:")
    print(overview_table)
    
    # 事件類別分佈表格
    category_table = PrettyTable()
    category_table.field_names = ["事件類別", "數量", "百分比", "說明"]
    
    category_descriptions = {
        'RACE_END': '比賽結束',
        'ACCIDENT': '碰撞事故',
        'SAFETY_CAR': '安全車',
        'RED_FLAG': '紅旗中斷',
        'YELLOW_FLAG': '黃旗警告',
        'INVESTIGATION': '調查事件',
        'PENALTY': '處罰事件',
        'CONTACT': '車輛接觸',
        'PIT_RELATED': '維修站相關',
        'TRACK_LIMITS': '賽道界限',
        'OTHER': '其他事件'
    }
    
    for category, count in data['incident_summary']['by_category'].items():
        percentage = f"{(count/total_incidents)*100:.1f}%"
        description = category_descriptions.get(category, '未知類型')
        category_table.add_row([category, count, percentage, description])
    
    print(f"\n📋 事件類別分佈:")
    print(category_table)
    
    # 詳細事件列表表格 (顯示前15筆)
    details_table = PrettyTable()
    details_table.field_names = ["序號", "圈數", "時間", "類別", "嚴重程度", "涉及車手", "事件描述"]
    details_table.max_width["事件描述"] = 60
    
    for incident in data['all_incidents'][:15]:
        drivers_str = ", ".join(incident['driver_codes']) if incident['driver_codes'] else "N/A"
        description = incident['message'][:60] + "..." if len(incident['message']) > 60 else incident['message']
        
        details_table.add_row([
            incident['sequence_number'],
            f"第{incident['lap']}圈",
            incident['time'],
            incident['category'],
            incident['severity'],
            drivers_str,
            description
        ])
    
    print(f"\n📋 詳細事件列表 (顯示前15筆，共{total_incidents}筆):")
    print(details_table)
    
    if total_incidents > 15:
        print(f"   💡 完整事件列表已保存至 JSON 檔案")
    
    # 車手參與統計表格
    if data['driver_involvement']:
        driver_table = PrettyTable()
        driver_table.field_names = ["車手代碼", "參與事件數", "最高嚴重程度", "主要事件類型"]
        
        for driver, incidents in data['driver_involvement'].items():
            incident_count = len(incidents)
            severities = [inc['severity'] for inc in incidents]
            categories = [inc['category'] for inc in incidents]
            
            # 找出最高嚴重程度
            severity_order = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
            max_severity = max(severities, key=lambda x: severity_order.index(x) if x in severity_order else 0)
            
            # 找出最常見的事件類型
            most_common_category = max(set(categories), key=categories.count)
            
            driver_table.add_row([driver, incident_count, max_severity, most_common_category])
        
        print(f"\n🏎️ 車手事件參與統計:")
        print(driver_table)

def save_json_results(data, session_info):
    """保存分析結果為 JSON 檔案"""
    os.makedirs("json", exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    event_name = session_info.get('event_name', 'Unknown').replace(' ', '_')
    filename = f"all_incidents_summary_{session_info.get('year', 2024)}_{event_name}_{timestamp}.json"
    filepath = os.path.join("json", filename)
    
    json_result = {
        "function_id": 8,
        "function_name": "All Incidents Summary",
        "analysis_type": "all_incidents_summary",
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

def report_analysis_results(data, analysis_type="所有事件詳細列表"):
    """報告分析結果狀態"""
    if not data:
        print(f"❌ {analysis_type}失敗：無可用數據")
        return False
    
    total_incidents = data.get('incident_summary', {}).get('total_count', 0)
    involved_drivers = len(data.get('incident_summary', {}).get('involved_drivers', []))
    categories = len(data.get('incident_summary', {}).get('by_category', {}))
    
    print(f"📊 {analysis_type}結果摘要：")
    print(f"   • 總事件數量: {total_incidents}")
    print(f"   • 涉及車手數量: {involved_drivers}")
    print(f"   • 事件類型數量: {categories}")
    print(f"   • 數據完整性: {'✅ 良好' if total_incidents >= 0 else '❌ 異常'}")
    
    print(f"✅ {analysis_type}分析完成！")
    return True

def run_all_incidents_summary(data_loader, year=None, race=None, session='R'):
    """執行所有事件詳細列表分析 - Function 8"""
    print("🚀 開始執行所有事件詳細列表分析...")
    
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
        incidents_data = cached_data
    else:
        print("🔄 重新計算 - 開始數據分析...")
        
        # 3. 執行分析
        if hasattr(data_loader, 'session') and data_loader.session is not None:
            incidents_data = analyze_all_incidents(data_loader.session)
        else:
            print("❌ 無法獲取賽事數據")
            return None
        
        if incidents_data:
            # 4. 保存快取
            if save_cache(incidents_data, cache_key):
                print("💾 分析結果已緩存")
    
    # 5. 結果驗證和反饋
    if not report_analysis_results(incidents_data, "所有事件詳細列表"):
        return None
    
    # 6. 顯示分析結果表格
    display_all_incidents_summary(incidents_data)
    
    # 7. 保存 JSON 結果
    save_json_results(incidents_data, session_info)
    
    print("\n✅ 所有事件詳細列表分析完成！")
    return incidents_data

def run_all_incidents_summary_json(data_loader, dynamic_team_mapping=None, f1_analysis_instance=None, enable_debug=False, show_detailed_output=True):
    """執行所有事件詳細列表分析並返回JSON格式結果 - API專用版本
    
    Args:
        data_loader: 數據載入器
        dynamic_team_mapping: 動態車隊映射
        f1_analysis_instance: F1分析實例
        enable_debug: 是否啟用調試模式
        show_detailed_output: 是否顯示詳細輸出（即使使用緩存也顯示完整表格）
    """
    if enable_debug:
        print(f"\n[NEW_MODULE] 執行所有事件詳細列表分析模組 (JSON輸出版)...")
    
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
                "message": "成功執行 所有事件詳細列表分析 (緩存)",
                "data": {
                    "function_id": 8,
                    "function_name": "All Incidents Summary",
                    "analysis_type": "all_incidents_summary",
                    "session_info": session_info,
                    "incidents_analysis": cached_data
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
                "message": "成功執行 所有事件詳細列表分析 (緩存+詳細)",
                "data": {
                    "function_id": 8,
                    "function_name": "All Incidents Summary",
                    "analysis_type": "all_incidents_summary",
                    "session_info": session_info,
                    "incidents_analysis": cached_data
                },
                "cache_used": True,
                "cache_key": cache_key,
                "timestamp": datetime.now().isoformat()
            }
        else:
            if enable_debug:
                print("🔄 重新計算 - 開始數據分析...")
        
        # 執行分析
        incidents_data = run_all_incidents_summary(
            data_loader, 
            year=session_info.get('year'),
            race=session_info.get('event_name'),
            session=session_info.get('session_type', 'R')
        )
        
        # 保存緩存
        if incidents_data:
            save_cache(incidents_data, cache_key)
            if enable_debug:
                print("💾 分析結果已緩存")
        
        if incidents_data:
            return {
                "success": True,
                "message": "成功執行 所有事件詳細列表分析",
                "data": {
                    "function_id": 8,
                    "function_name": "All Incidents Summary",
                    "analysis_type": "all_incidents_summary",
                    "session_info": session_info,
                    "incidents_analysis": incidents_data
                },
                "cache_used": cache_used,
                "cache_key": cache_key,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "message": "所有事件詳細列表分析執行失敗 - 無可用數據",
                "data": None,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        if enable_debug:
            print(f"[ERROR] 所有事件詳細列表分析模組執行錯誤: {e}")
            import traceback
            traceback.print_exc()
        return {
            "success": False,
            "message": f"所有事件詳細列表分析執行錯誤: {str(e)}",
            "data": None,
            "timestamp": datetime.now().isoformat()
        }

def _display_cached_detailed_output(incidents_data, session_info):
    """顯示緩存數據的詳細輸出 - Function 15 標準
    
    Args:
        incidents_data: 事件詳細列表數據 (複雜字典結構)
        session_info: 賽事基本信息
    """
    print("\n📊 詳細事件列表 (緩存數據)")
    print("=" * 80)
    
    if not incidents_data:
        print("❌ 無事件數據可顯示")
        return
    
    # 檢查數據結構並正確提取
    if isinstance(incidents_data, dict):
        # 檢查是否有 incident_summary 結構
        if 'incident_summary' in incidents_data:
            summary = incidents_data['incident_summary']
            total_incidents = summary.get('total_count', 0)
            print(f"🚨 總事件數量: {total_incidents}")
            
            # 總覽統計表格
            overview_table = PrettyTable()
            overview_table.field_names = ["統計項目", "數值", "說明"]
            
            overview_table.add_row(["總事件數量", total_incidents, "所有記錄的事故事件"])
            overview_table.add_row(["涉及車手數量", len(summary.get('involved_drivers', [])), "受事故影響的車手總數"])
            overview_table.add_row(["事件類型數量", len(summary.get('by_category', {})), "不同類型的事故分類"])
            overview_table.add_row(["影響等級數量", len(summary.get('by_impact', {})), "不同影響程度的分類"])
            
            print("\n📊 事件總覽統計:")
            print(overview_table)
            
            # 詳細事件表格
            incidents_table = PrettyTable()
            incidents_table.field_names = [
                "序號", "車手", "圈數", "事件類型", "影響級別", "描述"
            ]
            
            # 從詳細事件中顯示前20個
            detailed_events = incidents_data.get('detailed_incidents', [])
            display_count = min(20, len(detailed_events))
            
            for i, incident in enumerate(detailed_events[:20], 1):
                driver = incident.get('driver', 'Unknown')[:10]
                lap = incident.get('lap', 'N/A')
                category = incident.get('category', 'Unknown')[:12]
                impact = incident.get('impact_level', 'Unknown')[:8]
                description = incident.get('description', 'No description')[:35]
                
                incidents_table.add_row([
                    i, driver, lap, category, impact, description
                ])
            
            if display_count > 0:
                print(f"\n📋 詳細事件記錄 (前 {display_count} 項):")
                print(incidents_table)
            
            # 統計摘要
            print(f"\n📈 統計摘要:")
            print(f"   • 顯示事件數: {display_count}")
            print(f"   • 總事件數: {len(detailed_events)}")
            if len(detailed_events) > 20:
                print(f"   • 隱藏事件數: {len(detailed_events) - 20}")
                
        else:
            # 舊格式數據處理
            print("⚠️ 檢測到舊格式緩存數據")
            if isinstance(incidents_data, list):
                total_incidents = len(incidents_data)
                print(f"🚨 總事件數量: {total_incidents}")
                
                # 詳細事件表格
                incidents_table = PrettyTable()
                incidents_table.field_names = [
                    "序號", "時間", "圈數", "事件類型", "車手", "描述"
                ]
                
                # 顯示前20個事件
                for i, incident in enumerate(incidents_data[:20], 1):
                    time_str = incident.get('time', 'N/A')
                    lap_str = str(incident.get('lap', 'N/A'))
                    event_type = incident.get('type', 'Unknown')[:15]
                    driver = incident.get('driver', 'Unknown')[:10]
                    description = incident.get('description', 'No description')[:30]
                    
                    incidents_table.add_row([
                        i, time_str, lap_str, event_type, driver, description
                    ])
                
                print(incidents_table)
            else:
                print(f"⚠️ 未知數據格式: {type(incidents_data)}")
                print(f"   數據鍵值: {list(incidents_data.keys()) if isinstance(incidents_data, dict) else '非字典格式'}")
    else:
        print(f"⚠️ 意外的數據類型: {type(incidents_data)}")
    
    print("\n💾 數據來源: 緩存檔案")
    print(f"📅 賽事: {session_info.get('year', 'Unknown')} {session_info.get('event_name', 'Unknown')}")
    print(f"🏁 賽段: {session_info.get('session_type', 'Unknown')}")
    print("✅ 緩存數據詳細輸出完成")

if __name__ == "__main__":
    print("F1 所有事件詳細列表模組 - 獨立測試模式")
    print("此模組需要配合 F1 數據載入器使用")
