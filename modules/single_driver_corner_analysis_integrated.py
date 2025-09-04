#!/usr/bin/env python3
"""
F1 單一車手詳細彎道分析模組 (集成進站與事件版)
功能 12.1 - 整合進站資料與特殊事件報告的彎道分析
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import traceback
from datetime import datetime
import fastf1
from pathlib import Path
import pickle
import hashlib
from prettytable import PrettyTable

# 添加模組路徑
sys.path.append(str(Path(__file__).parent.parent))
from modules.race_pitstop_statistics_enhanced import RacePitstopStatisticsEnhanced
from modules.gui.accident_analysis.accident_analysis_complete import F1AccidentAnalyzer

class SingleDriverCornerAnalysisIntegrated:
    """單一車手詳細彎道分析 - 集成進站與事件版本"""
    
    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.setup_matplotlib()
        self.cache_dir = Path("corner_analysis_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # 初始化進站統計分析器
        self.pitstop_analyzer = None
        self.accident_analyzer = None
        
    def setup_matplotlib(self):
        """設置中文字體"""
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
        
    def load_pitstop_data(self):
        """載入進站資料"""
        try:
            print("[INFO] 載入進站統計資料...")
            self.pitstop_analyzer = RacePitstopStatisticsEnhanced()
            
            # 從data_loader獲取賽事資訊
            metadata = self.data_loader.get_loaded_data().get('metadata', {})
            year = metadata.get('year', 2025)
            race = metadata.get('race_name', 'Japan')
            session = metadata.get('session_type', 'R')
            
            if self.pitstop_analyzer.load_race_data(year, race, session):
                print("[SUCCESS] 進站資料載入成功")
                return True
            else:
                print("[ERROR] 進站資料載入失敗")
                return False
                
        except Exception as e:
            print(f"[ERROR] 載入進站資料時發生錯誤: {e}")
            return False
    
    def load_incident_data(self):
        """載入特殊事件資料"""
        try:
            print("[CRITICAL] 載入特殊事件資料...")
            self.accident_analyzer = F1AccidentAnalyzer()
            
            # 從data_loader獲取session並分析事故
            session = self.data_loader.session
            if session and hasattr(session, 'race_control_messages'):
                self.accident_analyzer.analyze_accidents(session)
                print("[SUCCESS] 特殊事件資料載入成功")
                return True
            else:
                print("[ERROR] 無法獲取賽事控制訊息")
                return False
                
        except Exception as e:
            print(f"[ERROR] 載入特殊事件資料時發生錯誤: {e}")
            return False
    
    def get_pitstop_info_for_driver(self, driver):
        """獲取指定車手的進站資訊"""
        if not self.pitstop_analyzer:
            return []
            
        try:
            # 從pitstop_analyzer獲取進站數據
            if hasattr(self.pitstop_analyzer, 'openf1_pitstops') and self.pitstop_analyzer.openf1_pitstops:
                # 使用OpenF1數據
                pitstops = []
                for stop in self.pitstop_analyzer.openf1_pitstops:
                    driver_info = stop.get('driver_info', {})
                    driver_name = driver_info.get('name_acronym', '')
                    
                    if driver_name == driver:
                        pitstops.append({
                            'lap_number': stop.get('lap_number'),
                            'duration': stop.get('pit_duration'),
                            'source': 'OpenF1'
                        })
                return pitstops
            else:
                # 使用FastF1數據
                if hasattr(self.data_loader, 'laps') and self.data_loader.laps is not None:
                    driver_laps = self.data_loader.laps[self.data_loader.laps['Driver'] == driver]
                    pitstops = []
                    
                    for _, lap in driver_laps.iterrows():
                        if pd.notna(lap.get('PitOutTime')) or pd.notna(lap.get('PitInTime')):
                            pitstops.append({
                                'lap_number': lap['LapNumber'],
                                'duration': 25.0,  # 估算時間
                                'source': 'FastF1'
                            })
                    return pitstops
                    
        except Exception as e:
            print(f"[WARNING] 獲取車手 {driver} 進站資訊時發生錯誤: {e}")
            
        return []
    
    def get_incident_info_for_lap_range(self, start_lap, end_lap):
        """獲取指定圈數範圍內的特殊事件"""
        if not self.accident_analyzer or not hasattr(self.accident_analyzer, 'accidents'):
            return []
            
        try:
            incidents = []
            for accident in self.accident_analyzer.accidents:
                lap_num = accident.get('lap', 0)
                if lap_num and start_lap <= lap_num <= end_lap:
                    incidents.append({
                        'lap': lap_num,
                        'type': self._classify_incident_type(accident.get('message', '')),
                        'message': accident.get('message', ''),
                        'time': accident.get('time', 'N/A')
                    })
            return incidents
            
        except Exception as e:
            print(f"[WARNING] 獲取事件資訊時發生錯誤: {e}")
            return []
    
    def _classify_incident_type(self, message):
        """分類事件類型"""
        msg = str(message).upper()
        
        if 'RED' in msg and 'FLAG' in msg:
            return '🔴 紅旗'
        elif 'SAFETY CAR' in msg:
            return '🚗 安全車'
        elif 'VIRTUAL SAFETY CAR' in msg or 'VSC' in msg:
            return '🟡 虛擬安全車'
        elif 'YELLOW' in msg and 'FLAG' in msg:
            return '🟡 黃旗'
        elif 'INVESTIGATION' in msg:
            return '[DEBUG] 調查'
        elif 'PENALTY' in msg:
            return '[WARNING] 處罰'
        else:
            return '[LIST] 其他事件'
    
    def analyze_single_driver_corner(self, driver="LEC", corner_number=1, auto_mode=True):
        """
        分析單一車手在指定彎道的表現 - 集成進站與事件資料
        """
        try:
            print(f"\n🏎️ 單一車手詳細彎道分析 - 功能 12.1 (集成版)")
            print(f"[DEBUG] 分析車手: {driver}")
            print(f"[TARGET] 分析彎道: 第 {corner_number} 彎 (T{corner_number})")
            print("="*80)
            
            # 載入進站資料
            pitstop_loaded = self.load_pitstop_data()
            
            # 載入事件資料
            incident_loaded = self.load_incident_data()
            
            # 獲取車手遙測數據
            if not hasattr(self.data_loader, 'laps') or self.data_loader.laps is None:
                print("[ERROR] 無法獲取圈速數據")
                return False
                
            driver_laps = self.data_loader.laps[self.data_loader.laps['Driver'] == driver]
            if driver_laps.empty:
                print(f"[ERROR] 找不到車手 {driver} 的數據")
                return False
            
            # 獲取彎道遙測數據
            corner_data = self._get_corner_telemetry_data(driver, corner_number)
            if not corner_data:
                print(f"[ERROR] 無法獲取 T{corner_number} 彎道遙測數據")
                return False
            
            # 獲取進站資訊
            pitstop_info = self.get_pitstop_info_for_driver(driver) if pitstop_loaded else []
            
            # 生成詳細分析表格
            self._display_detailed_corner_analysis_table(
                driver, corner_number, corner_data, pitstop_info, incident_loaded
            )
            
            # 生成JSON輸出
            json_output = self._generate_json_output(
                driver, corner_number, corner_data, pitstop_info, incident_loaded
            )
            
            # 保存JSON文件
            # 確保json資料夾存在
            import os
            json_dir = "json"
            os.makedirs(json_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(json_dir, f"single_driver_corner_analysis_integrated_{driver}_T{corner_number}_{timestamp}.json")
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(json_output, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"\n[SUCCESS] 分析完成！JSON輸出已保存到: {filename}")
            return True
            
        except Exception as e:
            print(f"[ERROR] 彎道分析過程中發生錯誤: {e}")
            traceback.print_exc()
            return False
    
    def _get_corner_telemetry_data(self, driver, corner_number):
        """獲取彎道遙測數據"""
        try:
            # 獲取車手的遙測數據
            driver_laps = self.data_loader.laps[self.data_loader.laps['Driver'] == driver]
            
            corner_data = []
            for _, lap in driver_laps.iterrows():
                try:
                    lap_telemetry = lap.get_telemetry()
                    if lap_telemetry is not None and not lap_telemetry.empty:
                        # 計算彎道位置
                        total_distance = lap_telemetry['Distance'].max()
                        corner_start = (corner_number - 1) * (total_distance / 20)  # 假設20個主要彎道
                        corner_end = corner_start + (total_distance / 40)  # 彎道範圍
                        
                        # 彎道內遙測數據 (用於計算彎中心速度)
                        corner_telemetry = lap_telemetry[
                            (lap_telemetry['Distance'] >= corner_start) & 
                            (lap_telemetry['Distance'] <= corner_end)
                        ]
                        
                        # 進彎前遙測數據 (用於計算進彎前最高速度)
                        pre_corner_telemetry = lap_telemetry[
                            (lap_telemetry['Distance'] >= corner_start - 200) & 
                            (lap_telemetry['Distance'] <= corner_start)
                        ]
                        
                        if not corner_telemetry.empty:
                            # 彎中心速度 (彎道內平均速度)
                            corner_center_speed = corner_telemetry['Speed'].mean()
                            
                            # 進彎前最高速度
                            entry_max_speed = None
                            if not pre_corner_telemetry.empty:
                                entry_max_speed = pre_corner_telemetry['Speed'].max()
                            else:
                                # 如果沒有進彎前數據，使用彎道內最高速度作為替代
                                entry_max_speed = corner_telemetry['Speed'].max()
                            
                            corner_data.append({
                                'lap_number': lap['LapNumber'],
                                'lap_time': lap['LapTime'].total_seconds() if pd.notna(lap['LapTime']) else None,
                                'avg_speed': corner_center_speed,  # 彎中心速度
                                'min_speed': corner_telemetry['Speed'].min(),  # 彎道內最低速度（保留參考）
                                'max_speed': entry_max_speed,  # 進彎前最高速度
                                'compound': lap.get('Compound', 'Unknown')
                            })
                            
                except Exception as e:
                    # 如果無法獲取遙測數據，使用基本數據
                    corner_data.append({
                        'lap_number': lap['LapNumber'],
                        'lap_time': lap['LapTime'].total_seconds() if pd.notna(lap['LapTime']) else None,
                        'avg_speed': None,
                        'min_speed': None,
                        'max_speed': None,
                        'compound': lap.get('Compound', 'Unknown')
                    })
                    continue
            
            return corner_data
            
        except Exception as e:
            print(f"[WARNING] 獲取彎道遙測數據時發生錯誤: {e}")
            return []
            return []
    
    def _display_detailed_corner_analysis_table(self, driver, corner_number, corner_data, pitstop_info, incident_loaded):
        """顯示詳細彎道分析表格 - 包含進站與事件資訊"""
        # 獲取P1車手資料
        session = self.data_loader.session
        p1_data = self._get_p1_driver_data(session)
        p1_performance = None
        
        if p1_data and p1_data['abbreviation'] != driver:
            p1_performance = self._get_p1_corner_performance(session, p1_data, corner_number)
            if p1_performance:
                print(f"\n[LIST] {driver} - T{corner_number} 彎道詳細分析表格")
                print(f"   🏆 P1車手比較基準: {p1_data['name']} ({p1_data['abbreviation']})")
                print(f"   [INFO] P1平均彎中心速度: {p1_performance['avg_corner_speed']:.1f} km/h")
                print(f"   [INFO] P1平均進彎速度: {p1_performance['avg_entry_speed']:.1f} km/h" if p1_performance['avg_entry_speed'] else "   [INFO] P1平均進彎速度: N/A")
            else:
                print(f"\n[LIST] {driver} - T{corner_number} 彎道詳細分析表格")
                print(f"   🏆 P1車手比較基準: {p1_data['name']} ({p1_data['abbreviation']}) - 無法獲取彎道資料")
        else:
            print(f"\n[LIST] {driver} - T{corner_number} 彎道詳細分析表格")
            if p1_data and p1_data['abbreviation'] == driver:
                print(f"   🏆 {driver} 就是P1車手！")
        
        print("-"*120)
        
        # 創建進站圈數字典供快速查找
        pitstop_laps = {p['lap_number']: p for p in pitstop_info} if pitstop_info else {}
        
        # 創建詳細分析表格
        detail_table = PrettyTable()
        detail_table.field_names = [
            "圈數", "圈速", "彎中心速度", "進彎前最高速度", "與P1彎速差", "與P1進彎差",
            "輪胎", "進站資訊", "異常標註"
        ]
        detail_table.align = "c"
        
        # 計算異常檢測閾值
        valid_corner_speeds = [d['avg_speed'] for d in corner_data if d['avg_speed'] and d['avg_speed'] > 0]
        valid_max_speeds = [d['max_speed'] for d in corner_data if d['max_speed'] and d['max_speed'] > 0]
        valid_lap_times = [d['lap_time'] for d in corner_data if d['lap_time'] and d['lap_time'] > 0]
        
        corner_speed_std = np.std(valid_corner_speeds) if valid_corner_speeds else 0
        corner_speed_mean = np.mean(valid_corner_speeds) if valid_corner_speeds else 0
        max_speed_std = np.std(valid_max_speeds) if valid_max_speeds else 0
        max_speed_mean = np.mean(valid_max_speeds) if valid_max_speeds else 0
        lap_time_std = np.std(valid_lap_times) if valid_lap_times else 0
        lap_time_mean = np.mean(valid_lap_times) if valid_lap_times else 0
        
        for data in corner_data[:20]:  # 顯示前20圈
            lap_num = data['lap_number']
            
            # 圈速
            lap_time_str = f"{data['lap_time']:.3f}s" if data['lap_time'] else "N/A"
            
            # 彎中心速度 (使用avg_speed作為彎中心速度)
            corner_speed_str = f"{data['avg_speed']:.1f}" if data['avg_speed'] else "N/A"
            
            # 進彎前最高速度
            entry_speed_str = f"{data['max_speed']:.1f}" if data['max_speed'] else "N/A"
            
            # 與P1車手的速度差
            p1_corner_diff_str = "N/A"
            p1_entry_diff_str = "N/A"
            
            if p1_performance and data['avg_speed'] and data['max_speed']:
                if p1_performance['avg_corner_speed']:
                    corner_diff = data['avg_speed'] - p1_performance['avg_corner_speed']
                    p1_corner_diff_str = f"{corner_diff:+.1f}"
                
                if p1_performance['avg_entry_speed']:
                    entry_diff = data['max_speed'] - p1_performance['avg_entry_speed']
                    p1_entry_diff_str = f"{entry_diff:+.1f}"
            
            # 異常標註
            anomaly_flags = []
            if data['lap_time'] and lap_time_mean > 0:
                if abs(data['lap_time'] - lap_time_mean) > 2 * lap_time_std:
                    if data['lap_time'] > lap_time_mean:
                        anomaly_flags.append("圈速慢")
                    else:
                        anomaly_flags.append("圈速快")
            
            if data['avg_speed'] and corner_speed_mean > 0:
                if abs(data['avg_speed'] - corner_speed_mean) > 1.5 * corner_speed_std:
                    if data['avg_speed'] < corner_speed_mean:
                        anomaly_flags.append("彎速慢")
                    else:
                        anomaly_flags.append("彎速快")
            
            if data['max_speed'] and max_speed_mean > 0:
                if abs(data['max_speed'] - max_speed_mean) > 1.5 * max_speed_std:
                    if data['max_speed'] < max_speed_mean:
                        anomaly_flags.append("進彎慢")
                    else:
                        anomaly_flags.append("進彎快")
            
            anomaly_str = " | ".join(anomaly_flags) if anomaly_flags else "[SUCCESS]"
            
            # 進站資訊
            pitstop_str = ""
            if lap_num in pitstop_laps:
                pit_info = pitstop_laps[lap_num]
                pitstop_str = f"[CONFIG] {pit_info['duration']:.1f}s"
            else:
                pitstop_str = "-"
            
            detail_table.add_row([
                f"L{lap_num}",
                lap_time_str,
                corner_speed_str,
                entry_speed_str,
                p1_corner_diff_str,
                p1_entry_diff_str,
                data['compound'],
                pitstop_str,
                anomaly_str[:20] + "..." if len(anomaly_str) > 20 else anomaly_str
            ])
        
        print(detail_table)
        
        # 顯示異常檢測閾值
        if corner_speed_std > 0 or max_speed_std > 0 or lap_time_std > 0:
            print(f"\n� 異常檢測閾值:")
            if lap_time_std > 0:
                print(f"   圈速: ±{2*lap_time_std:.3f}s")
            if corner_speed_std > 0:
                print(f"   彎中心速度: ±{1.5*corner_speed_std:.1f} km/h")
            if max_speed_std > 0:
                print(f"   進彎前速度: ±{1.5*max_speed_std:.1f} km/h")
        
        # P1車手比較摘要
        if p1_performance:
            print(f"\n🏆 與P1車手 {p1_data['abbreviation']} 比較摘要:")
            if p1_performance['avg_corner_speed']:
                avg_corner_diff = corner_speed_mean - p1_performance['avg_corner_speed']
                print(f"   彎中心速度差平均: {avg_corner_diff:+.1f} km/h ({'較快' if avg_corner_diff > 0 else '較慢'})")
            if p1_performance['avg_entry_speed']:
                avg_entry_diff = max_speed_mean - p1_performance['avg_entry_speed']
                print(f"   進彎前速度差平均: {avg_entry_diff:+.1f} km/h ({'較快' if avg_entry_diff > 0 else '較慢'})")
        
        # 進站統計摘要
        if pitstop_info:
            print(f"\n� {driver} 進站統計摘要:")
            print(f"   總進站次數: {len(pitstop_info)}")
            pitstop_laps_list = [str(p['lap_number']) for p in pitstop_info]
            print(f"   進站圈數: {', '.join(pitstop_laps_list)}")
            avg_duration = np.mean([p['duration'] for p in pitstop_info if p['duration']])
            print(f"   平均進站時間: {avg_duration:.1f}秒")
        
    def _generate_json_output(self, driver, corner_number, corner_data, pitstop_info, incident_loaded):
        """生成JSON輸出"""
        # 獲取事件資訊
        incidents = []
        if incident_loaded:
            total_laps = len(corner_data)
            incidents = self.get_incident_info_for_lap_range(1, total_laps)
        
        output = {
            "analysis_info": {
                "function_id": "12.1_integrated",
                "analysis_type": "single_driver_corner_analysis_with_pitstops_and_incidents",
                "driver": driver,
                "corner_number": corner_number,
                "timestamp": datetime.now().isoformat()
            },
            "driver_summary": {
                "total_laps_analyzed": len(corner_data),
                "pitstop_summary": {
                    "total_pitstops": len(pitstop_info),
                    "pitstop_laps": [p['lap_number'] for p in pitstop_info],
                    "average_pitstop_duration": np.mean([p['duration'] for p in pitstop_info if p['duration']]) if pitstop_info else 0
                },
                "incident_summary": {
                    "total_incidents": len(incidents),
                    "incident_types": list(set([inc['type'] for inc in incidents]))
                }
            },
            "detailed_lap_data": [],
            "pitstop_details": pitstop_info,
            "incident_details": incidents
        }
        
        # 進站圈數字典
        pitstop_laps = {p['lap_number']: p for p in pitstop_info} if pitstop_info else {}
        incident_laps = {}
        for inc in incidents:
            lap = inc['lap']
            if lap not in incident_laps:
                incident_laps[lap] = []
            incident_laps[lap].append(inc)
        
        # 詳細圈數數據
        for data in corner_data:
            lap_num = data['lap_number']
            
            lap_detail = {
                "lap_number": lap_num,
                "lap_time": data['lap_time'],
                "corner_performance": {
                    "avg_speed": data['avg_speed'],
                    "min_speed": data['min_speed'],
                    "max_speed": data['max_speed']
                },
                "tire_compound": data['compound'],
                "pitstop_data": pitstop_laps.get(lap_num, None),
                "incidents_this_lap": incident_laps.get(lap_num, [])
            }
            
            output["detailed_lap_data"].append(lap_detail)
        
        return output

    def _get_p1_driver_data(self, session):
        """獲取P1車手資料"""
        try:
            results_df = session.results
            
            # 查找Position為1的車手
            p1_driver = results_df[results_df['Position'] == 1]
            if not p1_driver.empty:
                p1_row = p1_driver.iloc[0]
                return {
                    'name': p1_row['FullName'],
                    'abbreviation': p1_row['Abbreviation'],
                    'driver_number': p1_row['DriverNumber'],
                    'team': p1_row['TeamName']
                }
            return None
        except Exception as e:
            print(f"[WARNING] 無法獲取P1車手資料: {e}")
            return None
    
    def _get_p1_corner_performance(self, session, p1_data, corner_number):
        """獲取P1車手在指定彎道的平均表現"""
        try:
            # 獲取P1車手的圈數資料
            p1_laps = session.laps.pick_drivers(p1_data['abbreviation'])
            
            if p1_laps.empty:
                return None
            
            # 過濾有效圈數（排除進站圈、事故圈等）
            valid_p1_laps = []
            for _, lap in p1_laps.iterrows():
                # 基本過濾條件
                if (lap['IsAccurate'] and 
                    pd.notna(lap['LapTime']) and 
                    lap['LapTime'] > pd.Timedelta(minutes=1) and
                    pd.isna(lap['PitOutTime']) and pd.isna(lap['PitInTime'])):
                    valid_p1_laps.append(lap)
            
            if not valid_p1_laps:
                return None
            
            # 分析P1車手在該彎道的表現
            corner_speeds = []
            entry_speeds = []
            
            for lap in valid_p1_laps:
                lap_number = lap['LapNumber']
                
                # 跳過T1第一圈
                if corner_number == 1 and lap_number == 1:
                    continue
                
                try:
                    # 獲取該圈遙測數據
                    telemetry = lap.get_telemetry().add_distance()
                    if telemetry.empty:
                        continue
                    
                    # 計算彎道位置（簡化計算）
                    total_distance = telemetry['Distance'].max()
                    corner_start = (corner_number - 1) * (total_distance / 20)  # 假設20個主要彎道
                    corner_end = corner_start + (total_distance / 40)  # 彎道寬度
                    
                    # 獲取彎道內的速度數據
                    corner_telemetry = telemetry[
                        (telemetry['Distance'] >= corner_start) & 
                        (telemetry['Distance'] <= corner_end)
                    ]
                    
                    if not corner_telemetry.empty:
                        corner_speed = corner_telemetry['Speed'].mean()
                        if corner_speed >= 20:  # 過濾過低速度
                            corner_speeds.append(corner_speed)
                            
                            # 進彎前最高速度
                            pre_corner = telemetry[
                                (telemetry['Distance'] >= corner_start - 100) & 
                                (telemetry['Distance'] <= corner_start)
                            ]
                            if not pre_corner.empty:
                                entry_max_speed = pre_corner['Speed'].max()
                                entry_speeds.append(entry_max_speed)
                                
                except Exception as e:
                    continue
            
            if corner_speeds:
                result = {
                    'avg_corner_speed': np.mean(corner_speeds),
                    'avg_entry_speed': np.mean(entry_speeds) if entry_speeds else None,
                    'laps_analyzed': len(corner_speeds)
                }
                return result
            
            return None
            
        except Exception as e:
            return None


def run_single_driver_corner_analysis_integrated(data_loader, f1_analysis_instance=None):
    """
    執行單一車手詳細彎道分析 - 集成進站與事件版 (功能 12.1)
    支援用戶選擇車手和彎道，整合進站資料與特殊事件報告
    """
    try:
        analyzer = SingleDriverCornerAnalysisIntegrated(data_loader)
        
        # 檢查是否為參數模式（自動模式）
        # 如果有設定f1_analysis_instance，表示是從主程序調用，使用自動模式
        if f1_analysis_instance is not None:
            return analyzer.analyze_single_driver_corner(driver="LEC", corner_number=1, auto_mode=True)
        else:
            return analyzer.analyze_single_driver_corner(driver="LEC", corner_number=None, auto_mode=False)
    except Exception as e:
        print(f"[ERROR] 執行單一車手彎道分析(集成版)失敗: {e}")
        return False


def main():
    """主函數"""
    print("🏎️ 單一車手詳細彎道分析 - 集成進站與事件版")
    print("="*60)
    
    # 參數設置
    driver = "VER"
    corner_number = 1
    
    if len(sys.argv) > 1:
        driver = sys.argv[1]
    if len(sys.argv) > 2:
        corner_number = int(sys.argv[2])
    
    print(f"📅 分析設定: 車手 {driver}, 彎道 T{corner_number}")
    print(f"[TIP] 功能特色: 整合進站資料與特殊事件報告")
    
    # 需要data_loader，這裡示例用法
    # analyzer = SingleDriverCornerAnalysisIntegrated(data_loader)
    # result = analyzer.analyze_single_driver_corner(driver, corner_number)
    
    print("[WARNING] 此模組需要配合 f1_analysis_modular_main.py 使用")
    print("請執行: python f1_analysis_modular_main.py -f 12.1")


if __name__ == "__main__":
    main()
