#!/usr/bin/env python3
"""
F1 事故分析模組 - 符合核心開發原則
Accident Analysis Module - Following Core Development Standards
完全符合開發核心要求：快取機制、執行結果反饋、JSON輸出、時間格式標準
"""

import os
import json
import pickle
import pandas as pd
import numpy as np
from datetime import datetime
from prettytable import PrettyTable
import traceback
from core.logger import get_logger


logger = get_logger("accident_analysis", component="gui")

def generate_cache_key(session_info):
    """生成快取鍵值"""
    return f"accident_analysis_{session_info.get('year', 2024)}_{session_info.get('event_name', 'Unknown')}_{session_info.get('session_type', 'R')}"

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
    """標準時間格式化函數 - 禁止包含 'day' 或 'days'"""
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

def report_analysis_results(data, analysis_type="事故分析"):
    """報告分析結果狀態 - 符合核心開發要求"""
    if not data:
        logger.error("❌ %s失敗：無可用數據", analysis_type)
        return False
    
    total_incidents = data.get('total_incidents', 0)
    incident_details = data.get('incident_details', [])
    affected_drivers = data.get('affected_drivers', 0)
    
    logger.info(
        "📊 %s結果摘要： 總事故數量: %s, 詳細記錄數量: %s, 涉及車手數量: %s, 數據完整性: %s",
        analysis_type,
        total_incidents,
        len(incident_details),
        affected_drivers,
        "✅ 良好" if total_incidents > 0 else "⚠️ 無事故記錄"
    )
    logger.info("✅ %s分析完成！", analysis_type)
    return True

def analyze_accidents_from_session(session):
    """從賽事數據中分析事故"""
    accidents = []
    
    try:
        # 獲取比賽控制消息
        if hasattr(session, 'race_control_messages'):
            race_control = session.race_control_messages
            
            if race_control is not None and not race_control.empty:
                # 分析每條消息
                for _, message in race_control.iterrows():
                    msg_text = str(message.get('Message', '')).upper()
                    
                    # 識別事故相關關鍵字
                    if any(keyword in msg_text for keyword in [
                        'ACCIDENT', 'COLLISION', 'CRASH', 'INCIDENT', 
                        'SAFETY CAR', 'RED FLAG', 'YELLOW FLAG',
                        'INVESTIGATION', 'PENALTY', 'CONTACT'
                    ]):
                        accident = {
                            'time': format_time(message.get('Time', 'N/A')),
                            'lap': message.get('Lap', 'N/A'),
                            'driver': message.get('Driver', 'N/A'),
                            'message': message.get('Message', ''),
                            'category': categorize_incident(msg_text),
                            'severity': assess_severity(msg_text)
                        }
                        accidents.append(accident)
        
        # 如果沒有找到事故記錄，創建空記錄
        if not accidents:
            return {
                'total_incidents': 0,
                'incident_details': [],
                'affected_drivers': 0,
                'incident_types': {
                    'accidents': 0,
                    'flags': 0,
                    'investigations': 0,
                    'penalties': 0
                },
                'severity_distribution': {
                    'LOW': 0,
                    'MEDIUM': 0,
                    'HIGH': 0,
                    'CRITICAL': 0
                }
            }
        
        # 統計分析
        incident_types = {
            'accidents': sum(1 for acc in accidents if 'ACCIDENT' in acc['category'] or 'COLLISION' in acc['category']),
            'flags': sum(1 for acc in accidents if 'FLAG' in acc['category']),
            'investigations': sum(1 for acc in accidents if 'INVESTIGATION' in acc['category']),
            'penalties': sum(1 for acc in accidents if 'PENALTY' in acc['category'])
        }
        
        severity_dist = {
            'LOW': sum(1 for acc in accidents if acc['severity'] == 'LOW'),
            'MEDIUM': sum(1 for acc in accidents if acc['severity'] == 'MEDIUM'),
            'HIGH': sum(1 for acc in accidents if acc['severity'] == 'HIGH'),
            'CRITICAL': sum(1 for acc in accidents if acc['severity'] == 'CRITICAL')
        }
        
        affected_drivers = len(set(acc['driver'] for acc in accidents if acc['driver'] != 'N/A'))
        
        return {
            'total_incidents': len(accidents),
            'incident_details': accidents,
            'affected_drivers': affected_drivers,
            'incident_types': incident_types,
            'severity_distribution': severity_dist
        }
        
    except Exception as e:
        logger.exception("[ERROR] 分析事故數據時發生錯誤: %s", e)
        return None

def categorize_incident(message):
    """事故分類"""
    message = message.upper()
    if any(word in message for word in ['ACCIDENT', 'COLLISION', 'CRASH', 'CONTACT']):
        return 'ACCIDENT'
    elif any(word in message for word in ['SAFETY CAR', 'RED FLAG', 'YELLOW FLAG']):
        return 'FLAG'
    elif 'INVESTIGATION' in message:
        return 'INVESTIGATION'
    elif 'PENALTY' in message:
        return 'PENALTY'
    else:
        return 'OTHER'

def assess_severity(message):
    """評估事故嚴重程度"""
    message = message.upper()
    if any(word in message for word in ['RED FLAG', 'SERIOUS', 'CRITICAL']):
        return 'CRITICAL'
    elif any(word in message for word in ['SAFETY CAR', 'YELLOW FLAG']):
        return 'HIGH'
    elif any(word in message for word in ['INVESTIGATION', 'CONTACT']):
        return 'MEDIUM'
    else:
        return 'LOW'

def display_accident_analysis(data):
    """顯示事故分析結果表格"""
    if not data or data['total_incidents'] == 0:
        logger.info("\n📋 事故分析結果:")
        logger.info("✅ 本場比賽未發現任何事故記錄，比賽進行順利！")
        return
    
    logger.info("\n📋 事故分析結果:")
    
    # 1. 事故摘要表格
    summary_table = PrettyTable()
    summary_table.field_names = ["統計項目", "數量", "百分比"]
    
    total = data['total_incidents']
    summary_table.add_row(["總事故數量", total, "100%"])
    summary_table.add_row(["涉及車手數量", data['affected_drivers'], f"{(data['affected_drivers']/20)*100:.1f}%"])
    
    for category, count in data['incident_types'].items():
        if count > 0:
            percentage = f"{(count/total)*100:.1f}%" if total > 0 else "0%"
            summary_table.add_row([category.title(), count, percentage])
    
    logger.info("\n📊 事故統計摘要:")
    logger.info("%s", summary_table)
    
    # 2. 嚴重程度分佈表格
    severity_table = PrettyTable()
    severity_table.field_names = ["嚴重程度", "事故數量", "比例"]
    
    for severity, count in data['severity_distribution'].items():
        if count > 0:
            percentage = f"{(count/total)*100:.1f}%" if total > 0 else "0%"
            severity_table.add_row([severity, count, percentage])
    
    logger.info("\n⚠️ 嚴重程度分佈:")
    logger.info("%s", severity_table)
    
    # 3. 詳細事故記錄表格
    detail_table = PrettyTable()
    detail_table.field_names = ["時間", "圈數", "車手", "事故類型", "嚴重程度", "詳細描述"]
    detail_table.max_width["詳細描述"] = 50
    
    for incident in data['incident_details'][:10]:  # 顯示前10筆
        detail_table.add_row([
            incident['time'],
            incident['lap'],
            incident['driver'],
            incident['category'],
            incident['severity'],
            incident['message'][:50] + "..." if len(incident['message']) > 50 else incident['message']
        ])
    
    logger.info("\n📋 詳細事故記錄 (顯示前10筆，共%s筆):", len(data['incident_details']))
    logger.info("%s", detail_table)
    
    if len(data['incident_details']) > 10:
        logger.info("   💡 完整記錄已保存至 JSON 檔案")

def save_json_results(data, session_info):
    """保存分析結果為 JSON 檔案"""
    os.makedirs("json", exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    event_name = session_info.get('event_name', 'Unknown').replace(' ', '_')
    filename = f"accident_analysis_{session_info.get('year', 2024)}_{event_name}_{timestamp}.json"
    filepath = os.path.join("json", filename)
    
    json_result = {
        "function_id": 6,
        "function_name": "Accident Analysis",
        "analysis_type": "accident_analysis",
        "session_info": session_info,
        "timestamp": datetime.now().isoformat(),
        "data": data
    }
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(json_result, f, ensure_ascii=False, indent=2)
        
        abs_filepath = os.path.abspath(filepath)
        logger.info("💾 JSON結果已保存到: file:///%s", abs_filepath)
        return True
    except Exception as e:
        logger.exception("❌ JSON保存失敗: %s", e)
        return False

def run_accident_analysis(data_loader, year=None, race=None, session='R'):
    """執行事故分析 - 符合核心開發原則的主要函數"""
    logger.info("🚀 開始執行事故分析...")
    
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
        logger.info("📦 使用緩存數據")
        analysis_data = cached_data
    else:
        logger.info("🔄 重新計算 - 開始數據分析...")
        
        # 3. 執行分析
        if hasattr(data_loader, 'session') and data_loader.session is not None:
            analysis_data = analyze_accidents_from_session(data_loader.session)
        else:
            logger.error("❌ 無法獲取賽事數據")
            return None
        
        if analysis_data:
            # 4. 保存快取
            if save_cache(analysis_data, cache_key):
                logger.info("💾 分析結果已緩存")
    
    # 5. 結果驗證和反饋
    if not report_analysis_results(analysis_data, "事故分析"):
        return None
    
    # 6. 顯示分析結果表格
    display_accident_analysis(analysis_data)
    
    # 7. 保存 JSON 結果
    save_json_results(analysis_data, session_info)
    
    logger.info("\n✅ 事故分析完成！")
    return analysis_data

def run_accident_analysis_json(data_loader, dynamic_team_mapping=None, f1_analysis_instance=None, enable_debug=False):
    """執行事故分析並返回JSON格式結果 - API專用版本"""
    if enable_debug:
        logger.info("\n[NEW_MODULE] 執行新版事故分析模組 (JSON輸出版)...")
    
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
        
        # 執行分析
        analysis_data = run_accident_analysis(
            data_loader, 
            year=session_info.get('year'),
            race=session_info.get('event_name'),
            session=session_info.get('session_type', 'R')
        )
        
        if analysis_data:
            return {
                "success": True,
                "message": "成功執行 事故分析",
                "data": {
                    "function_id": 6,
                    "function_name": "Accident Analysis",
                    "analysis_type": "accident_analysis",
                    "session_info": session_info,
                    "accident_analysis": analysis_data
                },
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "message": "事故分析執行失敗 - 無可用數據",
                "data": None,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        if enable_debug:
            logger.exception("[ERROR] 事故分析模組執行錯誤: %s", e)
        return {
            "success": False,
            "message": f"事故分析執行錯誤: {str(e)}",
            "data": None,
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    logger.info("F1 事故分析模組 - 獨立測試模式")
    logger.info("此模組需要配合 F1 數據載入器使用")
