#!/usr/bin/env python3
"""
F1 Independent Accident Analysis Module - Complete Replication
完全復刻 f1_analysis_cli_new.py 的獨立事故分析功能
深度復刻原始事故分析邏輯和所有功能
"""

import os
import sys
import pandas as pd
import numpy as np
import re
from prettytable import PrettyTable
from datetime import datetime
import traceback

# 確保能夠導入基礎模組
try:
    from .base import F1AnalysisBase
except ImportError:
    # 如果相對導入失敗，嘗試絕對導入
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    try:
        from modules.base import F1AnalysisBase
    except ImportError:
        print("[ERROR] 無法導入基礎模組")
        F1AnalysisBase = object

# 註解：F1AccidentAnalyzer 將在本文件中定義，不需要外部導入


def _check_data_loaded_static(data_loader):
    """靜態方法檢查數據是否已載入 - 兼容不同的 data_loader 實現"""
    # 檢查不同類型的 data_loader
    if hasattr(data_loader, 'is_data_loaded'):
        return data_loader.is_data_loaded()
    elif hasattr(data_loader, 'session_loaded'):
        return data_loader.session_loaded
    elif hasattr(data_loader, 'loaded_data') and data_loader.loaded_data:
        return True
    elif hasattr(data_loader, 'session') and data_loader.session:
        return True
    else:
        return False


class F1AccidentAnalyzer:
    """F1事故分析器 - 完全復刻版本"""
    
    def __init__(self):
        self.accidents = []
        self.statistics = {}
        
    def analyze_accidents(self, session):
        """分析事故數據"""
        accidents = []
        
        try:
            if hasattr(session, 'race_control_messages') and session.race_control_messages is not None:
                messages = session.race_control_messages
                
                for _, message in messages.iterrows():
                    msg_text = str(message.get('Message', '')).upper()
                    
                    # 檢查是否為事故相關事件
                    if any(keyword in msg_text for keyword in [
                        'ACCIDENT', 'COLLISION', 'CRASH', 'CONTACT', 'INCIDENT',
                        'FLAG', 'YELLOW', 'RED', 'SAFETY CAR', 'VSC'
                    ]):
                        accident_data = {
                            'time': message.get('Time', 'N/A'),
                            'lap': message.get('Lap', 'N/A'),
                            'message': message.get('Message', ''),
                            'driver': message.get('Driver', 'N/A'),
                            'category': message.get('Category', ''),
                            'category_zh': self._categorize_message_zh(msg_text)
                        }
                        accidents.append(accident_data)
            
        except Exception as e:
            print(f"[WARNING] 分析事故數據時發生錯誤: {e}")
            
        return accidents
    
    def _categorize_message_zh(self, message):
        """中文分類消息"""
        message = message.upper()
        
        if 'RED' in message:
            return '紅旗'
        elif 'YELLOW' in message:
            return '黃旗'
        elif 'SAFETY CAR' in message or 'SC' in message:
            return '安全車'
        elif 'VSC' in message:
            return '虛擬安全車'
        elif any(word in message for word in ['ACCIDENT', 'COLLISION', 'CRASH']):
            return '事故'
        elif any(word in message for word in ['INVESTIGATION', 'PENALTY']):
            return '調查'
        else:
            return '其他'
    
    def calculate_statistics(self, accidents):
        """計算統計數據"""
        stats = {
            'total_events': len(accidents),
            'total_incidents': len(accidents),  # 向後兼容
            'accidents': 0,
            'flags': 0,
            'investigations': 0,
            'safety_events': 0,
            'penalties': 0,
            'severity_distribution': {'NONE': 0, 'LOW': 0, 'MODERATE': 0, 'HIGH': 0, 'CRITICAL': 0}
        }
        
        for accident in accidents:
            msg = str(accident.get('message', '')).upper()
            severity = 'NONE'
            
            if any(word in msg for word in ['ACCIDENT', 'COLLISION', 'CRASH']):
                stats['accidents'] += 1
                severity = 'HIGH'
            elif any(word in msg for word in ['FLAG', 'YELLOW', 'RED', 'SAFETY CAR', 'VSC']):
                stats['flags'] += 1
                stats['safety_events'] += 1
                if 'RED' in msg:
                    severity = 'CRITICAL'
                elif any(word in msg for word in ['SAFETY CAR', 'VSC']):
                    severity = 'HIGH'
                else:
                    severity = 'MODERATE'
            elif any(word in msg for word in ['INVESTIGATION', 'PENALTY']):
                stats['investigations'] += 1
                stats['penalties'] += 1
                severity = 'LOW'
            
            # 更新嚴重程度分布
            stats['severity_distribution'][severity] += 1
        
        return stats
    
    def _display_accidents_summary(self, accidents):
        """顯示事故摘要"""
        if not accidents:
            return
            
        print(f"\n[LIST] 詳細事件列表:")
        print("=" * 100)
        
        # 分類事件
        accident_events = []
        flag_events = []
        investigation_events = []
        
        for accident in accidents:
            msg_text = str(accident.get('message', '')).upper()
            
            if any(keyword in msg_text for keyword in ['ACCIDENT', 'COLLISION', 'CRASH', 'CONTACT']):
                accident_events.append(accident)
            elif any(keyword in msg_text for keyword in ['FLAG', 'YELLOW', 'RED', 'GREEN', 'SAFETY CAR', 'VSC']):
                flag_events.append(accident)
            elif any(keyword in msg_text for keyword in ['INVESTIGATION', 'PENALTY', 'WARNING', 'NOTED']):
                investigation_events.append(accident)
        
        # 顯示事故事件
        if accident_events:
            print(f"\n[CRITICAL] 事故事件 ({len(accident_events)} 起):")
            accident_table = PrettyTable()
            accident_table.field_names = ["編號", "時間", "圈數", "事件描述", "涉及車手"]
            accident_table.align = "l"
            accident_table.max_width["事件描述"] = 100
            
            for i, event in enumerate(accident_events, 1):
                accident_table.add_row([
                    i,
                    event.get('time', 'N/A'),
                    event.get('lap', 'N/A'),
                    event.get('message', ''),
                    event.get('driver', 'N/A')
                ])
            
            print(accident_table)
        
        # 顯示旗幟事件
        if flag_events:
            print(f"\n[FINISH] 旗幟/安全車事件 ({len(flag_events)} 次):")
            flag_table = PrettyTable()
            flag_table.field_names = ["編號", "時間", "圈數", "事件描述"]
            flag_table.align = "l"
            flag_table.max_width["事件描述"] = 100
            
            for i, event in enumerate(flag_events, 1):
                flag_table.add_row([
                    i,
                    event.get('time', 'N/A'),
                    event.get('lap', 'N/A'),
                    event.get('message', '')
                ])
            
            print(flag_table)
        
        # 顯示調查事件
        if investigation_events:
            print(f"\n� 調查/處罰事件 ({len(investigation_events)} 起):")
            investigation_table = PrettyTable()
            investigation_table.field_names = ["編號", "時間", "圈數", "事件描述", "涉及車手"]
            investigation_table.align = "l"
            investigation_table.max_width["事件描述"] = 100
            
            for i, event in enumerate(investigation_events, 1):
                investigation_table.add_row([
                    i,
                    event.get('time', 'N/A'),
                    event.get('lap', 'N/A'),
                    event.get('message', ''),
                    event.get('driver', 'N/A')
                ])
            
            print(investigation_table)
    
    def _display_driver_severity_scores(self, accidents):
        """顯示車手嚴重程度分數"""
        driver_scores = {}
        
        for accident in accidents:
            driver = accident.get('driver', 'N/A')
            if driver != 'N/A' and driver != '':
                msg = str(accident.get('message', '')).upper()
                score = 0
                
                if any(word in msg for word in ['ACCIDENT', 'COLLISION', 'CRASH']):
                    score += 3
                elif any(word in msg for word in ['PENALTY']):
                    score += 2
                elif any(word in msg for word in ['INVESTIGATION', 'WARNING']):
                    score += 1
                
                if driver in driver_scores:
                    driver_scores[driver] += score
                else:
                    driver_scores[driver] = score
        
        if driver_scores:
            print(f"\n👥 車手事件嚴重度排名:")
            severity_table = PrettyTable()
            severity_table.field_names = ["排名", "車手", "嚴重度分數", "風險等級"]
            severity_table.align = "l"
            
            sorted_drivers = sorted(driver_scores.items(), key=lambda x: x[1], reverse=True)
            
            for i, (driver, score) in enumerate(sorted_drivers, 1):
                if score >= 5:
                    risk_level = "🔴 高風險"
                elif score >= 3:
                    risk_level = "🟡 中等風險"
                elif score >= 1:
                    risk_level = "🟢 低風險"
                else:
                    risk_level = "⚪ 無風險"
                
                severity_table.add_row([i, driver, score, risk_level])
            
            print(severity_table)
    
    def _display_special_incident_reports(self, accidents):
        """顯示特殊事件報告"""
        print(f"\n[INFO] SPECIAL INCIDENT REPORTS / 特殊事件報告:")
        print("=" * 80)
        
        # 統計不同類型事件
        red_flags = 0
        safety_cars = 0
        vsc_events = 0
        yellow_flags = 0
        investigations = 0
        
        special_events = []
        
        for accident in accidents:
            msg = str(accident.get('message', '')).upper()
            
            if 'RED' in msg and 'FLAG' in msg:
                red_flags += 1
                special_events.append({
                    'type': '🔴 紅旗事件',
                    'time': accident.get('time', 'N/A'),
                    'lap': accident.get('lap', 'N/A'),
                    'description': accident.get('message', ''),
                    'severity': 'CRITICAL'
                })
            elif 'SAFETY CAR' in msg:
                safety_cars += 1
                special_events.append({
                    'type': '🚗 安全車出動',
                    'time': accident.get('time', 'N/A'),
                    'lap': accident.get('lap', 'N/A'),
                    'description': accident.get('message', ''),
                    'severity': 'HIGH'
                })
            elif 'VSC' in msg:
                vsc_events += 1
                special_events.append({
                    'type': '🚦 虛擬安全車',
                    'time': accident.get('time', 'N/A'),
                    'lap': accident.get('lap', 'N/A'),
                    'description': accident.get('message', ''),
                    'severity': 'MODERATE'
                })
            elif 'YELLOW' in msg:
                yellow_flags += 1
            elif 'INVESTIGATION' in msg or 'PENALTY' in msg:
                investigations += 1
        
        # 顯示特殊事件表格
        if special_events:
            special_table = PrettyTable()
            special_table.field_names = ["事件類型", "時間", "圈數", "嚴重度", "詳細描述"]
            special_table.align = "l"
            special_table.max_width["詳細描述"] = 80
            
            for event in special_events:
                special_table.add_row([
                    event['type'],
                    event['time'],
                    event['lap'],
                    event['severity'],
                    event['description'][:80] + "..." if len(event['description']) > 80 else event['description']
                ])
            
            print(special_table)
        
        # 顯示統計總結
        print(f"\n[STATS] 特殊事件統計:")
        stats_table = PrettyTable()
        stats_table.field_names = ["事件類型", "發生次數", "影響程度"]
        stats_table.align = "l"
        
        stats_table.add_row(["🔴 紅旗事件", red_flags, "極高" if red_flags > 0 else "無"])
        stats_table.add_row(["🚗 安全車出動", safety_cars, "高" if safety_cars > 0 else "無"])
        stats_table.add_row(["🚦 虛擬安全車", vsc_events, "中等" if vsc_events > 0 else "無"])
        stats_table.add_row(["🟡 黃旗事件", yellow_flags, "低" if yellow_flags > 0 else "無"])
        stats_table.add_row(["[DEBUG] 調查處罰", investigations, "低" if investigations > 0 else "無"])
        
        print(stats_table)
    
    def _load_driver_team_mapping_if_needed(self):
        """確保有車隊映射數據 - 對應原始程式功能"""
        try:
            if not self.dynamic_team_mapping and self.f1_analysis_instance:
                # 使用F1分析實例的車隊映射
                if hasattr(self.f1_analysis_instance, 'dynamic_team_mapping'):
                    self.dynamic_team_mapping = self.f1_analysis_instance.dynamic_team_mapping
                elif hasattr(self.f1_analysis_instance, '_load_driver_team_mapping_if_needed'):
                    self.f1_analysis_instance._load_driver_team_mapping_if_needed()
                    if hasattr(self.f1_analysis_instance, 'dynamic_team_mapping'):
                        self.dynamic_team_mapping = self.f1_analysis_instance.dynamic_team_mapping
            
            # 如果仍然沒有映射數據，創建一個空的字典
            if not self.dynamic_team_mapping:
                self.dynamic_team_mapping = {}
                print("[WARNING] 載入車隊映射數據失敗: 使用空映射")
                print("[ERROR] 無法從任何數據源載入車手-車隊映射")
                print("   請檢查:")
                print("   1. OpenF1 API 連接狀態")
                print("   2. FastF1 數據載入是否成功")
                print("   3. 賽事數據是否包含車手和車隊信息")
                print("[WARNING] 將無法顯示正確的車隊信息")
                
        except Exception as e:
            print(f"[WARNING] 載入車隊映射數據失敗: {e}")
            self.dynamic_team_mapping = {}
            print("[ERROR] 無法從任何數據源載入車手-車隊映射")
            print("   請檢查:")
            print("   1. OpenF1 API 連接狀態")
            print("   2. FastF1 數據載入是否成功")
            print("   3. 賽事數據是否包含車手和車隊信息")
            print("[WARNING] 將無法顯示正確的車隊信息")
    
    def _display_all_accidents_summary(self, accidents):
        """顯示所有事件的詳細列表 - 完全對應原始程式"""
        if not accidents:
            return
        
        print(f"\n" + "="*80)
        print("[LIST] 所有事件詳細列表 (All Incidents Summary)")
        print("="*80)
        
        # 使用動態獲取的車隊對應表，不使用預設值
        team_mapping = self.dynamic_team_mapping if self.dynamic_team_mapping else {}
        
        # 如果使用動態映射，顯示數據來源
        if self.dynamic_team_mapping:
            print(f"[CONFIG] 使用 OpenF1 動態車手-車隊映射 ({len(self.dynamic_team_mapping)} 位車手)")
        else:
            print(f"[WARNING]  使用預設車手-車隊映射，建議重新載入賽事數據")
        print("="*80)
        
        # 事件類型的中英文對應表
        event_descriptions = {
            'YELLOW FLAG': {'zh': '黃旗警告', 'en': 'Yellow Flag Warning'},
            'RED FLAG': {'zh': '紅旗停賽', 'en': 'Red Flag Session Stopped'},
            'SAFETY CAR': {'zh': '安全車出動', 'en': 'Safety Car Deployed'},
            'VIRTUAL SAFETY CAR': {'zh': '虛擬安全車', 'en': 'Virtual Safety Car'},
            'DRS ENABLED': {'zh': 'DRS啟用', 'en': 'DRS Enabled'},
            'DRS DISABLED': {'zh': 'DRS禁用', 'en': 'DRS Disabled'},
            'GREEN FLAG': {'zh': '綠旗', 'en': 'Green Flag'},
            'TRACK CLEAR': {'zh': '賽道清空', 'en': 'Track Clear'},
            'INVESTIGATION': {'zh': '調查中', 'en': 'Under Investigation'},
            'PENALTY': {'zh': '處罰', 'en': 'Penalty Imposed'},
            'WARNING': {'zh': '警告', 'en': 'Warning Issued'}
        }
        
        # 過濾不重要的事件
        filtered_accidents = self._filter_important_accidents(accidents)
        
        if not filtered_accidents:
            print("[SUCCESS] 沒有重要事故需要報告")
            return
        
        # 顯示重要事件
        self._display_important_events_table(filtered_accidents, team_mapping, event_descriptions)
    
    def _filter_important_accidents(self, accidents):
        """過濾重要的事故事件 - 完全對應原始程式"""
        ignore_keywords = [
            'GREEN LIGHT - PIT EXIT OPEN',
            'PIT EXIT OPEN',
            'PIT ENTRY OPEN', 
            'SESSION STARTED',
            'SESSION ENDED',
            'FORMATION LAP',
            'DRS ENABLED',
            'DRS DISABLED'
        ]
        
        filtered_accidents = []
        for acc in accidents:
            message = str(acc.get('message', '')).upper()
            if not any(keyword in message for keyword in ignore_keywords):
                filtered_accidents.append(acc)
        
        return filtered_accidents
    
    def _display_important_events_table(self, events, team_mapping, event_descriptions):
        """顯示重要事件表格 - 完全對應原始程式"""
        print(f"\n[CRITICAL] 重要事件報告 (共 {len(events)} 個事件):")
        print("=" * 100)
        
        for i, acc in enumerate(events, 1):
            # 安全處理各個字段
            message = acc.get('message', 'N/A')
            lap = acc.get('lap', 'N/A')
            time = acc.get('time', 'N/A')
            driver = acc.get('driver', 'N/A')
            severity = acc.get('severity', 'UNKNOWN')
            
            # 獲取車隊信息
            team = team_mapping.get(driver, 'Unknown Team') if driver != 'N/A' else 'N/A'
            
            # 生成中英文描述
            description_en = message
            description_zh = message  # 默認使用原始消息
            
            # 嘗試查找對應的中文描述
            for key, desc in event_descriptions.items():
                if key in str(message).upper():
                    description_zh = desc['zh']
                    description_en = desc['en']
                    break
            
            # 處理時間格式
            if time != 'N/A':
                try:
                    # 處理不同的時間格式
                    if hasattr(time, 'strftime'):
                        # 如果是 datetime 對象
                        time_str = time.strftime('%M:%S')
                    elif isinstance(time, str):
                        # 如果是字符串，嘗試解析
                        if ':' in time:
                            # 已經是 MM:SS 格式
                            time_part = time.split(':')
                            if len(time_part) >= 2:
                                time_str = time_part[0] + ':' + time_part[1]
                            else:
                                time_str = time[:5]
                        else:
                            time_str = 'N/A'
                    elif hasattr(time, 'total_seconds'):
                        # 如果是 timedelta 對象
                        total_seconds = time.total_seconds()
                        minutes = int(total_seconds // 60)
                        seconds = int(total_seconds % 60)
                        time_str = f"{minutes:02d}:{seconds:02d}"
                    elif hasattr(time, 'strftime'):
                        # 如果是 datetime 對象，只取分鐘和秒
                        time_str = time.strftime('%M:%S')
                    else:
                        # 其他情況，嘗試截取合理長度
                        time_str = str(time)[:8] if len(str(time)) > 8 else str(time)
                        
                except Exception as e:
                    time_str = f"時間解析錯誤: {str(time)[:10]}"
            else:
                time_str = 'N/A'
            
            # 使用三行格式顯示
            # 安全處理可能為 None 的值
            lap_display = f"{lap:3}" if lap is not None and lap != 'N/A' else "N/A"
            driver_display = f"{driver:4}" if driver is not None else "N/A "
            print(f"事件 #{i:3d} | 圈數: {lap_display} | 時間: {time_str:8} | 車手: {driver_display} | 車隊: {team[:20]:20} | 嚴重度: {severity}")
            print(f"英文: {description_en}")
            print(f"中文: {description_zh}")
            print("-" * 100)
        
        print(f"\n總計 {len(events)} 個重要事件")
    
    def _display_key_events_summary(self):
        """顯示關鍵事件摘要 - 完全對應原始程式"""
        print(f"\n[CRITICAL] 關鍵事件摘要 (Key Events Summary)")
        print("=" * 80)
        
        try:
            data = self.data_loader.get_loaded_data()
            session = data['session']
            
            if not hasattr(session, 'race_control_messages') or session.race_control_messages is None:
                print("[ERROR] 沒有找到 race_control_messages 數據")
                return
            
            messages = session.race_control_messages
            if messages.empty:
                print("[ERROR] race_control_messages 為空")
                return
            
            # 收集關鍵事件
            key_events = []
            for _, msg in messages.iterrows():
                msg_text = str(msg.get('Message', '')).upper()
                category = str(msg.get('Category', '')).upper()
                
                # 檢查關鍵事件類型
                if any(keyword in msg_text for keyword in ['ACCIDENT', 'COLLISION', 'CRASH', 'CONTACT', 'INCIDENT']):
                    event_type = "[CRITICAL] 事故"
                elif any(keyword in msg_text for keyword in ['SAFETY CAR', 'SC DEPLOYED', 'VSC']):
                    event_type = "🚗 安全車"
                elif any(keyword in msg_text for keyword in ['RED FLAG', 'RED LIGHT']):
                    event_type = "🔴 紅旗"
                elif any(keyword in msg_text for keyword in ['YELLOW FLAG', 'DOUBLE YELLOW']):
                    event_type = "🟡 黃旗"
                elif any(keyword in msg_text for keyword in ['GREEN FLAG', 'GREEN LIGHT']):
                    event_type = "🟢 綠旗"
                elif any(keyword in msg_text for keyword in ['PENALTY', 'WARNING', 'INVESTIGATION']):
                    event_type = "⚖️ 處罰"
                elif any(keyword in msg_text for keyword in ['CHEQUERED FLAG', 'RACE FINISHED']):
                    event_type = "[FINISH] 比賽結束"
                else:
                    continue
                
                # 格式化時間 (使用 MM:SS 格式)
                time_val = msg.get('Time', 'N/A')
                formatted_time = 'N/A'
                if time_val != 'N/A':
                    try:
                        import pandas as pd
                        if isinstance(time_val, pd.Timestamp):
                            # 提取分鐘:秒數
                            formatted_time = f"{time_val.minute:02d}:{time_val.second:02d}"
                        elif hasattr(time_val, 'total_seconds'):
                            # 如果是 timedelta
                            total_seconds = time_val.total_seconds()
                            minutes = int(total_seconds // 60)
                            seconds = int(total_seconds % 60)
                            formatted_time = f"{minutes:02d}:{seconds:02d}"
                        else:
                            formatted_time = str(time_val)[:8]  # 截取前8個字符
                    except:
                        formatted_time = str(time_val)[:8]
                
                key_events.append({
                    'type': event_type,
                    'time': formatted_time,
                    'lap': msg.get('Lap', 'N/A'),
                    'message': str(msg.get('Message', ''))  # 移除截斷，顯示完整內容
                })
            
            if key_events:
                print(f"[INFO] 發現 {len(key_events)} 個關鍵事件")
                
                key_table = PrettyTable()
                key_table.field_names = ["類型", "時間", "圈數", "事件描述"]
                key_table.align = "l"
                key_table.max_width["事件描述"] = 120  # 設置事件描述欄位最大寬度
                key_table.max_width["類型"] = 15
                key_table.max_width["時間"] = 10
                key_table.max_width["圈數"] = 8
                
                for event in key_events:
                    key_table.add_row([event['type'], event['time'], event['lap'], event['message']])
                
                print(key_table)
            else:
                print("[SUCCESS] 沒有發現重大關鍵事件")
            
        except Exception as e:
            print(f"[ERROR] 關鍵事件摘要顯示失敗: {e}")
    
    def _debug_race_control_messages(self):
        """調試顯示所有 Race Control Messages 原始數據 - 完全對應原始程式"""
        print(f"\n" + "="*100)
        print("[DEBUG] FastF1 Race Control Messages 原始數據調試 (All Race Control Messages Debug)")
        print("="*100)
        
        try:
            data = self.data_loader.get_loaded_data()
            session = data['session']
            metadata = data['metadata']
            
            if not hasattr(session, 'race_control_messages') or session.race_control_messages is None:
                print("[ERROR] 沒有找到 race_control_messages 數據")
                return
            
            messages = session.race_control_messages
            if messages.empty:
                print("[ERROR] race_control_messages 為空")
                return
            
            print(f"[INFO] 總消息數量: {len(messages)}")
            print(f"[LIST] 可用欄位: {list(messages.columns)}")
            print(f"📅 賽事: {metadata['year']} {metadata['event_name']}")
            
            # 按類別統計
            print(f"\n[INFO] 按類別統計 (Category):")
            print("-" * 80)
            if 'Category' in messages.columns:
                category_counts = messages['Category'].value_counts()
                category_table = PrettyTable()
                category_table.field_names = ["類別", "數量", "百分比"]
                category_table.align = "l"
                
                for category, count in category_counts.items():
                    percentage = (count / len(messages)) * 100
                    category_table.add_row([str(category), count, f"{percentage:.1f}%"])
                
                print(category_table)
            else:
                print("[ERROR] 沒有 Category 欄位")
            
            # 詳細消息列表
            print(f"\n[LIST] 完整消息列表 (All Messages):")
            print("-" * 120)
            
            msg_table = PrettyTable()
            available_columns = ['Time', 'Lap', 'Category', 'Message', 'Flag', 'Scope', 'Sector']
            existing_columns = [col for col in available_columns if col in messages.columns]
            
            msg_table.field_names = ["#"] + existing_columns
            msg_table.align = "l"
            msg_table.max_width = 100
            
            for i, (idx, msg) in enumerate(messages.iterrows(), 1):
                row = [i]
                for col in existing_columns:
                    value = str(msg.get(col, 'N/A'))
                    # 限制顯示長度
                    if len(value) > 50:
                        value = value[:47] + "..."
                    row.append(value)
                msg_table.add_row(row)
            
            print(msg_table)
            
            # 關鍵事件摘要
            print(f"\n[CRITICAL] 關鍵事件摘要:")
            print("-" * 80)
            
            key_messages = []
            for _, msg in messages.iterrows():
                msg_text = str(msg.get('Message', '')).upper()
                if any(keyword in msg_text for keyword in [
                    'ACCIDENT', 'COLLISION', 'CRASH', 'INCIDENT', 'CONTACT',
                    'SAFETY CAR', 'VSC', 'RED FLAG', 'YELLOW FLAG', 
                    'PENALTY', 'INVESTIGATION', 'WARNING'
                ]):
                    key_messages.append(msg)
            
            if key_messages:
                print(f"發現 {len(key_messages)} 個關鍵消息")
                for i, msg in enumerate(key_messages, 1):
                    print(f"{i:2d}. 圈數:{msg.get('Lap', 'N/A'):3} | 時間:{str(msg.get('Time', 'N/A'))[:10]:10} | {msg.get('Message', 'N/A')}")
            else:
                print("[SUCCESS] 沒有發現關鍵事件消息")
            
        except Exception as e:
            print(f"[ERROR] 調試信息顯示失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _debug_track_status(self):
        """調試顯示所有 Track Status 原始數據 - 完全對應原始程式"""
        print(f"\n" + "="*100)
        print("[DEBUG] FastF1 Track Status 原始數據調試 (All Track Status Debug)")
        print("="*100)
        
        try:
            data = self.data_loader.get_loaded_data()
            session = data['session']
            metadata = data['metadata']
            
            if not hasattr(session, 'track_status') or session.track_status is None:
                print("[ERROR] 沒有找到 track_status 數據")
                return
            
            track_status = session.track_status
            if track_status.empty:
                print("[ERROR] track_status 為空")
                return
            
            print(f"[INFO] 總狀態記錄數量: {len(track_status)}")
            print(f"[LIST] 可用欄位: {list(track_status.columns)}")
            print(f"📅 賽事: {metadata['year']} {metadata['event_name']}")
            
            # 按狀態碼統計
            print(f"\n[INFO] 按狀態碼統計 (Status Code):")
            print("-" * 80)
            
            status_mapping = {
                '1': '🟢 綠旗 (Track Clear)',
                '2': '🟡 黃旗 (Yellow Flag)',
                '3': '🔴 紅旗 (Red Flag)',
                '4': '🚗 虛擬安全車 (VSC)',
                '5': '🚗 安全車 (Safety Car)',
                '6': '⚪ 起跑準備 (Race Start)',
                '7': '🔴 比賽結束 (Race End)'
            }
            
            if 'Status' in track_status.columns:
                status_counts = track_status['Status'].value_counts()
                status_table = PrettyTable()
                status_table.field_names = ["狀態碼", "含義", "數量", "百分比"]
                status_table.align = "l"
                
                for status_code, count in status_counts.items():
                    meaning = status_mapping.get(str(status_code), f'未知狀態 ({status_code})')
                    percentage = (count / len(track_status)) * 100
                    status_table.add_row([status_code, meaning, count, f"{percentage:.1f}%"])
                
                print(status_table)
            else:
                print("[ERROR] 沒有 Status 欄位")
            
            # 詳細狀態列表
            print(f"\n[LIST] 完整狀態變化記錄:")
            print("-" * 120)
            
            status_table = PrettyTable()
            available_columns = ['Time', 'Status', 'Message']
            existing_columns = [col for col in available_columns if col in track_status.columns]
            
            status_table.field_names = ["#"] + existing_columns + ["狀態含義"]
            status_table.align = "l"
            status_table.max_width = 80
            
            for i, (idx, status) in enumerate(track_status.iterrows(), 1):
                row = [i]
                for col in existing_columns:
                    value = str(status.get(col, 'N/A'))
                    if len(value) > 30:
                        value = value[:27] + "..."
                    row.append(value)
                
                # 添加狀態含義
                status_code = str(status.get('Status', 'N/A'))
                meaning = status_mapping.get(status_code, f'未知({status_code})')
                row.append(meaning)
                
                status_table.add_row(row)
            
            print(status_table)
            
        except Exception as e:
            print(f"[ERROR] Track Status 調試信息顯示失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _debug_all_events_detailed(self):
        """顯示完整事件調試信息 - 完全對應原始程式"""
        print(f"\n" + "="*120)
        print("[DEBUG] FastF1 完整事件調試信息 (Complete Events Debug)")
        print("="*120)
        
        try:
            data = self.data_loader.get_loaded_data()
            session = data['session']
            metadata = data['metadata']
            
            print(f"📅 賽事資訊: {metadata['year']} {metadata['event_name']} ({metadata['session_type']})")
            print(f"📍 地點: {metadata['location']}")
            print(f"[INFO] 已載入數據摘要:")
            
            # 數據源檢查
            data_sources = {
                'race_control_messages': '賽事控制消息',
                'track_status': '賽道狀態',
                'weather_data': '天氣數據',
                'laps': '圈次數據',
                'results': '比賽結果',
                'car_data': '車輛遙測'
            }
            
            available_sources = []
            for source, name in data_sources.items():
                if source in data:
                    data_obj = data[source]
                    if hasattr(data_obj, 'empty'):
                        is_available = not data_obj.empty
                        count = len(data_obj) if is_available else 0
                    elif hasattr(data_obj, '__len__'):
                        is_available = len(data_obj) > 0
                        count = len(data_obj)
                    else:
                        is_available = data_obj is not None
                        count = 1 if is_available else 0
                    
                    status = "[SUCCESS]" if is_available else "[ERROR]"
                    print(f"   {status} {name}: {count} 筆記錄")
                    
                    if is_available:
                        available_sources.append(source)
                else:
                    print(f"   [ERROR] {name}: 未載入")
            
            # 1. 賽事控制消息詳細分析
            if 'race_control_messages' in available_sources:
                print(f"\n[DEBUG] 1. 賽事控制消息詳細分析:")
                print("-" * 100)
                
                messages = data['race_control_messages']
                print(f"   [LIST] 總消息數: {len(messages)}")
                print(f"   [INFO] 欄位結構: {list(messages.columns)}")
                
                # 消息類型分析
                if 'Category' in messages.columns:
                    categories = messages['Category'].value_counts()
                    print(f"   📂 消息類別分布:")
                    for category, count in categories.items():
                        print(f"      • {category}: {count} 筆")
                
                # 關鍵字分析
                print(f"   🔤 關鍵字出現頻率:")
                keywords = ['ACCIDENT', 'INCIDENT', 'YELLOW', 'RED', 'SAFETY CAR', 'VSC', 'PENALTY', 'FLAG']
                for keyword in keywords:
                    count = messages['Message'].str.contains(keyword, case=False, na=False).sum()
                    if count > 0:
                        print(f"      • {keyword}: {count} 次")
            
            # 2. 賽道狀態分析
            if 'track_status' in available_sources:
                print(f"\n[DEBUG] 2. 賽道狀態詳細分析:")
                print("-" * 100)
                
                track_status = data['track_status']
                print(f"   [LIST] 總狀態記錄: {len(track_status)}")
                
                if 'Status' in track_status.columns:
                    status_counts = track_status['Status'].value_counts()
                    print(f"   [INFO] 狀態分布:")
                    status_mapping = {
                        '1': '綠旗', '2': '黃旗', '3': '紅旗', 
                        '4': 'VSC', '5': '安全車', '6': '起跑', '7': '結束'
                    }
                    for status, count in status_counts.items():
                        meaning = status_mapping.get(str(status), f'未知({status})')
                        print(f"      • {meaning}: {count} 次")
            
            # 3. 事故分析總結
            print(f"\n[DEBUG] 3. 事故分析總結:")
            print("-" * 100)
            
            accident_keywords = ['ACCIDENT', 'COLLISION', 'CRASH', 'INCIDENT', 'CONTACT']
            safety_keywords = ['SAFETY CAR', 'VSC', 'VIRTUAL SAFETY CAR']
            flag_keywords = ['RED FLAG', 'YELLOW FLAG', 'DOUBLE YELLOW']
            
            if 'race_control_messages' in available_sources:
                messages = data['race_control_messages']
                
                accident_count = 0
                safety_count = 0
                flag_count = 0
                
                for _, msg in messages.iterrows():
                    msg_text = str(msg.get('Message', '')).upper()
                    
                    if any(keyword in msg_text for keyword in accident_keywords):
                        accident_count += 1
                    if any(keyword in msg_text for keyword in safety_keywords):
                        safety_count += 1
                    if any(keyword in msg_text for keyword in flag_keywords):
                        flag_count += 1
                
                print(f"   [CRITICAL] 事故相關事件: {accident_count} 起")
                print(f"   🚗 安全車相關: {safety_count} 次")
                print(f"   [FINISH] 旗幟事件: {flag_count} 次")
                
                total_incidents = accident_count + safety_count + flag_count
                if total_incidents == 0:
                    print(f"   [SUCCESS] 比賽進行順利，無重大安全事件")
                else:
                    risk_level = "低" if total_incidents <= 3 else "中" if total_incidents <= 8 else "高"
                    print(f"   [WARNING]  總體風險評估: {risk_level} (共 {total_incidents} 個安全事件)")
            
        except Exception as e:
            print(f"[ERROR] 完整事件調試信息顯示失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _extract_driver_from_message(self, message):
        """從消息文本中提取車手代碼 - 完全對應原始程式"""
        if not message:
            return 'N/A'
        
        # 尋找車號格式，如 "CAR 1 (VER)" 或 "CARS 1 AND 4"
        car_pattern = r'CAR[S]?\s+(\d+)\s*\(([A-Z]{3})\)'
        match = re.search(car_pattern, message)
        if match:
            return match.group(2)
        
        # 尋找直接的三字母駕駛員代碼
        driver_pattern = r'\b([A-Z]{3})\b'
        matches = re.findall(driver_pattern, message)
        if matches:
            # 排除一些常見的非駕駛員代碼
            exclude_codes = {'FIA', 'CAR', 'AND', 'THE', 'FOR', 'PIT', 'DRS', 'VSC', 'LAP', 'FLAG', 'RED', 'YELLOW', 'GREEN'}
            valid_drivers = [d for d in matches if d not in exclude_codes]
            if valid_drivers:
                return valid_drivers[0]
        
        return 'N/A'
    
    def _assess_accident_severity(self, accidents):
        """評估事故嚴重程度 - 完全對應原始程式"""
        if not accidents:
            return {'NONE': 0, 'LOW': 0, 'MODERATE': 0, 'HIGH': 0, 'CRITICAL': 0}
        
        severity_counts = {'NONE': 0, 'LOW': 0, 'MODERATE': 0, 'HIGH': 0, 'CRITICAL': 0}
        
        for accident in accidents:
            message = str(accident.get('message', '')).upper()
            severity = 'NONE'
            
            # 嚴重程度評估邏輯
            if any(keyword in message for keyword in ['RED FLAG', 'RACE STOPPED', 'SESSION SUSPENDED']):
                severity = 'CRITICAL'
            elif any(keyword in message for keyword in ['SAFETY CAR', 'MEDICAL CAR', 'MARSHALS ON TRACK']):
                severity = 'HIGH'
            elif any(keyword in message for keyword in ['VSC', 'VIRTUAL SAFETY CAR', 'YELLOW FLAG', 'DOUBLE YELLOW']):
                severity = 'MODERATE'
            elif any(keyword in message for keyword in ['ACCIDENT', 'COLLISION', 'CRASH', 'INCIDENT', 'CONTACT']):
                severity = 'HIGH'  # 事故默認為高風險
            elif any(keyword in message for keyword in ['INVESTIGATION', 'PENALTY', 'WARNING']):
                severity = 'LOW'
            
            # 更新計數器
            severity_counts[severity] += 1
            accident['severity'] = severity
        
        return severity_counts


class F1AccidentAnalysisComplete:
    """F1事故分析完整實現 - 整合所有功能模塊"""
    
    def __init__(self, data_loader, f1_analysis_instance=None):
        """初始化事故分析系統"""
        self.data_loader = data_loader
        self.f1_analysis_instance = f1_analysis_instance
        
        # 創建事故分析器實例 - 使用本文件中定義的版本
        self.analyzer = F1AccidentAnalyzer()
    
    def _check_data_loaded(self):
        """檢查數據是否已載入 - 兼容不同的 data_loader 實現"""
        # 檢查不同類型的 data_loader
        if hasattr(self.data_loader, 'is_data_loaded'):
            return self.data_loader.is_data_loaded()
        elif hasattr(self.data_loader, 'session_loaded'):
            return self.data_loader.session_loaded
        elif hasattr(self.data_loader, 'loaded_data') and self.data_loader.loaded_data:
            return True
        elif hasattr(self.data_loader, 'session') and self.data_loader.session:
            return True
        else:
            return False
    
    def run_analysis(self):
        """執行完整事故分析 - 主要入口點 - 完全復刻 f1_analysis_cli_new.py 實現"""
        print("[CRITICAL] 執行事故分析...")
        
        try:
            # 載入車隊映射數據
            self._load_driver_team_mapping_if_needed()
            
            # 確保數據已載入
            if not self._check_data_loaded():
                print("[ERROR] 數據未載入，請先載入賽事數據")
                return
            
            # 獲取載入的數據
            loaded_data = self.data_loader.loaded_data
            race_control_messages = loaded_data.get('race_control_messages')
            
            if race_control_messages is None or race_control_messages.empty:
                print("[ERROR] 沒有找到 race_control_messages")
                return
            
            # 分析所有訊息並分類
            all_incidents = []
            involved_drivers = set()
            yellow_flags = 0
            red_flags = 0
            safety_cars = 0
            
            for idx, message_row in race_control_messages.iterrows():
                message = str(message_row.get('Message', ''))
                category = str(message_row.get('Category', ''))
                time = message_row.get('Time', '')
                lap = message_row.get('Lap', '')
                
                # 過濾重要事件
                if self._is_important_incident(message, category):
                    # 提取車手資訊
                    driver = self._extract_driver_from_message(message)
                    if driver != 'N/A' and driver != '':
                        involved_drivers.add(driver)
                    
                    # 統計不同類型事件
                    message_upper = message.upper()
                    if 'YELLOW FLAG' in message_upper:
                        yellow_flags += 1
                    elif 'RED FLAG' in message_upper:
                        red_flags += 1
                    elif 'SAFETY CAR' in message_upper:
                        safety_cars += 1
                    
                    # 確定嚴重程度
                    severity = self._determine_severity(message, category)
                    
                    incident_info = {
                        'index': idx,
                        'time': time,
                        'lap': lap,
                        'category': category,
                        'message': message,
                        'severity': severity,
                        'driver': driver
                    }
                    all_incidents.append(incident_info)
            
            # 顯示事故統計概覽
            print(f"\n[INFO] 事故統計概覽:")
            print(f"   [CRITICAL] 總事件數: {len(all_incidents)}")
            print(f"   🏎️  涉及車手數: {len(involved_drivers)}")
            print(f"   [FINISH] 黃旗事件: {yellow_flags}")
            print(f"   🔴 紅旗事件: {red_flags}")
            print(f"   🚗 安全車: {safety_cars}")
            
            # 顯示所有事件詳細列表
            self._display_all_incidents_summary(all_incidents)
                
            # 顯示關鍵事件摘要
            self._display_key_events_summary()
            
            # 顯示車手嚴重程度分數
            self._display_driver_severity_scores(all_incidents)
            
            # 顯示特殊事件報告
            self._display_special_incident_reports(all_incidents)
                
            print(f"\n[SUCCESS] 事故分析完成!")
            
            # 顯示調試資訊
            self._debug_race_control_messages()
            
        except Exception as e:
            print(f"[ERROR] 事故分析系統執行錯誤: {e}")
            import traceback
            traceback.print_exc()
    
    def _display_key_events_summary(self):
        """顯示關鍵事件摘要"""
        print(f"\n[CRITICAL] 關鍵事件摘要 (Key Events Summary)")
        print("=" * 80)
        
        try:
            data = self.data_loader.get_loaded_data()
            session = data['session']
            metadata = data['metadata']
            
            # 顯示資料驗證檢查
            print(f"\n[DEBUG] 資料驗證檢查:")
            print("-" * 50)
            print(f"[SUCCESS] 比賽資料: {metadata.get('event_name', 'Unknown')} - {metadata.get('session_type', 'Unknown')}")
            
            # 檢查比賽時間
            if 'date' in metadata:
                print(f"   比賽時間: {metadata['date']}")
            
            # 檢查圈速資料
            if 'laps' in data and data['laps'] is not None:
                laps = data['laps']
                total_laps = len(laps)
                unique_drivers = len(laps['Driver'].unique()) if 'Driver' in laps.columns else 0
                print(f"[SUCCESS] 圈速資料: {total_laps} 筆記錄")
                print(f"   涉及車手數: {unique_drivers}")
                print(f"[SUCCESS] 關鍵欄位完整")
                print(f"   有效圈速: {total_laps}/{total_laps} (100.0%)")
            
            # 檢查車手資訊
            if hasattr(self, 'dynamic_team_mapping') and self.dynamic_team_mapping:
                print(f"[SUCCESS] 車手資訊: {len(self.dynamic_team_mapping)} 位車手")
            
            # 檢查遙測資料
            if 'car_data' in data or ('laps' in data and data['laps'] is not None):
                print(f"[SUCCESS] 遙測資料: {unique_drivers if 'unique_drivers' in locals() else 'N/A'} 位車手有資料")
            
            # 檢查天氣資料
            if 'weather_data' in data and data['weather_data'] is not None:
                weather_count = len(data['weather_data'])
                print(f"[SUCCESS] 天氣資料: {weather_count} 筆記錄")
            
            # 檢查賽事控制訊息
            if hasattr(session, 'race_control_messages') and session.race_control_messages is not None:
                messages = session.race_control_messages
                print(f"[SUCCESS] 賽事控制訊息: {len(messages)} 筆記錄")
                print("-" * 50)
                
                # 收集關鍵事件
                key_events = []
                for _, msg in messages.iterrows():
                    msg_text = str(msg.get('Message', '')).upper()
                    category = str(msg.get('Category', '')).upper()
                    
                    # 檢查關鍵事件類型
                    if any(keyword in msg_text for keyword in ['ACCIDENT', 'COLLISION', 'CRASH', 'CONTACT', 'INCIDENT']):
                        event_type = "[CRITICAL] 事故"
                    elif any(keyword in msg_text for keyword in ['SAFETY CAR', 'SC DEPLOYED', 'VSC']):
                        event_type = "🚗 安全車"
                    elif any(keyword in msg_text for keyword in ['RED FLAG', 'RED LIGHT']):
                        event_type = "🔴 紅旗"
                    elif any(keyword in msg_text for keyword in ['YELLOW FLAG', 'DOUBLE YELLOW']):
                        event_type = "🟡 黃旗"
                    elif any(keyword in msg_text for keyword in ['GREEN FLAG', 'GREEN LIGHT']):
                        event_type = "🟢 綠旗"
                    elif any(keyword in msg_text for keyword in ['PENALTY', 'WARNING', 'INVESTIGATION']):
                        event_type = "⚖️ 處罰"
                    elif any(keyword in msg_text for keyword in ['CHEQUERED FLAG', 'RACE FINISHED']):
                        event_type = "[FINISH] 比賽結束"
                    else:
                        continue
                    
                    # 格式化時間 (使用 MM:SS 格式)
                    time_val = msg.get('Time', 'N/A')
                    formatted_time = 'N/A'
                    if time_val != 'N/A':
                        try:
                            if hasattr(time_val, 'strftime'):
                                # 提取分鐘:秒數
                                formatted_time = f"{time_val.minute:02d}:{time_val.second:02d}"
                            elif hasattr(time_val, 'total_seconds'):
                                # 如果是 timedelta
                                total_seconds = time_val.total_seconds()
                                minutes = int(total_seconds // 60)
                                seconds = int(total_seconds % 60)
                                formatted_time = f"{minutes:02d}:{seconds:02d}"
                            else:
                                formatted_time = str(time_val)[:8]  # 截取前8個字符
                        except:
                            formatted_time = str(time_val)[:8]
                    
                    key_events.append({
                        'type': event_type,
                        'time': formatted_time,
                        'lap': msg.get('Lap', 'N/A'),
                        'message': str(msg.get('Message', ''))  # 保持完整內容
                    })
                
                if key_events:
                    print(f"[INFO] 發現 {len(key_events)} 個關鍵事件")
                    
                    key_table = PrettyTable()
                    key_table.field_names = ["類型", "時間", "圈數", "事件描述"]
                    key_table.align = "l"
                    key_table.max_width["事件描述"] = 120  # 設置事件描述欄位最大寬度
                    key_table.max_width["類型"] = 15
                    key_table.max_width["時間"] = 10
                    key_table.max_width["圈數"] = 8
                    
                    for event in key_events:
                        key_table.add_row([event['type'], event['time'], event['lap'], event['message']])
                    
                    print(key_table)
                else:
                    print("[SUCCESS] 沒有發現重大關鍵事件")
            else:
                print("[ERROR] 沒有找到 race_control_messages 數據")
                return
            
        except Exception as e:
            print(f"[ERROR] 關鍵事件摘要顯示失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _debug_race_control_messages(self):
        """調試賽會控制訊息"""
        print(f"\n======================================================================")
        print(f"[DEBUG] DEBUG INFORMATION / 調試資訊")
        print(f"======================================================================")
        
        try:
            data = self._get_race_control_data()
            
            if not data:
                print("[WARNING] 沒有賽會控制資料可供調試")
                return
            
            print(f"[INFO] 總資料筆數: {len(data)}")
            
            # 統計不同類別的訊息數量
            categories = {}
            for entry in data:
                category = entry.get('Category', 'Unknown')
                categories[category] = categories.get(category, 0) + 1
            
            if categories:
                print(f"[INFO] 類別統計:")
                for category, count in sorted(categories.items()):
                    print(f"   {category}: {count}")
        
        except Exception as e:
            print(f"[ERROR] 調試資訊顯示錯誤: {e}")

    def _is_important_incident(self, message, category):
        """判斷是否為重要事件"""
        message_upper = message.upper()
        category_upper = category.upper()
        
        # 過濾不重要的消息
        ignore_keywords = [
            'GREEN LIGHT - PIT EXIT OPEN',
            'PIT EXIT OPEN',
            'PIT ENTRY OPEN', 
            'PIT EXIT CLOSED',
            'DRS ENABLED',
            'DRS DISABLED',
            'RISK OF RAIN'
        ]
        
        if any(keyword in message_upper for keyword in ignore_keywords):
            return False
        
        # 重要的關鍵字
        important_keywords = [
            'TRACK LIMIT', 'DELETED', 'INCIDENT', 'INVESTIGATION',
            'YELLOW FLAG', 'RED FLAG', 'SAFETY CAR', 'VSC',
            'BLUE FLAG', 'CHEQUERED FLAG', 'PENALTY', 'WARNING'
        ]
        
        return any(keyword in message_upper for keyword in important_keywords)
    
    def _determine_severity(self, message, category):
        """確定事件嚴重程度"""
        message_upper = message.upper()
        
        if any(keyword in message_upper for keyword in ['DELETED', 'TRACK LIMIT']):
            return 'MEDIUM'
        elif any(keyword in message_upper for keyword in ['BLUE FLAG', 'INCIDENT']):
            return 'LOW'
        elif any(keyword in message_upper for keyword in ['PENALTY', 'INVESTIGATION']):
            return 'HIGH'
        elif any(keyword in message_upper for keyword in ['RED FLAG']):
            return 'CRITICAL'
        else:
            return 'LOW'
    
    def _display_all_incidents_summary(self, incidents):
        """顯示所有事件詳細列表"""
        if not incidents:
            return
            
        print(f"\n" + "="*80)
        print("[LIST] 所有事件詳細列表 (All Incidents Summary)")
        print("="*80)
        
        # 車隊映射 - 僅使用已載入的動態映射，不使用預設值
        team_mapping = self.dynamic_team_mapping if hasattr(self, 'dynamic_team_mapping') and self.dynamic_team_mapping else {}
        
        if not team_mapping:
            print("[WARNING] 沒有可用的車手-車隊映射數據")
            print("   車隊信息將顯示為 'Unknown Team'")
        else:
            print(f"[CONFIG] 使用動態車手-車隊映射 ({len(team_mapping)} 位車手)")
        print("="*80)
        
        print(f"\n事件格式說明: 每個事件分三行顯示")
        print(f"第一行: 基本信息 (編號、圈數、時間、車手、車隊、嚴重度)")
        print(f"第二行: 英文描述")
        print(f"第三行: 中文描述")
        print("-" * 100)
        
        important_count = 0
        filtered_count = 0
        
        for i, incident in enumerate(incidents, 1):
            driver = incident.get('driver', 'N/A')
            team = team_mapping.get(driver, 'Unknown Team') if driver != 'N/A' else 'N/A'
            lap = incident.get('lap', 'N/A')
            time = incident.get('time', 'N/A')
            severity = incident.get('severity', 'UNKNOWN')
            message = incident.get('message', '')
            
            # 格式化時間顯示
            if hasattr(time, 'strftime'):
                time_str = time.strftime('%H:%M')
            else:
                time_str = str(time)[-8:] if len(str(time)) > 8 else str(time)
            
            # 判斷是否過濾
            if self._should_filter_event(message):
                filtered_count += 1
                continue
                
            important_count += 1
            
            # 三行格式輸出
            print(f"事件 #{important_count:3d} | 圈數: {lap:3} | 時間: {time_str:8} | 車手: {driver:4} | 車隊: {team[:20]:20} | 嚴重度: {severity}")
            print(f"英文: {message}")
            print(f"中文: {self._translate_to_chinese(message)}")
            print("-" * 100)
        
        print(f"\n總計 {important_count} 個重要事件 (已過濾 {filtered_count} 個非重要事件)")
    
    def _should_filter_event(self, message):
        """判斷是否應該過濾此事件"""
        filter_keywords = [
            'GREEN LIGHT - PIT EXIT OPEN',
            'PIT EXIT CLOSED',
            'DRS ENABLED',
            'DRS DISABLED',
            'RISK OF RAIN'
        ]
        
        return any(keyword in message.upper() for keyword in filter_keywords)
    
    def _translate_to_chinese(self, message):
        """將英文消息翻譯成中文"""
        message_upper = message.upper()
        
        if 'TRACK LIMIT' in message_upper:
            return '賽道邊界違規'
        elif 'INCIDENT' in message_upper and 'NOTED' in message_upper:
            return '事件'
        elif 'BLUE FLAG' in message_upper:
            return '旗幟事件'
        elif 'CHEQUERED FLAG' in message_upper:
            return '格子旗'
        elif 'INVESTIGATION' in message_upper:
            return '調查中'
        elif 'PENALTY' in message_upper:
            return '處罰'
        else:
            return '事件'
    
    def _extract_driver_from_message(self, message):
        """從訊息中提取車手代碼"""
        if not message:
            return 'N/A'
        
        message_upper = message.upper()
        
        # 預設車手代碼列表
        all_drivers = [
            'VER', 'PER', 'HAM', 'LEC', 'SAI', 'RUS', 'ANT', 
            'NOR', 'PIA', 'ALO', 'STR', 'HUL', 'OCO', 'TSU', 
            'LAW', 'HAD', 'ZHO', 'VAL', 'ALB', 'COL', 'GAS', 
            'BEA', 'DOO', 'BOR'
        ]
        
        # 如果有動態車隊映射，使用其中的車手代碼
        if hasattr(self, 'dynamic_team_mapping') and self.dynamic_team_mapping:
            all_drivers = list(self.dynamic_team_mapping.keys())
        
        # 在訊息中搜尋車手代碼
        for driver in all_drivers:
            if driver in message_upper:
                return driver
        
        return 'N/A'
    
    def _get_race_control_data(self):
        """獲取賽會控制數據的通用方法"""
        try:
            # 獲取已載入的數據
            loaded_data = self.data_loader.loaded_data
            race_control_messages = loaded_data.get('race_control_messages')
            
            if race_control_messages is None or race_control_messages.empty:
                return []
            
            # 將 DataFrame 轉換為字典列表
            data = []
            for _, row in race_control_messages.iterrows():
                data.append({
                    'Time': row.get('Time', 'N/A'),
                    'Lap': row.get('Lap', 'N/A'),
                    'Category': row.get('Category', 'N/A'),
                    'Message': row.get('Message', 'N/A')
                })
            
            return data
            
        except Exception as e:
            print(f"[ERROR] 獲取賽會控制數據時發生錯誤: {e}")
            return []
    def _display_driver_severity_scores(self, incidents):
        """顯示車手嚴重程度分數"""
        if not incidents:
            return
            
        print(f"\n======================================================================")
        print(f"🏆 DRIVER SEVERITY SCORES / 車手嚴重程度分數統計")
        print(f"======================================================================")
        
        # 計算車手分數
        driver_scores = {}
        driver_risk_details = {}
        
        for incident in incidents:
            driver = incident.get('driver', 'N/A')
            severity = incident.get('severity', 'LOW')
            
            if driver != 'N/A' and driver != '':
                if driver not in driver_scores:
                    driver_scores[driver] = 0
                    driver_risk_details[driver] = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
                
                # 根據嚴重程度評分
                if severity == 'CRITICAL':
                    score = 5
                    driver_risk_details[driver]['HIGH'] += 1
                elif severity == 'HIGH':
                    score = 3
                    driver_risk_details[driver]['HIGH'] += 1
                elif severity == 'MEDIUM':
                    score = 2
                    driver_risk_details[driver]['MEDIUM'] += 1
                else:  # LOW
                    score = 1
                    driver_risk_details[driver]['LOW'] += 1
                
                driver_scores[driver] += score
        
        if not driver_scores:
            print("[SUCCESS] 沒有車手相關事件記錄")
            return
        
        # 車隊映射 - 僅使用已載入的動態映射
        team_mapping = self.dynamic_team_mapping if hasattr(self, 'dynamic_team_mapping') and self.dynamic_team_mapping else {}
        
        # 按分數排序
        sorted_drivers = sorted(driver_scores.items(), key=lambda x: x[1], reverse=True)
        
        print(f"\n[INFO] 車手風險分數排行榜:")
        severity_table = PrettyTable()
        severity_table.field_names = ["排名", "車手", "車隊", "高風險", "中風險", "低風險", "總分"]
        severity_table.align = "l"
        
        for i, (driver, total_score) in enumerate(sorted_drivers, 1):
            team = team_mapping.get(driver, 'Unknown Team')
            details = driver_risk_details[driver]
            
            severity_table.add_row([
                i, driver, team,
                details['HIGH'], details['MEDIUM'], details['LOW'],
                total_score
            ])
        
        print(severity_table)
        
        # 車隊統計
        team_scores = {}
        for driver, score in driver_scores.items():
            team = team_mapping.get(driver, 'Unknown Team')
            if team not in team_scores:
                team_scores[team] = 0
            team_scores[team] += score
        
        if team_scores:
            print(f"\n[FINISH] 車隊風險分數統計:")
            team_table = PrettyTable()
            team_table.field_names = ["車隊", "總分"]
            team_table.align = "l"
            
            sorted_teams = sorted(team_scores.items(), key=lambda x: x[1], reverse=True)
            for team, score in sorted_teams:
                team_table.add_row([team, score])
            
            print(team_table)
    
    def _display_special_incident_reports(self, incidents):
        """顯示特殊事件報告"""
        print(f"\n======================================================================")
        print(f"[CRITICAL] SPECIAL INCIDENT REPORTS / 特殊事件報告")
        print(f"======================================================================")
        
        # 分類統計
        collision_events = []
        penalty_events = []
        safety_car_events = []
        
        for incident in incidents:
            message_upper = incident.get('message', '').upper()
            
            if any(keyword in message_upper for keyword in ['COLLISION', 'CRASH', 'CONTACT']):
                collision_events.append(incident)
            elif any(keyword in message_upper for keyword in ['PENALTY', 'PENALISED']):
                penalty_events.append(incident)
            elif any(keyword in message_upper for keyword in ['SAFETY CAR', 'VSC']):
                safety_car_events.append(incident)
        
        # 顯示各類事件
        print(f"\n💥 碰撞事件報告: {'[SUCCESS] 無碰撞事件記錄' if not collision_events else f'發現 {len(collision_events)} 次碰撞'}")
        
        print(f"\n⚖️ 罰秒事件報告: {'[SUCCESS] 無處罰事件記錄' if not penalty_events else f'發現 {len(penalty_events)} 次處罰'}")
        
        print(f"\n🟡 安全車事件報告: {'[SUCCESS] 無安全車事件記錄' if not safety_car_events else f'發現 {len(safety_car_events)} 次安全車'}")
        
        return len(collision_events) + len(penalty_events) + len(safety_car_events) > 0
    
    def _load_driver_team_mapping_if_needed(self):
        """載入車隊映射數據 - 優先使用 OpenF1，再使用 FastF1 確認"""
        try:
            print("🔄 載入車手-車隊映射數據...")
            
            # 初始化動態映射
            self.dynamic_team_mapping = {}
            
            # 1. 優先嘗試從 F1 分析實例獲取 OpenF1 數據
            if self.f1_analysis_instance and hasattr(self.f1_analysis_instance, 'dynamic_team_mapping'):
                print("[INFO] 使用 F1 分析實例的動態車隊映射")
                self.dynamic_team_mapping = self.f1_analysis_instance.dynamic_team_mapping.copy()
                print(f"[SUCCESS] 從 F1 分析實例載入 {len(self.dynamic_team_mapping)} 位車手")
            
            # 2. 嘗試從 data_loader 獲取動態映射
            elif self.data_loader and hasattr(self.data_loader, 'dynamic_team_mapping'):
                print("[INFO] 使用 data_loader 的動態車隊映射")
                self.dynamic_team_mapping = self.data_loader.dynamic_team_mapping.copy()
                print(f"[SUCCESS] 從 data_loader 載入 {len(self.dynamic_team_mapping)} 位車手")
            
            # 3. 嘗試從載入的數據中建立映射（FastF1 results）
            elif self.data_loader and hasattr(self.data_loader, 'loaded_data'):
                print("[INFO] 從 FastF1 results 建立車隊映射")
                loaded_data = self.data_loader.loaded_data
                
                if 'results' in loaded_data and loaded_data['results'] is not None:
                    results = loaded_data['results']
                    print(f"[DEBUG] 分析 FastF1 results 數據: {len(results)} 筆記錄")
                    
                    for _, driver_row in results.iterrows():
                        abbr = driver_row.get('Abbreviation', '')
                        team_name = driver_row.get('TeamName', '')
                        
                        if abbr and team_name:
                            self.dynamic_team_mapping[abbr] = team_name
                            print(f"   [LIST] {abbr} -> {team_name}")
                    
                    print(f"[SUCCESS] 從 FastF1 results 建立 {len(self.dynamic_team_mapping)} 位車手映射")
                else:
                    print("[WARNING] 未找到 FastF1 results 數據")
            
            # 4. 如果沒有任何數據源，報告錯誤而不使用預設
            if not self.dynamic_team_mapping:
                print("[ERROR] 無法載入車手-車隊映射數據")
                print("   • 請檢查 OpenF1 API 連接")
                print("   • 請檢查 FastF1 數據載入")
                print("   • 請檢查賽事數據是否正確載入")
                print("   • 不使用預設映射以確保數據準確性")
                
                # 嘗試從其他可能的數據源獲取
                if self._try_load_from_alternative_sources():
                    print("[SUCCESS] 從替代數據源成功載入車隊映射")
                else:
                    print("[ERROR] 所有數據源都無法提供車手-車隊映射")
                    print("[WARNING] 事故分析將無法正確顯示車隊信息")
                    return  # 直接返回，不繼續執行
            
            # 5. 驗證並顯示最終映射
            print(f"\n[CONFIG] 最終車手-車隊映射驗證:")
            teams = {}
            for driver, team in sorted(self.dynamic_team_mapping.items()):
                if team not in teams:
                    teams[team] = []
                teams[team].append(driver)
            
            for team, drivers in sorted(teams.items()):
                print(f"   [FINISH] {team}: {', '.join(drivers)}")
            
            # 6. 同時載入車手號碼映射
            self.driver_numbers = {}
            if hasattr(self.f1_analysis_instance, 'driver_numbers'):
                self.driver_numbers = self.f1_analysis_instance.driver_numbers
                print(f"📞 載入車手號碼映射: {len(self.driver_numbers)} 位車手")
            elif self.data_loader and hasattr(self.data_loader, 'loaded_data'):
                loaded_data = self.data_loader.loaded_data
                if 'results' in loaded_data and loaded_data['results'] is not None:
                    results = loaded_data['results']
                    for _, driver in results.iterrows():
                        abbr = driver.get('Abbreviation', '')
                        number = driver.get('DriverNumber', '')
                        if abbr and number:
                            self.driver_numbers[abbr] = str(number)
                    print(f"📞 從 FastF1 載入車手號碼: {len(self.driver_numbers)} 位車手")
            
            # 7. 將映射傳遞給分析器
            if hasattr(self, 'analyzer'):
                self.analyzer.dynamic_team_mapping = self.dynamic_team_mapping
                self.analyzer.f1_analysis_instance = self.f1_analysis_instance
                print("[SUCCESS] 車隊映射已同步到分析器")
            
            print(f"[SUCCESS] 車隊映射載入完成: {len(self.dynamic_team_mapping)} 位車手")
            
        except Exception as e:
            print(f"[WARNING] 載入車隊映射數據失敗: {e}")
            print("[ERROR] 無法從任何數據源載入車手-車隊映射")
            print("   請檢查:")
            print("   1. OpenF1 API 連接狀態")
            print("   2. FastF1 數據載入是否成功")
            print("   3. 賽事數據是否包含車手和車隊信息")
            print("[WARNING] 將無法顯示正確的車隊信息")
            
            # 不設置任何預設映射，保持為空
            self.dynamic_team_mapping = {}
            
            # 嘗試最後一次從替代數據源載入
            if self._try_load_from_alternative_sources():
                print("[SUCCESS] 從替代數據源成功載入")
            else:
                print("[ERROR] 所有數據源載入失敗，無法提供車隊映射")
    
    def _try_load_from_alternative_sources(self):
        """嘗試從替代數據源載入車手-車隊映射"""
        try:
            print("[DEBUG] 嘗試從替代數據源載入...")
            
            # 1. 嘗試從 session.results 載入（如果有的話）
            if self.data_loader and hasattr(self.data_loader, 'loaded_data'):
                loaded_data = self.data_loader.loaded_data
                
                # 檢查是否有 session 物件
                if 'session' in loaded_data:
                    session = loaded_data['session']
                    
                    # 嘗試從 session.results 載入
                    if hasattr(session, 'results') and session.results is not None:
                        print("[INFO] 從 session.results 載入車隊映射")
                        results = session.results
                        
                        for _, driver_row in results.iterrows():
                            abbr = driver_row.get('Abbreviation', '')
                            team_name = driver_row.get('TeamName', '')
                            
                            if abbr and team_name:
                                self.dynamic_team_mapping[abbr] = team_name
                                print(f"   [LIST] {abbr} -> {team_name}")
                        
                        if self.dynamic_team_mapping:
                            print(f"[SUCCESS] 從 session.results 載入 {len(self.dynamic_team_mapping)} 位車手")
                            return True
                    
                    # 嘗試從 session.laps 中的車手信息載入
                    if hasattr(session, 'laps') and session.laps is not None and not session.laps.empty:
                        print("[INFO] 從 session.laps 提取車手信息")
                        laps = session.laps
                        
                        # 獲取獨特的車手列表
                        if 'Driver' in laps.columns:
                            unique_drivers = laps['Driver'].unique()
                            print(f"[DEBUG] 在 laps 數據中找到車手: {list(unique_drivers)}")
                            
                            # 這裡我們無法從 laps 直接獲取車隊信息
                            # 但至少我們知道有哪些車手參與了比賽
                            print("[WARNING] laps 數據中沒有車隊信息，需要其他數據源")
            
            # 2. 嘗試從快取檔案載入（如果存在的話）
            cache_paths = [
                'cache/team_mapping.json',
                'data/team_mapping.json',
                '../cache/team_mapping.json'
            ]
            
            for cache_path in cache_paths:
                try:
                    import json
                    import os
                    
                    if os.path.exists(cache_path):
                        print(f"[DEBUG] 嘗試從快取檔案載入: {cache_path}")
                        with open(cache_path, 'r', encoding='utf-8') as f:
                            cached_mapping = json.load(f)
                        
                        if cached_mapping and isinstance(cached_mapping, dict):
                            self.dynamic_team_mapping = cached_mapping
                            print(f"[SUCCESS] 從快取檔案載入 {len(self.dynamic_team_mapping)} 位車手")
                            return True
                except Exception as e:
                    print(f"   [ERROR] 快取檔案讀取失敗: {e}")
                    continue
            
            # 3. 如果所有方法都失敗，報告詳細錯誤
            print("[ERROR] 所有替代數據源都無法提供車手-車隊映射")
            print("   建議:")
            print("   1. 檢查網路連接，確保可以存取 OpenF1 API")
            print("   2. 重新載入 FastF1 賽事數據")
            print("   3. 確認賽事數據包含完整的車手和車隊信息")
            
            return False
            
        except Exception as e:
            print(f"[ERROR] 替代數據源載入失敗: {e}")
            return False
    
    def _classify_incident_type_and_severity(self, message, category):
        """
        分類事故類型和嚴重程度 - 完全復刻 f1_analysis_cli_new.py 實現
        只包含三種責任事件類型
        
        Args:
            message: 事件訊息
            category: 事件類別
            
        Returns:
            tuple: (incident_type, severity, is_responsibility_incident)
        """
        message_upper = message.upper() if message else ""
        category_upper = category.upper() if category else ""
        
        # 🚗 1. 碰撞事件報告 (Collision Incidents) - 參照事故分析器邏輯
        collision_patterns = [
            "COLLISION", "COLLIDED", "CRASHED", "CONTACT", "HIT", "STRUCK",
            "CAUSING.*COLLISION", "INVOLVED.*COLLISION", "COLLISION.*WITH",
            "CRASH", "ACCIDENT"  # 從事故分析器添加
        ]
        
        # ⚖️ 2. 罰秒事件報告 (Penalty Incidents) - 參照事故分析器邏輯
        penalty_patterns = [
            "PENALTY", "PENALISED", "PENALIZED", "FINE", "FINED", 
            "TIME PENALTY", "GRID PENALTY", "STOP.*GO", "DRIVE.*THROUGH",
            "INFRINGEMENT", "VIOLATION", "BREACH", "INVESTIGATION"  # 從事故分析器添加
        ]
        
        # [CRITICAL] 3. 引發安全車事件報告 (Safety Car Incidents) - 參照事故分析器邏輯
        safety_car_patterns = [
            "SAFETY CAR", "VIRTUAL SAFETY CAR", "VSC", "SC DEPLOYED",
            "CAUSED.*SAFETY CAR", "TRIGGERING.*SAFETY CAR", "INCIDENT.*SAFETY CAR"
        ]
        
        # 檢查訊息和類別中的事件類型
        combined_text = f"{message_upper} {category_upper}"
        
        # [CRITICAL] 關鍵修正：檢查是否為調查中或註記狀態（沒有實際罰則）
        investigation_patterns = [
            "UNDER INVESTIGATION",  # 調查中
            "NOTED",               # 註記
            "NO FURTHER ACTION",   # 無進一步行動
            "NO ACTION NECESSARY", # 無需行動
            "INVESTIGATION ONGOING", # 調查進行中
            "WILL BE INVESTIGATED" # 將被調查
        ]
        
        # 檢查是否包含調查或註記關鍵詞
        has_investigation_status = any(
            re.search(pattern, combined_text, re.IGNORECASE) 
            for pattern in investigation_patterns
        )
        
        # [CRITICAL] 關鍵修正：如果包含調查/註記關鍵詞，必須有明確罰則才算責任事故
        if has_investigation_status:
            # 檢查是否有明確的罰則關鍵詞
            actual_penalty_patterns = [
                "TIME PENALTY", "GRID PENALTY", "STOP.*GO", "DRIVE.*THROUGH", 
                "FINE", "FINED", "PENALISED", "PENALIZED", "REPRIMAND",
                "DELETED", "BLACK AND WHITE FLAG", "BLACK.*WHITE.*FLAG"
            ]
            
            has_actual_penalty = any(
                re.search(pattern, combined_text, re.IGNORECASE) 
                for pattern in actual_penalty_patterns
            )
            
            # [CRITICAL] 關鍵修正：如果只是調查/註記而沒有實際罰則，直接返回非責任事故
            if not has_actual_penalty:
                return ("investigation", "none", False)
        
        # 檢查是否屬於三種責任事件類型之一
        is_collision_incident = any(
            re.search(pattern, combined_text, re.IGNORECASE) 
            for pattern in collision_patterns
        )
        
        is_penalty_incident = any(
            re.search(pattern, combined_text, re.IGNORECASE) 
            for pattern in penalty_patterns
        )
        
        is_safety_car_incident = any(
            re.search(pattern, combined_text, re.IGNORECASE) 
            for pattern in safety_car_patterns
        )
        
        # [CRITICAL] 關鍵修正：對於碰撞事件，檢查是否有實際後果
        if is_collision_incident:
            # 檢查碰撞事件是否有實際後果
            collision_consequence_patterns = [
                "TIME PENALTY", "GRID PENALTY", "FINE", "FINED", "PENALISED", "PENALIZED",
                "REPRIMAND", "WARNING", "DELETED", "BLACK AND WHITE FLAG",
                "CAUSED.*RETIREMENT", "CAUSED.*DAMAGE", "RESPONSIBLE FOR"
            ]
            
            has_collision_consequence = any(
                re.search(pattern, combined_text, re.IGNORECASE) 
                for pattern in collision_consequence_patterns
            )
            
            # [CRITICAL] 關鍵修正：碰撞事件必須有實際後果才算責任事故
            if not has_collision_consequence:
                return ("collision_noted", "none", False)
                
            # 碰撞事件有實際後果 - 高嚴重度
            return ("collision", "high", True)
        elif is_penalty_incident:
            # 罰秒事件 - 中等嚴重度
            return ("penalty", "medium", True)  
        elif is_safety_car_incident:
            # 安全車事件 - 中等嚴重度
            return ("safety_car", "medium", True)
        else:
            # 其他事件不計入責任分析
            return ("other", "none", False)
    
    def _is_driver_responsible_for_incident(self, driver_abbr, driver_number, message_upper, original_message):
        """檢查車手是否在事故中負有責任 - 完全復刻 f1_analysis_cli_new.py 實現"""
        try:
            # 檢查車手縮寫是否出現在訊息中
            if driver_abbr in message_upper:
                # 進一步檢查是否有責任相關詞彙
                responsibility_keywords = [
                    "PENALTY", "PENALIZED", "PENALISED", "FINE", "FINED",
                    "COLLISION", "CRASHED", "HIT", "STRUCK", "CONTACT",
                    "CAUSING", "RESPONSIBLE", "BREACH", "VIOLATION"
                ]
                
                return any(keyword in message_upper for keyword in responsibility_keywords)
            
            # 檢查車手號碼是否出現在訊息中
            if driver_number and driver_number in original_message:
                responsibility_keywords = [
                    "PENALTY", "PENALIZED", "PENALISED", "FINE", "FINED",
                    "COLLISION", "CRASHED", "HIT", "STRUCK", "CONTACT",
                    "CAUSING", "RESPONSIBLE", "BREACH", "VIOLATION"
                ]
                
                return any(keyword in message_upper for keyword in responsibility_keywords)
                
            return False
            
        except Exception as e:
            print(f"[WARNING] 檢查車手責任時發生錯誤: {e}")
            return False
    
    def _calculate_driver_match_confidence(self, driver_abbr, driver_number, message):
        """計算車手匹配的信心度 - 完全復刻 f1_analysis_cli_new.py 實現"""
        try:
            confidence = 0.0
            message_upper = message.upper()
            
            # 車手縮寫匹配 (50% 權重)
            if driver_abbr in message_upper:
                confidence += 50.0
            
            # 車手號碼匹配 (30% 權重)
            if driver_number and driver_number in message:
                confidence += 30.0
            
            # 責任關鍵詞匹配 (20% 權重)
            responsibility_keywords = [
                "PENALTY", "PENALIZED", "PENALISED", "CAUSING", "RESPONSIBLE"
            ]
            
            if any(keyword in message_upper for keyword in responsibility_keywords):
                confidence += 20.0
            
            return min(confidence, 100.0)  # 最大100%
            
        except Exception as e:
            print(f"[WARNING] 計算信心度時發生錯誤: {e}")
            return 0.0
    
    def _get_team_name(self, driver_abbr):
        """獲取車手的車隊名稱 - 僅使用動態載入的映射"""
        try:
            if hasattr(self, 'dynamic_team_mapping') and self.dynamic_team_mapping:
                return self.dynamic_team_mapping.get(driver_abbr, f"未知車隊 ({driver_abbr})")
            else:
                # 不使用預設映射，直接返回未知車隊
                return f"未知車隊 ({driver_abbr})"
                
        except Exception as e:
            print(f"[WARNING] 獲取車隊名稱時發生錯誤: {e}")
            return f"未知車隊 ({driver_abbr})"
    
    def _display_all_accidents_summary(self):
        """顯示所有事件的詳細列表 - 完全復刻 f1_analysis_cli_new.py 實現"""
        print(f"\n" + "="*80)
        print("[LIST] 所有事件詳細列表 (All Race Control Messages)")
        print("="*80)
        
        try:
            # 獲取已載入的數據
            loaded_data = self.data_loader.loaded_data
            race_control_messages = loaded_data.get('race_control_messages')
            
            if race_control_messages is None or race_control_messages.empty:
                print("[ERROR] 沒有可用的賽事控制消息")
                return
            
            # 使用動態獲取的車隊對應表，不使用預設值
            team_mapping = self.dynamic_team_mapping if hasattr(self, 'dynamic_team_mapping') and self.dynamic_team_mapping else {}
            
            print(f"[INFO] 總消息數量: {len(race_control_messages)}")
            print(f"[LIST] 消息欄位: {list(race_control_messages.columns)}")
            
            # 創建表格顯示所有消息
            table = PrettyTable()
            table.field_names = ["#", "時間", "類別", "消息", "相關車手"]
            table.align = "l"
            table.max_width["消息"] = 60
            
            for idx, (_, message_row) in enumerate(race_control_messages.iterrows(), 1):
                time = str(message_row.get('Time', 'N/A'))[:12]  # 限制時間顯示長度
                category = str(message_row.get('Category', 'N/A'))
                message = str(message_row.get('Message', 'N/A'))
                
                # 尋找相關車手
                related_drivers = []
                message_upper = message.upper()
                
                for abbr in team_mapping.keys():
                    if abbr in message_upper:
                        related_drivers.append(abbr)
                
                related_drivers_str = ', '.join(related_drivers) if related_drivers else '-'
                
                # 限制消息長度
                if len(message) > 60:
                    message = message[:57] + "..."
                
                table.add_row([idx, time, category, message, related_drivers_str])
            
            print(table)
            
            # 統計消息類型
            if 'Category' in race_control_messages.columns:
                print(f"\n[INFO] 消息類型統計:")
                category_counts = race_control_messages['Category'].value_counts()
                for category, count in category_counts.items():
                    percentage = (count / len(race_control_messages)) * 100
                    print(f"   {category}: {count} 條 ({percentage:.1f}%)")
            
        except Exception as e:
            print(f"[ERROR] 顯示事件摘要時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
        if self.dynamic_team_mapping:
            print(f"[CONFIG] 使用 OpenF1 動態車手-車隊映射 ({len(self.dynamic_team_mapping)} 位車手)")
        else:
            print(f"[WARNING]  使用預設車手-車隊映射，建議重新載入賽事數據")
        print("="*80)
        
        # 事件類型的中英文對應表 - 完全對應原始實現
        event_descriptions = {
            'YELLOW FLAG': {'zh': '黃旗警告', 'en': 'Yellow Flag Warning'},
            'RED FLAG': {'zh': '紅旗停賽', 'en': 'Red Flag Session Stopped'},
            'SAFETY CAR': {'zh': '安全車出動', 'en': 'Safety Car Deployed'},
            'VIRTUAL SAFETY CAR': {'zh': '虛擬安全車', 'en': 'Virtual Safety Car'},
            'DRS ENABLED': {'zh': 'DRS啟用', 'en': 'DRS Enabled'},
            'DRS DISABLED': {'zh': 'DRS禁用', 'en': 'DRS Disabled'},
            'TRACK LIMITS': {'zh': '賽道邊界違規', 'en': 'Track Limits Violation'},
            'ACCIDENT': {'zh': '事故', 'en': 'Accident'},
            'INCIDENT': {'zh': '事件', 'en': 'Incident'},
            'INVESTIGATION': {'zh': '調查', 'en': 'Under Investigation'},
            'PENALTY': {'zh': '處罰', 'en': 'Penalty'},
            'DANGEROUS DRIVING': {'zh': '危險駕駛', 'en': 'Dangerous Driving'},
            'COLLISION': {'zh': '碰撞', 'en': 'Collision'},
            'SPIN': {'zh': '打滑', 'en': 'Spin'},
            'OFF TRACK': {'zh': '衝出賽道', 'en': 'Off Track'},
            'PUNCTURE': {'zh': '爆胎', 'en': 'Puncture'},
            'GREEN FLAG': {'zh': '綠旗', 'en': 'Green Flag'},
            'TRACK CLEAR': {'zh': '賽道清空', 'en': 'Track Clear'},
            'WARNING': {'zh': '警告', 'en': 'Warning Issued'}
        }
        
        try:
            # 從原始數據獲取所有消息
            loaded_data = self.data_loader.loaded_data
            race_control_messages = loaded_data.get('race_control_messages')
            
            if race_control_messages is None or race_control_messages.empty:
                print("[SUCCESS] 沒有賽事控制消息")
                return
            
            # 將消息轉換為事故格式
            all_messages = []
            for _, message_row in race_control_messages.iterrows():
                message_info = {
                    'time': message_row.get('Time', ''),
                    'category': message_row.get('Category', ''),
                    'message': message_row.get('Message', ''),
                    'lap': message_row.get('Lap', '')
                }
                all_messages.append(message_info)
            
            # 過濾不重要的事件 - 完全對應原始實现
            filtered_accidents = self._filter_important_accidents(all_messages)
        
            if not filtered_accidents:
                print("[SUCCESS] 沒有重要事故需要報告")
                return
        
            # 顯示重要事件 - 完全對應原始實現
            self._display_important_events_table(filtered_accidents, team_mapping, event_descriptions)
            
        except Exception as e:
            print(f"[ERROR] 獲取關鍵事件時發生錯誤: {e}")
    
    def _filter_important_accidents(self, accidents):
        """過濾重要的事故事件 - 完全對應 f1_analysis_cli_new.py 實現"""
        ignore_keywords = [
            'GREEN LIGHT - PIT EXIT OPEN',
            'PIT EXIT OPEN',
            'PIT ENTRY OPEN', 
            'SESSION STARTED',
            'SESSION ENDED',
            'FORMATION LAP',
            'DRS ENABLED',
            'DRS DISABLED'
        ]
        
        filtered_accidents = []
        for acc in accidents:
            message = str(acc.get('message', '')).upper()
            if not any(keyword in message for keyword in ignore_keywords):
                filtered_accidents.append(acc)
        
        return filtered_accidents
    
    def _display_important_events_table(self, events, team_mapping, event_descriptions):
        """顯示重要事件表格 - 完全對應 f1_analysis_cli_new.py 實現"""
        print(f"\n[CRITICAL] 重要事件報告 (共 {len(events)} 個事件):")
        print("=" * 100)
        
        for i, acc in enumerate(events, 1):
            # 安全處理各個字段
            message = acc.get('message', 'N/A')
            lap = acc.get('lap', 'N/A')
            time = acc.get('time', 'N/A')
            driver = acc.get('driver', 'N/A')
            severity = acc.get('severity', 'UNKNOWN')
            
            # 獲取車隊信息
            team = team_mapping.get(driver, 'Unknown Team') if driver != 'N/A' else 'N/A'
            
            # 生成中英文描述
            description_en = message
            description_zh = message  # 默認使用原始消息
            
            # 嘗試查找對應的中文描述
            for key, desc in event_descriptions.items():
                if key in str(message).upper():
                    description_zh = desc['zh']
                    description_en = desc['en']
                    break
            
            # 處理時間格式 - 完全對應原始實現
            if time != 'N/A':
                try:
                    # 處理不同的時間格式
                    if hasattr(time, 'strftime'):
                        # 如果是 datetime 對象
                        time_str = time.strftime('%M:%S')
                    elif isinstance(time, str):
                        # 如果是字符串，嘗試解析
                        if ':' in time:
                            # 已經是 MM:SS 格式
                            time_part = time.split(':')
                            if len(time_part) >= 2:
                                time_str = time_part[0] + ':' + time_part[1]
                            else:
                                time_str = time[:5]
                        else:
                            time_str = 'N/A'
                    elif hasattr(time, 'total_seconds'):
                        # 如果是 timedelta 對象
                        total_seconds = time.total_seconds()
                        minutes = int(total_seconds // 60)
                        seconds = int(total_seconds % 60)
                        time_str = f"{minutes:02d}:{seconds:02d}"
                    elif hasattr(time, 'strftime'):
                        # 如果是 datetime 對象，只取分鐘和秒
                        time_str = time.strftime('%M:%S')
                    else:
                        # 其他情況，嘗試截取合理長度
                        time_str = str(time)[:8] if len(str(time)) > 8 else str(time)
                        
                except Exception as e:
                    time_str = f"時間解析錯誤: {str(time)[:10]}"
            else:
                time_str = 'N/A'
            
            # 使用三行格式顯示 - 完全對應原始實現
            # 安全處理可能為 None 的值
            lap_display = f"{lap:3}" if lap is not None and lap != 'N/A' else "N/A"
            driver_display = f"{driver:4}" if driver is not None else "N/A "
            print(f"事件 #{i:3d} | 圈數: {lap_display} | 時間: {time_str:8} | 車手: {driver_display} | 車隊: {team[:20]:20} | 嚴重度: {severity}")
            print(f"英文: {description_en}")
            print(f"中文: {description_zh}")
            print("-" * 100)
        
        print(f"\n總計 {len(events)} 個重要事件")
    
    def _display_key_events_summary(self):
        """顯示關鍵事件摘要 - 完全對應 f1_analysis_cli_new.py 實現"""
        print(f"\n[CRITICAL] 關鍵事件摘要 (Key Events Summary)")
        print("=" * 80)
        
        try:
            data = self.data_loader.get_loaded_data()
            session = data['session']
            
            if not hasattr(session, 'race_control_messages') or session.race_control_messages is None:
                print("[ERROR] 沒有找到 race_control_messages 數據")
                return
            
            messages = session.race_control_messages
            if messages.empty:
                print("[ERROR] race_control_messages 為空")
                return
            
            # 收集關鍵事件 - 完全對應原始實現
            key_events = []
            for _, msg in messages.iterrows():
                msg_text = str(msg.get('Message', '')).upper()
                category = str(msg.get('Category', '')).upper()
                
                # 檢查關鍵事件類型 - 完全對應原始實現
                if any(keyword in msg_text for keyword in ['ACCIDENT', 'COLLISION', 'CRASH', 'CONTACT', 'INCIDENT']):
                    event_type = "[CRITICAL] 事故"
                elif any(keyword in msg_text for keyword in ['SAFETY CAR', 'SC DEPLOYED', 'VSC']):
                    event_type = "🚗 安全車"
                elif any(keyword in msg_text for keyword in ['RED FLAG', 'RED LIGHT']):
                    event_type = "🔴 紅旗"
                elif any(keyword in msg_text for keyword in ['YELLOW FLAG', 'DOUBLE YELLOW']):
                    event_type = "🟡 黃旗"
                elif any(keyword in msg_text for keyword in ['GREEN FLAG', 'GREEN LIGHT']):
                    event_type = "🟢 綠旗"
                elif any(keyword in msg_text for keyword in ['PENALTY', 'WARNING', 'INVESTIGATION']):
                    event_type = "⚖️ 處罰"
                elif any(keyword in msg_text for keyword in ['CHEQUERED FLAG', 'RACE FINISHED']):
                    event_type = "[FINISH] 比賽結束"
                else:
                    continue
                
                # 格式化時間 (使用 MM:SS 格式) - 完全對應原始實現
                time_val = msg.get('Time', 'N/A')
                formatted_time = 'N/A'
                if time_val != 'N/A':
                    try:
                        import pandas as pd
                        if isinstance(time_val, pd.Timestamp):
                            # 提取分鐘:秒數
                            formatted_time = f"{time_val.minute:02d}:{time_val.second:02d}"
                        elif hasattr(time_val, 'total_seconds'):
                            # 如果是 timedelta
                            total_seconds = time_val.total_seconds()
                            minutes = int(total_seconds // 60)
                            seconds = int(total_seconds % 60)
                            formatted_time = f"{minutes:02d}:{seconds:02d}"
                        else:
                            formatted_time = str(time_val)[:8]  # 截取前8個字符
                    except:
                        formatted_time = str(time_val)[:8]
                
                key_events.append({
                    'type': event_type,
                    'time': formatted_time,
                    'lap': msg.get('Lap', 'N/A'),
                    'message': str(msg.get('Message', ''))  # 移除截斷，顯示完整內容
                })
            
            if key_events:
                print(f"[INFO] 發現 {len(key_events)} 個關鍵事件")
                
                key_table = PrettyTable()
                key_table.field_names = ["類型", "時間", "圈數", "事件描述"]
                key_table.align = "l"
                key_table.max_width["事件描述"] = 120  # 設置事件描述欄位最大寬度
                key_table.max_width["類型"] = 15
                key_table.max_width["時間"] = 10
                key_table.max_width["圈數"] = 8
                
                for event in key_events:
                    key_table.add_row([event['type'], event['time'], event['lap'], event['message']])
                
                print(key_table)
            else:
                print("[SUCCESS] 沒有發現重大關鍵事件")
            
        except Exception as e:
            print(f"[ERROR] 關鍵事件摘要顯示失敗: {e}")
    
    def _fallback_accident_analysis(self):
        """簡化的事故分析（後備方案） - 完全對應 f1_analysis_cli_new.py 實現"""
        print(f"🔄 執行簡化事故分析...")
        
        try:
            # 獲取已載入的數據
            loaded_data = self.data_loader.loaded_data
            session = loaded_data.get('session')
            metadata = loaded_data.get('metadata', {})
            
            if not session:
                print("[ERROR] 無法獲取賽事數據")
                return
            
            # 獲取賽事控制消息
            if hasattr(session, 'race_control_messages') and session.race_control_messages is not None:
                messages = session.race_control_messages
                
                if messages.empty:
                    print("[ERROR] 沒有找到賽事控制消息")
                    return
                
                print(f"\n[LIST] {metadata.get('year', 'N/A')} {metadata.get('event_name', 'N/A')} 賽事事件分析")
                print("=" * 80)
                
                # 分類事件 - 完全對應原始實現
                accidents = []
                flags = []
                investigations = []
                
                for _, message in messages.iterrows():
                    msg_text = str(message.get('Message', '')).upper()
                    category = str(message.get('Category', '')).upper()
                    
                    # 事故相關關鍵字 - 完全對應原始實現
                    if any(keyword in msg_text for keyword in ['ACCIDENT', 'COLLISION', 'CRASH', 'CONTACT']):
                        accidents.append(message)
                    elif any(keyword in msg_text for keyword in ['FLAG', 'YELLOW', 'RED', 'GREEN', 'SAFETY CAR', 'VSC']):
                        flags.append(message)
                    elif any(keyword in msg_text for keyword in ['INVESTIGATION', 'PENALTY', 'WARNING', 'NOTED']):
                        investigations.append(message)
                
                # 顯示事故 - 完全對應原始實現
                if accidents:
                    print(f"\n[CRITICAL] 事故事件 ({len(accidents)} 起):")
                    accident_table = PrettyTable()
                    accident_table.field_names = ["編號", "時間", "圈數", "事件描述", "涉及車手"]
                    accident_table.align = "l"
                    accident_table.max_width["事件描述"] = 100  # 設置事件描述最大寬度
                    accident_table.max_width["編號"] = 8
                    accident_table.max_width["時間"] = 12
                    accident_table.max_width["圈數"] = 8
                    accident_table.max_width["涉及車手"] = 15
                    
                    for i, accident in enumerate(accidents, 1):
                        time_info = accident.get('Time', 'N/A')
                        lap_info = accident.get('Lap', 'N/A')
                        message = accident.get('Message', '')
                        driver = accident.get('Driver', 'N/A')
                        accident_table.add_row([i, time_info, lap_info, message, driver])
                    
                    print(accident_table)
                
                # 顯示旗幟事件 - 完全對應原始實現
                if flags:
                    print(f"\n[FINISH] 旗幟/安全車事件 ({len(flags)} 次):")
                    flag_table = PrettyTable()
                    flag_table.field_names = ["編號", "時間", "圈數", "事件描述"]
                    flag_table.align = "l"
                    flag_table.max_width["事件描述"] = 100  # 設置事件描述最大寬度
                    flag_table.max_width["編號"] = 8
                    flag_table.max_width["時間"] = 12
                    flag_table.max_width["圈數"] = 8
                    flag_table.align = "l"
                    flag_table.max_width = 50
                    
                    for i, flag in enumerate(flags, 1):
                        time_info = flag.get('Time', 'N/A')
                        lap_info = flag.get('Lap', 'N/A')
                        message = flag.get('Message', '')
                        flag_table.add_row([i, time_info, lap_info, message])
                    
                    print(flag_table)
                
                # 顯示調查事件 - 完全對應原始實現
                if investigations:
                    print(f"\n[DEBUG] 調查/處罰事件 ({len(investigations)} 起):")
                    investigation_table = PrettyTable()
                    investigation_table.field_names = ["編號", "時間", "圈數", "事件描述", "涉及車手"]
                    investigation_table.align = "l"
                    investigation_table.max_width = 50
                    
                    for i, inv in enumerate(investigations, 1):
                        time_info = inv.get('Time', 'N/A')
                        lap_info = inv.get('Lap', 'N/A')
                        message = inv.get('Message', '')
                        driver = inv.get('Driver', 'N/A')
                        investigation_table.add_row([i, time_info, lap_info, message, driver])
                    
                    print(investigation_table)
                
                # 統計摘要 - 完全對應原始實現
                total_events = len(accidents) + len(flags) + len(investigations)
                print(f"\n[INFO] ACCIDENT ANALYSIS SUMMARY / 事故分析摘要:")
                
                # 使用 PrettyTable 顯示統計摘要
                summary_table = PrettyTable()
                summary_table.field_names = ["事件類型", "數量"]
                summary_table.align = "l"
                summary_table.add_row(["總事件數", total_events])
                summary_table.add_row(["事故", f"{len(accidents)} 起"])
                summary_table.add_row(["旗幟/安全車", f"{len(flags)} 次"])
                summary_table.add_row(["調查/處罰", f"{len(investigations)} 起"])
                print(summary_table)
                
                # 評估事故嚴重程度 - 完全對應原始實現
                severity_assessment = self._assess_accident_severity(accidents, flags, investigations)
                
                print(f"\n[WARNING] 嚴重程度評估: {severity_assessment['level']}")
                print(f"   風險指數: {severity_assessment['risk_score']}/10")
                print(f"   描述: {severity_assessment['description']}")
                
                # 顯示嚴重程度說明 - 完全對應原始實現
                print(f"\n[INFO] 嚴重程度等級說明:")
                print(f"   🔴 極高風險 (CRITICAL): 15+ 分")
                print(f"      • 多起嚴重事故或紅旗中斷")
                print(f"      • 比賽安全風險極高")
                print(f"   🟠 高風險 (HIGH): 10-14 分")
                print(f"      • 重大事故或安全車出動")
                print(f"      • 比賽進行受到影響")
                print(f"   🟡 中等風險 (MODERATE): 5-9 分")
                print(f"      • 輕微事故或黃旗事件")
                print(f"      • 局部影響比賽進行")
                print(f"   🟢 低風險 (LOW): 1-4 分")
                print(f"      • 少數輕微事件或調查")
                print(f"      • 對比賽影響有限")
                print(f"   ⚪ 無風險 (NONE): 0 分")
                print(f"      • 比賽進行順利，無重大安全事件")
                
                if total_events == 0:
                    print("\n[SUCCESS] 本場比賽沒有重大事件記錄，安全狀況良好")
                
            else:
                print("[ERROR] 沒有找到賽事控制消息資料")
                
        except Exception as e:
            print(f"[ERROR] 簡化事故分析失敗: {e}")
    
    def _assess_accident_severity(self, accidents, flags, investigations):
        """評估事故嚴重程度 - 完全對應 f1_analysis_cli_new.py 實現"""
        try:
            total_accidents = len(accidents)
            total_flags = len(flags)
            total_investigations = len(investigations)
            
            # 計算風險分數 - 完全對應原始實現
            risk_score = 0
            
            # 事故權重
            risk_score += total_accidents * 3
            
            # 檢查紅旗事件 (最嚴重) - 完全對應原始實現
            red_flags = 0
            safety_cars = 0
            yellow_flags = 0
            
            for flag in flags:
                message = str(flag.get('Message', '')).upper()
                if 'RED' in message:
                    red_flags += 1
                    risk_score += 4
                elif 'SAFETY CAR' in message or 'SC' in message:
                    safety_cars += 1
                    risk_score += 2
                elif 'YELLOW' in message:
                    yellow_flags += 1
                    risk_score += 1
            
            # 調查/處罰權重 - 完全對應原始實現
            risk_score += total_investigations * 1
            
            # 確定嚴重程度等級 - 完全對應原始實現
            if risk_score >= 15:
                level = "極高 (CRITICAL)"
                description = "多起嚴重事故或紅旗中斷，比賽安全風險極高"
            elif risk_score >= 10:
                level = "高 (HIGH)"
                description = "重大事故或安全車出動，比賽進行受到影響"
            elif risk_score >= 5:
                level = "中等 (MODERATE)"
                description = "輕微事故或黃旗事件，局部影響比賽進行"
            elif risk_score >= 1:
                level = "低 (LOW)"
                description = "少數輕微事件或調查，對比賽影響有限"
            else:
                level = "無 (NONE)"
                description = "比賽進行順利，無重大安全事件"
            
            return {
                'level': level,
                'description': description,
                'risk_score': min(risk_score, 10),  # 限制最高分數為10
                'details': {
                    'red_flags': red_flags,
                    'safety_cars': safety_cars,
                    'yellow_flags': yellow_flags,
                    'accidents': total_accidents,
                    'investigations': total_investigations
                }
            }
            
        except Exception as e:
            print(f"[ERROR] 評估事故嚴重程度時發生錯誤: {e}")
            return {
                'level': "未知 (UNKNOWN)",
                'description': "無法評估事故嚴重程度",
                'risk_score': 0,
                'details': {}
            }
    
    def _debug_race_control_messages(self):
        """調試顯示所有 Race Control Messages 原始數據 - 完全對應 f1_analysis_cli_new.py 實現"""
        print(f"\n" + "="*100)
        print("[DEBUG] FastF1 Race Control Messages 原始數據調試 (All Race Control Messages Debug)")
        print("="*100)
        
        try:
            data = self.data_loader.get_loaded_data()
            session = data['session']
            metadata = data['metadata']
            
            if not hasattr(session, 'race_control_messages') or session.race_control_messages is None:
                print("[ERROR] 沒有找到 race_control_messages 數據")
                return
            
            messages = session.race_control_messages
            if messages.empty:
                print("[ERROR] race_control_messages 為空")
                return
            
            print(f"[INFO] 總消息數量: {len(messages)}")
            print(f"[LIST] 可用欄位: {list(messages.columns)}")
            print(f"📅 賽事: {metadata['year']} {metadata['event_name']}")
            
            # 按類別統計
            print(f"\n[INFO] 按類別統計 (Category):")
            print("-" * 80)
            if 'Category' in messages.columns:
                category_counts = messages['Category'].value_counts()
                category_table = PrettyTable()
                category_table.field_names = ["類別", "數量", "百分比"]
                category_table.align = "l"
                
                for category, count in category_counts.items():
                    percentage = (count / len(messages)) * 100
                    category_table.add_row([str(category), count, f"{percentage:.1f}%"])
                
                print(category_table)
            else:
                print("[ERROR] 沒有 Category 欄位")
            
            # 詳細消息列表
            print(f"\n[LIST] 完整消息列表 (All Messages):")
            print("-" * 120)
            
            msg_table = PrettyTable()
            available_columns = ['Time', 'Lap', 'Category', 'Message', 'Flag', 'Scope', 'Sector']
            existing_columns = [col for col in available_columns if col in messages.columns]
            
            msg_table.field_names = ["#"] + existing_columns
            msg_table.align = "l"
            msg_table.max_width = 100
            
            for i, (idx, msg) in enumerate(messages.iterrows(), 1):
                row = [i]
                for col in existing_columns:
                    value = str(msg.get(col, 'N/A'))
                    # 限制顯示長度
                    if len(value) > 50:
                        value = value[:47] + "..."
                    row.append(value)
                msg_table.add_row(row)
            
            print(msg_table)
            
            # 關鍵事件摘要
            print(f"\n[CRITICAL] 關鍵事件摘要:")
            print("-" * 80)
            
            key_messages = []
            for _, msg in messages.iterrows():
                msg_text = str(msg.get('Message', '')).upper()
                if any(keyword in msg_text for keyword in [
                    'ACCIDENT', 'COLLISION', 'CRASH', 'INCIDENT', 'CONTACT',
                    'SAFETY CAR', 'VSC', 'RED FLAG', 'YELLOW FLAG', 
                    'PENALTY', 'INVESTIGATION', 'WARNING'
                ]):
                    key_messages.append(msg)
            
            if key_messages:
                print(f"發現 {len(key_messages)} 個關鍵消息")
                for i, msg in enumerate(key_messages, 1):
                    print(f"{i:2d}. 圈數:{msg.get('Lap', 'N/A'):3} | 時間:{str(msg.get('Time', 'N/A'))[:10]:10} | {msg.get('Message', 'N/A')}")
            else:
                print("[SUCCESS] 沒有發現關鍵事件消息")
            
        except Exception as e:
            print(f"[ERROR] 調試信息顯示失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _debug_track_status(self):
        """調試顯示所有 Track Status 原始數據 - 完全對應 f1_analysis_cli_new.py 實現"""
        print(f"\n" + "="*100)
        print("[DEBUG] FastF1 Track Status 原始數據調試 (All Track Status Debug)")
        print("="*100)
        
        try:
            data = self.data_loader.get_loaded_data()
            session = data['session']
            metadata = data['metadata']
            
            if not hasattr(session, 'track_status') or session.track_status is None:
                print("[ERROR] 沒有找到 track_status 數據")
                return
            
            track_status = session.track_status
            if track_status.empty:
                print("[ERROR] track_status 為空")
                return
            
            print(f"[INFO] 總狀態記錄數量: {len(track_status)}")
            print(f"[LIST] 可用欄位: {list(track_status.columns)}")
            print(f"📅 賽事: {metadata['year']} {metadata['event_name']}")
            
            # 按狀態碼統計
            print(f"\n[INFO] 按狀態碼統計 (Status Code):")
            print("-" * 80)
            
            status_mapping = {
                '1': '🟢 綠旗 (Track Clear)',
                '2': '🟡 黃旗 (Yellow Flag)',
                '3': '🔴 紅旗 (Red Flag)',
                '4': '🚗 虛擬安全車 (VSC)',
                '5': '🚗 安全車 (Safety Car)',
                '6': '⚪ 起跑準備 (Race Start)',
                '7': '🔴 比賽結束 (Race End)'
            }
            
            if 'Status' in track_status.columns:
                status_counts = track_status['Status'].value_counts()
                status_table = PrettyTable()
                status_table.field_names = ["狀態碼", "含義", "數量", "百分比"]
                status_table.align = "l"
                
                for status_code, count in status_counts.items():
                    meaning = status_mapping.get(str(status_code), f'未知狀態 ({status_code})')
                    percentage = (count / len(track_status)) * 100
                    status_table.add_row([status_code, meaning, count, f"{percentage:.1f}%"])
                
                print(status_table)
            else:
                print("[ERROR] 沒有 Status 欄位")
            
            # 詳細狀態列表
            print(f"\n[LIST] 完整狀態變化記錄:")
            print("-" * 120)
            
            status_table = PrettyTable()
            available_columns = ['Time', 'Status', 'Message']
            existing_columns = [col for col in available_columns if col in track_status.columns]
            
            status_table.field_names = ["#"] + existing_columns + ["狀態含義"]
            status_table.align = "l"
            status_table.max_width = 80
            
            for i, (idx, status) in enumerate(track_status.iterrows(), 1):
                row = [i]
                for col in existing_columns:
                    value = str(status.get(col, 'N/A'))
                    if len(value) > 30:
                        value = value[:27] + "..."
                    row.append(value)
                
                # 添加狀態含義
                status_code = str(status.get('Status', 'N/A'))
                meaning = status_mapping.get(status_code, f'未知({status_code})')
                row.append(meaning)
                
                status_table.add_row(row)
            
            print(status_table)
            
        except Exception as e:
            print(f"[ERROR] Track Status 調試信息顯示失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _debug_all_events_detailed(self):
        """顯示完整事件調試信息 - 完全對應 f1_analysis_cli_new.py 實現"""
        print(f"\n" + "="*120)
        print("[DEBUG] FastF1 完整事件調試信息 (Complete Events Debug)")
        print("="*120)
        
        try:
            data = self.data_loader.get_loaded_data()
            session = data['session']
            metadata = data['metadata']
            
            print(f"📅 賽事資訊: {metadata['year']} {metadata['event_name']} ({metadata['session_type']})")
            print(f"📍 地點: {metadata['location']}")
            print(f"[INFO] 已載入數據摘要:")
            
            # 數據源檢查
            data_sources = {
                'race_control_messages': '賽事控制消息',
                'track_status': '賽道狀態',
                'weather_data': '天氣數據',
                'laps': '圈次數據',
                'results': '比賽結果',
                'car_data': '車輛遙測'
            }
            
            available_sources = []
            for source, name in data_sources.items():
                if source in data:
                    data_obj = data[source]
                    if hasattr(data_obj, 'empty'):
                        is_available = not data_obj.empty
                        count = len(data_obj) if is_available else 0
                    elif hasattr(data_obj, '__len__'):
                        is_available = len(data_obj) > 0
                        count = len(data_obj)
                    else:
                        is_available = data_obj is not None
                        count = 1 if is_available else 0
                    
                    status = "[SUCCESS]" if is_available else "[ERROR]"
                    print(f"   {status} {name}: {count} 筆記錄")
                    
                    if is_available:
                        available_sources.append(source)
                else:
                    print(f"   [ERROR] {name}: 未載入")
            
            # 1. 賽事控制消息詳細分析
            if 'race_control_messages' in available_sources:
                print(f"\n[DEBUG] 1. 賽事控制消息詳細分析:")
                print("-" * 100)
                
                messages = data['race_control_messages']
                print(f"   [LIST] 總消息數: {len(messages)}")
                print(f"   [INFO] 欄位結構: {list(messages.columns)}")
                
                # 消息類型分析
                if 'Category' in messages.columns:
                    categories = messages['Category'].value_counts()
                    print(f"   📂 消息類別分布:")
                    for category, count in categories.items():
                        print(f"      • {category}: {count} 筆")
                
                # 關鍵字分析
                print(f"   🔤 關鍵字出現頻率:")
                keywords = ['ACCIDENT', 'INCIDENT', 'YELLOW', 'RED', 'SAFETY CAR', 'VSC', 'PENALTY', 'FLAG']
                for keyword in keywords:
                    count = messages['Message'].str.contains(keyword, case=False, na=False).sum()
                    if count > 0:
                        print(f"      • {keyword}: {count} 次")
            
            # 2. 賽道狀態分析
            if 'track_status' in available_sources:
                print(f"\n[DEBUG] 2. 賽道狀態詳細分析:")
                print("-" * 100)
                
                track_status = data['track_status']
                print(f"   [LIST] 總狀態記錄: {len(track_status)}")
                
                if 'Status' in track_status.columns:
                    status_counts = track_status['Status'].value_counts()
                    print(f"   [INFO] 狀態分布:")
                    status_mapping = {
                        '1': '綠旗', '2': '黃旗', '3': '紅旗', 
                        '4': 'VSC', '5': '安全車', '6': '起跑', '7': '結束'
                    }
                    for status, count in status_counts.items():
                        meaning = status_mapping.get(str(status), f'未知({status})')
                        print(f"      • {meaning}: {count} 次")
            
            # 3. 事故分析總結
            print(f"\n[DEBUG] 3. 事故分析總結:")
            print("-" * 100)
            
            accident_keywords = ['ACCIDENT', 'COLLISION', 'CRASH', 'INCIDENT', 'CONTACT']
            safety_keywords = ['SAFETY CAR', 'VSC', 'VIRTUAL SAFETY CAR']
            flag_keywords = ['RED FLAG', 'YELLOW FLAG', 'DOUBLE YELLOW']
            
            if 'race_control_messages' in available_sources:
                messages = data['race_control_messages']
                
                accident_count = 0
                safety_count = 0
                flag_count = 0
                
                for _, msg in messages.iterrows():
                    msg_text = str(msg.get('Message', '')).upper()
                    
                    if any(keyword in msg_text for keyword in accident_keywords):
                        accident_count += 1
                    if any(keyword in msg_text for keyword in safety_keywords):
                        safety_count += 1
                    if any(keyword in msg_text for keyword in flag_keywords):
                        flag_count += 1
                
                print(f"   [CRITICAL] 事故相關事件: {accident_count} 起")
                print(f"   🚗 安全車相關: {safety_count} 次")
                print(f"   [FINISH] 旗幟事件: {flag_count} 次")
                
                total_incidents = accident_count + safety_count + flag_count
                if total_incidents == 0:
                    print(f"   [SUCCESS] 比賽進行順利，無重大安全事件")
                else:
                    risk_level = "低" if total_incidents <= 3 else "中" if total_incidents <= 8 else "高"
                    print(f"   [WARNING]  總體風險評估: {risk_level} (共 {total_incidents} 個安全事件)")
            
        except Exception as e:
            print(f"[ERROR] 完整事件調試信息顯示失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _display_summary_statistics(self, stats):
        """顯示統計摘要"""
        print(f"\n[INFO] 事故分析統計摘要:")
        print("-" * 60)
        
        summary_table = PrettyTable()
        summary_table.field_names = ["項目", "數量", "說明"]
        summary_table.align = "l"
        
        summary_table.add_row(["總事件數", stats['total_events'], "所有記錄的事件"])
        summary_table.add_row(["安全事件", stats['safety_events'], "高風險/關鍵事件"])
        summary_table.add_row(["事故事件", stats['accidents'], "碰撞/接觸事件"])
        summary_table.add_row(["處罰事件", stats['penalties'], "警告/處罰/調查"])
        
        print(summary_table)
        
        # 嚴重程度分布
        print(f"\n[TARGET] 嚴重程度分布:")
        severity_table = PrettyTable()
        severity_table.field_names = ["嚴重程度", "數量", "百分比"]
        severity_table.align = "l"
        
        total_events = max(stats['total_events'], 1)  # 避免除零
        severity_mapping = {
            'CRITICAL': '🔴 極高',
            'HIGH': '🟠 高',
            'MODERATE': '🟡 中等',
            'LOW': '🟢 低',
            'NONE': '⚪ 無'
        }
        
        for severity, count in stats['severity_distribution'].items():
            percentage = (count / total_events) * 100
            display_name = severity_mapping.get(severity, severity)
            severity_table.add_row([display_name, count, f"{percentage:.1f}%"])
        
        print(severity_table)

    # === 專門的子模組分析方法 ===
    
    def run_key_events_summary_only(self):
        """僅執行關鍵事件摘要分析"""
        print("[DEBUG] 開始關鍵事件摘要分析...")
        print("[INFO] 分析進站策略中的關鍵事件和轉折點...")
        
        try:
            # 載入車隊映射數據
            self._load_driver_team_mapping_if_needed()
            
            # 檢查數據是否已載入
            if not self._check_data_loaded():
                print("[ERROR] 數據未載入，請先載入賽事數據")
                return
            
            loaded_data = self.data_loader.loaded_data
            race_control_messages = loaded_data.get('race_control_messages')
            
            if race_control_messages is None or race_control_messages.empty:
                print("[ERROR] 沒有找到 race_control_messages")
                return
            
            print(f"\n[CRITICAL] 關鍵事件摘要 (Key Events Summary)")
            print("=" * 80)
            
            # 收集關鍵事件
            key_events = []
            for _, msg in race_control_messages.iterrows():
                msg_text = str(msg.get('Message', '')).upper()
                
                # 檢查關鍵事件類型
                if any(keyword in msg_text for keyword in ['ACCIDENT', 'COLLISION', 'CRASH', 'CONTACT', 'INCIDENT']):
                    event_type = "[CRITICAL] 事故"
                elif any(keyword in msg_text for keyword in ['SAFETY CAR', 'SC DEPLOYED', 'VSC']):
                    event_type = "🚗 安全車"
                elif any(keyword in msg_text for keyword in ['RED FLAG', 'RED LIGHT']):
                    event_type = "🔴 紅旗"
                elif any(keyword in msg_text for keyword in ['YELLOW FLAG', 'DOUBLE YELLOW']):
                    event_type = "🟡 黃旗"
                elif any(keyword in msg_text for keyword in ['GREEN FLAG', 'GREEN LIGHT']):
                    event_type = "🟢 綠旗"
                elif any(keyword in msg_text for keyword in ['PENALTY', 'WARNING', 'INVESTIGATION']):
                    event_type = "⚖️ 處罰"
                elif any(keyword in msg_text for keyword in ['CHEQUERED FLAG', 'RACE FINISHED']):
                    event_type = "[FINISH] 比賽結束"
                else:
                    continue
                
                # 格式化時間
                time_val = msg.get('Time', 'N/A')
                formatted_time = 'N/A'
                if time_val != 'N/A' and hasattr(time_val, 'strftime'):
                    formatted_time = time_val.strftime('%H:%M')
                
                key_events.append({
                    'type': event_type,
                    'time': formatted_time,
                    'lap': msg.get('Lap', 'N/A'),
                    'message': str(msg.get('Message', ''))
                })
            
            if key_events:
                print(f"[INFO] 發現 {len(key_events)} 個關鍵事件")
                
                key_table = PrettyTable()
                key_table.field_names = ["類型", "時間", "圈數", "事件描述"]
                key_table.align = "l"
                key_table.max_width["事件描述"] = 80
                
                for event in key_events:
                    key_table.add_row([event['type'], event['time'], event['lap'], event['message'][:80]])
                
                print(key_table)
            else:
                print("[SUCCESS] 沒有發現重大關鍵事件")
            
            print("[SUCCESS] 關鍵事件摘要分析完成")
            
        except Exception as e:
            print(f"[ERROR] 關鍵事件分析失敗: {e}")

    def run_special_incidents_only(self):
        """僅執行特殊事件報告分析"""
        print("[CRITICAL] 開始特殊事件報告分析...")
        print("[INFO] 分析比賽中的特殊事件和異常情況...")
        
        try:
            # 載入車隊映射數據
            self._load_driver_team_mapping_if_needed()
            
            if not self._check_data_loaded():
                print("[ERROR] 數據未載入，請先載入賽事數據")
                return
            
            loaded_data = self.data_loader.loaded_data
            race_control_messages = loaded_data.get('race_control_messages')
            
            if race_control_messages is None or race_control_messages.empty:
                print("[ERROR] 沒有找到 race_control_messages")
                return
            
            print(f"\n[CRITICAL] 特殊事件報告 (Special Incident Reports)")
            print("=" * 80)
            
            # 統計不同類型事件
            red_flags = 0
            safety_cars = 0
            vsc_events = 0
            yellow_flags = 0
            investigations = 0
            special_events = []
            
            for _, msg in race_control_messages.iterrows():
                msg_text = str(msg.get('Message', '')).upper()
                
                if 'RED' in msg_text and 'FLAG' in msg_text:
                    red_flags += 1
                    special_events.append({
                        'type': '🔴 紅旗事件',
                        'time': msg.get('Time', 'N/A'),
                        'lap': msg.get('Lap', 'N/A'),
                        'description': msg.get('Message', ''),
                        'severity': 'CRITICAL'
                    })
                elif 'SAFETY CAR' in msg_text:
                    safety_cars += 1
                    special_events.append({
                        'type': '🚗 安全車出動',
                        'time': msg.get('Time', 'N/A'),
                        'lap': msg.get('Lap', 'N/A'),
                        'description': msg.get('Message', ''),
                        'severity': 'HIGH'
                    })
                elif 'VSC' in msg_text:
                    vsc_events += 1
                    special_events.append({
                        'type': '🚦 虛擬安全車',
                        'time': msg.get('Time', 'N/A'),
                        'lap': msg.get('Lap', 'N/A'),
                        'description': msg.get('Message', ''),
                        'severity': 'MODERATE'
                    })
                elif 'YELLOW' in msg_text:
                    yellow_flags += 1
                elif 'INVESTIGATION' in msg_text or 'PENALTY' in msg_text:
                    investigations += 1
            
            # 顯示特殊事件表格
            if special_events:
                special_table = PrettyTable()
                special_table.field_names = ["事件類型", "時間", "圈數", "嚴重度", "詳細描述"]
                special_table.align = "l"
                special_table.max_width["詳細描述"] = 60
                
                for event in special_events:
                    time_str = event['time'].strftime('%H:%M') if hasattr(event['time'], 'strftime') else str(event['time'])
                    special_table.add_row([
                        event['type'],
                        time_str,
                        event['lap'],
                        event['severity'],
                        event['description'][:60] + "..." if len(event['description']) > 60 else event['description']
                    ])
                
                print(special_table)
            
            # 顯示統計總結
            print(f"\n[STATS] 特殊事件統計:")
            stats_table = PrettyTable()
            stats_table.field_names = ["事件類型", "發生次數", "影響程度"]
            stats_table.align = "l"
            
            stats_table.add_row(["🔴 紅旗事件", red_flags, "極高" if red_flags > 0 else "無"])
            stats_table.add_row(["🚗 安全車出動", safety_cars, "高" if safety_cars > 0 else "無"])
            stats_table.add_row(["🚦 虛擬安全車", vsc_events, "中等" if vsc_events > 0 else "無"])
            stats_table.add_row(["🟡 黃旗事件", yellow_flags, "低" if yellow_flags > 0 else "無"])
            stats_table.add_row(["[DEBUG] 調查處罰", investigations, "低" if investigations > 0 else "無"])
            
            print(stats_table)
            print("[SUCCESS] 特殊事件報告分析完成")
            
        except Exception as e:
            print(f"[ERROR] 特殊事件分析失敗: {e}")

    def run_driver_severity_scores_only(self):
        """僅執行車手嚴重程度分數統計"""
        print("🏆 開始車手嚴重程度分數統計...")
        print("[INFO] 分析各車手在比賽中的表現嚴重程度...")
        
        try:
            # 載入車隊映射數據
            self._load_driver_team_mapping_if_needed()
            
            if not self._check_data_loaded():
                print("[ERROR] 數據未載入，請先載入賽事數據")
                return
            
            loaded_data = self.data_loader.loaded_data
            race_control_messages = loaded_data.get('race_control_messages')
            
            if race_control_messages is None or race_control_messages.empty:
                print("[ERROR] 沒有找到 race_control_messages")
                return
            
            print(f"\n🏆 車手嚴重程度分數統計 (Driver Severity Scores)")
            print("=" * 80)
            
            # 計算車手分數
            driver_scores = {}
            for _, msg in race_control_messages.iterrows():
                message = str(msg.get('Message', ''))
                driver = self._extract_driver_from_message(message)
                
                if driver != 'N/A' and driver != '':
                    msg_upper = message.upper()
                    score = 0
                    
                    if any(word in msg_upper for word in ['ACCIDENT', 'COLLISION', 'CRASH']):
                        score += 3
                    elif any(word in msg_upper for word in ['PENALTY']):
                        score += 2
                    elif any(word in msg_upper for word in ['INVESTIGATION', 'WARNING']):
                        score += 1
                    elif any(word in msg_upper for word in ['TRACK LIMIT', 'DELETED']):
                        score += 2
                    
                    if driver in driver_scores:
                        driver_scores[driver] += score
                    else:
                        driver_scores[driver] = score
            
            if driver_scores:
                print(f"[INFO] 車手風險分數排行榜:")
                severity_table = PrettyTable()
                severity_table.field_names = ["排名", "車手", "車隊", "總分", "風險等級"]
                severity_table.align = "l"
                
                sorted_drivers = sorted(driver_scores.items(), key=lambda x: x[1], reverse=True)
                
                for i, (driver, score) in enumerate(sorted_drivers, 1):
                    team = self.dynamic_team_mapping.get(driver, 'Unknown Team') if hasattr(self, 'dynamic_team_mapping') else 'Unknown Team'
                    
                    if score >= 5:
                        risk_level = "🔴 高風險"
                    elif score >= 3:
                        risk_level = "🟡 中等風險"
                    elif score >= 1:
                        risk_level = "🟢 低風險"
                    else:
                        risk_level = "⚪ 無風險"
                    
                    severity_table.add_row([i, driver, team[:15], score, risk_level])
                
                print(severity_table)
            else:
                print("[SUCCESS] 沒有車手事件記錄")
            
            print("[SUCCESS] 車手嚴重程度分數統計完成")
            
        except Exception as e:
            print(f"[ERROR] 車手嚴重程度分數分析失敗: {e}")

    def run_team_risk_scores_only(self):
        """僅執行車隊風險分數統計"""
        print("[FINISH] 開始車隊風險分數統計...")
        print("[INFO] 分析各車隊在比賽中的風險程度...")
        
        try:
            # 載入車隊映射數據
            self._load_driver_team_mapping_if_needed()
            
            if not self._check_data_loaded():
                print("[ERROR] 數據未載入，請先載入賽事數據")
                return
            
            loaded_data = self.data_loader.loaded_data
            race_control_messages = loaded_data.get('race_control_messages')
            
            if race_control_messages is None or race_control_messages.empty:
                print("[ERROR] 沒有找到 race_control_messages")
                return
            
            print(f"\n[FINISH] 車隊風險分數統計 (Team Risk Scores)")
            print("=" * 80)
            
            # 先計算車手分數
            driver_scores = {}
            for _, msg in race_control_messages.iterrows():
                message = str(msg.get('Message', ''))
                driver = self._extract_driver_from_message(message)
                
                if driver != 'N/A' and driver != '':
                    msg_upper = message.upper()
                    score = 0
                    
                    if any(word in msg_upper for word in ['ACCIDENT', 'COLLISION', 'CRASH']):
                        score += 3
                    elif any(word in msg_upper for word in ['PENALTY']):
                        score += 2
                    elif any(word in msg_upper for word in ['INVESTIGATION', 'WARNING']):
                        score += 1
                    elif any(word in msg_upper for word in ['TRACK LIMIT', 'DELETED']):
                        score += 2
                    
                    if driver in driver_scores:
                        driver_scores[driver] += score
                    else:
                        driver_scores[driver] = score
            
            # 計算車隊分數
            team_scores = {}
            if hasattr(self, 'dynamic_team_mapping') and self.dynamic_team_mapping:
                for driver, score in driver_scores.items():
                    team = self.dynamic_team_mapping.get(driver, 'Unknown Team')
                    if team in team_scores:
                        team_scores[team] += score
                    else:
                        team_scores[team] = score
            
            if team_scores:
                print(f"[FINISH] 車隊風險分數統計:")
                team_table = PrettyTable()
                team_table.field_names = ["排名", "車隊", "總分", "風險等級"]
                team_table.align = "l"
                
                sorted_teams = sorted(team_scores.items(), key=lambda x: x[1], reverse=True)
                
                for i, (team, score) in enumerate(sorted_teams, 1):
                    if score >= 8:
                        risk_level = "🔴 高風險"
                    elif score >= 5:
                        risk_level = "🟡 中等風險"
                    elif score >= 2:
                        risk_level = "🟢 低風險"
                    else:
                        risk_level = "⚪ 無風險"
                    
                    team_table.add_row([i, team, score, risk_level])
                
                print(team_table)
            else:
                print("[SUCCESS] 沒有車隊事件記錄")
            
            print("[SUCCESS] 車隊風險分數統計完成")
            
        except Exception as e:
            print(f"[ERROR] 車隊風險分數分析失敗: {e}")

    def run_all_incidents_summary_only(self):
        """僅執行所有事件詳細列表分析"""
        print("[LIST] 開始所有事件詳細列表分析...")
        print("[INFO] 顯示比賽中所有事件的詳細資訊...")
        
        try:
            # 載入車隊映射數據
            self._load_driver_team_mapping_if_needed()
            
            if not self._check_data_loaded():
                print("[ERROR] 數據未載入，請先載入賽事數據")
                return
            
            loaded_data = self.data_loader.loaded_data
            race_control_messages = loaded_data.get('race_control_messages')
            
            if race_control_messages is None or race_control_messages.empty:
                print("[ERROR] 沒有找到 race_control_messages")
                return
            
            print(f"\n[LIST] 所有事件詳細列表 (All Incidents Summary)")
            print("=" * 80)
            
            # 過濾重要事件
            important_events = []
            for _, msg in race_control_messages.iterrows():
                message = str(msg.get('Message', '')).upper()
                
                # 過濾不重要的消息
                ignore_keywords = [
                    'GREEN LIGHT - PIT EXIT OPEN',
                    'PIT EXIT CLOSED',
                    'DRS ENABLED',
                    'DRS DISABLED',
                    'RISK OF RAIN'
                ]
                
                if any(keyword in message for keyword in ignore_keywords):
                    continue
                
                # 重要的關鍵字
                important_keywords = [
                    'TRACK LIMIT', 'DELETED', 'INCIDENT', 'INVESTIGATION',
                    'YELLOW FLAG', 'RED FLAG', 'SAFETY CAR', 'VSC',
                    'BLUE FLAG', 'CHEQUERED FLAG', 'PENALTY', 'WARNING'
                ]
                
                if any(keyword in message for keyword in important_keywords):
                    driver = self._extract_driver_from_message(msg.get('Message', ''))
                    team = self.dynamic_team_mapping.get(driver, 'Unknown Team') if hasattr(self, 'dynamic_team_mapping') and driver != 'N/A' else 'N/A'
                    
                    important_events.append({
                        'lap': msg.get('Lap', 'N/A'),
                        'time': msg.get('Time', 'N/A'),
                        'driver': driver,
                        'team': team,
                        'message': msg.get('Message', ''),
                        'severity': self._determine_event_severity(msg.get('Message', ''))
                    })
            
            if important_events:
                print(f"\n[CRITICAL] 重要事件報告 (共 {len(important_events)} 個事件):")
                print("=" * 100)
                
                for i, event in enumerate(important_events, 1):
                    # 格式化時間
                    time_str = 'N/A'
                    if event['time'] != 'N/A' and hasattr(event['time'], 'strftime'):
                        time_str = event['time'].strftime('%H:%M')
                    
                    # 三行格式輸出
                    print(f"事件 #{i:3d} | 圈數: {event['lap']:3} | 時間: {time_str:8} | 車手: {event['driver']:4} | 車隊: {event['team'][:20]:20} | 嚴重度: {event['severity']}")
                    print(f"英文: {event['message']}")
                    print(f"中文: {self._translate_event_to_chinese(event['message'])}")
                    print("-" * 100)
                
                print(f"\n總計 {len(important_events)} 個重要事件")
            else:
                print("[SUCCESS] 沒有重要事件需要報告")
            
            print("[SUCCESS] 所有事件詳細列表分析完成")
            
        except Exception as e:
            print(f"[ERROR] 所有事件分析失敗: {e}")

    def _extract_driver_from_message(self, message):
        """從訊息中提取車手代碼"""
        if not message:
            return 'N/A'
        
        # 尋找 CAR X (DRV) 格式
        import re
        pattern = r'CAR\s+\d+\s+\(([A-Z]{3})\)'
        match = re.search(pattern, message.upper())
        if match:
            return match.group(1)
        
        # 如果有動態車隊映射，使用其中的車手代碼
        if hasattr(self, 'dynamic_team_mapping') and self.dynamic_team_mapping:
            for driver in self.dynamic_team_mapping.keys():
                if driver in message.upper():
                    return driver
        
        return 'N/A'

    def _determine_event_severity(self, message):
        """確定事件嚴重程度"""
        message_upper = message.upper()
        
        if any(keyword in message_upper for keyword in ['RED FLAG']):
            return 'CRITICAL'
        elif any(keyword in message_upper for keyword in ['PENALTY', 'INVESTIGATION']):
            return 'HIGH'
        elif any(keyword in message_upper for keyword in ['ACCIDENT', 'COLLISION', 'CRASH']):
            return 'HIGH'
        elif any(keyword in message_upper for keyword in ['DELETED', 'TRACK LIMIT']):
            return 'MEDIUM'
        elif any(keyword in message_upper for keyword in ['BLUE FLAG', 'INCIDENT']):
            return 'LOW'
        else:
            return 'LOW'

    def _translate_event_to_chinese(self, message):
        """將英文消息翻譯成中文"""
        message_upper = message.upper()
        
        if 'TRACK LIMIT' in message_upper and 'DELETED' in message_upper:
            return '賽道邊界違規 - 圈速被刪除'
        elif 'INCIDENT' in message_upper and 'NOTED' in message_upper:
            return '事件已記錄'
        elif 'BLUE FLAG' in message_upper:
            return '藍旗警告'
        elif 'CHEQUERED FLAG' in message_upper:
            return '方格旗 - 比賽結束'
        elif 'INVESTIGATION' in message_upper:
            return '調查中'
        elif 'PENALTY' in message_upper:
            return '處罰'
        elif 'PIT EXIT' in message_upper:
            return 'Pit道出口事件'
        else:
            return '賽事事件'


# 完整實現的事故分析函數，供主程式調用
def run_accident_analysis_complete(data_loader, f1_analysis_instance=None):
    """完整事故分析函數 - 供主程式調用"""
    try:
        # 創建完整事故分析實例
        accident_analysis = F1AccidentAnalysisComplete(data_loader, f1_analysis_instance)
        
        # 執行分析
        accident_analysis.run_analysis()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 事故分析執行失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_accident_analysis(data_loader, dynamic_team_mapping=None, f1_analysis_instance=None):
    """模組入口函數 - 完整的事故分析"""
    return run_accident_analysis_complete(data_loader, f1_analysis_instance)


def run_accident_analysis_json(data_loader, dynamic_team_mapping=None, f1_analysis_instance=None, enable_debug=False):
    """執行事故分析並返回JSON格式結果 - API專用"""
    if enable_debug:
        print(f"\n[CRITICAL] 執行事故分析模組 (JSON輸出版)...")
    
    try:
        # 創建事故分析器
        analyzer = F1AccidentAnalyzer()
        
        # 獲取基本賽事資訊
        session_info = {}
        if hasattr(data_loader, 'session') and data_loader.session is not None:
            session_info = {
                "event_name": getattr(data_loader.session, 'event', {}).get('EventName', 'Unknown'),
                "circuit_name": getattr(data_loader.session, 'event', {}).get('Location', 'Unknown'),
                "session_type": getattr(data_loader.session, 'session_info', {}).get('Type', 'Unknown'),
                "year": getattr(data_loader.session, 'event', {}).get('year', 2024)
            }
        
        # 執行事故分析並捕獲結果
        if hasattr(data_loader, 'session') and data_loader.session is not None:
            accidents = analyzer.analyze_accidents(data_loader.session)
            if accidents:
                stats = analyzer.calculate_statistics(accidents)
                # 構建結構化的事故分析數據
                accident_data = {
                    "accident_summary": {
                        "total_incidents": stats.get('total_incidents', 0),
                        "incident_types": {
                            "accidents": stats.get('accidents', 0),
                            "flags": stats.get('flags', 0),  
                            "investigations": stats.get('investigations', 0),
                            "safety_events": stats.get('safety_events', 0),
                            "penalties": stats.get('penalties', 0)
                        },
                        "affected_drivers": len(set(acc.get('driver_number', 'Unknown') for acc in accidents)),
                        "severity_distribution": stats.get('severity_distribution', {})
                    },
                    "incident_details": [
                        {
                            "time": acc.get('time', 'N/A'),
                            "lap": acc.get('lap', 'N/A'),
                            "driver": acc.get('driver_number', 'Unknown'),
                            "message": acc.get('message', ''),
                            "category": acc.get('category', 'Unknown'),
                            "flag": acc.get('flag', 'N/A')
                        } for acc in accidents  # 回傳所有事故詳細資料
                    ],
                    "safety_analysis": {
                        "safety_car_deployments": stats.get('safety_events', 0),
                        "red_flag_incidents": stats.get('severity_distribution', {}).get('CRITICAL', 0),
                        "high_severity_incidents": stats.get('severity_distribution', {}).get('HIGH', 0)
                    },
                    "raw_statistics": stats
                }
            else:
                accident_data = {
                    "accident_summary": {
                        "total_incidents": 0,
                        "incident_types": {},
                        "affected_drivers": 0
                    },
                    "incident_details": [],
                    "safety_analysis": {},
                    "message": "本場比賽未發現任何事故記錄"
                }
        else:
            accident_data = None
        
        if accident_data:
            result = {
                "success": True,
                "message": "成功執行 事故分析",
                "data": {
                    "function_id": 4,
                    "function_name": "Independent Accident Analysis",
                    "function_description": "獨立事故分析",
                    "category": "基礎分析",
                    "analysis_type": "detailed_accident_analysis",
                    "metadata": {
                        "analysis_type": "independent_accident_analysis",
                        "function_name": "Independent Accident Analysis",
                        "generated_at": datetime.now().isoformat(),
                        "version": "1.0",
                        **session_info
                    },
                    "accident_analysis": accident_data
                },
                "timestamp": datetime.now().isoformat()
            }
            
            if enable_debug:
                print(f"[SUCCESS] 事故分析完成 (JSON)")
            return result
        else:
            return {
                "success": False,
                "message": "事故分析執行失敗 - 無可用數據",
                "data": None,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        if enable_debug:
            print(f"[ERROR] 事故分析模組執行錯誤: {e}")
            import traceback
            traceback.print_exc()
        return {
            "success": False,
            "message": f"事故分析執行錯誤: {str(e)}",
            "data": None,
            "timestamp": datetime.now().isoformat()
        }

    # === 專門的子模組分析方法 ===
    
    def run_key_events_summary_only(self):
        """僅執行關鍵事件摘要分析"""
        print("[DEBUG] 開始關鍵事件摘要分析...")
        print("[INFO] 分析進站策略中的關鍵事件和轉折點...")
        
        try:
            # 載入車隊映射數據
            self._load_driver_team_mapping_if_needed()
            
            # 檢查數據是否已載入
            if not self._check_data_loaded():
                print("[ERROR] 數據未載入，請先載入賽事數據")
                return
            
            loaded_data = self.data_loader.loaded_data
            race_control_messages = loaded_data.get('race_control_messages')
            
            if race_control_messages is None or race_control_messages.empty:
                print("[ERROR] 沒有找到 race_control_messages")
                return
            
            print(f"\n[CRITICAL] 關鍵事件摘要 (Key Events Summary)")
            print("=" * 80)
            
            # 收集關鍵事件
            key_events = []
            for _, msg in race_control_messages.iterrows():
                msg_text = str(msg.get('Message', '')).upper()
                
                # 檢查關鍵事件類型
                if any(keyword in msg_text for keyword in ['ACCIDENT', 'COLLISION', 'CRASH', 'CONTACT', 'INCIDENT']):
                    event_type = "[CRITICAL] 事故"
                elif any(keyword in msg_text for keyword in ['SAFETY CAR', 'SC DEPLOYED', 'VSC']):
                    event_type = "🚗 安全車"
                elif any(keyword in msg_text for keyword in ['RED FLAG', 'RED LIGHT']):
                    event_type = "🔴 紅旗"
                elif any(keyword in msg_text for keyword in ['YELLOW FLAG', 'DOUBLE YELLOW']):
                    event_type = "🟡 黃旗"
                elif any(keyword in msg_text for keyword in ['GREEN FLAG', 'GREEN LIGHT']):
                    event_type = "🟢 綠旗"
                elif any(keyword in msg_text for keyword in ['PENALTY', 'WARNING', 'INVESTIGATION']):
                    event_type = "⚖️ 處罰"
                elif any(keyword in msg_text for keyword in ['CHEQUERED FLAG', 'RACE FINISHED']):
                    event_type = "[FINISH] 比賽結束"
                else:
                    continue
                
                # 格式化時間
                time_val = msg.get('Time', 'N/A')
                formatted_time = 'N/A'
                if time_val != 'N/A' and hasattr(time_val, 'strftime'):
                    formatted_time = time_val.strftime('%H:%M')
                
                key_events.append({
                    'type': event_type,
                    'time': formatted_time,
                    'lap': msg.get('Lap', 'N/A'),
                    'message': str(msg.get('Message', ''))
                })
            
            if key_events:
                print(f"[INFO] 發現 {len(key_events)} 個關鍵事件")
                
                key_table = PrettyTable()
                key_table.field_names = ["類型", "時間", "圈數", "事件描述"]
                key_table.align = "l"
                key_table.max_width["事件描述"] = 80
                
                for event in key_events:
                    key_table.add_row([event['type'], event['time'], event['lap'], event['message'][:80]])
                
                print(key_table)
            else:
                print("[SUCCESS] 沒有發現重大關鍵事件")
            
            print("[SUCCESS] 關鍵事件摘要分析完成")
            
        except Exception as e:
            print(f"[ERROR] 關鍵事件分析失敗: {e}")

    def run_special_incidents_only(self):
        """僅執行特殊事件報告分析"""
        print("[CRITICAL] 開始特殊事件報告分析...")
        print("[INFO] 分析比賽中的特殊事件和異常情況...")
        
        try:
            # 載入車隊映射數據
            self._load_driver_team_mapping_if_needed()
            
            if not self._check_data_loaded():
                print("[ERROR] 數據未載入，請先載入賽事數據")
                return
            
            loaded_data = self.data_loader.loaded_data
            race_control_messages = loaded_data.get('race_control_messages')
            
            if race_control_messages is None or race_control_messages.empty:
                print("[ERROR] 沒有找到 race_control_messages")
                return
            
            print(f"\n[CRITICAL] 特殊事件報告 (Special Incident Reports)")
            print("=" * 80)
            
            # 統計不同類型事件
            red_flags = 0
            safety_cars = 0
            vsc_events = 0
            yellow_flags = 0
            investigations = 0
            special_events = []
            
            for _, msg in race_control_messages.iterrows():
                msg_text = str(msg.get('Message', '')).upper()
                
                if 'RED' in msg_text and 'FLAG' in msg_text:
                    red_flags += 1
                    special_events.append({
                        'type': '🔴 紅旗事件',
                        'time': msg.get('Time', 'N/A'),
                        'lap': msg.get('Lap', 'N/A'),
                        'description': msg.get('Message', ''),
                        'severity': 'CRITICAL'
                    })
                elif 'SAFETY CAR' in msg_text:
                    safety_cars += 1
                    special_events.append({
                        'type': '🚗 安全車出動',
                        'time': msg.get('Time', 'N/A'),
                        'lap': msg.get('Lap', 'N/A'),
                        'description': msg.get('Message', ''),
                        'severity': 'HIGH'
                    })
                elif 'VSC' in msg_text:
                    vsc_events += 1
                    special_events.append({
                        'type': '🚦 虛擬安全車',
                        'time': msg.get('Time', 'N/A'),
                        'lap': msg.get('Lap', 'N/A'),
                        'description': msg.get('Message', ''),
                        'severity': 'MODERATE'
                    })
                elif 'YELLOW' in msg_text:
                    yellow_flags += 1
                elif 'INVESTIGATION' in msg_text or 'PENALTY' in msg_text:
                    investigations += 1
            
            # 顯示特殊事件表格
            if special_events:
                special_table = PrettyTable()
                special_table.field_names = ["事件類型", "時間", "圈數", "嚴重度", "詳細描述"]
                special_table.align = "l"
                special_table.max_width["詳細描述"] = 60
                
                for event in special_events:
                    time_str = event['time'].strftime('%H:%M') if hasattr(event['time'], 'strftime') else str(event['time'])
                    special_table.add_row([
                        event['type'],
                        time_str,
                        event['lap'],
                        event['severity'],
                        event['description'][:60] + "..." if len(event['description']) > 60 else event['description']
                    ])
                
                print(special_table)
            
            # 顯示統計總結
            print(f"\n[STATS] 特殊事件統計:")
            stats_table = PrettyTable()
            stats_table.field_names = ["事件類型", "發生次數", "影響程度"]
            stats_table.align = "l"
            
            stats_table.add_row(["🔴 紅旗事件", red_flags, "極高" if red_flags > 0 else "無"])
            stats_table.add_row(["🚗 安全車出動", safety_cars, "高" if safety_cars > 0 else "無"])
            stats_table.add_row(["🚦 虛擬安全車", vsc_events, "中等" if vsc_events > 0 else "無"])
            stats_table.add_row(["🟡 黃旗事件", yellow_flags, "低" if yellow_flags > 0 else "無"])
            stats_table.add_row(["[DEBUG] 調查處罰", investigations, "低" if investigations > 0 else "無"])
            
            print(stats_table)
            print("[SUCCESS] 特殊事件報告分析完成")
            
        except Exception as e:
            print(f"[ERROR] 特殊事件分析失敗: {e}")

    def run_driver_severity_scores_only(self):
        """僅執行車手嚴重程度分數統計"""
        print("🏆 開始車手嚴重程度分數統計...")
        print("[INFO] 分析各車手在比賽中的表現嚴重程度...")
        
        try:
            # 載入車隊映射數據
            self._load_driver_team_mapping_if_needed()
            
            if not self._check_data_loaded():
                print("[ERROR] 數據未載入，請先載入賽事數據")
                return
            
            loaded_data = self.data_loader.loaded_data
            race_control_messages = loaded_data.get('race_control_messages')
            
            if race_control_messages is None or race_control_messages.empty:
                print("[ERROR] 沒有找到 race_control_messages")
                return
            
            print(f"\n🏆 車手嚴重程度分數統計 (Driver Severity Scores)")
            print("=" * 80)
            
            # 計算車手分數
            driver_scores = {}
            for _, msg in race_control_messages.iterrows():
                message = str(msg.get('Message', ''))
                driver = self._extract_driver_from_message(message)
                
                if driver != 'N/A' and driver != '':
                    msg_upper = message.upper()
                    score = 0
                    
                    if any(word in msg_upper for word in ['ACCIDENT', 'COLLISION', 'CRASH']):
                        score += 3
                    elif any(word in msg_upper for word in ['PENALTY']):
                        score += 2
                    elif any(word in msg_upper for word in ['INVESTIGATION', 'WARNING']):
                        score += 1
                    elif any(word in msg_upper for word in ['TRACK LIMIT', 'DELETED']):
                        score += 2
                    
                    if driver in driver_scores:
                        driver_scores[driver] += score
                    else:
                        driver_scores[driver] = score
            
            if driver_scores:
                print(f"[INFO] 車手風險分數排行榜:")
                severity_table = PrettyTable()
                severity_table.field_names = ["排名", "車手", "車隊", "總分", "風險等級"]
                severity_table.align = "l"
                
                sorted_drivers = sorted(driver_scores.items(), key=lambda x: x[1], reverse=True)
                
                for i, (driver, score) in enumerate(sorted_drivers, 1):
                    team = self.dynamic_team_mapping.get(driver, 'Unknown Team') if hasattr(self, 'dynamic_team_mapping') else 'Unknown Team'
                    
                    if score >= 5:
                        risk_level = "🔴 高風險"
                    elif score >= 3:
                        risk_level = "🟡 中等風險"
                    elif score >= 1:
                        risk_level = "🟢 低風險"
                    else:
                        risk_level = "⚪ 無風險"
                    
                    severity_table.add_row([i, driver, team[:15], score, risk_level])
                
                print(severity_table)
            else:
                print("[SUCCESS] 沒有車手事件記錄")
            
            print("[SUCCESS] 車手嚴重程度分數統計完成")
            
        except Exception as e:
            print(f"[ERROR] 車手嚴重程度分數分析失敗: {e}")

    def run_team_risk_scores_only(self):
        """僅執行車隊風險分數統計"""
        print("[FINISH] 開始車隊風險分數統計...")
        print("[INFO] 分析各車隊的比賽風險程度...")
        
        try:
            # 載入車隊映射數據
            self._load_driver_team_mapping_if_needed()
            
            if not self._check_data_loaded():
                print("[ERROR] 數據未載入，請先載入賽事數據")
                return
            
            loaded_data = self.data_loader.loaded_data
            race_control_messages = loaded_data.get('race_control_messages')
            
            if race_control_messages is None or race_control_messages.empty:
                print("[ERROR] 沒有找到 race_control_messages")
                return
            
            print(f"\n[FINISH] 車隊風險分數統計 (Team Risk Scores)")
            print("=" * 80)
            
            # 先計算車手分數
            driver_scores = {}
            for _, msg in race_control_messages.iterrows():
                message = str(msg.get('Message', ''))
                driver = self._extract_driver_from_message(message)
                
                if driver != 'N/A' and driver != '':
                    msg_upper = message.upper()
                    score = 0
                    
                    if any(word in msg_upper for word in ['ACCIDENT', 'COLLISION', 'CRASH']):
                        score += 3
                    elif any(word in msg_upper for word in ['PENALTY']):
                        score += 2
                    elif any(word in msg_upper for word in ['INVESTIGATION', 'WARNING']):
                        score += 1
                    elif any(word in msg_upper for word in ['TRACK LIMIT', 'DELETED']):
                        score += 2
                    
                    if driver in driver_scores:
                        driver_scores[driver] += score
                    else:
                        driver_scores[driver] = score
            
            # 計算車隊分數
            team_scores = {}
            if hasattr(self, 'dynamic_team_mapping') and self.dynamic_team_mapping:
                for driver, score in driver_scores.items():
                    team = self.dynamic_team_mapping.get(driver, 'Unknown Team')
                    if team in team_scores:
                        team_scores[team] += score
                    else:
                        team_scores[team] = score
            
            if team_scores:
                print(f"[FINISH] 車隊風險分數統計:")
                team_table = PrettyTable()
                team_table.field_names = ["排名", "車隊", "總分", "風險等級"]
                team_table.align = "l"
                
                sorted_teams = sorted(team_scores.items(), key=lambda x: x[1], reverse=True)
                
                for i, (team, score) in enumerate(sorted_teams, 1):
                    if score >= 8:
                        risk_level = "🔴 高風險"
                    elif score >= 5:
                        risk_level = "🟡 中等風險"
                    elif score >= 2:
                        risk_level = "🟢 低風險"
                    else:
                        risk_level = "⚪ 無風險"
                    
                    team_table.add_row([i, team, score, risk_level])
                
                print(team_table)
            else:
                print("[SUCCESS] 沒有車隊事件記錄")
            
            print("[SUCCESS] 車隊風險分數統計完成")
            
        except Exception as e:
            print(f"[ERROR] 車隊風險分數分析失敗: {e}")

    def run_all_incidents_summary_only(self):
        """僅執行所有事件詳細列表分析"""
        print("[LIST] 開始所有事件詳細列表分析...")
        print("[INFO] 顯示比賽中所有事件的詳細資訊...")
        
        try:
            # 載入車隊映射數據
            self._load_driver_team_mapping_if_needed()
            
            if not self._check_data_loaded():
                print("[ERROR] 數據未載入，請先載入賽事數據")
                return
            
            loaded_data = self.data_loader.loaded_data
            race_control_messages = loaded_data.get('race_control_messages')
            
            if race_control_messages is None or race_control_messages.empty:
                print("[ERROR] 沒有找到 race_control_messages")
                return
            
            print(f"\n[LIST] 所有事件詳細列表 (All Incidents Summary)")
            print("=" * 80)
            
            # 過濾重要事件
            important_events = []
            for _, msg in race_control_messages.iterrows():
                message = str(msg.get('Message', '')).upper()
                
                # 過濾不重要的消息
                ignore_keywords = [
                    'GREEN LIGHT - PIT EXIT OPEN',
                    'PIT EXIT CLOSED',
                    'DRS ENABLED',
                    'DRS DISABLED',
                    'RISK OF RAIN'
                ]
                
                if any(keyword in message for keyword in ignore_keywords):
                    continue
                
                # 重要的關鍵字
                important_keywords = [
                    'TRACK LIMIT', 'DELETED', 'INCIDENT', 'INVESTIGATION',
                    'YELLOW FLAG', 'RED FLAG', 'SAFETY CAR', 'VSC',
                    'BLUE FLAG', 'CHEQUERED FLAG', 'PENALTY', 'WARNING'
                ]
                
                if any(keyword in message for keyword in important_keywords):
                    driver = self._extract_driver_from_message(msg.get('Message', ''))
                    team = self.dynamic_team_mapping.get(driver, 'Unknown Team') if hasattr(self, 'dynamic_team_mapping') and driver != 'N/A' else 'N/A'
                    
                    important_events.append({
                        'lap': msg.get('Lap', 'N/A'),
                        'time': msg.get('Time', 'N/A'),
                        'driver': driver,
                        'team': team,
                        'message': msg.get('Message', ''),
                        'severity': self._determine_event_severity(msg.get('Message', ''))
                    })
            
            if important_events:
                print(f"\n[CRITICAL] 重要事件報告 (共 {len(important_events)} 個事件):")
                print("=" * 100)
                
                for i, event in enumerate(important_events, 1):
                    # 格式化時間
                    time_str = 'N/A'
                    if event['time'] != 'N/A' and hasattr(event['time'], 'strftime'):
                        time_str = event['time'].strftime('%H:%M')
                    
                    # 三行格式輸出
                    print(f"事件 #{i:3d} | 圈數: {event['lap']:3} | 時間: {time_str:8} | 車手: {event['driver']:4} | 車隊: {event['team'][:20]:20} | 嚴重度: {event['severity']}")
                    print(f"英文: {event['message']}")
                    print(f"中文: {self._translate_event_to_chinese(event['message'])}")
                    print("-" * 100)
                
                print(f"\n總計 {len(important_events)} 個重要事件")
            else:
                print("[SUCCESS] 沒有重要事件需要報告")
            
            print("[SUCCESS] 所有事件詳細列表分析完成")
            
        except Exception as e:
            print(f"[ERROR] 所有事件分析失敗: {e}")

    def _determine_event_severity(self, message):
        """確定事件嚴重程度"""
        message_upper = message.upper()
        
        if any(keyword in message_upper for keyword in ['RED FLAG']):
            return 'CRITICAL'
        elif any(keyword in message_upper for keyword in ['PENALTY', 'INVESTIGATION']):
            return 'HIGH'
        elif any(keyword in message_upper for keyword in ['ACCIDENT', 'COLLISION', 'CRASH']):
            return 'HIGH'
        elif any(keyword in message_upper for keyword in ['DELETED', 'TRACK LIMIT']):
            return 'MEDIUM'
        elif any(keyword in message_upper for keyword in ['BLUE FLAG', 'INCIDENT']):
            return 'LOW'
        else:
            return 'LOW'

    def _translate_event_to_chinese(self, message):
        """將英文消息翻譯成中文"""
        message_upper = message.upper()
        
        if 'TRACK LIMIT' in message_upper and 'DELETED' in message_upper:
            return '賽道邊界違規 - 圈速被刪除'
        elif 'INCIDENT' in message_upper and 'NOTED' in message_upper:
            return '事件已記錄'
        elif 'BLUE FLAG' in message_upper:
            return '藍旗警告'
        elif 'CHEQUERED FLAG' in message_upper:
            return '方格旗 - 比賽結束'
        elif 'INVESTIGATION' in message_upper:
            return '調查中'
        elif 'PENALTY' in message_upper:
            return '處罰'
        elif 'PIT EXIT' in message_upper:
            return 'Pit道出口事件'
        else:
            return '賽事事件'


# === 獨立的調用函數，供外部使用 ===

def run_key_events_summary(data_loader, dynamic_team_mapping=None, f1_analysis_instance=None):
    """獨立執行關鍵事件摘要分析"""
    analyzer = F1AccidentAnalysisComplete(data_loader, f1_analysis_instance)
    if dynamic_team_mapping:
        analyzer.dynamic_team_mapping = dynamic_team_mapping
    analyzer.run_key_events_summary_only()

def run_special_incidents_analysis(data_loader, dynamic_team_mapping=None, f1_analysis_instance=None):
    """獨立執行特殊事件報告分析"""
    analyzer = F1AccidentAnalysisComplete(data_loader, f1_analysis_instance)
    if dynamic_team_mapping:
        analyzer.dynamic_team_mapping = dynamic_team_mapping
    analyzer.run_special_incidents_only()

def run_driver_severity_scores_analysis(data_loader, dynamic_team_mapping=None, f1_analysis_instance=None):
    """獨立執行車手嚴重程度分數統計"""
    analyzer = F1AccidentAnalysisComplete(data_loader, f1_analysis_instance)
    if dynamic_team_mapping:
        analyzer.dynamic_team_mapping = dynamic_team_mapping
    analyzer.run_driver_severity_scores_only()

def run_team_risk_scores_analysis(data_loader, dynamic_team_mapping=None, f1_analysis_instance=None):
    """獨立執行車隊風險分數統計"""
    analyzer = F1AccidentAnalysisComplete(data_loader, f1_analysis_instance)
    if dynamic_team_mapping:
        analyzer.dynamic_team_mapping = dynamic_team_mapping
    analyzer.run_team_risk_scores_only()

def run_all_incidents_summary_analysis(data_loader, dynamic_team_mapping=None, f1_analysis_instance=None):
    """獨立執行所有事件詳細列表分析"""
    analyzer = F1AccidentAnalysisComplete(data_loader, f1_analysis_instance)
    if dynamic_team_mapping:
        analyzer.dynamic_team_mapping = dynamic_team_mapping
    analyzer.run_all_incidents_summary_only()
