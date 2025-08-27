#!/usr/bin/env python3
"""
F1 事故嚴重程度分佈模組 - Function 7
Accident Severity Distribution Module - Following Core Development Standards
分析事故的嚴重程度分佈，包含風險評估和安全性分析
"""

import os
import json
import pickle
import pandas as pd
from datetime import datetime
from prettytable import PrettyTable

def generate_cache_key(session_info):
    """生成快取鍵值"""
    return f"severity_distribution_{session_info.get('year', 2024)}_{session_info.get('event_name', 'Unknown')}_{session_info.get('session_type', 'R')}"

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

def assess_severity(message):
    """評估事故嚴重程度"""
    message = message.upper()
    
    # CRITICAL - 最高嚴重程度
    if any(word in message for word in ['RED FLAG', 'RACE SUSPENSION', 'MEDICAL CAR', 'AMBULANCE', 'CHEQUERED FLAG']):
        return 'CRITICAL'
    
    # HIGH - 高嚴重程度  
    elif any(word in message for word in ['SAFETY CAR', 'YELLOW FLAG', 'COLLISION', 'CRASH']):
        return 'HIGH'
    
    # MEDIUM - 中等嚴重程度
    elif any(word in message for word in ['INVESTIGATION', 'CONTACT', 'PENALTY', 'TIME PENALTY']):
        return 'MEDIUM'
    
    # LOW - 低嚴重程度
    else:
        return 'LOW'

def calculate_risk_score(severity_data):
    """計算比賽風險評分 (0-100)"""
    weights = {
        'CRITICAL': 25,
        'HIGH': 15,
        'MEDIUM': 8,
        'LOW': 3
    }
    
    total_score = 0
    for severity, count in severity_data.items():
        total_score += count * weights.get(severity, 0)
    
    # 標準化到 0-100 分
    max_possible = 100  # 假設最高風險情況
    risk_score = min(total_score, max_possible)
    
    return risk_score

def get_safety_level(risk_score):
    """根據風險評分獲取安全等級"""
    if risk_score >= 80:
        return "極高風險", "🔴"
    elif risk_score >= 60:
        return "高風險", "🟠"
    elif risk_score >= 40:
        return "中等風險", "🟡"
    elif risk_score >= 20:
        return "低風險", "🟢"
    else:
        return "安全", "✅"

def analyze_severity_distribution(session):
    """分析事故嚴重程度分佈"""
    severity_data = {
        'severity_distribution': {
            'CRITICAL': 0,
            'HIGH': 0,
            'MEDIUM': 0,
            'LOW': 0
        },
        'severity_details': [],
        'risk_assessment': {
            'overall_risk_score': 0,
            'safety_level': 'UNKNOWN',
            'safety_icon': '❓',
            'most_common_severity': 'NONE',
            'critical_incidents_count': 0,
            'safety_recommendations': []
        },
        'incident_progression': [],
        'severity_by_lap': {}
    }
    
    try:
        if hasattr(session, 'race_control_messages'):
            race_control = session.race_control_messages
            
            if race_control is not None and not race_control.empty:
                # 找出最後一圈圈數，用於過濾正常結束的 CHEQUERED FLAG
                max_lap = race_control['Lap'].max() if 'Lap' in race_control.columns else 0
                incidents_by_lap = {}
                
                for _, message in race_control.iterrows():
                    msg_text = str(message.get('Message', '')).upper()
                    lap = message.get('Lap', 0)
                    time = message.get('Time', 'N/A')
                    
                    # 過濾最後一圈的正常比賽結束 CHEQUERED FLAG
                    if 'CHEQUERED FLAG' in msg_text and lap == max_lap:
                        continue  # 跳過正常的比賽結束標誌
                    
                    # 識別事故相關關鍵字
                    if any(keyword in msg_text for keyword in [
                        'ACCIDENT', 'COLLISION', 'CRASH', 'INCIDENT', 
                        'SAFETY CAR', 'RED FLAG', 'YELLOW FLAG',
                        'INVESTIGATION', 'PENALTY', 'CONTACT'
                    ]):
                        severity = assess_severity(msg_text)
                        severity_data['severity_distribution'][severity] += 1
                        
                        # 詳細記錄
                        incident_detail = {
                            'lap': lap,
                            'time': str(time),
                            'severity': severity,
                            'message': message.get('Message', ''),
                            'category': categorize_incident(msg_text)
                        }
                        severity_data['severity_details'].append(incident_detail)
                        
                        # 按圈數記錄嚴重程度
                        if lap not in incidents_by_lap:
                            incidents_by_lap[lap] = []
                        incidents_by_lap[lap].append(severity)
                
                severity_data['severity_by_lap'] = incidents_by_lap
                
                # 計算風險評估
                risk_score = calculate_risk_score(severity_data['severity_distribution'])
                safety_level, safety_icon = get_safety_level(risk_score)
                
                # 找出最常見的嚴重程度
                most_common = max(severity_data['severity_distribution'], 
                                key=severity_data['severity_distribution'].get)
                if severity_data['severity_distribution'][most_common] == 0:
                    most_common = 'NONE'
                
                # 生成安全建議
                recommendations = generate_safety_recommendations(severity_data['severity_distribution'])
                
                severity_data['risk_assessment'] = {
                    'overall_risk_score': risk_score,
                    'safety_level': safety_level,
                    'safety_icon': safety_icon,
                    'most_common_severity': most_common,
                    'critical_incidents_count': severity_data['severity_distribution']['CRITICAL'],
                    'safety_recommendations': recommendations
                }
                
                # 事故升級趨勢
                progression = analyze_incident_progression(severity_data['severity_details'])
                severity_data['incident_progression'] = progression
        
        return severity_data
        
    except Exception as e:
        print(f"[ERROR] 分析嚴重程度分佈時發生錯誤: {e}")
        return severity_data

def categorize_incident(message):
    """事故分類"""
    message = message.upper()
    if any(word in message for word in ['ACCIDENT', 'COLLISION', 'CRASH', 'CONTACT']):
        return 'ACCIDENT'
    elif any(word in message for word in ['SAFETY CAR', 'RED FLAG', 'YELLOW FLAG', 'CHEQUERED FLAG']):
        return 'FLAG'
    elif 'INVESTIGATION' in message:
        return 'INVESTIGATION'
    elif 'PENALTY' in message:
        return 'PENALTY'
    else:
        return 'OTHER'

def generate_safety_recommendations(severity_dist):
    """生成安全建議"""
    recommendations = []
    
    if severity_dist['CRITICAL'] > 0:
        recommendations.append("建議加強賽道安全措施")
        recommendations.append("檢討緊急應變程序")
    
    if severity_dist['HIGH'] > 2:
        recommendations.append("建議增加安全車待命時間")
        recommendations.append("加強車手安全培訓")
    
    if severity_dist['MEDIUM'] > 5:
        recommendations.append("檢討賽車規則執行")
        recommendations.append("加強車手賽道行為監管")
    
    if sum(severity_dist.values()) == 0:
        recommendations.append("比賽安全狀況良好")
        recommendations.append("保持現有安全標準")
    
    return recommendations

def analyze_incident_progression(incidents):
    """分析事故升級趨勢"""
    progression = []
    
    # 按時間排序
    sorted_incidents = sorted(incidents, key=lambda x: x['lap'])
    
    severity_values = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'CRITICAL': 4}
    
    for i, incident in enumerate(sorted_incidents):
        severity_value = severity_values.get(incident['severity'], 0)
        progression.append({
            'sequence': i + 1,
            'lap': incident['lap'],
            'severity': incident['severity'],
            'severity_value': severity_value,
            'trend': 'ESCALATING' if i > 0 and severity_value > severity_values.get(sorted_incidents[i-1]['severity'], 0) else 'STABLE'
        })
    
    return progression

def display_severity_distribution(data):
    """顯示嚴重程度分佈分析表格"""
    print(f"\n⚠️ 事故嚴重程度分佈分析 (Function 7):")
    
    total_incidents = sum(data['severity_distribution'].values())
    
    if total_incidents == 0:
        print("✅ 本場比賽未發現任何事故記錄，安全狀況優良！")
        return
    
    # 風險評估摘要
    risk_info = data['risk_assessment']
    summary_table = PrettyTable()
    summary_table.field_names = ["評估項目", "結果", "說明"]
    
    summary_table.add_row(["總體風險評分", f"{risk_info['overall_risk_score']}/100", "綜合風險指數"])
    summary_table.add_row(["安全等級", f"{risk_info['safety_icon']} {risk_info['safety_level']}", "當前安全狀態"])
    summary_table.add_row(["主要風險類型", risk_info['most_common_severity'], "最常見的事故嚴重程度"])
    summary_table.add_row(["關鍵事件數量", risk_info['critical_incidents_count'], "需特別關注的嚴重事故"])
    
    print("\n📊 風險評估摘要:")
    print(summary_table)
    
    # 嚴重程度分佈表格
    severity_table = PrettyTable()
    severity_table.field_names = ["嚴重程度", "事故數量", "百分比", "風險等級", "說明"]
    
    severity_descriptions = {
        'CRITICAL': ('🔴 極危險', '賽事中斷或生命安全威脅'),
        'HIGH': ('🟠 高危險', '需要安全車或黃旗干預'),
        'MEDIUM': ('🟡 中等風險', '需要調查或處罰的事件'),
        'LOW': ('🟢 低風險', '輕微違規或技術問題')
    }
    
    for severity, count in data['severity_distribution'].items():
        if count > 0:
            percentage = f"{(count/total_incidents)*100:.1f}%"
            risk_level, description = severity_descriptions.get(severity, ('❓ 未知', '未分類事件'))
            severity_table.add_row([severity, count, percentage, risk_level, description])
    
    print("\n⚠️ 嚴重程度詳細分佈:")
    print(severity_table)
    
    # 安全建議表格
    if risk_info['safety_recommendations']:
        rec_table = PrettyTable()
        rec_table.field_names = ["建議編號", "安全建議"]
        
        for i, recommendation in enumerate(risk_info['safety_recommendations'], 1):
            rec_table.add_row([f"建議{i}", recommendation])
        
        print(f"\n💡 安全改善建議:")
        print(rec_table)
    
    # 事故升級趨勢 (顯示前5個事件)
    if data['incident_progression']:
        trend_table = PrettyTable()
        trend_table.field_names = ["順序", "圈數", "嚴重程度", "趨勢", "備註"]
        
        for incident in data['incident_progression'][:5]:
            trend_icon = "⬆️" if incident['trend'] == 'ESCALATING' else "➡️"
            trend_table.add_row([
                incident['sequence'],
                f"第{incident['lap']}圈",
                incident['severity'],
                f"{trend_icon} {incident['trend']}",
                "需關注" if incident['trend'] == 'ESCALATING' else "正常"
            ])
        
        print(f"\n📈 事故升級趨勢 (前5個事件):")
        print(trend_table)

def save_json_results(data, session_info):
    """保存分析結果為 JSON 檔案"""
    os.makedirs("json", exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    event_name = session_info.get('event_name', 'Unknown').replace(' ', '_')
    filename = f"severity_distribution_{session_info.get('year', 2024)}_{event_name}_{timestamp}.json"
    filepath = os.path.join("json", filename)
    
    json_result = {
        "function_id": 7,
        "function_name": "Severity Distribution Analysis",
        "analysis_type": "severity_distribution",
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

def report_analysis_results(data, analysis_type="嚴重程度分佈分析"):
    """報告分析結果狀態"""
    if not data:
        print(f"❌ {analysis_type}失敗：無可用數據")
        return False
    
    total_incidents = sum(data.get('severity_distribution', {}).values())
    risk_score = data.get('risk_assessment', {}).get('overall_risk_score', 0)
    critical_count = data.get('severity_distribution', {}).get('CRITICAL', 0)
    
    print(f"📊 {analysis_type}結果摘要：")
    print(f"   • 總事故數量: {total_incidents}")
    print(f"   • 風險評分: {risk_score}/100")
    print(f"   • 關鍵事件數量: {critical_count}")
    print(f"   • 數據完整性: {'✅ 良好' if total_incidents >= 0 else '❌ 異常'}")
    
    print(f"✅ {analysis_type}分析完成！")
    return True

def run_severity_distribution_analysis(data_loader, year=None, race=None, session='R'):
    """執行嚴重程度分佈分析 - Function 7"""
    print("🚀 開始執行嚴重程度分佈分析...")
    
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
        severity_data = cached_data
    else:
        print("🔄 重新計算 - 開始數據分析...")
        
        # 3. 執行分析
        if hasattr(data_loader, 'session') and data_loader.session is not None:
            severity_data = analyze_severity_distribution(data_loader.session)
        else:
            print("❌ 無法獲取賽事數據")
            return None
        
        if severity_data:
            # 4. 保存快取
            if save_cache(severity_data, cache_key):
                print("💾 分析結果已緩存")
    
    # 5. 結果驗證和反饋
    if not report_analysis_results(severity_data, "嚴重程度分佈分析"):
        return None
    
    # 6. 顯示分析結果表格
    display_severity_distribution(severity_data)
    
    # 7. 保存 JSON 結果
    save_json_results(severity_data, session_info)
    
    print("\n✅ 嚴重程度分佈分析完成！")
    return severity_data

def run_severity_distribution_analysis_json(data_loader, dynamic_team_mapping=None, f1_analysis_instance=None, enable_debug=False, show_detailed_output=True):
    """執行嚴重程度分佈分析並返回JSON格式結果 - API專用版本
    
    Args:
        data_loader: 數據載入器
        dynamic_team_mapping: 動態車隊映射
        f1_analysis_instance: F1分析實例
        enable_debug: 是否啟用調試模式
        show_detailed_output: 是否顯示詳細輸出（即使使用緩存也顯示完整表格）
    """
    if enable_debug:
        print(f"\n[NEW_MODULE] 執行嚴重程度分佈分析模組 (JSON輸出版)...")
    
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
                "message": "成功執行 嚴重程度分佈分析 (緩存)",
                "data": {
                    "function_id": 7,
                    "function_name": "Severity Distribution Analysis",
                    "analysis_type": "severity_distribution",
                    "session_info": session_info,
                    "severity_analysis": cached_data
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
                "message": "成功執行 嚴重程度分佈分析 (緩存+詳細)",
                "data": {
                    "function_id": 7,
                    "function_name": "Severity Distribution Analysis",
                    "analysis_type": "severity_distribution",
                    "session_info": session_info,
                    "severity_analysis": cached_data
                },
                "cache_used": True,
                "cache_key": cache_key,
                "timestamp": datetime.now().isoformat()
            }
        else:
            if enable_debug:
                print("🔄 重新計算 - 開始數據分析...")
        
        # 執行分析
        severity_data = run_severity_distribution_analysis(
            data_loader, 
            year=session_info.get('year'),
            race=session_info.get('event_name'),
            session=session_info.get('session_type', 'R')
        )
        
        # 保存緩存
        if severity_data:
            save_cache(severity_data, cache_key)
            if enable_debug:
                print("💾 分析結果已緩存")
        
        if severity_data:
            return {
                "success": True,
                "message": "成功執行 嚴重程度分佈分析",
                "data": {
                    "function_id": 7,
                    "function_name": "Severity Distribution Analysis",
                    "analysis_type": "severity_distribution",
                    "session_info": session_info,
                    "severity_analysis": severity_data
                },
                "cache_used": cache_used,
                "cache_key": cache_key,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "message": "嚴重程度分佈分析執行失敗 - 無可用數據",
                "data": None,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        if enable_debug:
            print(f"[ERROR] 嚴重程度分佈分析模組執行錯誤: {e}")
            import traceback
            traceback.print_exc()
        return {
            "success": False,
            "message": f"嚴重程度分佈分析執行錯誤: {str(e)}",
            "data": None,
            "timestamp": datetime.now().isoformat()
        }


def _display_cached_detailed_output(cached_data, session_info):
    """顯示緩存數據的詳細輸出 - Function 15 標準
    
    Args:
        cached_data: 嚴重程度分佈分析數據
        session_info: 賽事基本信息
    """
    print("\n📊 詳細嚴重程度分佈分析 (緩存數據)")
    print("=" * 80)
    
    if not cached_data:
        print("❌ 緩存數據為空")
        return
    
    print(f"🏆 賽事: {session_info.get('year', 'Unknown')} {session_info.get('event_name', 'Unknown')}")
    print(f"🏁 賽段: {session_info.get('session_type', 'Unknown')}")
    print(f"🏟️ 賽道: {session_info.get('circuit_name', 'Unknown')}")
    
    # 使用原有的顯示函數
    display_severity_distribution(cached_data)
    
    print("\n💾 數據來源: 緩存檔案")
    print("✅ 緩存數據詳細輸出完成")


if __name__ == "__main__":
    print("F1 嚴重程度分佈分析模組 - 獨立測試模式")
    print("此模組需要配合 F1 數據載入器使用")
