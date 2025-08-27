# -*- coding: utf-8 -*-
"""
雙車手比較分析模組 - 完全復刻 f1_analysis_cli_new.py 選項 6
完全復刻原始程式的「6. 🆚 雙車手比較分析 (Two Driver Comparison)」功能

版本: 完全復刻版 v1.0
基於: f1_analysis_cli_new.py 的 _run_driver_comparison_analysis 功能
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

class DriverComparisonAdvanced(F1AnalysisBase):
    """雙車手比較分析模組 - 完全復刻原始程式功能"""
    
    def __init__(self, data_loader, f1_analysis_instance=None):
        super().__init__()
        self.data_loader = data_loader
        self.f1_analysis_instance = f1_analysis_instance
    
    def run_driver_comparison_analysis(self):
        """執行雙車手比較分析（可比較同一車手的不同圈次）- 完全復刻原始程式"""
        print(f"\n🆚 雙車手比較分析")
        print("⚡ 可選擇不同車手比較，或同一車手的不同圈次比較")
        print("=" * 80)
        try:
            data = self.data_loader.get_loaded_data()
            session = data['session']
            laps = data['laps']
            drivers_info = data['drivers_info']

            # 顯示可用車手
            available_drivers = list(drivers_info.keys())
            print("[LIST] 可用車手:")
            
            # 使用 PrettyTable 顯示可用車手
            drivers_table = PrettyTable()
            drivers_table.field_names = ["選項", "車手代號", "車手姓名", "車隊"]
            drivers_table.align = "l"
            drivers_table.max_width = 30
            
            for i, (abbr, info) in enumerate(drivers_info.items(), 1):
                drivers_table.add_row([i, abbr, info['name'], info['team']])
            
            print(drivers_table)

            # 選擇第一個車手
            while True:
                try:
                    choice1 = input(f"\n請選擇第一個車手 (1-{len(available_drivers)}): ").strip()
                    idx1 = int(choice1) - 1
                    if 0 <= idx1 < len(available_drivers):
                        driver1 = available_drivers[idx1]
                        break
                    else:
                        print("[ERROR] 無效選擇")
                except ValueError:
                    print("[ERROR] 請輸入數字")

            # 選擇第二個車手（可以是同一個車手）
            while True:
                try:
                    choice2 = input(f"請選擇第二個車手 (1-{len(available_drivers)}, 可選同一車手): ").strip()
                    idx2 = int(choice2) - 1
                    if 0 <= idx2 < len(available_drivers):
                        driver2 = available_drivers[idx2]
                        break
                    else:
                        print("[ERROR] 無效選擇")
                except ValueError:
                    print("[ERROR] 請輸入數字")

            # 分別選擇圈次
            lap_choices = {
                '1': '[FINISH] 最快圈',
                '2': '[INFO] 指定圈數',
                '3': '🔄 出站後第一圈'
            }
            
            print(f"\n[STATS] 請選擇 {driver1} 的圈次:")
            # 使用 PrettyTable 顯示圈次選項
            lap_table = PrettyTable()
            lap_table.field_names = ["選項", "圈次類型"]
            lap_table.align = "l"
            for key, desc in lap_choices.items():
                lap_table.add_row([key, desc])
            print(lap_table)
            
            while True:
                lap_choice1 = input(f"選擇 {driver1} 的圈次 (1-3): ").strip()
                if lap_choice1 in lap_choices:
                    break
                print("[ERROR] 無效選擇")

            print(f"\n[STATS] 請選擇 {driver2} 的圈次:")
            print(lap_table)
            while True:
                lap_choice2 = input(f"選擇 {driver2} 的圈次 (1-3): ").strip()
                if lap_choice2 in lap_choices:
                    break
                print("[ERROR] 無效選擇")

            # 如果選擇指定圈數，分別輸入圈數
            lap_num1 = None
            lap_num2 = None
            if lap_choice1 == '2':
                while True:
                    try:
                        lap_num1 = int(input(f"請輸入 {driver1} 的圈數: "))
                        break
                    except ValueError:
                        print("[ERROR] 請輸入有效的圈數")
            if lap_choice2 == '2':
                while True:
                    try:
                        lap_num2 = int(input(f"請輸入 {driver2} 的圈數: "))
                        break
                    except ValueError:
                        print("[ERROR] 請輸入有效的圈數")

            # 選擇比較項目（可多選，預設全選）
            compare_items = {
                '1': '圈速',
                '2': '最高速',
                '3': 'I1時間',
                '4': 'I2時間',
                '5': 'I3時間',
                '6': '輪胎(壽命)',
                '7': '🏎️ 遙測比較圖 (速度/RPM/油門煞車/加速度/檔位/速度差距/距離差距/摘要)'
            }
            print(f"\n[INFO] 可比較項目（預設全選）：")
            for key, desc in compare_items.items():
                print(f"   {key}. {desc}")
            user_input = input("請選擇要比較的項目 (可多選, 例如 123，直接按 Enter 全選): ").strip()
            if user_input:
                selected_items = [k for k in user_input if k in compare_items]
                if not selected_items:
                    print("[ERROR] 無效選擇，使用預設全選")
                    selected_items = list(compare_items.keys())
            else:
                selected_items = list(compare_items.keys())  # 預設全選

            # 執行比較
            self._perform_driver_comparison_replica(session, laps, drivers_info, driver1, driver2,
                                           lap_choice1, lap_choice2, lap_num1, lap_num2, selected_items)
        except Exception as e:
            print(f"[ERROR] 車手比較分析失敗: {e}")
            traceback.print_exc()
    
    def _perform_driver_comparison_replica(self, session, laps, drivers_info, driver1, driver2,
                                   lap_choice1, lap_choice2, lap_num1, lap_num2, selected_items):
        """執行具體的車手比較 - 完全復刻原始程式"""
        try:
            # 設定中文字體
            self._setup_chinese_font()
            
            driver1_info = drivers_info[driver1]
            driver2_info = drivers_info[driver2]
            
            # 根據是否為同一車手調整顯示標題
            if driver1 == driver2:
                print(f"\n🆚 同車手圈次比較: {driver1_info['name']}")
                print(f"[INFO] 圈次比較分析")
            else:
                print(f"\n🆚 雙車手比較: {driver1_info['name']} vs {driver2_info['name']}")
            print("=" * 80)
            
            # 獲取車手圈次數據
            driver1_laps = laps[laps['Driver'] == driver1]
            driver2_laps = laps[laps['Driver'] == driver2]

            # 根據選擇取得圈次資料
            def get_lap(laps, choice, lap_num):
                if choice == '1':
                    return laps.loc[laps['LapTime'].idxmin()] if not laps['LapTime'].isna().all() else None
                elif choice == '2':
                    lap = laps[laps['LapNumber'] == lap_num]
                    # 安全獲取圈次資料
                    try:
                        return lap.iloc[0] if hasattr(lap, 'iloc') and len(lap) > 0 else None
                    except:
                        return None
                elif choice == '3':
                    pit_laps = laps[(laps['TyreLife'] == 1) & (laps['LapNumber'] > 1)]
                    # 安全獲取圈次資料
                    try:
                        return pit_laps.iloc[0] if hasattr(pit_laps, 'iloc') and len(pit_laps) > 0 else None
                    except:
                        return None
                return None

            lap1 = get_lap(driver1_laps, lap_choice1, lap_num1)
            lap2 = get_lap(driver2_laps, lap_choice2, lap_num2)

            if lap1 is None or lap2 is None:
                print("[ERROR] 無法獲取比較數據")
                return

            print(f"\n[INFO] 比較項目：")
            
            # 使用 PrettyTable 顯示比較結果
            comparison_table = PrettyTable()
            
            # 解決同車手比較時欄位名稱重複的問題
            if driver1 == driver2:
                header1 = f"{driver1}_圈次1"
                header2 = f"{driver2}_圈次2"
            else:
                header1 = driver1
                header2 = driver2
            
            comparison_table.field_names = ["項目", header1, header2, "較快者", "差距"]
            comparison_table.align = "l"

            # 圈速
            if '1' in selected_items:
                time1 = lap1['LapTime'] if pd.notna(lap1['LapTime']) else None
                time2 = lap2['LapTime'] if pd.notna(lap2['LapTime']) else None
                if time1 and time2:
                    time1_str = self._format_time(time1)
                    time2_str = self._format_time(time2)
                    diff = abs(time1.total_seconds() - time2.total_seconds())
                    faster = driver1 if time1 < time2 else driver2
                    comparison_table.add_row(["圈速", time1_str, time2_str, faster, f"+{diff:.3f}s"])

            # 最高速
            if '2' in selected_items:
                speed1 = lap1.get('SpeedFL')
                speed2 = lap2.get('SpeedFL')
                if pd.notna(speed1) and pd.notna(speed2):
                    diff = abs(speed1 - speed2)
                    faster = driver1 if speed1 > speed2 else driver2
                    comparison_table.add_row(["最高速", f"{speed1:.0f} km/h", f"{speed2:.0f} km/h", faster, f"+{diff:.0f} km/h"])

            # I1時間
            if '3' in selected_items:
                s1_1 = lap1.get('Sector1Time')
                s1_2 = lap2.get('Sector1Time')
                if pd.notna(s1_1) and pd.notna(s1_2):
                    s1_1_str = self._format_time(s1_1) if hasattr(s1_1, 'total_seconds') else str(s1_1)
                    s1_2_str = self._format_time(s1_2) if hasattr(s1_2, 'total_seconds') else str(s1_2)
                    if hasattr(s1_1, 'total_seconds') and hasattr(s1_2, 'total_seconds'):
                        diff = abs(s1_1.total_seconds() - s1_2.total_seconds())
                        faster = driver1 if s1_1 < s1_2 else driver2
                        comparison_table.add_row(["I1時間", s1_1_str, s1_2_str, faster, f"+{diff:.3f}s"])
                    else:
                        comparison_table.add_row(["I1時間", s1_1_str, s1_2_str, "N/A", "N/A"])

            # I2時間
            if '4' in selected_items:
                s2_1 = lap1.get('Sector2Time')
                s2_2 = lap2.get('Sector2Time')
                if pd.notna(s2_1) and pd.notna(s2_2):
                    s2_1_str = self._format_time(s2_1) if hasattr(s2_1, 'total_seconds') else str(s2_1)
                    s2_2_str = self._format_time(s2_2) if hasattr(s2_2, 'total_seconds') else str(s2_2)
                    if hasattr(s2_1, 'total_seconds') and hasattr(s2_2, 'total_seconds'):
                        diff = abs(s2_1.total_seconds() - s2_2.total_seconds())
                        faster = driver1 if s2_1 < s2_2 else driver2
                        comparison_table.add_row(["I2時間", s2_1_str, s2_2_str, faster, f"+{diff:.3f}s"])
                    else:
                        comparison_table.add_row(["I2時間", s2_1_str, s2_2_str, "N/A", "N/A"])

            # I3時間
            if '5' in selected_items:
                s3_1 = lap1.get('Sector3Time')
                s3_2 = lap2.get('Sector3Time')
                if pd.notna(s3_1) and pd.notna(s3_2):
                    s3_1_str = self._format_time(s3_1) if hasattr(s3_1, 'total_seconds') else str(s3_1)
                    s3_2_str = self._format_time(s3_2) if hasattr(s3_2, 'total_seconds') else str(s3_2)
                    if hasattr(s3_1, 'total_seconds') and hasattr(s3_2, 'total_seconds'):
                        diff = abs(s3_1.total_seconds() - s3_2.total_seconds())
                        faster = driver1 if s3_1 < s3_2 else driver2
                        comparison_table.add_row(["I3時間", s3_1_str, s3_2_str, faster, f"+{diff:.3f}s"])
                    else:
                        comparison_table.add_row(["I3時間", s3_1_str, s3_2_str, "N/A", "N/A"])

            # 輪胎(壽命)
            if '6' in selected_items:
                compound1 = lap1.get('Compound', 'N/A')
                compound2 = lap2.get('Compound', 'N/A')
                age1 = lap1.get('TyreLife', 'N/A')
                age2 = lap2.get('TyreLife', 'N/A')
                comparison_table.add_row(["輪胎(壽命)", f"{compound1} ({age1})", f"{compound2} ({age2})", "-", "-"])

            # 顯示比較表格
            print(comparison_table)

            # 遙測比較圖
            if '7' in selected_items:
                try:
                    self._plot_driver_compare_replica(session, lap1, lap2, driver1, driver2)
                except Exception as e:
                    print(f"[WARNING] 遙測比較圖失敗: {e}")
                    traceback.print_exc()

            # 距離分析（可選，這裡預設執行）
            try:
                self._analyze_distance_gap_replica(session, lap1, lap2, driver1, driver2, "距離分析")
            except Exception as e:
                print(f"[WARNING] 距離分析失敗: {e}")
                
        except Exception as e:
            print(f"[ERROR] 比較執行失敗: {e}")
            traceback.print_exc()

    def _plot_driver_compare_replica(self, session, lap1, lap2, driver1, driver2):
        """繪製兩車手的詳細遙測比較圖 - 完全復刻原始程式"""
        try:
            # 設定白色主題 (車手比較圖使用白色背景)
            self._setup_chinese_font(dark_theme=False)

            # 取得圈次的車輛遙測數據
            lap1_data = session.laps[
                (session.laps['Driver'] == driver1) &
                (session.laps['LapNumber'] == lap1['LapNumber'])
            ]
            lap2_data = session.laps[
                (session.laps['Driver'] == driver2) &
                (session.laps['LapNumber'] == lap2['LapNumber'])
            ]
            if lap1_data.empty or lap2_data.empty:
                print("[ERROR] 無法獲取圈次數據")
                return

            # 安全獲取車輛數據
            car_data1, error_msg1 = self._safe_get_lap_telemetry(lap1_data)
            car_data2, error_msg2 = self._safe_get_lap_telemetry(lap2_data)
            
            if car_data1 is None:
                print(f"[ERROR] 車手1遙測數據獲取失敗: {error_msg1}")
                return
            if car_data2 is None:
                print(f"[ERROR] 車手2遙測數據獲取失敗: {error_msg2}")
                return

            print(f"[DEBUG] 車手1遙測數據檢查:")
            print(f"   數據量: {len(car_data1)} 行")
            print(f"   可用欄位: {list(car_data1.columns)}")
            print(f"[DEBUG] 車手2遙測數據檢查:")
            print(f"   數據量: {len(car_data2)} 行")
            print(f"   可用欄位: {list(car_data2.columns)}")

            # 建立一個包含兩個子圖的大圖窗 - 同時顯示 FIGURE1 和 FIGURE2
            print(f"\n🎨 創建包含 FIGURE1 和 FIGURE2 的綜合顯示...")
            
            # 創建一個大的圖窗，左邊是遙測比較，右邊是賽道地圖和彎道速度圖
            fig_main = plt.figure(figsize=(32, 16), facecolor='white')
            # 調整 GridSpec：4行6列，移除多餘空間
            gs = fig_main.add_gridspec(4, 6, hspace=0.25, wspace=0.4, 
                                      left=0.05, right=0.95, top=0.95, bottom=0.08)

            # FIGURE1: 遙測比較圖 (左側 4x2)
            print(f"   [INFO] 創建 FIGURE1: 遙測比較圖...")
            
            color1, color2 = 'blue', 'red'

            # 1. 速度對比 (左上)
            ax = fig_main.add_subplot(gs[0, 0:2])
            if 'Speed' in car_data1.columns and 'Speed' in car_data2.columns:
                ax.plot(car_data1['Distance'] if 'Distance' in car_data1.columns else range(len(car_data1)), 
                       car_data1['Speed'], color=color1, label=driver1, linewidth=1, alpha=0.8)
                ax.plot(car_data2['Distance'] if 'Distance' in car_data2.columns else range(len(car_data2)), 
                       car_data2['Speed'], color=color2, label=driver2, linewidth=1, alpha=0.8)
                ax.set_title('速度對比 (Speed)', fontweight='bold', fontsize=12)
                ax.set_ylabel('速度 (km/h)', fontsize=10)
                ax.legend(fontsize=9)
                ax.grid(True, alpha=0.3)
            else:
                ax.text(0.5, 0.5, '速度數據不可用', ha='center', va='center', transform=ax.transAxes, fontsize=10)
                ax.set_title('速度對比 (無數據)', fontsize=12)

            # 2. RPM 對比 (右上)
            ax = fig_main.add_subplot(gs[0, 2:4])
            if 'RPM' in car_data1.columns and 'RPM' in car_data2.columns:
                ax.plot(car_data1['Distance'] if 'Distance' in car_data1.columns else range(len(car_data1)), 
                       car_data1['RPM'], color=color1, label=driver1, linewidth=1, alpha=0.8)
                ax.plot(car_data2['Distance'] if 'Distance' in car_data2.columns else range(len(car_data2)), 
                       car_data2['RPM'], color=color2, label=driver2, linewidth=1, alpha=0.8)
                ax.set_title('引擎轉速對比 (RPM)', fontweight='bold', fontsize=12)
                ax.set_ylabel('轉速 (RPM)', fontsize=10)
                ax.legend(fontsize=9)
                ax.grid(True, alpha=0.3)
            else:
                ax.text(0.5, 0.5, 'RPM數據不可用', ha='center', va='center', transform=ax.transAxes, fontsize=10)
                ax.set_title('引擎轉速對比 (無數據)', fontsize=12)

            # 3. 油門對比
            ax = fig_main.add_subplot(gs[1, 0:2])
            if 'Throttle' in car_data1.columns and 'Throttle' in car_data2.columns:
                throttle1 = car_data1['Throttle']
                throttle2 = car_data2['Throttle']
                max_throttle = max(throttle1.max(), throttle2.max())
                y_max = max(105, min(120, max_throttle + 5))
                
                ax.plot(car_data1['Distance'] if 'Distance' in car_data1.columns else range(len(car_data1)), 
                       throttle1, color=color1, label=f'{driver1} 油門', linewidth=1, alpha=0.8)
                ax.plot(car_data2['Distance'] if 'Distance' in car_data2.columns else range(len(car_data2)), 
                       throttle2, color=color2, label=f'{driver2} 油門', linewidth=1, alpha=0.8)
                ax.set_title('油門開度對比', fontweight='bold', fontsize=12)
                ax.set_ylabel('油門開度 (%)', fontsize=10)
                ax.set_ylim(0, y_max)
                ax.axhline(y=100, color='gray', linestyle='--', alpha=0.5, label='100%基準')
                ax.legend(fontsize=9)
                ax.grid(True, alpha=0.3)
            else:
                ax.text(0.5, 0.5, '油門數據不可用', ha='center', va='center', transform=ax.transAxes, fontsize=10)
                ax.set_title('油門開度對比 (無數據)', fontsize=12)

            # 4. 檔位對比
            ax = fig_main.add_subplot(gs[1, 2:4])
            if 'nGear' in car_data1.columns and 'nGear' in car_data2.columns:
                ax.plot(car_data1['Distance'] if 'Distance' in car_data1.columns else range(len(car_data1)), 
                       car_data1['nGear'], color=color1, label=driver1, linewidth=1, alpha=0.8)
                ax.plot(car_data2['Distance'] if 'Distance' in car_data2.columns else range(len(car_data2)), 
                       car_data2['nGear'], color=color2, label=driver2, linewidth=1, alpha=0.8)
                ax.set_title('檔位對比 (Gear)', fontweight='bold', fontsize=12)
                ax.set_ylabel('檔位', fontsize=10)
                ax.set_ylim(1, 8)
                ax.set_yticks(range(1, 9))
                ax.legend(fontsize=9)
                ax.grid(True, alpha=0.3)
            else:
                ax.text(0.5, 0.5, '檔位數據不可用', ha='center', va='center', transform=ax.transAxes, fontsize=10)
                ax.set_title('檔位對比 (無數據)', fontsize=12)

            # 5. 煞車強度對比
            ax = fig_main.add_subplot(gs[2, 0:2])
            if 'Brake' in car_data1.columns and 'Brake' in car_data2.columns:
                brake1 = car_data1['Brake'] * 100
                brake2 = car_data2['Brake'] * 100
                ax.plot(car_data1['Distance'] if 'Distance' in car_data1.columns else range(len(car_data1)), 
                       brake1, color=color1, label=f'{driver1} 煞車', linewidth=1, alpha=0.8)
                ax.plot(car_data2['Distance'] if 'Distance' in car_data2.columns else range(len(car_data2)), 
                       brake2, color=color2, label=f'{driver2} 煞車', linewidth=1, alpha=0.8)
                y_max = max(105, min(150, max(brake1.max(), brake2.max()) + 10))
                ax.set_title('煞車強度對比', fontweight='bold', fontsize=12)
                ax.set_ylabel('煞車強度 (%)', fontsize=10)
                ax.set_ylim(0, y_max)
                ax.axhline(100, color='gray', linestyle='--', alpha=0.5)
                ax.legend(fontsize=9)
                ax.grid(True, alpha=0.3)
            else:
                ax.text(0.5, 0.5, '煞車數據不可用', ha='center', va='center', transform=ax.transAxes, fontsize=10)
                ax.set_title('煞車強度對比 (無數據)', fontsize=12)

            # 6. 加速度對比
            ax = fig_main.add_subplot(gs[2, 2:4])
            if 'Speed' in car_data1.columns and 'Speed' in car_data2.columns:
                distance1 = car_data1['Distance'] if 'Distance' in car_data1.columns else np.arange(len(car_data1))
                distance2 = car_data2['Distance'] if 'Distance' in car_data2.columns else np.arange(len(car_data2))
                acc1 = np.gradient(car_data1['Speed'], distance1)
                acc2 = np.gradient(car_data2['Speed'], distance2)
                ax.plot(distance1, acc1, color=color1, label=driver1, linewidth=1, alpha=0.8)
                ax.plot(distance2, acc2, color=color2, label=driver2, linewidth=1, alpha=0.8)
                ax.set_title('加速度對比', fontweight='bold', fontsize=12)
                ax.set_ylabel('加速度 (km/h per m)', fontsize=10)
                ax.axhline(0, color='black', linestyle='-', alpha=0.3)
                ax.legend(fontsize=9)
                ax.grid(True, alpha=0.3)
            else:
                ax.text(0.5, 0.5, '加速度數據不可用', ha='center', va='center', transform=ax.transAxes, fontsize=10)
                ax.set_title('加速度對比 (無數據)', fontsize=12)

            # 7-8. 速度和距離差距分析（合併到底部兩個子圖）
            if 'Speed' in car_data1.columns and 'Speed' in car_data2.columns:
                # 7. 速度差距分析
                ax = fig_main.add_subplot(gs[3, 0:2])
                
                # 使用較短的數據長度
                min_len = min(len(car_data1), len(car_data2))
                if min_len > 10:
                    distance1 = car_data1['Distance'].iloc[:min_len] if 'Distance' in car_data1.columns else np.arange(min_len)
                    distance2 = car_data2['Distance'].iloc[:min_len] if 'Distance' in car_data2.columns else np.arange(min_len)
                    speed1 = car_data1['Speed'].iloc[:min_len]
                    speed2 = car_data2['Speed'].iloc[:min_len]
                    
                    # 速度差距
                    speed_diff = speed1.values - speed2.values
                    x_axis = (distance1.values + distance2.values) / 2 if 'Distance' in car_data1.columns else np.arange(min_len)
                    
                    ax.fill_between(x_axis, 0, speed_diff, where=speed_diff >= 0, 
                                  color=color1, alpha=0.6, label=f'{driver1} 較快')
                    ax.fill_between(x_axis, 0, speed_diff, where=speed_diff < 0, 
                                  color=color2, alpha=0.6, label=f'{driver2} 較快')
                    ax.set_title('速度差距分析', fontweight='bold', fontsize=12)
                    ax.set_ylabel('速度差距 (km/h)', fontsize=10)
                    ax.set_xlabel('距離 (m)', fontsize=10)
                    ax.axhline(0, color='black', linestyle='-', alpha=0.5)
                    ax.legend(fontsize=9)
                    ax.grid(True, alpha=0.3)
                else:
                    ax.text(0.5, 0.5, '數據點不足\n無法計算速度差距', ha='center', va='center', transform=ax.transAxes, fontsize=10)
                    ax.set_title('速度差距分析 (數據不足)', fontsize=12)
                    
                # 8. 距離差距分析
                ax = fig_main.add_subplot(gs[3, 2:4])
                
                if min_len > 10 and 'Distance' in car_data1.columns and 'Distance' in car_data2.columns:
                    # 回退方法：使用Distance欄位直接計算
                    dist1 = car_data1['Distance'].iloc[:min_len].values
                    dist2 = car_data2['Distance'].iloc[:min_len].values
                    distance_gap = dist1 - dist2
                    
                    x_axis = (dist1 + dist2) / 2
                    
                    ax.fill_between(x_axis, 0, distance_gap, where=distance_gap >= 0, 
                                  color=color1, alpha=0.6, label=f'{driver1} 領先')
                    ax.fill_between(x_axis, 0, distance_gap, where=distance_gap < 0, 
                                  color=color2, alpha=0.6, label=f'{driver2} 領先')
                    ax.set_title('距離差距分析', fontweight='bold', fontsize=12)
                    ax.set_ylabel('距離差距 (m)', fontsize=10)
                    ax.set_xlabel('賽道距離 (m)', fontsize=10)
                    ax.axhline(0, color='black', linestyle='-', alpha=0.5)
                    ax.legend(fontsize=9)
                    ax.grid(True, alpha=0.3)
                    
                    # 顯示統計資訊
                    max_gap = abs(distance_gap).max()
                    ax.text(0.02, 0.98, f'最大差距: {max_gap:.1f}m', 
                           transform=ax.transAxes, fontsize=9, 
                           bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
                           verticalalignment='top')
                else:
                    ax.text(0.5, 0.5, '位置或距離數據不足\n無法計算距離差距', ha='center', va='center', transform=ax.transAxes, fontsize=10)
                    ax.set_title('距離差距分析 (數據不足)', fontsize=12)
            else:
                # 速度差距圖
                ax = fig_main.add_subplot(gs[3, 0:2])
                ax.text(0.5, 0.5, '速度數據不可用', ha='center', va='center', transform=ax.transAxes, fontsize=10)
                ax.set_title('速度差距分析 (無數據)', fontsize=12)
                
                # 距離差距圖
                ax = fig_main.add_subplot(gs[3, 2:4])
                ax.text(0.5, 0.5, '位置數據不可用', ha='center', va='center', transform=ax.transAxes, fontsize=10)
                ax.set_title('距離差距分析 (無數據)', fontsize=12)

            # FIGURE2: 賽道地圖比較 (右側)
            print(f"   🗺️  創建 FIGURE2: 賽道地圖比較...")
            self._create_track_map_subplot_replica(fig_main, gs, car_data1, car_data2, driver1, driver2, lap1, lap2, session)

            # 統一顯示
            print(f"   [TARGET] 顯示完整比較分析...")
            self._safe_show_plot()
            print(f"   [SUCCESS] FIGURE1 和 FIGURE2 已同時顯示！")

            print("[SUCCESS] 遙測比較圖和賽道地圖已顯示")
            
            # 計算並顯示一些統計數據
            print(f"\n[INFO] 遙測統計摘要:")
            print(f"[FINISH] {driver1} (圈次 {lap1['LapNumber']}):")
            if 'Speed' in car_data1.columns:
                print(f"  最高速度: {car_data1['Speed'].max():.1f} km/h")
                print(f"  平均速度: {car_data1['Speed'].mean():.1f} km/h")
            
            print(f"[FINISH] {driver2} (圈次 {lap2['LapNumber']}):")
            if 'Speed' in car_data2.columns:
                print(f"  最高速度: {car_data2['Speed'].max():.1f} km/h")
                print(f"  平均速度: {car_data2['Speed'].mean():.1f} km/h")

        except Exception as e:
            print(f"[ERROR] 遙測比較圖生成失敗: {e}")
            traceback.print_exc()

    def _create_track_map_subplot_replica(self, fig_main, gs, car_data1, car_data2, driver1, driver2, lap1, lap2, session):
        """在主圖窗中創建賽道地圖子圖 - 複製原始程式實現"""
        try:
            # 檢查是否有位置數據
            has_x1 = 'X' in car_data1.columns
            has_y1 = 'Y' in car_data1.columns
            has_x2 = 'X' in car_data2.columns
            has_y2 = 'Y' in car_data2.columns
            
            print(f"   🧭 位置數據檢查:")
            print(f"      車手1 - X: {has_x1}, Y: {has_y1}")
            print(f"      車手2 - X: {has_x2}, Y: {has_y2}")
            
            if not (has_x1 and has_y1 and has_x2 and has_y2):
                print(f"   [WARNING]  缺少位置數據，改為顯示距離-時間分析圖")
                # 創建替代的距離-時間分析圖
                ax_alt = fig_main.add_subplot(gs[0:2, 4:6])
                ax_alt.set_facecolor('white')
                
                # 繪製速度比較圖作為替代
                if 'Speed' in car_data1.columns and 'Speed' in car_data2.columns:
                    distance1 = car_data1['Distance'] if 'Distance' in car_data1.columns else range(len(car_data1))
                    distance2 = car_data2['Distance'] if 'Distance' in car_data2.columns else range(len(car_data2))
                    
                    ax_alt.plot(distance1, car_data1['Speed'], color='blue', linewidth=2, 
                               label=f'{driver1} 速度', alpha=0.8)
                    ax_alt.plot(distance2, car_data2['Speed'], color='red', linewidth=2, 
                               label=f'{driver2} 速度', alpha=0.8)
                    ax_alt.set_ylabel('速度 (km/h)', color='black')
                    ax_alt.set_xlabel('距離 (m)', color='black')
                    ax_alt.tick_params(colors='black')
                    ax_alt.set_title('速度比較分析', fontweight='bold', fontsize=14)
                    legend = ax_alt.legend(loc='best')
                    legend.get_frame().set_facecolor('white')
                    legend.get_frame().set_edgecolor('gray')
                    ax_alt.grid(True, alpha=0.3, color='gray')
                    print(f"   [STATS] 創建速度比較圖")
                else:
                    ax_alt.text(0.5, 0.5, f'[INFO] 車手數據摘要\n\n{driver1}:\n數據點: {len(car_data1)}\n\n{driver2}:\n數據點: {len(car_data2)}\n\n[WARNING] 位置數據不可用', 
                               ha='center', va='center', transform=ax_alt.transAxes, fontsize=12, color='black',
                               bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.9, edgecolor='gray'))
                    ax_alt.set_title('數據摘要', fontweight='bold', fontsize=14)
                    ax_alt.axis('off')
                    print(f"   [LIST] 創建數據摘要顯示")
                return
            
            # 創建軌道地圖子圖
            ax_analysis = fig_main.add_subplot(gs[0:2, 4:6])
            ax_analysis.set_facecolor('white')
            
            print(f"   [INFO] 準備距離差分析地圖...")
            
            # [CONFIG] 修復：使用完整賽道路徑，避免截斷18號彎到終點的部分
            len1, len2 = len(car_data1), len(car_data2)
            max_len = max(len1, len2)
            print(f"   📏 車手1數據點: {len1}, 車手2數據點: {len2}")
            print(f"   [CONFIG] 使用完整賽道路徑長度: {max_len} (避免截斷)")
            
            if max_len > 10:
                print(f"   ⚙️ 分析完整賽道路徑的 {max_len} 個數據點...")
                
                # [TARGET] 關鍵修復：使用較長的數據作為完整賽道，對較短數據進行延伸
                if len1 >= len2:
                    # 車手1數據較長，使用車手1的完整路徑
                    x1 = car_data1['X'].values
                    y1 = car_data1['Y'].values
                    x2_base = car_data2['X'].values
                    y2_base = car_data2['Y'].values
                    
                    # 延伸車手2的數據到完整長度
                    x2 = np.zeros(max_len)
                    y2 = np.zeros(max_len)
                    x2[:len2] = x2_base
                    y2[:len2] = y2_base
                    # 用最後已知位置填補剩餘部分
                    if len2 < max_len:
                        x2[len2:] = x2_base[-1]
                        y2[len2:] = y2_base[-1]
                        print(f"   ⚡ 車手2數據延伸 {max_len - len2} 個點到完整賽道")
                else:
                    # 車手2數據較長，使用車手2的完整路徑
                    x2 = car_data2['X'].values
                    y2 = car_data2['Y'].values
                    x1_base = car_data1['X'].values
                    y1_base = car_data1['Y'].values
                    
                    # 延伸車手1的數據到完整長度
                    x1 = np.zeros(max_len)
                    y1 = np.zeros(max_len)
                    x1[:len1] = x1_base
                    y1[:len1] = y1_base
                    # 用最後已知位置填補剩餘部分
                    if len1 < max_len:
                        x1[len1:] = x1_base[-1]
                        y1[len1:] = y1_base[-1]
                        print(f"   ⚡ 車手1數據延伸 {max_len - len1} 個點到完整賽道")
                
                # 使用距離數據計算距離差 - 使用完整數據
                if 'Distance' in car_data1.columns and 'Distance' in car_data2.columns:
                    print(f"   [SUCCESS] 使用 FastF1 累積距離計算 (完整賽道)")
                    if len1 >= len2:
                        # 延伸車手2的距離數據
                        dist1 = car_data1['Distance'].values
                        dist2_base = car_data2['Distance'].values
                        dist2 = np.zeros(max_len)
                        dist2[:len2] = dist2_base
                        if len2 < max_len:
                            dist2[len2:] = dist2_base[-1]  # 保持最後已知距離
                    else:
                        # 延伸車手1的距離數據
                        dist2 = car_data2['Distance'].values
                        dist1_base = car_data1['Distance'].values
                        dist1 = np.zeros(max_len)
                        dist1[:len1] = dist1_base
                        if len1 < max_len:
                            dist1[len1:] = dist1_base[-1]  # 保持最後已知距離
                    
                    distance_gap = dist1 - dist2
                else:
                    print(f"   [WARNING]  回退使用 X,Y 坐標計算距離差 (完整賽道)")
                    distance_gap = np.zeros(max_len)
                    for i in range(1, max_len):
                        dist1_segment = np.sqrt((x1[i] - x1[i-1])**2 + (y1[i] - y1[i-1])**2)
                        dist2_segment = np.sqrt((x2[i] - x2[i-1])**2 + (y2[i] - y2[i-1])**2)
                        distance_gap[i] = distance_gap[i-1] + (dist1_segment - dist2_segment)
                
                # 使用平均路線位置作為基準路線
                x_avg = (x1 + x2) / 2
                y_avg = (y1 + y2) / 2
                
                print(f"   🎨 創建分段著色地圖...")
                
                # 創建線段點對
                points = np.array([x_avg, y_avg]).T.reshape(-1, 1, 2)
                segments = np.concatenate([points[:-1], points[1:]], axis=1)
                
                # 根據距離差創建顏色數組
                colors = []
                threshold = 0.1
                
                for i in range(len(distance_gap) - 1):
                    gap_avg = (distance_gap[i] + distance_gap[i+1]) / 2
                    
                    if abs(gap_avg) < threshold:
                        colors.append('lightgreen')
                    elif gap_avg > threshold:
                        colors.append('blue')
                    else:
                        colors.append('red')
                
                # 使用 LineCollection 繪製分段著色的路線
                lc = LineCollection(segments, colors=colors, linewidths=1, alpha=0.9)
                ax_analysis.add_collection(lc)
                
                # 設定統一的賽道風格和官方彎道標記
                if hasattr(self, '_setup_unified_track_style'):
                    self._setup_unified_track_style(ax_analysis, x_avg, y_avg, session=session, enable_markers=True)
                else:
                    # 基本賽道風格設定
                    ax_analysis.set_aspect('equal')
                    ax_analysis.grid(True, alpha=0.3)
                    x_margin = (x_avg.max() - x_avg.min()) * 0.1
                    y_margin = (y_avg.max() - y_avg.min()) * 0.1
                    ax_analysis.set_xlim(x_avg.min() - x_margin, x_avg.max() + x_margin)
                    ax_analysis.set_ylim(y_avg.min() - y_margin, y_avg.max() + y_margin)
                
                print(f"   [SUCCESS] 軌道地圖已完成")
                
                # 添加圖例
                legend_elements = [
                    Line2D([0], [0], color='blue', linewidth=6, label=f'{driver1} 領先區段'),
                    Line2D([0], [0], color='red', linewidth=6, label=f'{driver2} 領先區段'),
                    Line2D([0], [0], color='lightgreen', linewidth=6, label='平手區段')
                ]
                
                ax_analysis.legend(handles=legend_elements, loc='upper right', 
                                  fontsize=10, frameon=True, fancybox=True, 
                                  framealpha=0.95, edgecolor='gray', facecolor='white')
                
                # 計算統計信息
                max_gap = np.max(np.abs(distance_gap))
                print(f"\n🗺️  賽道距離差分析結果:")
                print(f"   📏 最大距離差: {max_gap:.1f}m")
                
            else:
                ax_analysis.text(0.5, 0.5, f'數據點不足\n只有 {max_len} 個數據點\n無法生成距離差分析\n(需要至少 10 個數據點)', 
                               ha='center', va='center', transform=ax_analysis.transAxes, fontsize=14,
                               bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.9,
                                       edgecolor='gray', linewidth=2), color='black')
                ax_analysis.set_title('距離差分析 (數據不足)', fontweight='bold', fontsize=14)
                ax_analysis.axis('off')
            
            print(f"   [SUCCESS] 距離差分析地圖已完成")
            
        except Exception as e:
            print(f"[ERROR] 賽道地圖子圖創建失敗: {e}")
            traceback.print_exc()

    def _analyze_distance_gap_replica(self, session, lap1, lap2, driver1, driver2, title):
        """分析兩車之間的距離差距 - 複製原始程式"""
        try:
            print(f"\n📏 車間距離分析")
            print("-" * 40)
            
            # 獲取遙測數據
            lap1_data = session.laps[
                (session.laps['Driver'] == driver1) & 
                (session.laps['LapNumber'] == lap1['LapNumber'])
            ]
            lap2_data = session.laps[
                (session.laps['Driver'] == driver2) & 
                (session.laps['LapNumber'] == lap2['LapNumber'])
            ]
            
            if lap1_data.empty or lap2_data.empty:
                print("[ERROR] 無法獲取遙測數據")
                return
            
            # 獲取車輛數據
            car_data1, _ = self._safe_get_lap_telemetry(lap1_data)
            car_data2, _ = self._safe_get_lap_telemetry(lap2_data)
            
            if car_data1 is None or car_data2 is None:
                print("[ERROR] 無法獲取車輛遙測數據")
                return
                
            # 計算平均距離差
            if len(car_data1) > 0 and len(car_data2) > 0:
                # 找共同的距離範圍
                if 'Distance' in car_data1.columns and 'Distance' in car_data2.columns:
                    min_dist = max(car_data1['Distance'].min(), car_data2['Distance'].min())
                    max_dist = min(car_data1['Distance'].max(), car_data2['Distance'].max())
                    
                    if max_dist > min_dist:
                        # 重新採樣到相同的距離點
                        common_distances = np.linspace(min_dist, max_dist, 100)
                        
                        speed1_interp = np.interp(common_distances, car_data1['Distance'], car_data1['Speed'])
                        speed2_interp = np.interp(common_distances, car_data2['Distance'], car_data2['Speed'])
                        
                        # 計算速度差異
                        speed_diff = speed1_interp - speed2_interp
                        avg_speed_diff = np.mean(speed_diff)
                        max_speed_diff = np.max(np.abs(speed_diff))
                        
                        print(f"平均速度差異: {avg_speed_diff:+.1f} km/h")
                        print(f"最大速度差異: {max_speed_diff:.1f} km/h")
                        
                        # 估算時間和距離差異
                        if abs(avg_speed_diff) > 0.1:
                            faster_driver = driver1 if avg_speed_diff > 0 else driver2
                            print(f"整體較快: {faster_driver}")
                        
                        # 分析關鍵區段
                        self._analyze_sector_performance_replica(common_distances, speed1_interp, speed2_interp, driver1, driver2)
                        
                    else:
                        print("[ERROR] 遙測數據範圍不匹配")
                else:
                    print("[ERROR] 缺少距離數據")
            else:
                print("[ERROR] 遙測數據為空")
                
        except Exception as e:
            print(f"[ERROR] 距離分析失敗: {e}")

    def _analyze_sector_performance_replica(self, distances, speed1, speed2, driver1, driver2):
        """分析區段表現 - 複製原始程式"""
        try:
            # 將賽道分為3個區段
            sector_size = len(distances) // 3
            sectors = [
                (0, sector_size, "第一區段"),
                (sector_size, sector_size * 2, "第二區段"),
                (sector_size * 2, len(distances), "第三區段")
            ]
            
            print(f"\n📍 區段表現分析:")
            for start_idx, end_idx, sector_name in sectors:
                sector_speed1 = speed1[start_idx:end_idx]
                sector_speed2 = speed2[start_idx:end_idx]
                
                avg_diff = np.mean(sector_speed1 - sector_speed2)
                if abs(avg_diff) > 0.5:
                    faster = driver1 if avg_diff > 0 else driver2
                    print(f"   {sector_name}: {faster} 較快 {abs(avg_diff):.1f} km/h")
                else:
                    print(f"   {sector_name}: 勢均力敵")
                    
        except Exception as e:
            print(f"[WARNING] 區段分析失敗: {e}")

    def _safe_get_lap_telemetry(self, lap_data):
        """安全獲取圈次遙測數據"""
        try:
            if lap_data.empty:
                return None, "圈次數據為空"
            
            lap_row = lap_data.iloc[0]
            
            if not hasattr(lap_row, 'get_car_data'):
                return None, "圈次資料缺少 get_car_data 方法"
            
            car_data = lap_row.get_car_data()
            
            if car_data is None or car_data.empty:
                return None, "車輛遙測數據為空"
            
            # 嘗試添加距離和位置數據
            try:
                car_data = car_data.add_distance()
            except Exception as e:
                print(f"[WARNING] 距離數據添加失敗: {e}")
            
            # 嘗試添加位置數據
            if 'X' not in car_data.columns or 'Y' not in car_data.columns:
                try:
                    if hasattr(lap_row, 'get_pos_data'):
                        pos_data = lap_row.get_pos_data()
                        if not pos_data.empty and 'X' in pos_data.columns and 'Y' in pos_data.columns:
                            car_data = car_data.merge(pos_data[['X', 'Y']], left_index=True, right_index=True, how='left')
                except Exception as e:
                    print(f"[WARNING] 位置數據合併失敗: {e}")
            
            return car_data, None
            
        except Exception as e:
            return None, f"遙測數據獲取異常: {e}"

    def _safe_show_plot(self):
        """安全顯示圖表"""
        try:
            plt.tight_layout()
            # plt.show()  # 圖表顯示已禁用
            print("[INFO] 圖表生成已完成（顯示已禁用）")
        except Exception as e:
            print(f"[WARNING] 圖表生成失敗: {e}")
    
    def _setup_unified_track_style(self, ax, x_coords, y_coords, session=None, enable_markers=True):
        """設定統一的賽道風格和官方彎道標記"""
        try:
            # 基本賽道風格設定
            ax.set_aspect('equal')
            ax.grid(True, alpha=0.3)
            
            # 設定坐標軸範圍
            x_margin = (x_coords.max() - x_coords.min()) * 0.1
            y_margin = (y_coords.max() - y_coords.min()) * 0.1
            ax.set_xlim(x_coords.min() - x_margin, x_coords.max() + x_margin)
            ax.set_ylim(y_coords.min() - y_margin, y_coords.max() + y_margin)
            
            # 設定標籤
            ax.set_xlabel('X 坐標 (m)', fontsize=10)
            ax.set_ylabel('Y 坐標 (m)', fontsize=10)
            ax.set_title('賽道距離差分析', fontweight='bold', fontsize=14)
            
            # 基本軌道風格
            ax.tick_params(colors='black')
            ax.spines['bottom'].set_color('black')
            ax.spines['top'].set_color('black')
            ax.spines['right'].set_color('black')
            ax.spines['left'].set_color('black')
            
        except Exception as e:
            print(f"[WARNING] 賽道風格設定失敗: {e}")

    def _format_time(self, time_value):
        """格式化時間顯示"""
        if pd.isna(time_value):
            return "N/A"
        
        try:
            if hasattr(time_value, 'total_seconds'):
                total_seconds = time_value.total_seconds()
                minutes = int(total_seconds // 60)
                seconds = total_seconds % 60
                return f"{minutes}:{seconds:06.3f}"
            else:
                return str(time_value)
        except:
            return "N/A"


def run_driver_comparison_analysis(data_loader=None, f1_analysis_instance=None):
    """模組入口函數 - 獨立運行雙車手比較分析"""
    if data_loader is None:
        from .base import initialize_data_loader
        data_loader = initialize_data_loader()
        if data_loader is None:
            return
    
    analyzer = DriverComparisonAdvanced(data_loader, f1_analysis_instance)
    analyzer.run_driver_comparison_analysis()

def run_driver_comparison_json(data_loader, f1_analysis_instance=None, enable_debug=False, driver1=None, driver2=None, lap1=None, lap2=None, show_detailed_output=True):
    """執行車手對比分析並返回JSON結果 - Function 15 標準
    
    Args:
        data_loader: 數據載入器
        f1_analysis_instance: F1分析實例
        enable_debug: 是否啟用調試模式
        driver1: 第一位車手代碼，如果為None則自動選擇前兩位車手
        driver2: 第二位車手代碼
        lap1: 第一位車手的特定圈數，如果為None則使用最快圈
        lap2: 第二位車手的特定圈數，如果為None則使用最快圈
        show_detailed_output: 是否顯示詳細輸出（即使使用緩存也顯示完整表格）
        
    Returns:
        dict: 包含成功狀態、數據、緩存狀態和緩存鍵的標準化返回格式
    """
    try:
        from datetime import datetime
        import pandas as pd
        import numpy as np
        import os
        import pickle
        import hashlib
        
        print("🚀 開始執行車手對比分析...")
        
        # 生成緩存鍵值
        cache_params = {
            'function': 'driver_comparison',
            'year': data_loader.year if hasattr(data_loader, 'year') else None,
            'race': data_loader.race if hasattr(data_loader, 'race') else None,
            'session': data_loader.session if hasattr(data_loader, 'session') else None,
            'driver1': driver1,
            'driver2': driver2,
            'lap1': lap1,
            'lap2': lap2
        }
        cache_key = f"driver_comparison_{hashlib.md5(str(cache_params).encode()).hexdigest()}"
        cache_path = os.path.join("cache", f"{cache_key}.pkl")
        
        # 檢查緩存
        cache_used = False
        if os.path.exists(cache_path):
            print("📦 發現緩存數據...")
            try:
                with open(cache_path, 'rb') as f:
                    cached_result = pickle.load(f)
                    
                if not show_detailed_output:
                    print("📦 使用緩存數據")
                    return {
                        "success": True,
                        "data": cached_result,
                        "cache_used": True,
                        "cache_key": cache_key,
                        "function_id": 13,
                        "timestamp": datetime.now().isoformat()
                    }
                elif show_detailed_output:
                    print("📦 使用緩存數據 + 📊 顯示詳細分析結果")
                    # 顯示詳細輸出
                    if 'driver_comparison' in cached_result:
                        comparison_analysis = cached_result['driver_comparison']
                        # 從metadata中獲取車手信息
                        metadata = cached_result.get('metadata', {})
                        driver1_name = metadata.get('driver1', driver1 or 'Driver1')
                        driver2_name = metadata.get('driver2', driver2 or 'Driver2')
                        
                        _display_driver_comparison_detailed_results(comparison_analysis, driver1_name, driver2_name)
                        
                        # 即使使用緩存，也保存JSON以顯示最新路徑 - 符合開發核心要求
                        _save_driver_comparison_json(cached_result, driver1_name, driver2_name)
                    else:
                        _display_cached_detailed_output_driver_comparison(cached_result)
                        
                        # 嘗試從緩存數據中提取車手信息進行JSON保存
                        try:
                            metadata = cached_result.get('metadata', {})
                            d1 = metadata.get('driver1', driver1 or 'Driver1')
                            d2 = metadata.get('driver2', driver2 or 'Driver2')
                            _save_driver_comparison_json(cached_result, d1, d2)
                        except Exception as e:
                            print(f"⚠️ JSON保存失敗: {e}")
                    
                    return {
                        "success": True,
                        "data": cached_result,
                        "cache_used": True,
                        "cache_key": cache_key,
                        "function_id": 13,
                        "timestamp": datetime.now().isoformat()
                    }
            except Exception as e:
                print(f"⚠️ 緩存讀取失敗，重新計算: {e}")
        
        print("🔄 重新計算 - 開始數據分析...")
        
        if enable_debug:
            print("[DEBUG] 開始執行車手對比分析 (JSON版)...")
        
        # 獲取已載入的數據
        data = data_loader.get_loaded_data()
        if not data:
            return {
                "success": False,
                "message": "沒有可用的數據，請先載入數據",
                "data": None,
                "cache_used": False,
                "cache_key": cache_key,
                "function_id": 13,
                "timestamp": datetime.now().isoformat()
            }
        
        laps = data['laps']
        session = data['session']
        drivers_info = data.get('drivers_info', {})
        
        # 獲取可用車手
        available_drivers = sorted(laps['Driver'].unique())
        if len(available_drivers) < 2:
            return {
                "success": False,
                "message": "需要至少兩位車手的數據才能進行比較",
                "data": None,
                "timestamp": datetime.now().isoformat()
            }
        
        # 選擇車手
        if not driver1 or not driver2:
            # 自動選擇前兩位車手
            selected_driver1 = available_drivers[0]
            selected_driver2 = available_drivers[1]
        else:
            if driver1 not in available_drivers:
                return {
                    "success": False,
                    "message": f"指定的車手 '{driver1}' 不在可用車手列表中",
                    "data": None,
                    "timestamp": datetime.now().isoformat()
                }
            if driver2 not in available_drivers:
                return {
                    "success": False,
                    "message": f"指定的車手 '{driver2}' 不在可用車手列表中",
                    "data": None,
                    "timestamp": datetime.now().isoformat()
                }
            selected_driver1 = driver1
            selected_driver2 = driver2
        
        if enable_debug:
            print(f"[INFO] 比較車手: {selected_driver1} vs {selected_driver2}")
        
        # 獲取車手圈速數據
        driver1_laps = laps[laps['Driver'] == selected_driver1].copy()
        driver2_laps = laps[laps['Driver'] == selected_driver2].copy()
        
        if driver1_laps.empty or driver2_laps.empty:
            return {
                "success": False,
                "message": f"車手 {selected_driver1} 或 {selected_driver2} 沒有圈速數據",
                "data": None,
                "timestamp": datetime.now().isoformat()
            }
        
        # 選擇比較的圈次
        def get_comparison_lap(driver_laps, lap_num=None):
            valid_laps = driver_laps[driver_laps['LapTime'].notna()]
            if valid_laps.empty:
                return None
            
            if lap_num is not None:
                specific_lap = valid_laps[valid_laps['LapNumber'] == lap_num]
                if not specific_lap.empty:
                    return specific_lap.iloc[0]
            
            # 默認選擇最快圈
            return valid_laps.loc[valid_laps['LapTime'].idxmin()]
        
        lap_data1 = get_comparison_lap(driver1_laps, lap1)
        lap_data2 = get_comparison_lap(driver2_laps, lap2)
        
        if lap_data1 is None or lap_data2 is None:
            return {
                "success": False,
                "message": "無法獲取比較的圈次數據",
                "data": None,
                "timestamp": datetime.now().isoformat()
            }
        
        # 構建比較分析結果
        comparison_analysis = {
            "driver_comparison": {
                "driver1": {
                    "driver_code": selected_driver1,
                    "lap_number": int(lap_data1['LapNumber']),
                    "lap_time": _format_comparison_time(lap_data1['LapTime']),
                    "lap_time_seconds": lap_data1['LapTime'].total_seconds() if pd.notna(lap_data1['LapTime']) else None
                },
                "driver2": {
                    "driver_code": selected_driver2,
                    "lap_number": int(lap_data2['LapNumber']),
                    "lap_time": _format_comparison_time(lap_data2['LapTime']),
                    "lap_time_seconds": lap_data2['LapTime'].total_seconds() if pd.notna(lap_data2['LapTime']) else None
                }
            },
            "performance_comparison": {},
            "telemetry_comparison": {},
            "summary": {}
        }
        
        # 圈速比較
        if pd.notna(lap_data1['LapTime']) and pd.notna(lap_data2['LapTime']):
            time1_seconds = lap_data1['LapTime'].total_seconds()
            time2_seconds = lap_data2['LapTime'].total_seconds()
            time_diff = abs(time1_seconds - time2_seconds)
            faster_driver = selected_driver1 if time1_seconds < time2_seconds else selected_driver2
            
            comparison_analysis["performance_comparison"]["lap_time"] = {
                "faster_driver": faster_driver,
                "time_difference": f"{time_diff:.3f}s",
                "time_difference_seconds": time_diff
            }
        
        # 最高速度比較
        speed1 = lap_data1.get('SpeedFL')
        speed2 = lap_data2.get('SpeedFL')
        if pd.notna(speed1) and pd.notna(speed2):
            speed_diff = abs(speed1 - speed2)
            faster_speed_driver = selected_driver1 if speed1 > speed2 else selected_driver2
            
            comparison_analysis["performance_comparison"]["max_speed"] = {
                "driver1_speed": f"{speed1:.1f} km/h",
                "driver2_speed": f"{speed2:.1f} km/h",
                "faster_driver": faster_speed_driver,
                "speed_difference": f"{speed_diff:.1f} km/h"
            }
        
        # 區間時間比較
        sector_comparison = {}
        for sector_num, sector_col in enumerate([('Sector1Time', '第一區間'), ('Sector2Time', '第二區間'), ('Sector3Time', '第三區間')], 1):
            sector_field, sector_name = sector_col
            s1 = lap_data1.get(sector_field)
            s2 = lap_data2.get(sector_field)
            
            if pd.notna(s1) and pd.notna(s2):
                if hasattr(s1, 'total_seconds') and hasattr(s2, 'total_seconds'):
                    s1_seconds = s1.total_seconds()
                    s2_seconds = s2.total_seconds()
                    sector_diff = abs(s1_seconds - s2_seconds)
                    faster_sector_driver = selected_driver1 if s1_seconds < s2_seconds else selected_driver2
                    
                    sector_comparison[f"sector_{sector_num}"] = {
                        "sector_name": sector_name,
                        "driver1_time": _format_comparison_time(s1),
                        "driver2_time": _format_comparison_time(s2),
                        "faster_driver": faster_sector_driver,
                        "time_difference": f"{sector_diff:.3f}s"
                    }
        
        comparison_analysis["performance_comparison"]["sector_times"] = sector_comparison
        
        # 輪胎比較
        compound1 = lap_data1.get('Compound', 'N/A')
        compound2 = lap_data2.get('Compound', 'N/A')
        age1 = lap_data1.get('TyreLife', 'N/A')
        age2 = lap_data2.get('TyreLife', 'N/A')
        
        comparison_analysis["performance_comparison"]["tire_data"] = {
            "driver1_tire": f"{compound1} ({age1}圈)" if age1 != 'N/A' else f"{compound1}",
            "driver2_tire": f"{compound2} ({age2}圈)" if age2 != 'N/A' else f"{compound2}"
        }
        
        # 遙測數據分析（簡化版本）
        try:
            # 嘗試獲取遙測數據進行基本分析
            lap1_data_query = session.laps[
                (session.laps['Driver'] == selected_driver1) &
                (session.laps['LapNumber'] == lap_data1['LapNumber'])
            ]
            lap2_data_query = session.laps[
                (session.laps['Driver'] == selected_driver2) &
                (session.laps['LapNumber'] == lap_data2['LapNumber'])
            ]
            
            if not lap1_data_query.empty and not lap2_data_query.empty:
                comparison_analysis["telemetry_comparison"]["telemetry_available"] = True
                comparison_analysis["telemetry_comparison"]["note"] = "遙測數據可用，但API版本僅提供基本統計"
            else:
                comparison_analysis["telemetry_comparison"]["telemetry_available"] = False
                comparison_analysis["telemetry_comparison"]["note"] = "遙測數據不可用"
        except Exception as e:
            comparison_analysis["telemetry_comparison"]["telemetry_available"] = False
            comparison_analysis["telemetry_comparison"]["error"] = str(e)
        
        # 生成總結
        if "lap_time" in comparison_analysis["performance_comparison"]:
            faster_overall = comparison_analysis["performance_comparison"]["lap_time"]["faster_driver"]
            time_gap = comparison_analysis["performance_comparison"]["lap_time"]["time_difference"]
            comparison_analysis["summary"]["overall_faster"] = faster_overall
            comparison_analysis["summary"]["overall_time_gap"] = time_gap
            
            if faster_overall == selected_driver1:
                comparison_analysis["summary"]["result"] = f"{selected_driver1} 比 {selected_driver2} 快 {time_gap}"
            else:
                comparison_analysis["summary"]["result"] = f"{selected_driver2} 比 {selected_driver1} 快 {time_gap}"
        else:
            comparison_analysis["summary"]["result"] = "無法確定整體表現差異"
        
        # 創建metadata
        metadata = {
            "analysis_type": "driver_comparison_analysis",
            "function_name": "Driver Comparison Analysis",
            "generated_at": datetime.now().isoformat(),
            "version": "1.0",
            "comparison_type": "same_driver" if selected_driver1 == selected_driver2 else "different_drivers"
        }
        
        # 構建最終結果
        result_data = {
            "metadata": metadata,
            "driver_comparison": comparison_analysis
        }
        
        # Function 15 標準格式結果
        result = {
            "success": True,
            "data": result_data,
            "cache_used": cache_used,
            "cache_key": cache_key,
            "function_id": 13,
            "message": f"成功完成 {selected_driver1} vs {selected_driver2} 的對比分析",
            "timestamp": datetime.now().isoformat()
        }
        
        # 保存緩存
        try:
            os.makedirs("cache", exist_ok=True)
            with open(cache_path, 'wb') as f:
                pickle.dump(result_data, f)
            print("💾 分析結果已緩存")
        except Exception as e:
            print(f"⚠️ 緩存保存失敗: {e}")
        
        # 顯示詳細比較結果表格
        _display_driver_comparison_detailed_results(comparison_analysis, selected_driver1, selected_driver2)
        
        # 保存JSON結果 - 符合開發核心要求
        _save_driver_comparison_json(result_data, selected_driver1, selected_driver2)
        
        # 顯示結果反饋
        _report_driver_comparison_results(result_data)
        
        if enable_debug:
            print(f"[SUCCESS] 車手對比分析完成: {selected_driver1} vs {selected_driver2}")
        
        return result
        
    except Exception as e:
        if enable_debug:
            print(f"[ERROR] 車手對比分析失敗: {e}")
            import traceback
            traceback.print_exc()
        
        return {
            "success": False,
            "message": f"執行車手對比分析時發生錯誤: {str(e)}",
            "data": None,
            "cache_used": False,
            "cache_key": "",
            "function_id": 13,
            "timestamp": datetime.now().isoformat()
        }

def _format_comparison_time(time_value):
    """格式化時間顯示用於比較分析"""
    if pd.isna(time_value):
        return "N/A"
    
    try:
        if hasattr(time_value, 'total_seconds'):
            total_seconds = time_value.total_seconds()
            minutes = int(total_seconds // 60)
            seconds = total_seconds % 60
            return f"{minutes}:{seconds:06.3f}"
        else:
            return str(time_value)
    except:
        return "N/A"

def _display_cached_detailed_output_driver_comparison(cached_result):
    """顯示車手對比分析的詳細緩存輸出"""
    try:
        from prettytable import PrettyTable
        
        print("\n" + "="*80)
        print("📊 車手對比分析詳細結果 (使用緩存數據)")
        print("="*80)
        
        if not cached_result or 'driver_comparison' not in cached_result:
            print("❌ 緩存數據格式錯誤")
            return
            
        comparison_data = cached_result['driver_comparison']
        
        # 顯示基本信息
        if 'basic_info' in comparison_data:
            basic_info = comparison_data['basic_info']
            print("\n📋 基本信息:")
            info_table = PrettyTable()
            info_table.field_names = ["項目", "車手1", "車手2"]
            info_table.add_row(["車手", basic_info.get('driver1', 'N/A'), basic_info.get('driver2', 'N/A')])
            info_table.add_row(["比較圈數", basic_info.get('lap1', 'N/A'), basic_info.get('lap2', 'N/A')])
            print(info_table)
        
        # 顯示圈速比較
        if 'lap_times' in comparison_data:
            lap_times = comparison_data['lap_times']
            print("\n⏱️ 圈速比較:")
            lap_table = PrettyTable()
            lap_table.field_names = ["車手", "圈速", "差距"]
            for driver, time_data in lap_times.items():
                lap_table.add_row([
                    driver,
                    time_data.get('lap_time', 'N/A'),
                    time_data.get('gap', 'N/A')
                ])
            print(lap_table)
        
        # 顯示區間分析
        if 'sector_analysis' in comparison_data:
            sector_data = comparison_data['sector_analysis']
            print("\n🏁 區間分析:")
            sector_table = PrettyTable()
            sector_table.field_names = ["區間", "車手1", "車手2", "差距"]
            for i in range(1, 4):
                sector_key = f'sector_{i}'
                if sector_key in sector_data:
                    sector_info = sector_data[sector_key]
                    sector_table.add_row([
                        f"第{i}區間",
                        sector_info.get('driver1_time', 'N/A'),
                        sector_info.get('driver2_time', 'N/A'),
                        sector_info.get('difference', 'N/A')
                    ])
            print(sector_table)
        
        # 顯示摘要
        if 'summary' in comparison_data:
            summary = comparison_data['summary']
            print(f"\n📊 分析摘要:")
            print(f"   • {summary.get('result', '無結果')}")
            if 'overall_time_gap' in summary:
                print(f"   • 整體時間差距: {summary['overall_time_gap']}")
        
    except Exception as e:
        print(f"⚠️ 顯示詳細輸出時發生錯誤: {e}")

def _report_driver_comparison_results(data):
    """報告車手對比分析結果狀態"""
    if not data:
        print("❌ 車手對比分析失敗：無可用數據")
        return False
    
    try:
        print("📊 車手對比分析結果摘要：")
        
        # 檢查基本信息
        if 'driver_comparison' in data:
            comparison_data = data['driver_comparison']
            
            if 'basic_info' in comparison_data:
                basic_info = comparison_data['basic_info']
                print(f"   • 比較車手: {basic_info.get('driver1', 'N/A')} vs {basic_info.get('driver2', 'N/A')}")
                print(f"   • 比較圈數: {basic_info.get('lap1', 'N/A')} vs {basic_info.get('lap2', 'N/A')}")
            
            # 檢查數據完整性
            data_sections = ['lap_times', 'sector_analysis', 'telemetry_comparison']
            available_sections = [section for section in data_sections if section in comparison_data]
            print(f"   • 數據完整性: {len(available_sections)}/{len(data_sections)} 個區塊")
            
            if 'summary' in comparison_data:
                summary = comparison_data['summary']
                print(f"   • 分析結果: {summary.get('result', '無結果')}")
        
        print("✅ 車手對比分析完成！")
        return True
        
    except Exception as e:
        print(f"❌ 結果報告生成失敗: {e}")
        return False

def _display_driver_comparison_detailed_results(comparison_analysis, driver1, driver2):
    """顯示車手對比分析的詳細結果表格 - 符合開發核心要求"""
    try:
        from prettytable import PrettyTable
        
        print("\n" + "="*80)
        print(f"📊 車手對比分析詳細結果: {driver1} vs {driver2}")
        print("="*80)
        
        # 基本信息表格
        if 'basic_info' in comparison_analysis:
            basic_info = comparison_analysis['basic_info']
            print("\n📋 基本比較信息:")
            basic_table = PrettyTable()
            basic_table.field_names = ["項目", driver1, driver2]
            basic_table.add_row(["比較圈數", basic_info.get('lap1', 'N/A'), basic_info.get('lap2', 'N/A')])
            print(basic_table)
        
        # 圈速比較表格
        if 'lap_times' in comparison_analysis:
            lap_times = comparison_analysis['lap_times']
            print("\n⏱️ 圈速對比:")
            lap_table = PrettyTable()
            lap_table.field_names = ["車手", "圈速", "差距", "表現"]
            
            for driver, time_data in lap_times.items():
                gap = time_data.get('gap', 'N/A')
                performance = "較快" if gap and gap.startswith('+') else "較慢" if gap and gap.startswith('-') else "基準"
                lap_table.add_row([
                    driver,
                    time_data.get('lap_time', 'N/A'),
                    gap,
                    performance
                ])
            print(lap_table)
        
        # 區間分析表格
        if 'sector_analysis' in comparison_analysis:
            sector_data = comparison_analysis['sector_analysis']
            print("\n🏁 區間對比分析:")
            sector_table = PrettyTable()
            sector_table.field_names = ["區間", driver1, driver2, "差距", "優勢車手"]
            
            for i in range(1, 4):
                sector_key = f'sector_{i}'
                if sector_key in sector_data:
                    sector_info = sector_data[sector_key]
                    difference = sector_info.get('difference', 'N/A')
                    
                    # 判斷優勢車手
                    if difference != 'N/A':
                        if difference.startswith('+'):
                            advantage = driver2
                        elif difference.startswith('-'):
                            advantage = driver1
                        else:
                            advantage = "相等"
                    else:
                        advantage = "無數據"
                    
                    sector_table.add_row([
                        f"第{i}區間",
                        sector_info.get('driver1_time', 'N/A'),
                        sector_info.get('driver2_time', 'N/A'),
                        difference,
                        advantage
                    ])
            print(sector_table)
        
        # 遙測比較表格 - 修復顯示完整比較項目
        if 'performance_comparison' in comparison_analysis:
            performance_data = comparison_analysis['performance_comparison']
            print("\n📈 遙測數據對比:")
            telemetry_table = PrettyTable()
            telemetry_table.field_names = ["項目", driver1, driver2, "較快者", "差距"]
            
            # 圈速比較
            if 'lap_time' in performance_data:
                lap_data = performance_data['lap_time']
                driver1_lap = comparison_analysis.get('driver_comparison', {}).get('driver1', {})
                driver2_lap = comparison_analysis.get('driver_comparison', {}).get('driver2', {})
                
                telemetry_table.add_row([
                    "圈速",
                    driver1_lap.get('lap_time', 'N/A'),
                    driver2_lap.get('lap_time', 'N/A'),
                    lap_data.get('faster_driver', 'N/A'),
                    lap_data.get('time_difference', 'N/A')
                ])
            
            # 最高速比較
            if 'max_speed' in performance_data:
                speed_data = performance_data['max_speed']
                telemetry_table.add_row([
                    "最高速",
                    speed_data.get('driver1_speed', 'N/A'),
                    speed_data.get('driver2_speed', 'N/A'),
                    speed_data.get('faster_driver', 'N/A'),
                    speed_data.get('speed_difference', 'N/A')
                ])
            
            # 區間時間比較
            if 'sector_times' in performance_data:
                sector_data = performance_data['sector_times']
                
                # I1時間
                if 'sector_1' in sector_data:
                    s1 = sector_data['sector_1']
                    telemetry_table.add_row([
                        "I1時間",
                        s1.get('driver1_time', 'N/A'),
                        s1.get('driver2_time', 'N/A'),
                        s1.get('faster_driver', 'N/A'),
                        s1.get('time_difference', 'N/A')
                    ])
                
                # I2時間
                if 'sector_2' in sector_data:
                    s2 = sector_data['sector_2']
                    telemetry_table.add_row([
                        "I2時間",
                        s2.get('driver1_time', 'N/A'),
                        s2.get('driver2_time', 'N/A'),
                        s2.get('faster_driver', 'N/A'),
                        s2.get('time_difference', 'N/A')
                    ])
                
                # I3時間
                if 'sector_3' in sector_data:
                    s3 = sector_data['sector_3']
                    telemetry_table.add_row([
                        "I3時間",
                        s3.get('driver1_time', 'N/A'),
                        s3.get('driver2_time', 'N/A'),
                        s3.get('faster_driver', 'N/A'),
                        s3.get('time_difference', 'N/A')
                    ])
            
            # 輪胎比較
            if 'tire_data' in performance_data:
                tire_data = performance_data['tire_data']
                telemetry_table.add_row([
                    "輪胎(壽命)",
                    tire_data.get('driver1_tire', 'N/A'),
                    tire_data.get('driver2_tire', 'N/A'),
                    "-",
                    "-"
                ])
            
            print(telemetry_table)
        
        # 如果沒有performance_comparison，則檢查舊版本的telemetry_comparison
        elif 'telemetry_comparison' in comparison_analysis:
            telemetry_data = comparison_analysis['telemetry_comparison']
            print("\n📈 遙測數據對比:")
            telemetry_table = PrettyTable()
            telemetry_table.field_names = ["遙測項目", driver1, driver2, "差異", "說明"]
            
            telemetry_items = ['speed', 'throttle', 'brake', 'drs']
            for item in telemetry_items:
                if item in telemetry_data:
                    item_data = telemetry_data[item]
                    telemetry_table.add_row([
                        item.upper(),
                        item_data.get('driver1_avg', 'N/A'),
                        item_data.get('driver2_avg', 'N/A'),
                        item_data.get('difference', 'N/A'),
                        item_data.get('analysis', 'N/A')
                    ])
            print(telemetry_table)
        
        # 總結表格
        if 'summary' in comparison_analysis:
            summary = comparison_analysis['summary']
            print("\n📊 對比分析總結:")
            summary_table = PrettyTable()
            summary_table.field_names = ["分析項目", "結果"]
            summary_table.add_row(["整體表現", summary.get('result', 'N/A')])
            summary_table.add_row(["時間差距", summary.get('overall_time_gap', 'N/A')])
            summary_table.add_row(["優勢車手", summary.get('faster_driver', 'N/A')])
            print(summary_table)
        
        print("\n✅ 詳細結果顯示完成")
        
    except Exception as e:
        print(f"⚠️ 詳細結果顯示失敗: {e}")

def _save_driver_comparison_json(result_data, driver1, driver2):
    """保存車手對比分析的JSON結果 - 符合開發核心要求"""
    try:
        import json
        from datetime import datetime
        
        # 創建json目錄
        json_dir = "json"
        os.makedirs(json_dir, exist_ok=True)
        
        # 準備JSON數據
        json_data = {
            "function_id": 13,
            "function_name": "Driver Comparison Analysis",
            "analysis_type": "driver_comparison",
            "comparison_drivers": f"{driver1}_vs_{driver2}",
            "timestamp": datetime.now().isoformat(),
            "data": result_data
        }
        
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"driver_comparison_{driver1}_vs_{driver2}_{timestamp}.json"
        filepath = os.path.join(json_dir, filename)
        
        # 保存JSON文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 JSON結果已保存到: file:///{os.path.abspath(filepath)}")
        print(f"📄 文件名: {filename}")
        
    except Exception as e:
        print(f"⚠️ JSON保存失敗: {e}")

if __name__ == "__main__":
    run_driver_comparison_analysis()
