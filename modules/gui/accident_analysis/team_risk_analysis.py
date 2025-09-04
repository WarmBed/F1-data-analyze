#!/usr/bin/env python3
"""
F1 車隊風險分數統計模組 (功能 4.4)
作者: F1 Analysis Team
版本: 1.0

專門處理車隊風險分數統計，包括：
- 車隊事故率分析
- 車隊整體風險評估
- 車手對車隊風險的貢獻度
- 車隊安全性排名
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


# 基本車手-車隊映射 (2025賽季)
DRIVER_TEAM_MAPPING = {
    'VER': 'Red Bull Racing',
    'PER': 'Red Bull Racing',
    'HAM': 'Mercedes',
    'RUS': 'Mercedes',
    'LEC': 'Ferrari',
    'SAI': 'Ferrari',
    'NOR': 'McLaren',
    'PIA': 'McLaren',
    'ALO': 'Aston Martin',
    'STR': 'Aston Martin',
    'TSU': 'AlphaTauri',
    'RIC': 'AlphaTauri',
    'GAS': 'Alpine',
    'OCO': 'Alpine',
    'ALB': 'Williams',
    'SAR': 'Williams',
    'MAG': 'Haas',
    'HUL': 'Haas',
    'BOT': 'Alfa Romeo',
    'ZHO': 'Alfa Romeo'
}


def analyze_team_risk_data(data_loader):
    """分析車隊風險數據"""
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
        
        # 提取車手事件並映射到車隊
        race_control_messages = extract_race_control_messages(loaded_data)
        driver_incidents = extract_driver_incidents(race_control_messages)
        team_risks = calculate_team_risk_scores(driver_incidents)
        
        return {
            "session_info": session_info,
            "team_risks": team_risks,
            "driver_incidents": driver_incidents,
            "total_teams_involved": len(team_risks),
            "team_ranking": generate_team_ranking(team_risks)
        }
        
    except Exception as e:
        print(f"[ERROR] 分析車隊風險數據時發生錯誤: {e}")
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
            
            # 提取車手代號
            driver_matches = re.findall(r'CAR \d+ \(([A-Z]{3})\)', message_text.upper())
            
            if driver_matches:
                for driver in driver_matches:
                    if driver not in driver_incidents:
                        driver_incidents[driver] = []
                    
                    incident = {
                        "timestamp": str(timestamp),
                        "lap": lap_number,
                        "message": message_text,
                        "severity": categorize_incident_severity(message_text),
                        "type": categorize_incident_type(message_text),
                        "team": DRIVER_TEAM_MAPPING.get(driver, 'Unknown Team')
                    }
                    driver_incidents[driver].append(incident)
            
            # 處理多車手事件
            if 'INVOLVING' in message_text.upper():
                involved_drivers = re.findall(r'\(([A-Z]{3})\)', message_text.upper())
                for driver in involved_drivers:
                    if driver not in driver_incidents:
                        driver_incidents[driver] = []
                    
                    incident = {
                        "timestamp": str(timestamp),
                        "lap": lap_number,
                        "message": message_text,
                        "severity": categorize_incident_severity(message_text),
                        "type": "MULTI_DRIVER_INCIDENT",
                        "team": DRIVER_TEAM_MAPPING.get(driver, 'Unknown Team')
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


def calculate_team_risk_scores(driver_incidents):
    """計算車隊風險分數"""
    team_risks = {}
    
    # 按車隊分組車手事件
    for driver, incidents in driver_incidents.items():
        team_name = DRIVER_TEAM_MAPPING.get(driver, 'Unknown Team')
        
        if team_name not in team_risks:
            team_risks[team_name] = {
                'drivers': {},
                'total_score': 0,
                'total_incidents': 0,
                'incident_breakdown': {
                    'TRACK_LIMITS': 0,
                    'COLLISION': 0,
                    'UNSAFE_DRIVING': 0,
                    'PENALTY': 0,
                    'PIT_INCIDENT': 0,
                    'OTHER': 0
                },
                'risk_level': 'MINIMAL',
                'safety_rating': 0
            }
        
        # 計算該車手對車隊的貢獻
        driver_score = 0
        driver_incident_count = len(incidents)
        driver_incidents_breakdown = {
            'TRACK_LIMITS': 0,
            'COLLISION': 0,
            'UNSAFE_DRIVING': 0,
            'PENALTY': 0,
            'PIT_INCIDENT': 0,
            'OTHER': 0
        }
        
        for incident in incidents:
            severity = incident.get('severity', 1)
            incident_type = incident.get('type', 'OTHER')
            
            driver_score += severity
            
            if incident_type in driver_incidents_breakdown:
                driver_incidents_breakdown[incident_type] += 1
                team_risks[team_name]['incident_breakdown'][incident_type] += 1
            else:
                driver_incidents_breakdown['OTHER'] += 1
                team_risks[team_name]['incident_breakdown']['OTHER'] += 1
        
        # 記錄車手數據
        team_risks[team_name]['drivers'][driver] = {
            'score': driver_score,
            'incident_count': driver_incident_count,
            'incident_breakdown': driver_incidents_breakdown,
            'incidents': incidents
        }
        
        # 累加到車隊總分
        team_risks[team_name]['total_score'] += driver_score
        team_risks[team_name]['total_incidents'] += driver_incident_count
    
    # 計算車隊風險等級和安全評級
    for team_name, team_data in team_risks.items():
        total_score = team_data['total_score']
        total_incidents = team_data['total_incidents']
        driver_count = len(team_data['drivers'])
        
        # 計算風險等級
        if total_score >= 30 or total_incidents >= 8:
            team_data['risk_level'] = 'HIGH'
        elif total_score >= 20 or total_incidents >= 5:
            team_data['risk_level'] = 'MEDIUM'
        elif total_score >= 10 or total_incidents >= 3:
            team_data['risk_level'] = 'LOW'
        else:
            team_data['risk_level'] = 'MINIMAL'
        
        # 計算安全評級 (0-100，100最安全)
        base_rating = 100
        penalty = min(total_score * 2, 80)  # 最多扣80分
        team_data['safety_rating'] = max(base_rating - penalty, 20)
        
        # 計算平均數據
        team_data['average_score_per_driver'] = round(total_score / driver_count, 2) if driver_count > 0 else 0
        team_data['average_incidents_per_driver'] = round(total_incidents / driver_count, 2) if driver_count > 0 else 0
    
    return team_risks


def generate_team_ranking(team_risks):
    """生成車隊排名"""
    # 按安全評級排序 (越高越安全)
    sorted_teams = sorted(team_risks.items(), key=lambda x: x[1]['safety_rating'], reverse=True)
    
    ranking = []
    for i, (team_name, team_data) in enumerate(sorted_teams, 1):
        ranking.append({
            'rank': i,
            'team': team_name,
            'safety_rating': team_data['safety_rating'],
            'risk_level': team_data['risk_level'],
            'total_score': team_data['total_score'],
            'total_incidents': team_data['total_incidents'],
            'driver_count': len(team_data['drivers'])
        })
    
    return ranking


def display_team_risk_table(analysis_result):
    """顯示車隊風險表格"""
    if not analysis_result:
        print("[ERROR] 無分析結果可顯示")
        return
    
    session_info = analysis_result.get("session_info", {})
    team_risks = analysis_result.get("team_risks", {})
    team_ranking = analysis_result.get("team_ranking", [])
    
    print(f"\n[FINISH] 車隊風險分數統計 (功能 4.4)")
    print("=" * 80)
    print(f"📅 賽事: {session_info.get('year')} {session_info.get('track_name')}")
    print(f"[FINISH] 賽段: {session_info.get('session_type')} | 日期: {session_info.get('date')}")
    print(f"🏎️ 涉事車隊數: {analysis_result.get('total_teams_involved', 0)}")
    print("=" * 80)
    
    if team_ranking:
        # 車隊安全排名表格
        ranking_table = PrettyTable()
        ranking_table.field_names = ["排名", "車隊", "安全評級", "風險等級", "總分數", "事件數", "車手數", "平均分/車手"]
        ranking_table.align = "l"
        
        for team_rank in team_ranking:
            team_name = team_rank['team']
            team_data = team_risks.get(team_name, {})
            
            # 風險等級顏色標記
            risk_level = team_rank['risk_level']
            risk_display = {
                'HIGH': '🔴 高風險',
                'MEDIUM': '🟡 中風險',
                'LOW': '🟢 低風險',
                'MINIMAL': '⚪ 極低風險'
            }.get(risk_level, risk_level)
            
            ranking_table.add_row([
                team_rank['rank'],
                team_name,
                f"{team_rank['safety_rating']}/100",
                risk_display,
                team_rank['total_score'],
                team_rank['total_incidents'],
                team_rank['driver_count'],
                team_data.get('average_score_per_driver', 0)
            ])
        
        print(f"\n🏆 車隊安全排名 (按安全評級排序):")
        print(ranking_table)
        
        # 詳細車隊分析（前5名最高風險車隊）
        high_risk_teams = [team for team in team_ranking if team['risk_level'] in ['HIGH', 'MEDIUM']][:5]
        
        if high_risk_teams:
            print(f"\n[DEBUG] 高風險車隊詳細分析:")
            
            for team_rank in high_risk_teams:
                team_name = team_rank['team']
                team_data = team_risks.get(team_name, {})
                
                print(f"\n{team_rank['rank']}. {team_name} - 安全評級: {team_rank['safety_rating']}/100 | 風險等級: {team_rank['risk_level']}")
                print(f"   總分數: {team_rank['total_score']} | 總事件數: {team_rank['total_incidents']}")
                
                # 車手明細
                drivers_data = team_data.get('drivers', {})
                if drivers_data:
                    print(f"   車手明細:")
                    for driver, driver_data in drivers_data.items():
                        print(f"     - {driver}: 分數 {driver_data['score']}, 事件數 {driver_data['incident_count']}")
                
                # 事件類型分析
                incident_breakdown = team_data.get('incident_breakdown', {})
                main_incidents = [(k, v) for k, v in incident_breakdown.items() if v > 0]
                if main_incidents:
                    print(f"   主要事件類型: {', '.join([f'{k.replace('_', ' ')}: {v}' for k, v in main_incidents])}")


def save_team_risk_raw_data(analysis_result, data_loader):
    """保存車隊風險原始數據為JSON格式"""
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
        
        filename = os.path.join(json_dir, f"raw_data_team_risk_{session_info.get('year', '2025')}_{session_info.get('race', 'Unknown')}_{timestamp}.json")
        
        # 準備JSON數據
        json_data = {
            "analysis_type": "team_risk_analysis",
            "function": "4.4",
            "timestamp": datetime.now().isoformat(),
            "session_info": clean_for_json(session_info),
            "team_analysis": {
                "total_teams_involved": analysis_result.get("total_teams_involved", 0),
                "team_ranking": clean_for_json(analysis_result.get("team_ranking", [])),
                "has_high_risk_teams": any(team['risk_level'] == 'HIGH' for team in analysis_result.get("team_ranking", []))
            },
            "team_risks": clean_for_json(analysis_result.get("team_risks", {})),
            "driver_incidents": clean_for_json(analysis_result.get("driver_incidents", {})),
            "metadata": {
                "analysis_date": datetime.now().isoformat(),
                "data_source": "FastF1 + OpenF1",
                "scoring_system": "10=高嚴重, 5=中等, 2=低, 1=極低",
                "safety_rating_range": "20-100 (100最安全)",
                "risk_levels": ["MINIMAL", "LOW", "MEDIUM", "HIGH"],
                "team_mapping": DRIVER_TEAM_MAPPING,
                "version": "1.0"
            }
        }
        
        # 保存JSON文件
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 原始數據已保存至: {filename}")
        print(f"[INFO] JSON包含 {len(json_data.get('team_risks', {}))} 個車隊的詳細風險分析")
        
    except Exception as e:
        print(f"[ERROR] 保存JSON文件失敗: {e}")


def run_team_risk_analysis(data_loader):
    """執行車隊風險分數統計的主函數"""
    try:
        print("\n[FINISH] 開始車隊風險分數統計...")
        
        # 檢查數據載入器
        if not data_loader:
            print("[ERROR] 數據載入器未初始化")
            return False
        
        # 分析車隊風險數據
        analysis_result = analyze_team_risk_data(data_loader)
        
        if not analysis_result:
            print("[ERROR] 車隊風險分析失敗")
            return False
        
        # 顯示分析結果
        display_team_risk_table(analysis_result)
        
        # 保存原始數據
        save_team_risk_raw_data(analysis_result, data_loader)
        
        print("\n[SUCCESS] 車隊風險分數統計完成")
        return True
        
    except Exception as e:
        print(f"[ERROR] 執行車隊風險分數統計時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("[WARNING] 此模組需要通過主程式調用")
    print("請使用 F1_Analysis_Main_Menu.bat 選擇功能 4.4")
