#!/usr/bin/env python3
"""
F1 事故統計摘要模組 - Function 6
Accident Statistics Summary Module - Following Core Development Standards
統計事故總數、類型分佈、涉及車手數量等關鍵統計數據
"""

import os
import json
import pickle
import pandas as pd
from datetime import datetime
from prettytable import PrettyTable

def generate_cache_key(session_info):
    """生成快取鍵值"""
    return f"accident_statistics_{session_info.get('year', 2024)}_{session_info.get('event_name', 'Unknown')}_{session_info.get('session_type', 'R')}"

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

def analyze_accident_statistics(session):
    """分析事故統計數據"""
    statistics = {
        'total_incidents': 0,
        'incident_types': {
            'accidents': 0,
            'flags': 0,
            'investigations': 0,
            'penalties': 0,
            'safety_cars': 0,
            'red_flags': 0
        },
        'affected_drivers': 0,
        'incident_distribution_by_lap': {},
        'most_incident_prone_sectors': {},
        'incident_frequency': {
            'per_10_laps': 0,
            'peak_incident_period': 'N/A'
        }
    }
    
    try:
        if hasattr(session, 'race_control_messages'):
            race_control = session.race_control_messages
            
            if race_control is not None and not race_control.empty:
                # 找出最後一圈圈數，用於過濾正常結束的 CHEQUERED FLAG
                max_lap = race_control['Lap'].max() if 'Lap' in race_control.columns else 0
                involved_drivers = set()
                lap_incidents = {}
                
                for _, message in race_control.iterrows():
                    msg_text = str(message.get('Message', '')).upper()
                    lap = message.get('Lap', 0)
                    
                    # 過濾最後一圈的正常比賽結束 CHEQUERED FLAG
                    if 'CHEQUERED FLAG' in msg_text and lap == max_lap:
                        continue  # 跳過正常的比賽結束標誌
                    
                    # 識別事故相關關鍵字
                    if any(keyword in msg_text for keyword in [
                        'ACCIDENT', 'COLLISION', 'CRASH', 'INCIDENT', 
                        'SAFETY CAR', 'RED FLAG', 'YELLOW FLAG',
                        'INVESTIGATION', 'PENALTY', 'CONTACT'
                    ]):
                        statistics['total_incidents'] += 1
                        
                        # 分類統計
                        if any(word in msg_text for word in ['ACCIDENT', 'COLLISION', 'CRASH', 'CONTACT']):
                            statistics['incident_types']['accidents'] += 1
                        elif 'SAFETY CAR' in msg_text:
                            statistics['incident_types']['safety_cars'] += 1
                        elif 'RED FLAG' in msg_text:
                            statistics['incident_types']['red_flags'] += 1
                        elif any(word in msg_text for word in ['YELLOW FLAG', 'FLAG']):
                            statistics['incident_types']['flags'] += 1
                        elif 'INVESTIGATION' in msg_text:
                            statistics['incident_types']['investigations'] += 1
                        elif 'PENALTY' in msg_text:
                            statistics['incident_types']['penalties'] += 1
                        
                        # 提取涉及的車手
                        import re
                        car_numbers = re.findall(r'CAR[S]?\s+(\d+)', msg_text)
                        involved_drivers.update(car_numbers)
                        
                        # 按圈數分佈
                        if lap in lap_incidents:
                            lap_incidents[lap] += 1
                        else:
                            lap_incidents[lap] = 1
                
                statistics['affected_drivers'] = len(involved_drivers)
                statistics['incident_distribution_by_lap'] = lap_incidents
                
                # 計算事故頻率
                if statistics['total_incidents'] > 0 and lap_incidents:
                    max_lap = max(lap_incidents.keys()) if lap_incidents else 0
                    if max_lap > 0:
                        statistics['incident_frequency']['per_10_laps'] = round((statistics['total_incidents'] / max_lap) * 10, 2)
                
                # 找出事故最多的時段
                if lap_incidents:
                    peak_lap = max(lap_incidents, key=lap_incidents.get)
                    statistics['incident_frequency']['peak_incident_period'] = f"第{peak_lap}圈附近"
        
        return statistics
        
    except Exception as e:
        print(f"[ERROR] 分析事故統計時發生錯誤: {e}")
        return statistics

def display_accident_statistics(data):
    """顯示事故統計摘要表格"""
    print(f"\n📊 事故統計摘要 (Function 6):")
    
    if data['total_incidents'] == 0:
        print("✅ 本場比賽未發現任何事故記錄，比賽進行順利！")
        return
    
    # 主要統計表格
    main_table = PrettyTable()
    main_table.field_names = ["統計項目", "數值", "說明"]
    
    main_table.add_row(["總事故數量", data['total_incidents'], "所有類型事故總和"])
    main_table.add_row(["涉及車手數量", data['affected_drivers'], "受到事故影響的車手"])
    main_table.add_row(["事故頻率", f"{data['incident_frequency']['per_10_laps']}/10圈", "每10圈平均事故數"])
    main_table.add_row(["高峰時段", data['incident_frequency']['peak_incident_period'], "事故最集中的時段"])
    
    print(main_table)
    
    # 事故類型分佈表格
    type_table = PrettyTable()
    type_table.field_names = ["事故類型", "數量", "百分比", "說明"]
    
    total = data['total_incidents']
    for incident_type, count in data['incident_types'].items():
        if count > 0:
            percentage = f"{(count/total)*100:.1f}%" if total > 0 else "0%"
            type_descriptions = {
                'accidents': '碰撞事故',
                'flags': '旗幟事件',
                'investigations': '調查事件',
                'penalties': '處罰事件',
                'safety_cars': '安全車出動',
                'red_flags': '紅旗中斷'
            }
            description = type_descriptions.get(incident_type, '其他事件')
            type_table.add_row([incident_type.title(), count, percentage, description])
    
    print(f"\n📋 事故類型分佈:")
    print(type_table)
    
    # 圈數分佈表格 (顯示前5個高峰圈數)
    if data['incident_distribution_by_lap']:
        lap_table = PrettyTable()
        lap_table.field_names = ["圈數", "事故數量", "累計百分比"]
        
        sorted_laps = sorted(data['incident_distribution_by_lap'].items(), 
                           key=lambda x: x[1], reverse=True)[:5]
        
        cumulative = 0
        for lap, count in sorted_laps:
            cumulative += count
            percentage = f"{(cumulative/total)*100:.1f}%"
            lap_table.add_row([f"第{lap}圈", count, percentage])
        
        print(f"\n🏁 事故高峰圈數 (前5名):")
        print(lap_table)

def save_json_results(data, session_info):
    """保存分析結果為 JSON 檔案"""
    os.makedirs("json", exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    event_name = session_info.get('event_name', 'Unknown').replace(' ', '_')
    filename = f"accident_statistics_summary_{session_info.get('year', 2024)}_{event_name}_{timestamp}.json"
    filepath = os.path.join("json", filename)
    
    json_result = {
        "function_id": 6,
        "function_name": "Accident Statistics Summary",
        "analysis_type": "accident_statistics_summary",
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

def report_analysis_results(data, analysis_type="事故統計摘要"):
    """報告分析結果狀態"""
    if not data:
        print(f"❌ {analysis_type}失敗：無可用數據")
        return False
    
    total_incidents = data.get('total_incidents', 0)
    affected_drivers = data.get('affected_drivers', 0)
    incident_types = len([k for k, v in data.get('incident_types', {}).items() if v > 0])
    
    print(f"📊 {analysis_type}結果摘要：")
    print(f"   • 總事故數量: {total_incidents}")
    print(f"   • 涉及車手數量: {affected_drivers}")
    print(f"   • 事故類型數量: {incident_types}")
    print(f"   • 數據完整性: {'✅ 良好' if total_incidents >= 0 else '❌ 異常'}")
    
    print(f"✅ {analysis_type}分析完成！")
    return True

def run_accident_statistics_summary(data_loader, year=None, race=None, session='R'):
    """執行事故統計摘要分析 - Function 6"""
    print("🚀 開始執行事故統計摘要分析...")
    
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
        statistics_data = cached_data
    else:
        print("🔄 重新計算 - 開始數據分析...")
        
        # 3. 執行分析
        if hasattr(data_loader, 'session') and data_loader.session is not None:
            statistics_data = analyze_accident_statistics(data_loader.session)
        else:
            print("❌ 無法獲取賽事數據")
            return None
        
        if statistics_data:
            # 4. 保存快取
            if save_cache(statistics_data, cache_key):
                print("💾 分析結果已緩存")
    
    # 5. 結果驗證和反饋
    if not report_analysis_results(statistics_data, "事故統計摘要"):
        return None
    
    # 6. 顯示分析結果表格
    display_accident_statistics(statistics_data)
    
    # 7. 保存 JSON 結果
    save_json_results(statistics_data, session_info)
    
    print("\n✅ 事故統計摘要分析完成！")
    return statistics_data

def run_accident_statistics_summary_json(data_loader, dynamic_team_mapping=None, f1_analysis_instance=None, enable_debug=False, show_detailed_output=True):
    """執行事故統計摘要分析並返回JSON格式結果 - API專用版本
    
    Args:
        data_loader: 數據載入器
        dynamic_team_mapping: 動態車隊映射
        f1_analysis_instance: F1分析實例
        enable_debug: 是否啟用調試模式
        show_detailed_output: 是否顯示詳細輸出（即使使用緩存也顯示完整表格）
    """
    if enable_debug:
        print(f"\n[NEW_MODULE] 執行事故統計摘要分析模組 (JSON輸出版)...")
    
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
                "message": "成功執行 事故統計摘要分析 (緩存)",
                "data": {
                    "function_id": 6,
                    "function_name": "Accident Statistics Summary",
                    "analysis_type": "accident_statistics_summary",
                    "session_info": session_info,
                    "accident_statistics": cached_data
                },
                "cache_used": True,
                "cache_key": cache_key,
                "timestamp": datetime.now().isoformat()
            }
        elif cached_data and show_detailed_output:
            if enable_debug:
                print("📦 使用緩存數據 + 📊 顯示詳細分析結果")
            
            # 顯示詳細輸出 - 即使使用緩存也顯示完整表格
            _display_cached_detailed_output(cached_data, session_info)
            
            return {
                "success": True,
                "message": "成功執行 事故統計摘要分析 (緩存+詳細)",
                "data": {
                    "function_id": 6,
                    "function_name": "Accident Statistics Summary",
                    "analysis_type": "accident_statistics_summary",
                    "session_info": session_info,
                    "accident_statistics": cached_data
                },
                "cache_used": True,
                "cache_key": cache_key,
                "timestamp": datetime.now().isoformat()
            }
        else:
            if enable_debug:
                print("🔄 重新計算 - 開始數據分析...")
        
        # 執行分析
        statistics_data = run_accident_statistics_summary(
            data_loader, 
            year=session_info.get('year'),
            race=session_info.get('event_name'),
            session=session_info.get('session_type', 'R')
        )
        
        # 保存緩存
        if statistics_data:
            save_cache(statistics_data, cache_key)
            if enable_debug:
                print("💾 分析結果已緩存")
        
        if statistics_data:
            return {
                "success": True,
                "message": "成功執行 事故統計摘要分析",
                "data": {
                    "function_id": 6,
                    "function_name": "Accident Statistics Summary",
                    "analysis_type": "accident_statistics_summary",
                    "session_info": session_info,
                    "accident_statistics": statistics_data
                },
                "cache_used": cache_used,
                "cache_key": cache_key,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "message": "事故統計摘要分析執行失敗 - 無可用數據",
                "data": None,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        if enable_debug:
            print(f"[ERROR] 事故統計摘要分析模組執行錯誤: {e}")
            import traceback
            traceback.print_exc()
        return {
            "success": False,
            "message": f"事故統計摘要分析執行錯誤: {str(e)}",
            "data": None,
            "timestamp": datetime.now().isoformat()
        }


def _display_cached_detailed_output(cached_data, session_info):
    """顯示緩存數據的詳細輸出 - Function 15 標準
    
    Args:
        cached_data: 事故統計摘要數據
        session_info: 賽事基本信息
    """
    print("\n📊 詳細事故統計摘要 (緩存數據)")
    print("=" * 80)
    
    if not cached_data:
        print("❌ 緩存數據為空")
        return
    
    print(f"🏆 賽事: {session_info.get('year', 'Unknown')} {session_info.get('event_name', 'Unknown')}")
    print(f"🏁 賽段: {session_info.get('session_type', 'Unknown')}")
    print(f"🏟️ 賽道: {session_info.get('circuit_name', 'Unknown')}")
    
    # 使用原有的顯示函數
    display_accident_statistics(cached_data)
    
    print("\n💾 數據來源: 緩存檔案")
    print("✅ 緩存數據詳細輸出完成")


if __name__ == "__main__":
    print("F1 事故統計摘要模組 - 獨立測試模式")
    print("此模組需要配合 F1 數據載入器使用")
