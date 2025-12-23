# -*- coding: utf-8 -*-
"""
速度差距分析子模組 - 7.1
從 driver_comparison_advanced.py 拆分出來的速度差距分析功能

版本: 拆分獨立版 v1.0
基於: driver_comparison_advanced.py 的速度差距分析功能
"""

import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

import os
import traceback
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from prettytable import PrettyTable
from scipy.interpolate import interp1d
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D

# 添加父目錄到path以便導入base模組
sys.path.append(str(Path(__file__).parent.parent))

from modules.base import F1AnalysisBase

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')


class SpeedGapAnalyzer(F1AnalysisBase):
    """速度差距分析器 - 專門分析兩車手之間的速度差距"""
    
    def __init__(self, data_loader, f1_analysis_instance=None):
        super().__init__()
        self.data_loader = data_loader
        self.f1_analysis_instance = f1_analysis_instance
        self.selected_drivers = []
        self.selected_laps = []
        
    def run_speed_gap_analysis(self):
        """執行速度差距分析"""
        print(f"\n🏎️ 速度差距分析")
        print("=" * 80)
        
        try:
            data = self.data_loader.get_loaded_data()
            session = data['session']
            laps = data['laps']
            drivers_info = data['drivers_info']

            # 車手選擇
            if not self._select_drivers(drivers_info):
                return
                
            # 圈次選擇
            if not self._select_laps(laps):
                return
                
            # 執行速度差距分析
            self._analyze_speed_gap(session, laps)
            
        except Exception as e:
            print(f"[ERROR] 速度差距分析失敗: {e}")
            traceback.print_exc()
    
    def _select_drivers(self, drivers_info):
        """選擇兩個車手進行比較"""
        available_drivers = list(drivers_info.keys())
        print("[LIST] 可用車手:")
        
        # 使用 PrettyTable 顯示可用車手
        driver_table = PrettyTable()
        driver_table.field_names = ["編號", "代號", "車手姓名", "車隊"]
        driver_table.align = "l"
        
        driver_list = []
        for idx, (abbr, info) in enumerate(drivers_info.items(), 1):
            driver_table.add_row([
                idx,
                abbr,
                info.get('name', 'N/A'),
                info.get('team', 'N/A')
            ])
            driver_list.append(abbr)
        
        print(driver_table)
        
        # 選擇第一個車手
        while True:
            try:
                choice1 = input(f"\n請選擇第一個車手 (1-{len(driver_list)}): ").strip()
                idx1 = int(choice1) - 1
                if 0 <= idx1 < len(driver_list):
                    driver1 = driver_list[idx1]
                    break
                else:
                    print(f"[ERROR] 請輸入 1 到 {len(driver_list)} 之間的數字")
            except ValueError:
                print("[ERROR] 請輸入有效的數字")
        
        # 選擇第二個車手
        while True:
            try:
                choice2 = input(f"請選擇第二個車手 (1-{len(driver_list)}): ").strip()
                idx2 = int(choice2) - 1
                if 0 <= idx2 < len(driver_list):
                    driver2 = driver_list[idx2]
                    break
                else:
                    print(f"[ERROR] 請輸入 1 到 {len(driver_list)} 之間的數字")
            except ValueError:
                print("[ERROR] 請輸入有效的數字")
        
        self.selected_drivers = [driver1, driver2]
        print(f"[SUCCESS] 已選擇車手: {driver1} vs {driver2}")
        return True
    
    def _select_laps(self, laps):
        """選擇要比較的圈次"""
        print(f"\n[INFO] 圈次選擇")
        
        for i, driver in enumerate(self.selected_drivers, 1):
            print(f"\n車手 {driver} 的圈次選擇:")
            driver_laps = laps[laps['Driver'] == driver]
            
            if driver_laps.empty:
                print(f"[ERROR] 車手 {driver} 沒有圈次數據")
                return False
            
            # 顯示可用圈次
            valid_laps = driver_laps[driver_laps['LapTime'].notna()]
            if valid_laps.empty:
                print(f"[ERROR] 車手 {driver} 沒有有效的圈時數據")
                return False
            
            print(f"可用圈次: {sorted([int(lap) for lap in valid_laps['LapNumber'].tolist()])}")
            
            # 顯示最快圈建議
            fastest_lap = valid_laps.loc[valid_laps['LapTime'].idxmin()]
            fastest_lap_num = int(fastest_lap['LapNumber'])
            fastest_time = fastest_lap['LapTime']
            
            # 格式化最快圈時間 (MM:SS.sss)
            if pd.notna(fastest_time):
                total_seconds = fastest_time.total_seconds()
                minutes = int(total_seconds // 60)
                seconds = total_seconds % 60
                time_str = f"{minutes}:{seconds:06.3f}"
            else:
                time_str = "N/A"
            
            print(f"[TIP] 建議選擇最快圈: 第{fastest_lap_num}圈 ({time_str})")
            
            # 用戶選擇
            while True:
                try:
                    choice = input(f"請選擇車手{driver}的圈次 (直接按Enter選擇最快圈): ").strip()
                    if not choice:
                        selected_lap = fastest_lap_num
                    else:
                        selected_lap = int(choice)
                    
                    if selected_lap in valid_laps['LapNumber'].tolist():
                        self.selected_laps.append(selected_lap)
                        lap_time = valid_laps[valid_laps['LapNumber'] == selected_lap]['LapTime'].iloc[0]
                        
                        # 格式化選中圈次的時間
                        if pd.notna(lap_time):
                            total_seconds = lap_time.total_seconds()
                            minutes = int(total_seconds // 60)
                            seconds = total_seconds % 60
                            time_str = f"{minutes}:{seconds:06.3f}"
                        else:
                            time_str = "N/A"
                        
                        print(f"[SUCCESS] 已選擇車手{driver}的第{selected_lap}圈 ({time_str})")
                        break
                    else:
                        print(f"[ERROR] 圈次{selected_lap}不存在，請重新選擇")
                except ValueError:
                    print("[ERROR] 請輸入有效的圈次號碼")
        
        return True
    
    def _analyze_speed_gap(self, session, laps):
        """分析速度差距 - 輸出包含坐標的原始數據"""
        print(f"\n[DEBUG] 速度差距分析中...")
        
        try:
            # 獲取兩個車手的圈次數據
            driver1, driver2 = self.selected_drivers
            lap1_num, lap2_num = self.selected_laps
            
            # 獲取遙測數據
            lap1_data = session.laps.pick_driver(driver1).pick_lap(lap1_num)
            lap2_data = session.laps.pick_driver(driver2).pick_lap(lap2_num)
            
            if lap1_data.empty or lap2_data.empty:
                print("[ERROR] 無法獲取圈次數據")
                return
            
            # 獲取遙測數據
            try:
                telemetry1 = lap1_data.iloc[0].get_car_data().add_distance()
                telemetry2 = lap2_data.iloc[0].get_car_data().add_distance()
            except:
                try:
                    telemetry1 = lap1_data.iloc[0].get_telemetry().add_distance()
                    telemetry2 = lap2_data.iloc[0].get_telemetry().add_distance()
                except Exception as e:
                    print(f"[ERROR] 無法獲取遙測數據: {e}")
                    return
            
            if telemetry1.empty or telemetry2.empty:
                print("[ERROR] 遙測數據為空")
                return
            
            # 檢查遙測數據可用的欄位
            print(f"[DEBUG] 車手 {driver1} 遙測數據欄位: {list(telemetry1.columns)}")
            print(f"[DEBUG] 車手 {driver2} 遙測數據欄位: {list(telemetry2.columns)}")
            
            # 檢查基本必要欄位
            basic_required_cols = ['Distance', 'Speed']
            missing_basic1 = [col for col in basic_required_cols if col not in telemetry1.columns]
            missing_basic2 = [col for col in basic_required_cols if col not in telemetry2.columns]
            
            if missing_basic1:
                print(f"[ERROR] 車手{driver1}遙測數據缺少基本必要欄位: {missing_basic1}")
                return
            if missing_basic2:
                print(f"[ERROR] 車手{driver2}遙測數據缺少基本必要欄位: {missing_basic2}")
                return
            
            # 嘗試獲取坐標數據 - 檢查多種可能的欄位名稱
            x_col_names = ['X', 'x', 'PosX', 'PositionX']
            y_col_names = ['Y', 'y', 'PosY', 'PositionY']
            
            x_col1 = x_col2 = y_col1 = y_col2 = None
            
            # 為車手1找到坐標欄位
            for col in x_col_names:
                if col in telemetry1.columns:
                    x_col1 = col
                    break
            for col in y_col_names:
                if col in telemetry1.columns:
                    y_col1 = col
                    break
                    
            # 為車手2找到坐標欄位
            for col in x_col_names:
                if col in telemetry2.columns:
                    x_col2 = col
                    break
            for col in y_col_names:
                if col in telemetry2.columns:
                    y_col2 = col
                    break
            
            # 檢查是否找到坐標欄位
            if not (x_col1 and y_col1):
                print(f"[WARNING] 車手{driver1}沒有找到坐標欄位，將使用距離作為位置參考")
                x_col1 = y_col1 = None
            if not (x_col2 and y_col2):
                print(f"[WARNING] 車手{driver2}沒有找到坐標欄位，將使用距離作為位置參考")
                x_col2 = y_col2 = None
            
            # 獲取最短距離範圍
            min_distance = max(telemetry1['Distance'].min(), telemetry2['Distance'].min())
            max_distance = min(telemetry1['Distance'].max(), telemetry2['Distance'].max())
            
            if min_distance >= max_distance:
                print("[ERROR] 兩車手的距離數據沒有重疊範圍")
                return
            
            # 創建統一的距離網格 - 使用更高密度
            distance_grid = np.linspace(min_distance, max_distance, 2000)
            
            # 插值所有數據
            try:
                # 速度插值
                speed1_interp = interp1d(telemetry1['Distance'], telemetry1['Speed'], 
                                       kind='linear', fill_value='extrapolate')
                speed2_interp = interp1d(telemetry2['Distance'], telemetry2['Speed'], 
                                       kind='linear', fill_value='extrapolate')
                
                # 計算插值速度數據
                speed1_grid = speed1_interp(distance_grid)
                speed2_grid = speed2_interp(distance_grid)
                
                # 坐標插值 - 只有在有坐標數據時才進行
                x1_grid = y1_grid = x2_grid = y2_grid = None
                
                if x_col1 and y_col1:
                    x1_interp = interp1d(telemetry1['Distance'], telemetry1[x_col1], 
                                       kind='linear', fill_value='extrapolate')
                    y1_interp = interp1d(telemetry1['Distance'], telemetry1[y_col1], 
                                       kind='linear', fill_value='extrapolate')
                    x1_grid = x1_interp(distance_grid)
                    y1_grid = y1_interp(distance_grid)
                
                if x_col2 and y_col2:
                    x2_interp = interp1d(telemetry2['Distance'], telemetry2[x_col2], 
                                       kind='linear', fill_value='extrapolate')
                    y2_interp = interp1d(telemetry2['Distance'], telemetry2[y_col2], 
                                       kind='linear', fill_value='extrapolate')
                    x2_grid = x2_interp(distance_grid)
                    y2_grid = y2_interp(distance_grid)
                
                # 計算速度差距
                speed_gap = speed1_grid - speed2_grid
                
                # 輸出原始數據
                self._display_raw_speed_gap_data(distance_grid, speed1_grid, speed2_grid, speed_gap,
                                               x1_grid, y1_grid, x2_grid, y2_grid, driver1, driver2, 
                                               lap1_num, lap2_num)
                
            except Exception as e:
                print(f"[ERROR] 插值計算失敗: {e}")
                return
            
        except Exception as e:
            print(f"[ERROR] 速度差距分析失敗: {e}")
            traceback.print_exc()
    
    def _display_raw_speed_gap_data(self, distance_grid, speed1_grid, speed2_grid, speed_gap,
                                  x1_grid, y1_grid, x2_grid, y2_grid, driver1, driver2, 
                                  lap1_num, lap2_num):
        """顯示包含坐標的原始速度差距數據"""
        print(f"\n🏎️ 速度差距原始數據分析")
        print("=" * 100)
        print(f"比較對象: {driver1} (第{lap1_num}圈) vs {driver2} (第{lap2_num}圈)")
        print("=" * 100)
        
        # 統計摘要
        print(f"\n[INFO] 數據統計摘要:")
        summary_table = PrettyTable()
        summary_table.field_names = ["項目", f"{driver1}", f"{driver2}", "差距 ({driver1}-{driver2})"]
        summary_table.align = "r"
        
        # 平均速度
        avg_speed1 = np.mean(speed1_grid)
        avg_speed2 = np.mean(speed2_grid)
        avg_gap = avg_speed1 - avg_speed2
        summary_table.add_row([
            "平均速度 (km/h)", 
            f"{avg_speed1:.1f}", 
            f"{avg_speed2:.1f}", 
            f"{avg_gap:+.1f}"
        ])
        
        # 最高速度
        max_speed1 = np.max(speed1_grid)
        max_speed2 = np.max(speed2_grid)
        max_gap = max_speed1 - max_speed2
        summary_table.add_row([
            "最高速度 (km/h)", 
            f"{max_speed1:.1f}", 
            f"{max_speed2:.1f}", 
            f"{max_gap:+.1f}"
        ])
        
        # 最低速度
        min_speed1 = np.min(speed1_grid)
        min_speed2 = np.min(speed2_grid)
        min_gap = min_speed1 - min_speed2
        summary_table.add_row([
            "最低速度 (km/h)", 
            f"{min_speed1:.1f}", 
            f"{min_speed2:.1f}", 
            f"{min_gap:+.1f}"
        ])
        
        print(summary_table)
        
        # 速度差距統計
        max_advantage = np.max(speed_gap)
        max_disadvantage = np.min(speed_gap)
        avg_speed_gap = np.mean(speed_gap)
        std_speed_gap = np.std(speed_gap)
        
        print(f"\n[DEBUG] 速度差距統計分析:")
        gap_stats_table = PrettyTable()
        gap_stats_table.field_names = ["統計項目", "數值", "位置 (距離m)"]
        gap_stats_table.align["統計項目"] = "l"
        gap_stats_table.align["數值"] = "r"
        gap_stats_table.align["位置 (距離m)"] = "r"
        
        max_adv_idx = np.argmax(speed_gap)
        max_dis_idx = np.argmin(speed_gap)
        
        gap_stats_table.add_row([
            f"{driver1} 最大優勢", 
            f"+{max_advantage:.1f} km/h",
            f"{distance_grid[max_adv_idx]:.0f}m"
        ])
        gap_stats_table.add_row([
            f"{driver1} 最大劣勢", 
            f"{max_disadvantage:.1f} km/h",
            f"{distance_grid[max_dis_idx]:.0f}m"
        ])
        gap_stats_table.add_row([
            "平均速度差距", 
            f"{avg_speed_gap:+.1f} km/h",
            "全程"
        ])
        gap_stats_table.add_row([
            "速度差距變動", 
            f"±{std_speed_gap:.1f} km/h",
            "標準差"
        ])
        
        print(gap_stats_table)
        
        # 原始數據表格 - 顯示關鍵點位
        print(f"\n[LIST] 原始數據詳細表格 (每100m取樣):")
        
        # 根據是否有坐標數據決定表格結構
        if x1_grid is not None and y1_grid is not None and x2_grid is not None and y2_grid is not None:
            data_table = PrettyTable()
            data_table.field_names = [
                "距離(m)", 
                f"{driver1}_X(m)", f"{driver1}_Y(m)", f"{driver1}_速度(km/h)",
                f"{driver2}_X(m)", f"{driver2}_Y(m)", f"{driver2}_速度(km/h)",
                "速度差距(km/h)"
            ]
            data_table.align = "r"
            
            # 每100m取一個樣本點，最多顯示30行
            step = max(1, len(distance_grid) // 30)
            sample_indices = np.arange(0, len(distance_grid), step)
            
            for i in sample_indices[:30]:  # 限制最多30行
                data_table.add_row([
                    f"{distance_grid[i]:.0f}",
                    f"{x1_grid[i]:.1f}",
                    f"{y1_grid[i]:.1f}",
                    f"{speed1_grid[i]:.1f}",
                    f"{x2_grid[i]:.1f}",
                    f"{y2_grid[i]:.1f}",
                    f"{speed2_grid[i]:.1f}",
                    f"{speed_gap[i]:+.1f}"
                ])
        else:
            # 沒有坐標數據時的簡化表格
            data_table = PrettyTable()
            data_table.field_names = [
                "距離(m)", 
                f"{driver1}_速度(km/h)",
                f"{driver2}_速度(km/h)",
                "速度差距(km/h)"
            ]
            data_table.align = "r"
            
            # 每100m取一個樣本點，最多顯示30行
            step = max(1, len(distance_grid) // 30)
            sample_indices = np.arange(0, len(distance_grid), step)
            
            for i in sample_indices[:30]:  # 限制最多30行
                data_table.add_row([
                    f"{distance_grid[i]:.0f}",
                    f"{speed1_grid[i]:.1f}",
                    f"{speed2_grid[i]:.1f}",
                    f"{speed_gap[i]:+.1f}"
                ])
        
        print(data_table)
        
        # 完整數據導出提示
        print(f"\n💾 完整原始數據:")
        print(f"   • 總數據點: {len(distance_grid)} 個")
        print(f"   • 數據密度: {(distance_grid[-1] - distance_grid[0]) / len(distance_grid):.1f}m 每點")
        print(f"   • 分析範圍: {distance_grid[0]:.0f}m - {distance_grid[-1]:.0f}m")
        
        # 關鍵位置分析
        print(f"\n[TARGET] 關鍵位置分析:")
        
        # 根據是否有坐標數據決定表格結構
        if x1_grid is not None and y1_grid is not None and x2_grid is not None and y2_grid is not None:
            key_points_table = PrettyTable()
            key_points_table.field_names = ["位置類型", "距離(m)", "X坐標(m)", "Y坐標(m)", f"{driver1}速度", f"{driver2}速度", "速度差距"]
            key_points_table.align = "r"
            
            # 最大優勢位置
            key_points_table.add_row([
                f"{driver1}最大優勢點",
                f"{distance_grid[max_adv_idx]:.0f}",
                f"{x1_grid[max_adv_idx]:.1f}",
                f"{y1_grid[max_adv_idx]:.1f}",
                f"{speed1_grid[max_adv_idx]:.1f}",
                f"{speed2_grid[max_adv_idx]:.1f}",
                f"+{max_advantage:.1f}"
            ])
            
            # 最大劣勢位置
            key_points_table.add_row([
                f"{driver1}最大劣勢點",
                f"{distance_grid[max_dis_idx]:.0f}",
                f"{x1_grid[max_dis_idx]:.1f}",
                f"{y1_grid[max_dis_idx]:.1f}",
                f"{speed1_grid[max_dis_idx]:.1f}",
                f"{speed2_grid[max_dis_idx]:.1f}",
                f"{max_disadvantage:.1f}"
            ])
            
            # 起始點
            key_points_table.add_row([
                "起始點",
                f"{distance_grid[0]:.0f}",
                f"{x1_grid[0]:.1f}",
                f"{y1_grid[0]:.1f}",
                f"{speed1_grid[0]:.1f}",
                f"{speed2_grid[0]:.1f}",
                f"{speed_gap[0]:+.1f}"
            ])
            
            # 終點
            key_points_table.add_row([
                "終點",
                f"{distance_grid[-1]:.0f}",
                f"{x1_grid[-1]:.1f}",
                f"{y1_grid[-1]:.1f}",
                f"{speed1_grid[-1]:.1f}",
                f"{speed2_grid[-1]:.1f}",
                f"{speed_gap[-1]:+.1f}"
            ])
        else:
            # 沒有坐標數據時的簡化表格
            key_points_table = PrettyTable()
            key_points_table.field_names = ["位置類型", "距離(m)", f"{driver1}速度", f"{driver2}速度", "速度差距"]
            key_points_table.align = "r"
            
            # 最大優勢位置
            key_points_table.add_row([
                f"{driver1}最大優勢點",
                f"{distance_grid[max_adv_idx]:.0f}",
                f"{speed1_grid[max_adv_idx]:.1f}",
                f"{speed2_grid[max_adv_idx]:.1f}",
                f"+{max_advantage:.1f}"
            ])
            
            # 最大劣勢位置
            key_points_table.add_row([
                f"{driver1}最大劣勢點",
                f"{distance_grid[max_dis_idx]:.0f}",
                f"{speed1_grid[max_dis_idx]:.1f}",
                f"{speed2_grid[max_dis_idx]:.1f}",
                f"{max_disadvantage:.1f}"
            ])
            
            # 起始點
            key_points_table.add_row([
                "起始點",
                f"{distance_grid[0]:.0f}",
                f"{speed1_grid[0]:.1f}",
                f"{speed2_grid[0]:.1f}",
                f"{speed_gap[0]:+.1f}"
            ])
            
            # 終點
            key_points_table.add_row([
                "終點",
                f"{distance_grid[-1]:.0f}",
                f"{speed1_grid[-1]:.1f}",
                f"{speed2_grid[-1]:.1f}",
                f"{speed_gap[-1]:+.1f}"
            ])
        
        print(key_points_table)
        
        print("=" * 100)
        """顯示速度差距分析結果"""
        driver1, driver2 = self.selected_drivers
        lap1_num, lap2_num = self.selected_laps
        
        print(f"\n[INFO] 速度差距分析結果")
        print("=" * 80)
        
        # 基本統計
        stats_table = PrettyTable()
        stats_table.field_names = ["項目", f"{driver1} (第{lap1_num}圈)", f"{driver2} (第{lap2_num}圈)", "差距"]
        stats_table.align = "r"
        
        # 平均速度
        avg_speed1 = np.mean(speed1_grid)
        avg_speed2 = np.mean(speed2_grid)
        avg_gap = avg_speed1 - avg_speed2
        stats_table.add_row([
            "平均速度", 
            f"{avg_speed1:.1f} km/h", 
            f"{avg_speed2:.1f} km/h", 
            f"{avg_gap:+.1f} km/h"
        ])
        
        # 最高速度
        max_speed1 = np.max(speed1_grid)
        max_speed2 = np.max(speed2_grid)
        max_gap = max_speed1 - max_speed2
        stats_table.add_row([
            "最高速度", 
            f"{max_speed1:.1f} km/h", 
            f"{max_speed2:.1f} km/h", 
            f"{max_gap:+.1f} km/h"
        ])
        
        # 最低速度
        min_speed1 = np.min(speed1_grid)
        min_speed2 = np.min(speed2_grid)
        min_gap = min_speed1 - min_speed2
        stats_table.add_row([
            "最低速度", 
            f"{min_speed1:.1f} km/h", 
            f"{min_speed2:.1f} km/h", 
            f"{min_gap:+.1f} km/h"
        ])
        
        print(stats_table)
        
        # 速度差距統計
        print(f"\n[DEBUG] 速度差距詳細分析:")
        gap_table = PrettyTable()
        gap_table.field_names = ["統計項目", "數值", "說明"]
        gap_table.align["統計項目"] = "l"
        gap_table.align["數值"] = "r"
        gap_table.align["說明"] = "l"
        
        max_advantage = np.max(speed_gap)
        max_disadvantage = np.min(speed_gap)
        avg_gap = np.mean(speed_gap)
        std_gap = np.std(speed_gap)
        
        gap_table.add_row(["最大領先", f"{max_advantage:+.1f} km/h", f"{driver1}領先{driver2}"])
        gap_table.add_row(["最大落後", f"{max_disadvantage:+.1f} km/h", f"{driver1}落後{driver2}"])
        gap_table.add_row(["平均差距", f"{avg_gap:+.1f} km/h", "正值表示driver1較快"])
        gap_table.add_row(["差距標準差", f"{std_gap:.1f} km/h", "差距變化程度"])
        
        # 計算領先/落後距離百分比
        advantage_pct = (speed_gap > 0).sum() / len(speed_gap) * 100
        disadvantage_pct = (speed_gap < 0).sum() / len(speed_gap) * 100
        
        gap_table.add_row(["領先距離比例", f"{advantage_pct:.1f}%", f"{driver1}速度較快的賽道比例"])
        gap_table.add_row(["落後距離比例", f"{disadvantage_pct:.1f}%", f"{driver1}速度較慢的賽道比例"])
        
        print(gap_table)
        
        # 關鍵區域分析
        print(f"\n[TARGET] 關鍵區域分析:")
        
        # 找到最大優勢和劣勢位置
        max_adv_idx = np.argmax(speed_gap)
        max_dis_idx = np.argmin(speed_gap)
        
        print(f"  🟢 {driver1}最大優勢: 距離{distance_grid[max_adv_idx]:.0f}m處，領先{max_advantage:.1f} km/h")
        print(f"  🔴 {driver1}最大劣勢: 距離{distance_grid[max_dis_idx]:.0f}m處，落後{abs(max_disadvantage):.1f} km/h")
        
        # 分析速度差距變化趨勢
        if len(speed_gap) > 10:
            first_quarter = speed_gap[:len(speed_gap)//4]
            second_quarter = speed_gap[len(speed_gap)//4:len(speed_gap)//2]
            third_quarter = speed_gap[len(speed_gap)//2:3*len(speed_gap)//4]
            fourth_quarter = speed_gap[3*len(speed_gap)//4:]
            
            quarters = [first_quarter, second_quarter, third_quarter, fourth_quarter]
            quarter_names = ["第一段", "第二段", "第三段", "第四段"]
            
            print(f"\n[STATS] 賽道分段速度差距:")
            for i, (quarter, name) in enumerate(zip(quarters, quarter_names)):
                avg_quarter_gap = np.mean(quarter)
                print(f"  {name}: {avg_quarter_gap:+.1f} km/h")

    def _plot_speed_gap_analysis(self, distance_grid, speed1_grid, speed2_grid, speed_gap):
        """繪製速度差距分析圖表"""
        driver1, driver2 = self.selected_drivers
        lap1_num, lap2_num = self.selected_laps
        
        try:
            # 設置圖表樣式
            plt.style.use('default')
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
            fig.suptitle(f'速度差距分析: {driver1} (第{lap1_num}圈) vs {driver2} (第{lap2_num}圈)', 
                        fontsize=16, fontweight='bold')
            
            # 上圖：速度對比
            ax1.plot(distance_grid, speed1_grid, label=f'{driver1} (第{lap1_num}圈)', 
                    linewidth=2, color='blue')
            ax1.plot(distance_grid, speed2_grid, label=f'{driver2} (第{lap2_num}圈)', 
                    linewidth=2, color='red')
            
            ax1.set_title('速度對比圖', fontweight='bold', fontsize=14)
            ax1.set_ylabel('速度 (km/h)', fontsize=12)
            ax1.grid(True, alpha=0.3)
            ax1.legend(fontsize=11)
            
            # 下圖：速度差距
            # 使用顏色填充表示優劣勢
            ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3, linewidth=1)
            
            # 填充正值（優勢）和負值（劣勢）區域
            ax2.fill_between(distance_grid, 0, speed_gap, where=(speed_gap >= 0), 
                           color='green', alpha=0.3, label=f'{driver1}較快')
            ax2.fill_between(distance_grid, 0, speed_gap, where=(speed_gap < 0), 
                           color='red', alpha=0.3, label=f'{driver1}較慢')
            
            # 繪製差距線
            ax2.plot(distance_grid, speed_gap, color='black', linewidth=1.5, alpha=0.8)
            
            ax2.set_title('速度差距分析', fontweight='bold', fontsize=14)
            ax2.set_xlabel('距離 (m)', fontsize=12)
            ax2.set_ylabel('速度差距 (km/h)', fontsize=12)
            ax2.grid(True, alpha=0.3)
            ax2.legend(fontsize=11)
            
            # 標註關鍵點
            max_adv_idx = np.argmax(speed_gap)
            max_dis_idx = np.argmin(speed_gap)
            
            ax2.annotate(f'最大優勢\n{speed_gap[max_adv_idx]:+.1f} km/h', 
                        xy=(distance_grid[max_adv_idx], speed_gap[max_adv_idx]),
                        xytext=(10, 10), textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.3', fc='green', alpha=0.7),
                        arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
            
            ax2.annotate(f'最大劣勢\n{speed_gap[max_dis_idx]:+.1f} km/h', 
                        xy=(distance_grid[max_dis_idx], speed_gap[max_dis_idx]),
                        xytext=(10, -20), textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.3', fc='red', alpha=0.7),
                        arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
            
            plt.tight_layout()
            
            # 儲存圖表
            cache_dir = self.get_cache_dir()
            filename = f"speed_gap_analysis_{driver1}_vs_{driver2}_{lap1_num}_{lap2_num}.png"
            filepath = cache_dir / filename
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"[INFO] 速度差距分析圖已儲存: {filepath}")
            
            # 顯示圖表
            if self.f1_analysis_instance and hasattr(self.f1_analysis_instance, 'show_plots'):
                if self.f1_analysis_instance.show_plots:
                    plt.show()
            else:
                plt.show()
                
        except Exception as e:
            print(f"[ERROR] 圖表生成失敗: {e}")
            traceback.print_exc()
        finally:
            plt.close()

def run_speed_gap_analysis(data_loader, open_analyzer=None, f1_analysis_instance=None):
    """執行速度差距分析 - 對外接口函數"""
    analyzer = SpeedGapAnalyzer(data_loader, f1_analysis_instance)
    analyzer.run_speed_gap_analysis()
    return analyzer
