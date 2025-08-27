#!/usr/bin/env python3
"""
F1 團隊車手彎道對比分析模組 (集成進站與事件版)
功能 12.2 - 整合進站資料與特殊事件報告的車手對比分析
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
from modules.accident_analysis_complete import F1AccidentAnalyzer

class TeamDriversCornerComparisonIntegrated:
    """團隊車手彎道對比分析 - 集成進站與事件版本"""
    
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
    
    def analyze_team_drivers_corner_comparison(self, driver1="VER", driver2="NOR", corner_number=1, auto_mode=True):
        """
        分析兩位車手在指定彎道的對比表現 - 集成進站與事件資料
        """
        try:
            print(f"\n🆚 團隊車手彎道對比分析 - 功能 12.2 (集成版)")
            print(f"[DEBUG] 對比車手: {driver1} vs {driver2}")
            print(f"[TARGET] 分析彎道: 第 {corner_number} 彎 (T{corner_number})")
            print("="*80)
            
            # 載入進站資料
            pitstop_loaded = self.load_pitstop_data()
            
            # 載入事件資料
            incident_loaded = self.load_incident_data()
            
            # 獲取兩位車手的數據
            driver1_data = self._get_driver_corner_data(driver1, corner_number)
            driver2_data = self._get_driver_corner_data(driver2, corner_number)
            
            if not driver1_data or not driver2_data:
                print(f"[ERROR] 無法獲取車手數據")
                return False
            
            # 獲取進站資訊
            driver1_pitstops = self.get_pitstop_info_for_driver(driver1) if pitstop_loaded else []
            driver2_pitstops = self.get_pitstop_info_for_driver(driver2) if pitstop_loaded else []
            
            # 生成對比分析表格
            self._display_comparison_analysis_table(
                driver1, driver2, corner_number, 
                driver1_data, driver2_data,
                driver1_pitstops, driver2_pitstops,
                incident_loaded
            )
            
            # 生成JSON輸出
            json_output = self._generate_comparison_json_output(
                driver1, driver2, corner_number,
                driver1_data, driver2_data,
                driver1_pitstops, driver2_pitstops,
                incident_loaded
            )
            
            # 保存JSON文件
            # 確保json資料夾存在
            import os
            json_dir = "json"
            os.makedirs(json_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(json_dir, f"team_drivers_corner_comparison_integrated_{driver1}_vs_{driver2}_T{corner_number}_{timestamp}.json")
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(json_output, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"\n[SUCCESS] 對比分析完成！JSON輸出已保存到: {filename}")
            return True
            
        except Exception as e:
            print(f"[ERROR] 彎道對比分析過程中發生錯誤: {e}")
            traceback.print_exc()
            return False
    
    def _get_driver_corner_data(self, driver, corner_number):
        """獲取車手的彎道數據"""
        try:
            # 獲取車手的遙測數據
            driver_laps = self.data_loader.laps[self.data_loader.laps['Driver'] == driver]
            
            corner_data = []
            for _, lap in driver_laps.iterrows():
                try:
                    lap_telemetry = lap.get_telemetry()
                    if lap_telemetry is not None and not lap_telemetry.empty:
                        # 簡化的彎道位置計算
                        total_distance = lap_telemetry['Distance'].max()
                        corner_start = (corner_number - 1) * (total_distance / 10)
                        corner_end = corner_start + (total_distance / 20)
                        
                        corner_telemetry = lap_telemetry[
                            (lap_telemetry['Distance'] >= corner_start) & 
                            (lap_telemetry['Distance'] <= corner_end)
                        ]
                        
                        if not corner_telemetry.empty:
                            avg_speed = corner_telemetry['Speed'].mean()
                            min_speed = corner_telemetry['Speed'].min()
                            max_speed = corner_telemetry['Speed'].max()
                            
                            corner_data.append({
                                'lap_number': lap['LapNumber'],
                                'lap_time': lap['LapTime'].total_seconds() if pd.notna(lap['LapTime']) else None,
                                'avg_speed': avg_speed,
                                'min_speed': min_speed,
                                'max_speed': max_speed,
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
            print(f"[WARNING] 獲取車手 {driver} 彎道數據時發生錯誤: {e}")
            return []
    
    def _display_comparison_analysis_table(self, driver1, driver2, corner_number, 
                                         driver1_data, driver2_data,
                                         driver1_pitstops, driver2_pitstops,
                                         incident_loaded):
        """顯示車手對比分析表格 - 包含進站與事件資訊"""
        print(f"\n[LIST] {driver1} vs {driver2} - T{corner_number} 彎道詳細對比表格")
        print("----------------------------------------------------------------------------------------------------")
        
        # 創建進站圈數字典
        driver1_pitstop_laps = {p['lap_number']: p for p in driver1_pitstops} if driver1_pitstops else {}
        driver2_pitstop_laps = {p['lap_number']: p for p in driver2_pitstops} if driver2_pitstops else {}
        
        # 創建對比表格 - 添加異常檢測欄位
        comparison_table = PrettyTable()
        comparison_table.field_names = [
            "圈數", "圈速", "彎中心速度", "進彎前最高速度", "彎中心速差", "最高速差", f"{driver1}輪胎", f"{driver2}輪胎", "進站資訊", "異常標註"
        ]
        comparison_table.align = "c"
        
        # 獲取遙測數據
        session = self.data_loader.session
        driver1_laps = session.laps.pick_drivers(driver1)
        driver2_laps = session.laps.pick_drivers(driver2)
        
        # 顯示前20圈的對比分析
        max_laps = min(20, len(driver1_laps), len(driver2_laps))
        
        # 先收集所有資料用於異常檢測
        all_lap_data = []
        all_lap_times = []
        all_corner_speeds = []
        all_entry_speeds = []
        
        for lap_idx in range(max_laps):
            lap_num = lap_idx + 1
            try:
                # 直接從FastF1遙測數據獲取信息
                d1_lap = driver1_laps.iloc[lap_idx] if lap_idx < len(driver1_laps) else None
                d2_lap = driver2_laps.iloc[lap_idx] if lap_idx < len(driver2_laps) else None
                
                # 圈速
                d1_time = None
                d2_time = None
                if d1_lap is not None and pd.notna(d1_lap['LapTime']):
                    d1_time = d1_lap['LapTime'].total_seconds()
                if d2_lap is not None and pd.notna(d2_lap['LapTime']):
                    d2_time = d2_lap['LapTime'].total_seconds()
                
                # 彎道速度分析
                d1_corner_speed = self._get_corner_speed_for_lap(d1_lap, corner_number) if d1_lap is not None else None
                d2_corner_speed = self._get_corner_speed_for_lap(d2_lap, corner_number) if d2_lap is not None else None
                
                d1_entry_speed, _ = self._get_corner_entry_max_speed_for_lap(d1_lap, corner_number) if d1_lap is not None else (None, None)
                d2_entry_speed, _ = self._get_corner_entry_max_speed_for_lap(d2_lap, corner_number) if d2_lap is not None else (None, None)
                
                # 收集資料
                lap_data = {
                    'lap_num': lap_num,
                    'd1_time': d1_time,
                    'd2_time': d2_time,
                    'd1_corner_speed': d1_corner_speed,
                    'd2_corner_speed': d2_corner_speed,
                    'd1_entry_speed': d1_entry_speed,
                    'd2_entry_speed': d2_entry_speed,
                    'd1_lap': d1_lap,
                    'd2_lap': d2_lap
                }
                all_lap_data.append(lap_data)
                
                # 收集有效數值用於統計分析
                if d1_time: all_lap_times.append(d1_time)
                if d2_time: all_lap_times.append(d2_time)
                if d1_corner_speed: all_corner_speeds.append(d1_corner_speed)
                if d2_corner_speed: all_corner_speeds.append(d2_corner_speed)
                if d1_entry_speed: all_entry_speeds.append(d1_entry_speed)
                if d2_entry_speed: all_entry_speeds.append(d2_entry_speed)
                
            except Exception as e:
                print(f"[WARNING] 收集第{lap_num}圈資料時出錯: {e}")
        
        # 計算異常檢測閾值
        lap_time_mean = np.mean(all_lap_times) if all_lap_times else 0
        lap_time_std = np.std(all_lap_times) if all_lap_times else 0
        lap_time_threshold = lap_time_std * 1.5
        
        corner_speed_mean = np.mean(all_corner_speeds) if all_corner_speeds else 0
        corner_speed_std = np.std(all_corner_speeds) if all_corner_speeds else 0
        corner_speed_threshold = corner_speed_std * 1.5
        
        entry_speed_mean = np.mean(all_entry_speeds) if all_entry_speeds else 0
        entry_speed_std = np.std(all_entry_speeds) if all_entry_speeds else 0
        entry_speed_threshold = entry_speed_std * 1.5
        
        # 處理表格資料並添加異常檢測
        for lap_data in all_lap_data:
            lap_num = lap_data['lap_num']
            d1_time = lap_data['d1_time']
            d2_time = lap_data['d2_time']
            d1_corner_speed = lap_data['d1_corner_speed']
            d2_corner_speed = lap_data['d2_corner_speed']
            d1_entry_speed = lap_data['d1_entry_speed']
            d2_entry_speed = lap_data['d2_entry_speed']
            d1_lap = lap_data['d1_lap']
            d2_lap = lap_data['d2_lap']
            
            try:
                # 圈速
                if d1_time and d2_time:
                    faster_time = min(d1_time, d2_time)
                    lap_time_str = f"{faster_time:.3f}s"
                else:
                    lap_time_str = "N/A"
                
                # 彎道速度分析 - 使用遙測數據
                # (d1_corner_speed 和 d2_corner_speed 已在前面收集)
                
                # 格式化彎道速度
                if d1_corner_speed and d2_corner_speed:
                    corner_speeds_str = f"{d1_corner_speed:.1f}/{d2_corner_speed:.1f}"
                    corner_speed_diff = d2_corner_speed - d1_corner_speed
                    corner_diff_str = f"{corner_speed_diff:+.1f}"
                else:
                    corner_speeds_str = "N/A"
                    corner_diff_str = "N/A"
                
                # 格式化進彎前最高速度
                if d1_entry_speed and d2_entry_speed:
                    entry_speeds_str = f"{d1_entry_speed:.1f}/{d2_entry_speed:.1f}"
                    entry_speed_diff = d2_entry_speed - d1_entry_speed
                    entry_diff_str = f"{entry_speed_diff:+.1f}"
                else:
                    entry_speeds_str = "N/A"
                    entry_diff_str = "N/A"
                
                # 輪胎資訊 - 分別顯示
                d1_tire = d1_lap['Compound'] if d1_lap is not None and 'Compound' in d1_lap else "Unknown"
                d2_tire = d2_lap['Compound'] if d2_lap is not None and 'Compound' in d2_lap else "Unknown"
                
                # 進站資訊
                d1_pitstop = "[SUCCESS]" if lap_num in driver1_pitstop_laps else ""
                d2_pitstop = "[SUCCESS]" if lap_num in driver2_pitstop_laps else ""
                pit_str = f"{d1_pitstop}/{d2_pitstop}" if d1_pitstop or d2_pitstop else ""
                
                # 異常檢測
                anomaly_flags = []
                
                # 檢查圈速異常
                if d1_time and lap_time_threshold > 0 and abs(d1_time - lap_time_mean) > lap_time_threshold:
                    if d1_time > lap_time_mean:
                        anomaly_flags.append(f"{driver1}圈速慢")
                
                if d2_time and lap_time_threshold > 0 and abs(d2_time - lap_time_mean) > lap_time_threshold:
                    if d2_time > lap_time_mean:
                        anomaly_flags.append(f"{driver2}圈速慢")
                
                # 檢查彎中心速度異常
                if d1_corner_speed and corner_speed_threshold > 0 and abs(d1_corner_speed - corner_speed_mean) > corner_speed_threshold:
                    if d1_corner_speed < corner_speed_mean:
                        anomaly_flags.append(f"{driver1}彎速慢")
                    else:
                        anomaly_flags.append(f"{driver1}彎速快")
                
                if d2_corner_speed and corner_speed_threshold > 0 and abs(d2_corner_speed - corner_speed_mean) > corner_speed_threshold:
                    if d2_corner_speed < corner_speed_mean:
                        anomaly_flags.append(f"{driver2}彎速慢")
                    else:
                        anomaly_flags.append(f"{driver2}彎速快")
                
                # 檢查進彎速度異常
                if d1_entry_speed and entry_speed_threshold > 0 and abs(d1_entry_speed - entry_speed_mean) > entry_speed_threshold:
                    if d1_entry_speed < entry_speed_mean:
                        anomaly_flags.append(f"{driver1}進彎慢")
                    else:
                        anomaly_flags.append(f"{driver1}進彎快")
                
                if d2_entry_speed and entry_speed_threshold > 0 and abs(d2_entry_speed - entry_speed_mean) > entry_speed_threshold:
                    if d2_entry_speed < entry_speed_mean:
                        anomaly_flags.append(f"{driver2}進彎慢")
                    else:
                        anomaly_flags.append(f"{driver2}進彎快")
                
                # 合併異常標註
                anomaly_str = " | ".join(anomaly_flags) if anomaly_flags else "[SUCCESS]"
                
                comparison_table.add_row([
                    f"L{lap_num}",
                    lap_time_str,
                    corner_speeds_str,
                    entry_speeds_str,
                    corner_diff_str,
                    entry_diff_str,
                    d1_tire,
                    d2_tire,
                    pit_str,
                    anomaly_str
                ])
                
            except Exception as e:
                print(f"[WARNING] 處理第{lap_num}圈時出錯: {e}")
                comparison_table.add_row([
                    f"L{lap_num}",
                    "Error",
                    "Error",
                    "Error",
                    "Error",
                    "Error",
                    "Error",
                    "Error",
                    "Error",
                    "Error"
                ])
        
        print(comparison_table)
        
        # 顯示異常檢測統計
        print(f"\n[INFO] 異常檢測閾值:")
        print(f"   圈速: ±{lap_time_threshold:.3f}s")
        print(f"   彎中心速度: ±{corner_speed_threshold:.1f} km/h")
        print(f"   進彎前速度: ±{entry_speed_threshold:.1f} km/h")
        
        # 對比統計摘要
        self._display_enhanced_comparison_statistics(driver1, driver2, corner_number, session)

    def _get_corner_speed_for_lap(self, lap, corner_number):
        """獲取特定圈的彎道速度（彎中心速度）"""
        try:
            telemetry = lap.get_telemetry()
            if telemetry.empty:
                return None
            
            speed = telemetry['Speed']
            distance = telemetry['Distance']
            
            # 簡化的彎道檢測
            corner_start_distance = (corner_number - 1) * 500
            corner_end_distance = corner_number * 500
            
            if distance.empty:
                return speed.min()
            
            corner_mask = (distance >= corner_start_distance) & (distance <= corner_end_distance)
            corner_speeds = speed[corner_mask]
            
            if corner_speeds.empty:
                return speed.min()
            
            return corner_speeds.min()  # 彎中心速度（最低速度）
            
        except Exception:
            return None

    def _get_corner_entry_max_speed_for_lap(self, lap, corner_number):
        """獲取特定圈的進彎前最高速度"""
        try:
            telemetry = lap.get_telemetry()
            if telemetry.empty:
                return None, None
            
            speed = telemetry['Speed']
            distance = telemetry['Distance']
            
            # 簡化的彎道檢測
            corner_distance = corner_number * 500
            entry_start_distance = corner_distance - 200  # 彎道前200米
            entry_end_distance = corner_distance
            
            if distance.empty:
                return speed.max(), 100  # 預設距離
            
            entry_mask = (distance >= entry_start_distance) & (distance < entry_end_distance)
            entry_speeds = speed[entry_mask]
            entry_distances = distance[entry_mask]
            
            if entry_speeds.empty:
                return speed.max(), 100  # 預設距離
            
            max_speed_idx = entry_speeds.idxmax()
            max_speed = entry_speeds[max_speed_idx]
            distance_to_corner = corner_distance - entry_distances[max_speed_idx]
            
            return max_speed, abs(distance_to_corner)
            
        except Exception:
            return None, None

    def _display_enhanced_comparison_statistics(self, driver1, driver2, corner_number, session):
        """顯示增強的對比統計數據"""
        try:
            print(f"\n[INFO] {driver1} vs {driver2} 統計摘要:")
            
            driver1_laps = session.laps.pick_drivers(driver1)
            driver2_laps = session.laps.pick_drivers(driver2)
            max_laps = min(len(driver1_laps), len(driver2_laps))
            
            d1_corner_speeds = []
            d2_corner_speeds = []
            d1_entry_speeds = []
            d2_entry_speeds = []
            
            for lap_idx in range(max_laps):
                try:
                    d1_lap = driver1_laps.iloc[lap_idx]
                    d2_lap = driver2_laps.iloc[lap_idx]
                    
                    d1_corner = self._get_corner_speed_for_lap(d1_lap, corner_number)
                    d2_corner = self._get_corner_speed_for_lap(d2_lap, corner_number)
                    d1_entry, _ = self._get_corner_entry_max_speed_for_lap(d1_lap, corner_number)
                    d2_entry, _ = self._get_corner_entry_max_speed_for_lap(d2_lap, corner_number)
                    
                    if d1_corner: d1_corner_speeds.append(d1_corner)
                    if d2_corner: d2_corner_speeds.append(d2_corner)
                    if d1_entry: d1_entry_speeds.append(d1_entry)
                    if d2_entry: d2_entry_speeds.append(d2_entry)
                    
                except Exception:
                    continue
            
            if d1_corner_speeds and d2_corner_speeds:
                avg_corner_diff = np.mean(d2_corner_speeds) - np.mean(d1_corner_speeds)
                print(f"   彎中心速度差平均: {avg_corner_diff:+.1f} km/h ({driver2 if avg_corner_diff > 0 else driver1} 較快)")
            
            if d1_entry_speeds and d2_entry_speeds:
                avg_entry_diff = np.mean(d2_entry_speeds) - np.mean(d1_entry_speeds)
                print(f"   進彎前最高速度差平均: {avg_entry_diff:+.1f} km/h ({driver2 if avg_entry_diff > 0 else driver1} 較快)")
            
        except Exception as e:
            print(f"[WARNING] 統計計算失敗: {e}")
        
        print(f"\n[INFO] 進站統計已整合至表格中顯示")
    
    def _generate_comparison_json_output(self, driver1, driver2, corner_number,
                                       driver1_data, driver2_data,
                                       driver1_pitstops, driver2_pitstops,
                                       incident_loaded):
        """生成對比分析JSON輸出"""
        # 獲取事件資訊
        incidents = []
        if incident_loaded:
            total_laps = max(len(driver1_data), len(driver2_data))
            incidents = self.get_incident_info_for_lap_range(1, total_laps)
        
        output = {
            "analysis_info": {
                "function_id": "12.2_integrated",
                "analysis_type": "team_drivers_corner_comparison_with_pitstops_and_incidents",
                "drivers": [driver1, driver2],
                "corner_number": corner_number,
                "timestamp": datetime.now().isoformat()
            },
            "comparison_summary": {
                f"{driver1}_stats": {
                    "total_laps": len(driver1_data),
                    "pitstop_count": len(driver1_pitstops),
                    "average_corner_speed": np.mean([d['avg_speed'] for d in driver1_data if d['avg_speed']]) if driver1_data else 0
                },
                f"{driver2}_stats": {
                    "total_laps": len(driver2_data),
                    "pitstop_count": len(driver2_pitstops),
                    "average_corner_speed": np.mean([d['avg_speed'] for d in driver2_data if d['avg_speed']]) if driver2_data else 0
                },
                "incident_summary": {
                    "total_incidents": len(incidents),
                    "incident_types": list(set([inc['type'] for inc in incidents]))
                }
            },
            "detailed_comparison_data": {
                f"{driver1}_data": driver1_data,
                f"{driver2}_data": driver2_data
            },
            "pitstop_details": {
                f"{driver1}_pitstops": driver1_pitstops,
                f"{driver2}_pitstops": driver2_pitstops
            },
            "incident_details": incidents
        }
        
        return output


def run_team_drivers_corner_comparison_integrated(data_loader, f1_analysis_instance=None):
    """
    執行團隊車手彎道對比分析 - 集成進站與事件版 (功能 12.2)
    支援用戶選擇車手和彎道，整合進站資料與特殊事件報告
    """
    try:
        analyzer = TeamDriversCornerComparisonIntegrated(data_loader)
        
        # 檢查是否為參數模式（自動模式）
        # 如果有設定f1_analysis_instance，表示是從主程序調用，使用自動模式
        if f1_analysis_instance is not None:
            return analyzer.analyze_team_drivers_corner_comparison(driver1="VER", driver2="NOR", corner_number=1, auto_mode=True)
        else:
            return analyzer.analyze_team_drivers_corner_comparison(driver1="VER", driver2="NOR", corner_number=None, auto_mode=False)
    except Exception as e:
        print(f"[ERROR] 執行團隊車手彎道對比分析(集成版)失敗: {e}")
        return False


def main():
    """主函數"""
    print("🆚 團隊車手彎道對比分析 - 集成進站與事件版")
    print("="*60)
    
    # 參數設置
    driver1 = "VER"
    driver2 = "NOR"
    corner_number = 1
    
    if len(sys.argv) > 1:
        driver1 = sys.argv[1]
    if len(sys.argv) > 2:
        driver2 = sys.argv[2]
    if len(sys.argv) > 3:
        corner_number = int(sys.argv[3])
    
    print(f"📅 分析設定: {driver1} vs {driver2}, 彎道 T{corner_number}")
    print(f"[TIP] 功能特色: 整合進站資料與特殊事件報告")
    
    # 需要data_loader，這裡示例用法
    # analyzer = TeamDriversCornerComparisonIntegrated(data_loader)
    # result = analyzer.analyze_team_drivers_corner_comparison(driver1, driver2, corner_number)
    
    print("[WARNING] 此模組需要配合 f1_analysis_modular_main.py 使用")
    print("請執行: python f1_analysis_modular_main.py -f 12.2")


if __name__ == "__main__":
    main()
