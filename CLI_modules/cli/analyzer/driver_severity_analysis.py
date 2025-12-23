#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F1 車手嚴重程度分數統計模組 (功能 4.3)
作者: F1 Analysis Team
版本: 1.0

專門處理車手嚴重程度分數統計，包括：
- 事故參與度分析
- 處罰嚴重程度評分
- 車手風險等級評估
- DNF責任分析
"""

import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

import os
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


def analyze_driver_severity_data(data_loader):
    """分析車手嚴重程度數據"""
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
        
        # 提取車手相關事件
        race_control_messages = extract_race_control_messages(loaded_data)
        driver_incidents = extract_driver_incidents(race_control_messages)
        severity_scores = calculate_severity_scores(driver_incidents)
        
        return {
            "session_info": session_info,
            "driver_incidents": driver_incidents,
            "severity_scores": severity_scores,
            "total_drivers_involved": len(severity_scores),
            "risk_analysis": generate_risk_analysis(severity_scores)
        }
        
    except Exception as e:
        print(f"[ERROR] 分析車手嚴重程度數據時發生錯誤: {e}")
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


def extract_driver_incidents(race_control_messages):
    """提取車手相關事件"""
    driver_incidents = {}
    
    for message in race_control_messages:
        try:
            message_text = message.get('Message', '')
            lap_number = message.get('Lap', 'Unknown')
            timestamp = message.get('Time', 'Unknown')
            
            # 提取車手代號 (例如: CAR 1 (VER), CAR 44 (HAM))
            driver_matches = re.findall(r'CAR \d+ \(([A-Z]{3})\)', message_text.upper())
            incident_matches = re.findall(r'CARS? (\d+.*?\([A-Z]{3}\).*?)(?:AND|NOTED|REVIEWED)', message_text.upper())
            
            if driver_matches:
                for driver in driver_matches:
                    if driver not in driver_incidents:
                        driver_incidents[driver] = []
                    
                    incident = {
                        "timestamp": str(timestamp),
                        "lap": lap_number,
                        "message": message_text,
                        "severity": categorize_incident_severity(message_text),
                        "type": categorize_incident_type(message_text)
                    }
                    driver_incidents[driver].append(incident)
            
            # 處理多車手事件
            if 'INVOLVING' in message_text.upper():
                # 提取涉及的所有車手
                involved_drivers = re.findall(r'\(([A-Z]{3})\)', message_text.upper())
                for driver in involved_drivers:
                    if driver not in driver_incidents:
                        driver_incidents[driver] = []
                    
                    incident = {
                        "timestamp": str(timestamp),
                        "lap": lap_number,
                        "message": message_text,
                        "severity": categorize_incident_severity(message_text),
                        "type": "MULTI_DRIVER_INCIDENT"
                    }
                    driver_incidents[driver].append(incident)
            
        except Exception as e:
            print(f"[WARNING] 處理消息時發生錯誤: {e}")
            continue
    
    return driver_incidents


def categorize_incident_severity(message_text):
    """分類事件嚴重程度"""
    message_upper = message_text.upper()
    
    # 高嚴重程度 (10分)
    if any(keyword in message_upper for keyword in ['CRASH', 'COLLISION', 'DANGEROUS', 'PENALTY', 'DISQUALIFIED']):
        return 10
    
    # 中等嚴重程度 (5分)
    elif any(keyword in message_upper for keyword in ['INCIDENT', 'UNSAFE', 'CAUSING', 'IMPEDING']):
        return 5
    
    # 低嚴重程度 (2分)
    elif any(keyword in message_upper for keyword in ['TIME DELETED', 'TRACK LIMITS', 'WARNING']):
        return 2
    
    # 極低嚴重程度 (1分)
    elif any(keyword in message_upper for keyword in ['NOTED', 'UNDER INVESTIGATION']):
        return 1
    
    return 1


def categorize_incident_type(message_text):
    """分類事件類型"""
    message_upper = message_text.upper()
    
    if 'TRACK LIMITS' in message_upper:
        return 'TRACK_LIMITS'
    elif any(keyword in message_upper for keyword in ['CRASH', 'COLLISION']):
        return 'COLLISION'
    elif 'UNSAFE' in message_upper:
        return 'UNSAFE_DRIVING'
    elif 'PENALTY' in message_upper:
        return 'PENALTY'
    elif 'PIT' in message_upper:
        return 'PIT_INCIDENT'
    else:
        return 'OTHER'


def calculate_severity_scores(driver_incidents):
    """計算車手嚴重程度分數"""
    severity_scores = {}
    
    for driver, incidents in driver_incidents.items():
        total_score = 0
        incident_counts = {
            'TRACK_LIMITS': 0,
            'COLLISION': 0,
            'UNSAFE_DRIVING': 0,
            'PENALTY': 0,
            'PIT_INCIDENT': 0,
            'OTHER': 0
        }
        
        for incident in incidents:
            total_score += incident.get('severity', 1)
            incident_type = incident.get('type', 'OTHER')
            if incident_type in incident_counts:
                incident_counts[incident_type] += 1
            else:
                incident_counts['OTHER'] += 1
        
        severity_scores[driver] = {
            'total_score': total_score,
            'incident_count': len(incidents),
            'incident_breakdown': incident_counts,
            'risk_level': calculate_risk_level(total_score, len(incidents)),
            'incidents': incidents
        }
    
    return severity_scores


def calculate_risk_level(total_score, incident_count):
    """計算風險等級"""
    if total_score >= 20 or incident_count >= 5:
        return 'HIGH'
    elif total_score >= 10 or incident_count >= 3:
        return 'MEDIUM'
    elif total_score >= 5 or incident_count >= 2:
        return 'LOW'
    else:
        return 'MINIMAL'


def generate_risk_analysis(severity_scores):
    """生成風險分析摘要"""
    risk_levels = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'MINIMAL': 0}
    total_incidents = 0
    highest_score_driver = None
    highest_score = 0
    
    for driver, data in severity_scores.items():
        risk_level = data.get('risk_level', 'MINIMAL')
        if risk_level in risk_levels:
            risk_levels[risk_level] += 1
        
        total_incidents += data.get('incident_count', 0)
        
        if data.get('total_score', 0) > highest_score:
            highest_score = data.get('total_score', 0)
            highest_score_driver = driver
    
    return {
        'risk_distribution': risk_levels,
        'total_incidents_all_drivers': total_incidents,
        'highest_risk_driver': highest_score_driver,
        'highest_risk_score': highest_score,
        'average_incidents_per_driver': round(total_incidents / len(severity_scores), 2) if severity_scores else 0
    }


def display_driver_severity_table(analysis_result):
    """顯示車手嚴重程度表格"""
    if not analysis_result:
        print("[ERROR] 無分析結果可顯示")
        return
    
    session_info = analysis_result.get("session_info", {})
    severity_scores = analysis_result.get("severity_scores", {})
    risk_analysis = analysis_result.get("risk_analysis", {})
    
    print(f"\n🏆 車手嚴重程度分數統計 (功能 4.3)")
    print("=" * 80)
    print(f"📅 賽事: {session_info.get('year')} {session_info.get('track_name')}")
    print(f"[FINISH] 賽段: {session_info.get('session_type')} | 日期: {session_info.get('date')}")
    print(f"👥 涉事車手數: {analysis_result.get('total_drivers_involved', 0)}")
    print("=" * 80)
    
    # 風險分析摘要
    print(f"\n[INFO] 風險分析摘要:")
    print(f"🔴 高風險車手: {risk_analysis.get('risk_distribution', {}).get('HIGH', 0)} 位")
    print(f"🟡 中風險車手: {risk_analysis.get('risk_distribution', {}).get('MEDIUM', 0)} 位")
    print(f"🟢 低風險車手: {risk_analysis.get('risk_distribution', {}).get('LOW', 0)} 位")
    print(f"⚪ 極低風險車手: {risk_analysis.get('risk_distribution', {}).get('MINIMAL', 0)} 位")
    print(f"[TARGET] 最高風險車手: {risk_analysis.get('highest_risk_driver', 'N/A')} (分數: {risk_analysis.get('highest_risk_score', 0)})")
    
    if severity_scores:
        # 車手嚴重程度表格
        severity_table = PrettyTable()
        severity_table.field_names = ["車手", "總分數", "事件數", "風險等級", "主要事件類型", "處罰事件"]
        severity_table.align = "l"
        
        # 按總分數排序
        sorted_drivers = sorted(severity_scores.items(), key=lambda x: x[1].get('total_score', 0), reverse=True)
        
        for driver, data in sorted_drivers:
            incident_breakdown = data.get('incident_breakdown', {})
            main_incident_type = max(incident_breakdown.items(), key=lambda x: x[1])[0] if incident_breakdown else 'N/A'
            penalty_count = incident_breakdown.get('PENALTY', 0)
            
            # 風險等級顏色標記
            risk_level = data.get('risk_level', 'MINIMAL')
            risk_display = {
                'HIGH': '🔴 高風險',
                'MEDIUM': '🟡 中風險',
                'LOW': '🟢 低風險',
                'MINIMAL': '⚪ 極低風險'
            }.get(risk_level, risk_level)
            
            severity_table.add_row([
                driver,
                data.get('total_score', 0),
                data.get('incident_count', 0),
                risk_display,
                main_incident_type.replace('_', ' '),
                penalty_count
            ])
        
        print(f"\n[LIST] 車手嚴重程度排名:")
        print(severity_table)
        
        # 詳細事件分析（前5名最高風險車手）
        print(f"\n[DEBUG] 高風險車手詳細分析 (前5名):")
        top_drivers = sorted_drivers[:5]
        
        for i, (driver, data) in enumerate(top_drivers, 1):
            print(f"\n{i}. 車手 {driver} - 總分: {data.get('total_score', 0)} | 風險等級: {data.get('risk_level', 'MINIMAL')}")
            incidents = data.get('incidents', [])
            if incidents:
                for j, incident in enumerate(incidents[:3], 1):  # 只顯示前3個事件
                    print(f"   事件{j}: 圈{incident.get('lap', 'N/A')} - {incident.get('message', '')[:60]}...")
                if len(incidents) > 3:
                    print(f"   ... 還有 {len(incidents) - 3} 個事件")


def save_driver_severity_raw_data(analysis_result, data_loader):
    """保存車手嚴重程度原始數據為JSON格式"""
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
        
        filename = os.path.join(json_dir, f"raw_data_driver_severity_{session_info.get('year', '2025')}_{session_info.get('race', 'Unknown')}_{timestamp}.json")
        
        # 準備JSON數據
        json_data = {
            "analysis_type": "driver_severity_analysis",
            "function": "4.3",
            "timestamp": datetime.now().isoformat(),
            "session_info": clean_for_json(session_info),
            "severity_analysis": {
                "total_drivers_involved": analysis_result.get("total_drivers_involved", 0),
                "risk_analysis": clean_for_json(analysis_result.get("risk_analysis", {})),
                "has_high_risk_drivers": analysis_result.get("risk_analysis", {}).get("risk_distribution", {}).get("HIGH", 0) > 0
            },
            "driver_scores": clean_for_json(analysis_result.get("severity_scores", {})),
            "driver_incidents": clean_for_json(analysis_result.get("driver_incidents", {})),
            "metadata": {
                "analysis_date": datetime.now().isoformat(),
                "data_source": "FastF1 + OpenF1",
                "scoring_system": "10=高嚴重, 5=中等, 2=低, 1=極低",
                "risk_levels": ["MINIMAL", "LOW", "MEDIUM", "HIGH"],
                "version": "1.0"
            }
        }
        
        # 保存JSON文件
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 原始數據已保存至: {filename}")
        print(f"[INFO] JSON包含 {len(json_data.get('driver_scores', {}))} 位車手的詳細嚴重程度分析")
        
    except Exception as e:
        print(f"[ERROR] 保存JSON文件失敗: {e}")


def run_driver_severity_analysis(data_loader):
    """執行車手嚴重程度分數統計的主函數"""
    try:
        print("\n🏆 開始車手嚴重程度分數統計...")
        
        # 檢查數據載入器
        if not data_loader:
            print("[ERROR] 數據載入器未初始化")
            return False
        
        # 分析車手嚴重程度數據
        analysis_result = analyze_driver_severity_data(data_loader)
        
        if not analysis_result:
            print("[ERROR] 車手嚴重程度分析失敗")
            return False
        
        # 顯示分析結果
        display_driver_severity_table(analysis_result)
        
        # 保存原始數據
        save_driver_severity_raw_data(analysis_result, data_loader)
        
        print("\n[SUCCESS] 車手嚴重程度分數統計完成")
        return True
        
    except Exception as e:
        print(f"[ERROR] 執行車手嚴重程度分數統計時發生錯誤: {e}")
        import traceback

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("[WARNING] 此模組需要通過主程式調用")
    print("請使用 F1_Analysis_Main_Menu.bat 選擇功能 4.3")
