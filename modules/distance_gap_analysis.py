# -*- coding: utf-8 -*-
"""
距離差距分析子模組 - 7.2
從 driver_comparison_advanced.py 拆分出來的距離差距分析功能

版本: 拆分獨立版 v1.0
基於: driver_comparison_advanced.py 的距離差距分析功能
"""

import sys
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

class DistanceGapAnalyzer(F1AnalysisBase):
    """距離差距分析器 - 專門分析兩車手之間的距離差距"""
    
    def __init__(self, data_loader, f1_analysis_instance=None):
        super().__init__()
        self.data_loader = data_loader
        self.f1_analysis_instance = f1_analysis_instance
        self.selected_drivers = []
        self.selected_laps = []
        
    def run_distance_gap_analysis(self):
        """執行距離差距分析"""
        print(f"\n📏 距離差距分析")
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
                
            # 執行距離差距分析
            self._analyze_distance_gap(session, laps)
            
        except Exception as e:
            print(f"[ERROR] 距離差距分析失敗: {e}")
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
    
    def _analyze_distance_gap(self, session, laps):
        """分析距離差距 - 輸出包含坐標的原始數據"""
        print(f"\n[DEBUG] 距離差距分析中...")
        
        try:
            # 獲取兩個車手的圈次數據
            driver1, driver2 = self.selected_drivers
            lap1_num, lap2_num = self.selected_laps
            
            # 獲取遙測數據
            lap1_data = session.laps.pick_drivers(driver1).pick_lap(lap1_num)
            lap2_data = session.laps.pick_drivers(driver2).pick_lap(lap2_num)
            
            if lap1_data.empty or lap2_data.empty:
                print("[ERROR] 無法獲取圈次數據")
                return
            
            # 獲取完整遙測數據包含坐標
            try:
                # 首先嘗試獲取位置數據（包含X、Y坐標）
                pos_data1 = lap1_data.iloc[0].get_pos_data().add_distance()
                pos_data2 = lap2_data.iloc[0].get_pos_data().add_distance()
                
                # 獲取基本遙測數據
                telemetry1 = lap1_data.iloc[0].get_car_data().add_distance()
                telemetry2 = lap2_data.iloc[0].get_car_data().add_distance()
                
                # 合併位置數據和遙測數據
                # 確保時間對齊
                if not pos_data1.empty and not pos_data2.empty:
                    # 使用位置數據作為主要數據源，添加遙測欄位
                    telemetry1 = pos_data1.copy()
                    telemetry2 = pos_data2.copy()
                    print("[SUCCESS] 已獲取位置坐標數據")
                else:
                    print("[WARNING] 位置數據為空，嘗試其他方法")
                    raise Exception("Position data is empty")
                    
            except Exception as e1:
                print(f"[WARNING] 無法獲取位置數據，嘗試備用方法: {e1}")
                try:
                    telemetry1 = lap1_data.iloc[0].get_car_data().add_distance()
                    telemetry2 = lap2_data.iloc[0].get_car_data().add_distance()
                    print("[SUCCESS] 已獲取基本遙測數據")
                except:
                    try:
                        telemetry1 = lap1_data.iloc[0].get_telemetry().add_distance()
                        telemetry2 = lap2_data.iloc[0].get_telemetry().add_distance()
                        print("[SUCCESS] 已獲取基礎遙測數據")
                    except Exception as e:
                        print(f"[ERROR] 無法獲取任何遙測數據: {e}")
                        return
            
            if telemetry1.empty or telemetry2.empty:
                print("[ERROR] 遙測數據為空")
                return
            
            # 檢查遙測數據可用的欄位
            print(f"[DEBUG] 車手 {driver1} 遙測數據欄位: {list(telemetry1.columns)}")
            print(f"[DEBUG] 車手 {driver2} 遙測數據欄位: {list(telemetry2.columns)}")
            
            # 檢查基本必要欄位
            basic_required_cols = ['Distance']
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
            has_coordinates = (x_col1 and y_col1 and x_col2 and y_col2)
            
            if not has_coordinates:
                print(f"[WARNING] 未找到完整坐標數據，使用距離基礎分析方法")
                print(f"   車手{driver1}可用欄位: {list(telemetry1.columns)}")
                print(f"   車手{driver2}可用欄位: {list(telemetry2.columns)}")
                
                # 執行基於距離的差距分析
                self._analyze_distance_gap_by_distance(telemetry1, telemetry2, driver1, driver2, lap1_num, lap2_num)
                return
            
            print(f"[SUCCESS] 找到坐標數據，執行完整距離差距分析")
            print(f"   車手{driver1}: X={x_col1}, Y={y_col1}")
            print(f"   車手{driver2}: X={x_col2}, Y={y_col2}")
            
            # 計算原始距離差距數據
            print(f"[INFO] 計算距離差距數據...")
            
            # 創建時間對齊的數據
            # 使用較短的時間範圍
            min_samples = min(len(telemetry1), len(telemetry2))
            max_samples = 2000  # 限制最大樣本數
            
            if min_samples > max_samples:
                # 降採樣
                step1 = len(telemetry1) // max_samples
                step2 = len(telemetry2) // max_samples
                tel1_sampled = telemetry1.iloc[::step1][:max_samples].copy()
                tel2_sampled = telemetry2.iloc[::step2][:max_samples].copy()
            else:
                tel1_sampled = telemetry1.copy()
                tel2_sampled = telemetry2.copy()
            
            # 創建時間序列對齊
            time_range = min(len(tel1_sampled), len(tel2_sampled))
            
            # 計算每個時間點的距離差距
            distance_gaps = []
            x1_points = []
            y1_points = []
            x2_points = []
            y2_points = []
            distance1_points = []
            distance2_points = []
            
            for i in range(time_range):
                x1, y1 = tel1_sampled.iloc[i][x_col1], tel1_sampled.iloc[i][y_col1]
                x2, y2 = tel2_sampled.iloc[i][x_col2], tel2_sampled.iloc[i][y_col2]
                dist1 = tel1_sampled.iloc[i]['Distance']
                dist2 = tel2_sampled.iloc[i]['Distance']
                
                # 計算兩車間的實際距離
                euclidean_distance = np.sqrt((x1 - x2)**2 + (y1 - y2)**2)
                
                distance_gaps.append(euclidean_distance)
                x1_points.append(x1)
                y1_points.append(y1)
                x2_points.append(x2)
                y2_points.append(y2)
                distance1_points.append(dist1)
                distance2_points.append(dist2)
            
            # 轉換為numpy數組
            distance_gaps = np.array(distance_gaps)
            x1_points = np.array(x1_points)
            y1_points = np.array(y1_points)
            x2_points = np.array(x2_points)
            y2_points = np.array(y2_points)
            distance1_points = np.array(distance1_points)
            distance2_points = np.array(distance2_points)
            
            # 顯示原始數據
            self._display_raw_distance_gap_data(
                distance_gaps, x1_points, y1_points, x2_points, y2_points,
                distance1_points, distance2_points, driver1, driver2, lap1_num, lap2_num
            )
            
        except Exception as e:
            print(f"[ERROR] 距離差距分析失敗: {e}")
            traceback.print_exc()
    
    def _display_raw_distance_gap_data(self, distance_gaps, x1_points, y1_points, x2_points, y2_points,
                                     distance1_points, distance2_points, driver1, driver2, lap1_num, lap2_num):
        """顯示包含坐標的原始距離差距數據"""
        print(f"\n🏎️ 距離差距原始數據分析")
        print("=" * 100)
        print(f"比較對象: {driver1} (第{lap1_num}圈) vs {driver2} (第{lap2_num}圈)")
        print("=" * 100)
        
        # 統計摘要
        print(f"\n[INFO] 距離差距統計摘要:")
        summary_table = PrettyTable()
        summary_table.field_names = ["統計項目", "數值", "說明"]
        summary_table.align["統計項目"] = "l"
        summary_table.align["數值"] = "r"
        summary_table.align["說明"] = "l"
        
        min_distance = np.min(distance_gaps)
        max_distance = np.max(distance_gaps)
        avg_distance = np.mean(distance_gaps)
        std_distance = np.std(distance_gaps)
        
        summary_table.add_row(["最小距離", f"{min_distance:.1f} m", "兩車最接近時"])
        summary_table.add_row(["最大距離", f"{max_distance:.1f} m", "兩車最遠時"])
        summary_table.add_row(["平均距離", f"{avg_distance:.1f} m", "整個分析過程"])
        summary_table.add_row(["距離標準差", f"{std_distance:.1f} m", "距離變化程度"])
        
        print(summary_table)
        
        # 關鍵位置索引
        min_dist_idx = np.argmin(distance_gaps)
        max_dist_idx = np.argmax(distance_gaps)
        
        # 關鍵位置分析
        print(f"\n[TARGET] 關鍵位置分析:")
        key_points_table = PrettyTable()
        key_points_table.field_names = [
            "位置類型", "距離差(m)", 
            f"{driver1}_X(m)", f"{driver1}_Y(m)", f"{driver1}_距離進度(m)",
            f"{driver2}_X(m)", f"{driver2}_Y(m)", f"{driver2}_距離進度(m)"
        ]
        key_points_table.align = "r"
        
        # 最接近位置
        key_points_table.add_row([
            "最接近點",
            f"{distance_gaps[min_dist_idx]:.1f}",
            f"{x1_points[min_dist_idx]:.1f}",
            f"{y1_points[min_dist_idx]:.1f}",
            f"{distance1_points[min_dist_idx]:.0f}",
            f"{x2_points[min_dist_idx]:.1f}",
            f"{y2_points[min_dist_idx]:.1f}",
            f"{distance2_points[min_dist_idx]:.0f}"
        ])
        
        # 最遠距離位置
        key_points_table.add_row([
            "最遠距離點",
            f"{distance_gaps[max_dist_idx]:.1f}",
            f"{x1_points[max_dist_idx]:.1f}",
            f"{y1_points[max_dist_idx]:.1f}",
            f"{distance1_points[max_dist_idx]:.0f}",
            f"{x2_points[max_dist_idx]:.1f}",
            f"{y2_points[max_dist_idx]:.1f}",
            f"{distance2_points[max_dist_idx]:.0f}"
        ])
        
        # 起始點
        key_points_table.add_row([
            "起始點",
            f"{distance_gaps[0]:.1f}",
            f"{x1_points[0]:.1f}",
            f"{y1_points[0]:.1f}",
            f"{distance1_points[0]:.0f}",
            f"{x2_points[0]:.1f}",
            f"{y2_points[0]:.1f}",
            f"{distance2_points[0]:.0f}"
        ])
        
        # 終點
        key_points_table.add_row([
            "終點",
            f"{distance_gaps[-1]:.1f}",
            f"{x1_points[-1]:.1f}",
            f"{y1_points[-1]:.1f}",
            f"{distance1_points[-1]:.0f}",
            f"{x2_points[-1]:.1f}",
            f"{y2_points[-1]:.1f}",
            f"{distance2_points[-1]:.0f}"
        ])
        
        print(key_points_table)
        
        # 原始數據表格 - 顯示關鍵採樣點
        print(f"\n[LIST] 原始數據詳細表格 (等間距取樣):")
        data_table = PrettyTable()
        data_table.field_names = [
            "樣本點", "距離差(m)",
            f"{driver1}_X(m)", f"{driver1}_Y(m)", f"{driver1}_進度(m)",
            f"{driver2}_X(m)", f"{driver2}_Y(m)", f"{driver2}_進度(m)"
        ]
        data_table.align = "r"
        
        # 等間距取樣，最多顯示25行
        sample_count = min(25, len(distance_gaps))
        if sample_count > 1:
            step = len(distance_gaps) // sample_count
            sample_indices = np.arange(0, len(distance_gaps), step)[:sample_count]
        else:
            sample_indices = [0]
        
        for i, idx in enumerate(sample_indices):
            data_table.add_row([
                f"{i+1}",
                f"{distance_gaps[idx]:.1f}",
                f"{x1_points[idx]:.1f}",
                f"{y1_points[idx]:.1f}",
                f"{distance1_points[idx]:.0f}",
                f"{x2_points[idx]:.1f}",
                f"{y2_points[idx]:.1f}",
                f"{distance2_points[idx]:.0f}"
            ])
        
        print(data_table)
        
        # 分段分析
        if len(distance_gaps) > 10:
            print(f"\n[STATS] 分段距離差距分析:")
            segment_count = 5
            segment_size = len(distance_gaps) // segment_count
            segment_names = ["起始段", "前段", "中段", "後段", "結尾段"]
            
            segment_table = PrettyTable()
            segment_table.field_names = ["階段", "平均距離差(m)", "最小距離差(m)", "最大距離差(m)", "變化趨勢"]
            segment_table.align["階段"] = "l"
            segment_table.align = "r"
            
            for i, name in enumerate(segment_names):
                start_idx = i * segment_size
                end_idx = (i + 1) * segment_size if i < segment_count - 1 else len(distance_gaps)
                segment = distance_gaps[start_idx:end_idx]
                
                if len(segment) > 0:
                    avg_dist = np.mean(segment)
                    min_dist = np.min(segment)
                    max_dist = np.max(segment)
                    
                    # 簡單趨勢計算
                    if len(segment) > 1:
                        trend = segment[-1] - segment[0]
                        if trend > 5:
                            trend_desc = "距離增加"
                        elif trend < -5:
                            trend_desc = "距離縮小"
                        else:
                            trend_desc = "相對穩定"
                    else:
                        trend_desc = "單點"
                    
                    segment_table.add_row([
                        name,
                        f"{avg_dist:.1f}",
                        f"{min_dist:.1f}",
                        f"{max_dist:.1f}",
                        trend_desc
                    ])
            
            print(segment_table)
        
        # 完整數據統計
        print(f"\n💾 完整原始數據統計:")
        print(f"   • 總數據點: {len(distance_gaps)} 個")
        print(f"   • 時間密度: 約 {len(distance_gaps)/60:.1f} 點/分鐘" if len(distance_gaps) > 60 else f"   • 數據密度: {len(distance_gaps)} 個樣本點")
        print(f"   • 最小間距: {min_distance:.1f}m")
        print(f"   • 最大間距: {max_distance:.1f}m")
        print(f"   • 距離變化幅度: {max_distance - min_distance:.1f}m")
        
        print("=" * 100)

    def _plot_distance_gap_analysis(self, time_grid, distance_gap, x1_grid, y1_grid, x2_grid, y2_grid):
            print(f"\n[STATS] 距離變化趨勢分析:")
            
            # 分成幾個時間段分析
            segment_size = len(distance_gap) // 5
            segments = []
            segment_names = ["開始階段", "早期階段", "中期階段", "後期階段", "結束階段"]
            
            for i in range(5):
                start_idx = i * segment_size
                end_idx = (i + 1) * segment_size if i < 4 else len(distance_gap)
                segment = distance_gap[start_idx:end_idx]
                segments.append(segment)
            
            trend_table = PrettyTable()
            trend_table.field_names = ["階段", "平均距離", "最小距離", "最大距離", "變化趨勢"]
            trend_table.align = "l"
            
            for i, (name, segment) in enumerate(zip(segment_names, segments)):
                avg_seg = np.mean(segment)
                min_seg = np.min(segment)
                max_seg = np.max(segment)
                
                # 計算趨勢（簡單的線性趨勢）
                if len(segment) > 1:
                    trend = np.polyfit(range(len(segment)), segment, 1)[0]
                    if trend > 0.5:
                        trend_desc = "距離增加"
                    elif trend < -0.5:
                        trend_desc = "距離縮小"
                    else:
                        trend_desc = "距離穩定"
                else:
                    trend_desc = "數據不足"
                
                trend_table.add_row([
                    name,
                    f"{avg_seg:.1f}m",
                    f"{min_seg:.1f}m",
                    f"{max_seg:.1f}m",
                    trend_desc
                ])
            
            print(trend_table)

    def _plot_distance_gap_analysis(self, time_grid, distance_gap, x1_grid, y1_grid, x2_grid, y2_grid):
        """繪製距離差距分析圖表"""
        driver1, driver2 = self.selected_drivers
        lap1_num, lap2_num = self.selected_laps
        
        try:
            # 設置圖表樣式
            plt.style.use('default')
            fig = plt.figure(figsize=(16, 12))
            
            # 創建子圖布局
            gs = fig.add_gridspec(3, 2, height_ratios=[2, 1, 1], hspace=0.3, wspace=0.3)
            
            # 主標題
            fig.suptitle(f'距離差距分析: {driver1} (第{lap1_num}圈) vs {driver2} (第{lap2_num}圈)', 
                        fontsize=16, fontweight='bold')
            
            # 1. 賽道位置圖 (左上，跨兩列)
            ax1 = fig.add_subplot(gs[0, :])
            ax1.plot(x1_grid, y1_grid, label=f'{driver1} (第{lap1_num}圈)', 
                    linewidth=3, color='blue', alpha=0.8)
            ax1.plot(x2_grid, y2_grid, label=f'{driver2} (第{lap2_num}圈)', 
                    linewidth=3, color='red', alpha=0.8)
            
            # 標註起點和終點
            ax1.scatter(x1_grid[0], y1_grid[0], color='blue', s=100, marker='o', 
                       label=f'{driver1} 起點', zorder=5)
            ax1.scatter(x2_grid[0], y2_grid[0], color='red', s=100, marker='o', 
                       label=f'{driver2} 起點', zorder=5)
            ax1.scatter(x1_grid[-1], y1_grid[-1], color='blue', s=100, marker='s', 
                       label=f'{driver1} 終點', zorder=5)
            ax1.scatter(x2_grid[-1], y2_grid[-1], color='red', s=100, marker='s', 
                       label=f'{driver2} 終點', zorder=5)
            
            # 標註最近和最遠點
            min_dist_idx = np.argmin(distance_gap)
            max_dist_idx = np.argmax(distance_gap)
            
            ax1.plot([x1_grid[min_dist_idx], x2_grid[min_dist_idx]], 
                    [y1_grid[min_dist_idx], y2_grid[min_dist_idx]], 
                    'g-', linewidth=2, alpha=0.7, label=f'最近距離 ({distance_gap[min_dist_idx]:.1f}m)')
            ax1.plot([x1_grid[max_dist_idx], x2_grid[max_dist_idx]], 
                    [y1_grid[max_dist_idx], y2_grid[max_dist_idx]], 
                    'orange', linewidth=2, alpha=0.7, label=f'最遠距離 ({distance_gap[max_dist_idx]:.1f}m)')
            
            ax1.set_title('賽道位置對比', fontweight='bold', fontsize=14)
            ax1.set_xlabel('X 位置 (m)', fontsize=12)
            ax1.set_ylabel('Y 位置 (m)', fontsize=12)
            ax1.set_aspect('equal')
            ax1.grid(True, alpha=0.3)
            ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            
            # 2. 距離變化圖 (左下)
            ax2 = fig.add_subplot(gs[1, 0])
            ax2.plot(time_grid, distance_gap, color='purple', linewidth=2)
            ax2.fill_between(time_grid, 0, distance_gap, alpha=0.3, color='purple')
            
            # 標註關鍵點
            ax2.scatter(time_grid[min_dist_idx], distance_gap[min_dist_idx], 
                       color='green', s=80, zorder=5)
            ax2.scatter(time_grid[max_dist_idx], distance_gap[max_dist_idx], 
                       color='orange', s=80, zorder=5)
            
            ax2.set_title('兩車距離變化', fontweight='bold', fontsize=12)
            ax2.set_xlabel('時間 (s)', fontsize=11)
            ax2.set_ylabel('距離 (m)', fontsize=11)
            ax2.grid(True, alpha=0.3)
            
            # 3. 距離統計圖 (右下)
            ax3 = fig.add_subplot(gs[1, 1])
            
            # 創建距離分布直方圖
            ax3.hist(distance_gap, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
            ax3.axvline(np.mean(distance_gap), color='red', linestyle='--', 
                       label=f'平均: {np.mean(distance_gap):.1f}m')
            ax3.axvline(np.median(distance_gap), color='green', linestyle='--', 
                       label=f'中位數: {np.median(distance_gap):.1f}m')
            
            ax3.set_title('距離分布統計', fontweight='bold', fontsize=12)
            ax3.set_xlabel('距離 (m)', fontsize=11)
            ax3.set_ylabel('頻次', fontsize=11)
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            
            # 4. 速度對比圖 (如果有速度數據)
            ax4 = fig.add_subplot(gs[2, :])
            
            # 計算相對速度（距離變化率）
            if len(time_grid) > 1:
                dt = time_grid[1] - time_grid[0]
                relative_speed = np.gradient(distance_gap, dt)
                
                ax4.plot(time_grid, relative_speed, color='darkorange', linewidth=2)
                ax4.axhline(y=0, color='black', linestyle='-', alpha=0.3)
                ax4.fill_between(time_grid, 0, relative_speed, where=(relative_speed >= 0), 
                               color='red', alpha=0.3, label='距離增加')
                ax4.fill_between(time_grid, 0, relative_speed, where=(relative_speed < 0), 
                               color='green', alpha=0.3, label='距離縮小')
                
                ax4.set_title('相對速度分析 (距離變化率)', fontweight='bold', fontsize=12)
                ax4.set_xlabel('時間 (s)', fontsize=11)
                ax4.set_ylabel('相對速度 (m/s)', fontsize=11)
                ax4.legend()
                ax4.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # 儲存圖表
            cache_dir = self.get_cache_dir()
            filename = f"distance_gap_analysis_{driver1}_vs_{driver2}_{lap1_num}_{lap2_num}.png"
            filepath = cache_dir / filename
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"[INFO] 距離差距分析圖已儲存: {filepath}")
            
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
    
    def _analyze_distance_gap_by_distance(self, telemetry1, telemetry2, driver1, driver2, lap1_num, lap2_num):
        """基於距離數據的差距分析（當無坐標數據時使用）"""
        print(f"[INFO] 使用距離基礎分析方法...")
        
        try:
            # 檢查必要的欄位
            required_cols = ['Distance']
            optional_cols = ['Speed', 'Time', 'SessionTime']
            
            # 準備數據
            tel1 = telemetry1.copy()
            tel2 = telemetry2.copy()
            
            # 確保有距離數據
            if 'Distance' not in tel1.columns or 'Distance' not in tel2.columns:
                print("[ERROR] 缺少距離數據，無法進行分析")
                return
            
            # 獲取時間數據
            time_col1 = time_col2 = None
            for col in ['SessionTime', 'Time']:
                if col in tel1.columns:
                    time_col1 = col
                    break
            for col in ['SessionTime', 'Time']:
                if col in tel2.columns:
                    time_col2 = col
                    break
            
            if not time_col1 or not time_col2:
                print("[ERROR] 缺少時間數據，無法進行分析")
                return
            
            print(f"[SUCCESS] 使用時間欄位: {time_col1}, {time_col2}")
            
            # 數據預處理
            tel1 = tel1.dropna(subset=['Distance', time_col1])
            tel2 = tel2.dropna(subset=['Distance', time_col2])
            
            if tel1.empty or tel2.empty:
                print("[ERROR] 處理後數據為空")
                return
            
            # 轉換時間為數值（如果需要）
            if tel1[time_col1].dtype == 'object':
                try:
                    tel1[time_col1] = pd.to_timedelta(tel1[time_col1]).dt.total_seconds()
                except:
                    tel1[time_col1] = pd.to_numeric(tel1[time_col1], errors='coerce')
            
            if tel2[time_col2].dtype == 'object':
                try:
                    tel2[time_col2] = pd.to_timedelta(tel2[time_col2]).dt.total_seconds()
                except:
                    tel2[time_col2] = pd.to_numeric(tel2[time_col2], errors='coerce')
            
            # 創建統一的距離網格進行插值
            min_distance = max(tel1['Distance'].min(), tel2['Distance'].min())
            max_distance = min(tel1['Distance'].max(), tel2['Distance'].max())
            
            if min_distance >= max_distance:
                print("[ERROR] 距離範圍無重疊，無法進行比較")
                return
            
            # 創建共同的距離網格
            distance_grid = np.linspace(min_distance, max_distance, 500)
            
            # 對時間進行插值
            try:
                f1_time = interp1d(tel1['Distance'], tel1[time_col1], 
                                  kind='linear', bounds_error=False, fill_value='extrapolate')
                f2_time = interp1d(tel2['Distance'], tel2[time_col2], 
                                  kind='linear', bounds_error=False, fill_value='extrapolate')
                
                time1_interp = f1_time(distance_grid)
                time2_interp = f2_time(distance_grid)
                
                # 計算時間差距
                time_gap = time2_interp - time1_interp
                
                # 過濾無效值
                valid_mask = ~(np.isnan(time_gap) | np.isinf(time_gap))
                distance_grid_valid = distance_grid[valid_mask]
                time_gap_valid = time_gap[valid_mask]
                
                if len(time_gap_valid) == 0:
                    print("[ERROR] 無有效的時間差距數據")
                    return
                
                # 輸出統計結果
                self._print_distance_based_statistics(time_gap_valid, driver1, driver2, lap1_num, lap2_num)
                
                # 繪製圖表
                self._plot_distance_based_gap(distance_grid_valid, time_gap_valid, 
                                            driver1, driver2, lap1_num, lap2_num)
                
            except Exception as e:
                print(f"[ERROR] 插值計算失敗: {e}")
                traceback.print_exc()
                
        except Exception as e:
            print(f"[ERROR] 距離基礎分析失敗: {e}")
            traceback.print_exc()
    
    def _print_distance_based_statistics(self, time_gap, driver1, driver2, lap1_num, lap2_num):
        """輸出基於距離的統計結果"""
        try:
            # 基本統計
            avg_gap = np.mean(time_gap)
            max_gap = np.max(time_gap)
            min_gap = np.min(time_gap)
            std_gap = np.std(time_gap)
            
            # 創建統計表格
            table = PrettyTable()
            table.field_names = ["統計項目", "數值"]
            table.align["統計項目"] = "l"
            table.align["數值"] = "r"
            
            table.add_row(["平均時間差距", f"{avg_gap:.3f} 秒"])
            table.add_row(["最大時間差距", f"{max_gap:.3f} 秒"])
            table.add_row(["最小時間差距", f"{min_gap:.3f} 秒"])
            table.add_row(["標準差", f"{std_gap:.3f} 秒"])
            
            # 判斷領先情況
            if avg_gap > 0:
                leader = driver1
                follower = driver2
            else:
                leader = driver2
                follower = driver1
                avg_gap = abs(avg_gap)
            
            table.add_row(["領先車手", leader])
            table.add_row(["平均領先時間", f"{avg_gap:.3f} 秒"])
            
            print(f"\n[INFO] 距離基礎時間差距統計 ({driver1} 第{lap1_num}圈 vs {driver2} 第{lap2_num}圈)")
            print("=" * 80)
            print(table)
            
            # 領先變化統計
            lead_changes = 0
            current_leader = None
            for gap in time_gap:
                new_leader = driver1 if gap < 0 else driver2
                if current_leader is None:
                    current_leader = new_leader
                elif current_leader != new_leader:
                    lead_changes += 1
                    current_leader = new_leader
            
            print(f"\n🔄 領先變化次數: {lead_changes}")
            
        except Exception as e:
            print(f"[ERROR] 統計輸出失敗: {e}")
    
    def _plot_distance_based_gap(self, distance_grid, time_gap, driver1, driver2, lap1_num, lap2_num):
        """繪製基於距離的差距分析圖表"""
        try:
            plt.style.use('default')
            fig = plt.figure(figsize=(16, 10))
            gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
            
            # 設置中文字體
            plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            
            fig.suptitle(f'距離基礎時間差距分析\n{driver1} 第{lap1_num}圈 vs {driver2} 第{lap2_num}圈', 
                        fontsize=16, fontweight='bold', y=0.95)
            
            # 1. 時間差距隨距離變化圖
            ax1 = fig.add_subplot(gs[0, :])
            
            # 使用顏色表示領先者
            colors = ['red' if gap > 0 else 'blue' for gap in time_gap]
            ax1.scatter(distance_grid, time_gap, c=colors, alpha=0.6, s=20)
            ax1.plot(distance_grid, time_gap, color='gray', alpha=0.7, linewidth=1)
            ax1.axhline(y=0, color='black', linestyle='-', alpha=0.5)
            
            ax1.set_title('時間差距隨賽道距離變化', fontweight='bold', fontsize=14)
            ax1.set_xlabel('賽道距離 (m)', fontsize=12)
            ax1.set_ylabel('時間差距 (s)', fontsize=12)
            ax1.grid(True, alpha=0.3)
            
            # 添加圖例
            red_patch = plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='red', 
                                  markersize=8, label=f'{driver1} 領先')
            blue_patch = plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', 
                                   markersize=8, label=f'{driver2} 領先')
            ax1.legend(handles=[red_patch, blue_patch])
            
            # 2. 時間差距分布直方圖
            ax2 = fig.add_subplot(gs[1, 0])
            ax2.hist(time_gap, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
            ax2.axvline(np.mean(time_gap), color='red', linestyle='--', 
                       label=f'平均: {np.mean(time_gap):.3f}s')
            ax2.axvline(np.median(time_gap), color='green', linestyle='--', 
                       label=f'中位數: {np.median(time_gap):.3f}s')
            
            ax2.set_title('時間差距分布', fontweight='bold', fontsize=12)
            ax2.set_xlabel('時間差距 (s)', fontsize=11)
            ax2.set_ylabel('頻次', fontsize=11)
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            # 3. 累積分布圖
            ax3 = fig.add_subplot(gs[1, 1])
            sorted_gaps = np.sort(time_gap)
            cumulative = np.arange(1, len(sorted_gaps) + 1) / len(sorted_gaps)
            
            ax3.plot(sorted_gaps, cumulative, linewidth=2, color='purple')
            ax3.axvline(0, color='black', linestyle='--', alpha=0.7, label='零差距')
            ax3.axhline(0.5, color='gray', linestyle='--', alpha=0.7, label='50%分位')
            
            ax3.set_title('時間差距累積分布', fontweight='bold', fontsize=12)
            ax3.set_xlabel('時間差距 (s)', fontsize=11)
            ax3.set_ylabel('累積概率', fontsize=11)
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # 儲存圖表
            cache_dir = self.get_cache_dir()
            filename = f"distance_based_gap_analysis_{driver1}_vs_{driver2}_{lap1_num}_{lap2_num}.png"
            filepath = cache_dir / filename
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"[INFO] 距離基礎差距分析圖已儲存: {filepath}")
            
            # 顯示圖表
            if self.f1_analysis_instance and hasattr(self.f1_analysis_instance, 'show_plots'):
                if self.f1_analysis_instance.show_plots:
                    plt.show()
            else:
                plt.show()
                
        except Exception as e:
            print(f"[ERROR] 距離基礎圖表生成失敗: {e}")
            traceback.print_exc()
        finally:
            plt.close()

def run_distance_gap_analysis(data_loader, open_analyzer=None, f1_analysis_instance=None):
    """執行距離差距分析 - 對外接口函數"""
    analyzer = DistanceGapAnalyzer(data_loader, f1_analysis_instance)
    analyzer.run_distance_gap_analysis()
    return analyzer
