"""
雙車手遙測比較分析模組 - Two Driver Telemetry Comparison Analysis

仿照功能26進行雙車手的遙測參數比較，包括:
- 雙車手速度 vs 距離比較
- 雙車手RPM vs 距離        # 4. 顯示詳細分析結果（如果需要）
        if show_detailed_output and result:
            self._display_detailed_telemetry_tables(result)
        
        # 5. 結果驗證和反饋
        if not self._report_analysis_results(result, "雙車手遙測比較分析"):
            return None
        
        # 6. 保存緩存
        if self.cache_enabled and result:
            self._save_cache(result, cache_key)
            print("💾 分析結果已緩存")
        
        return result手煞車 vs 距離比較
- 雙車手檔位 vs 距離比較
- 雙車手油門開度 vs 距離比較
- 雙車手加速度變化 vs 距離比較
- 速度差 vs 距離分析
- 賽道累積距離差 vs 距離分析
"""

import os
import json
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from prettytable import PrettyTable
from .base import initialize_data_loader

# 設置中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

class TwoDriverTelemetryComparison:
    def __init__(self, data_loader=None, year=None, race=None, session='R'):
        self.data_loader = initialize_data_loader(data_loader)
        self.year = year
        self.race = race
        self.session = session
        self.cache_enabled = True
        
    def analyze(self, driver1, driver2, lap_number=1, lap1=None, lap2=None, lap_number1=None, lap_number2=None, file_lap1=None, file_lap2=None, show_detailed_output=True, **kwargs):
        """主要分析方法 - 比較兩位車手的指定圈數遙測數據"""
        
        # 優先使用新的lap_number1, lap_number2參數
        if lap_number1 is not None and lap_number2 is not None:
            actual_lap1 = lap_number1
            actual_lap2 = lap_number2
            print(f"🚀 開始執行雙車手遙測比較分析...")
            print(f"   • 車手1: {driver1} (第{actual_lap1}圈)")
            print(f"   • 車手2: {driver2} (第{actual_lap2}圈)")
            print(f"   • 比較模式: 不同圈數比較")
        # 支援舊的雙圈數參數
        elif lap1 is not None and lap2 is not None:
            actual_lap1 = lap1
            actual_lap2 = lap2
            print(f"🚀 開始執行雙車手遙測比較分析...")
            print(f"   • 車手1: {driver1} (第{actual_lap1}圈)")
            print(f"   • 車手2: {driver2} (第{actual_lap2}圈)")
            print(f"   • 比較模式: 不同圈數比較")
        else:
            actual_lap1 = lap_number
            actual_lap2 = lap_number
            print(f"🚀 開始執行雙車手遙測比較分析...")
            print(f"   • 車手1: {driver1}")
            print(f"   • 車手2: {driver2}")
            print(f"   • 指定圈數: {lap_number}")
        
        # 設定檔案命名用的圈數
        display_lap1 = file_lap1 if file_lap1 is not None else actual_lap1
        display_lap2 = file_lap2 if file_lap2 is not None else actual_lap2
        
        # 1. 檢查緩存 (使用雙圈數的緩存鍵)
        cache_key = self._generate_cache_key(driver1, driver2, actual_lap1, actual_lap2, **kwargs)
        if self.cache_enabled:
            cached_result = self._check_cache(cache_key)
            if cached_result:
                if show_detailed_output:
                    print("📦 使用緩存數據 + 📊 顯示詳細分析結果")
                    self._display_detailed_telemetry_tables(cached_result)
                else:
                    print("📦 使用緩存數據")
                
                # 保存JSON結果（即使是緩存數據也要保存）
                self._save_json_result(cached_result, driver1, driver2, display_lap1, display_lap2)
                
                # 結果驗證和反饋
                self._report_analysis_results(cached_result, "雙車手遙測比較分析")
                return cached_result
        
        print("🔄 重新計算 - 開始遙測數據分析...")
        
        # 2. 檢查數據載入器
        if not hasattr(self.data_loader, 'session') or self.data_loader.session is None:
            print("❌ 無法獲取會話數據，數據載入器未正確初始化")
            return None
        
        # 3. 獲取會話和圈速數據
        session = self.data_loader.session
        if not hasattr(self.data_loader, 'laps') or self.data_loader.laps is None:
            print("❌ 無法獲取圈速數據")
            return None
        
        # 4. 獲取兩位車手的數據
        driver1_data = self.data_loader.laps.pick_driver(driver1)
        driver2_data = self.data_loader.laps.pick_driver(driver2)
        
        if driver1_data.empty:
            print(f"❌ 找不到車手 {driver1} 的數據")
            return None
        
        if driver2_data.empty:
            print(f"❌ 找不到車手 {driver2} 的數據")
            return None
        
        # 4.5 處理最速圈邏輯
        if actual_lap1 is None:
            # 選擇車手1的最速圈
            valid_laps1 = driver1_data[driver1_data['LapTime'].notna()]
            if not valid_laps1.empty:
                fastest_lap1 = valid_laps1.loc[valid_laps1['LapTime'].idxmin()]
                actual_lap1 = fastest_lap1['LapNumber']
                print(f"🏃 車手 {driver1} 最速圈: 第 {actual_lap1} 圈 (時間: {fastest_lap1['LapTime']})")
            else:
                print(f"❌ 車手 {driver1} 沒有有效的圈速數據")
                return None
        
        if actual_lap2 is None:
            # 選擇車手2的最速圈
            valid_laps2 = driver2_data[driver2_data['LapTime'].notna()]
            if not valid_laps2.empty:
                fastest_lap2 = valid_laps2.loc[valid_laps2['LapTime'].idxmin()]
                actual_lap2 = fastest_lap2['LapNumber']
                print(f"🏃 車手 {driver2} 最速圈: 第 {actual_lap2} 圈 (時間: {fastest_lap2['LapTime']})")
            else:
                print(f"❌ 車手 {driver2} 沒有有效的圈速數據")
                return None
        
        # 統一變數命名（便於後續使用）
        lap_number1 = actual_lap1
        lap_number2 = actual_lap2
        
        # 5. 檢查指定圈數是否存在
        if lap_number1 not in driver1_data['LapNumber'].values:
            print(f"❌ 車手 {driver1} 沒有第 {lap_number1} 圈的數據")
            available_laps1 = sorted(driver1_data['LapNumber'].dropna().unique())
            print(f"   {driver1} 可用圈數: {available_laps1}")
            return None
        
        if lap_number2 not in driver2_data['LapNumber'].values:
            print(f"❌ 車手 {driver2} 沒有第 {lap_number2} 圈的數據")
            available_laps2 = sorted(driver2_data['LapNumber'].dropna().unique())
            print(f"   {driver2} 可用圈數: {available_laps2}")
            return None
        
        # 6. 獲取指定圈的數據
        lap_data1 = driver1_data[driver1_data['LapNumber'] == lap_number1].iloc[0]
        lap_data2 = driver2_data[driver2_data['LapNumber'] == lap_number2].iloc[0]
        
        # 7. 獲取遙測數據
        try:
            telemetry1 = lap_data1.get_telemetry()
            telemetry2 = lap_data2.get_telemetry()
            
            if telemetry1.empty:
                print(f"❌ 車手 {driver1} 第 {lap_number1} 圈沒有遙測數據")
                return None
            
            if telemetry2.empty:
                print(f"❌ 車手 {driver2} 第 {lap_number2} 圈沒有遙測數據")
                return None
                
        except Exception as e:
            print(f"❌ 無法獲取第 {lap_number} 圈的遙測數據: {e}")
            return None
        
        # 8. 執行分析
        result = self._perform_comparison_analysis(
            lap_data1, telemetry1, driver1,
            lap_data2, telemetry2, driver2,
            lap_number, lap_number1, lap_number2
        )
        
        # 9. 顯示詳細分析結果（如果需要）
        if show_detailed_output and result:
            self._display_detailed_telemetry_tables(result)
        
        # 10. 結果驗證和反饋
        if not self._report_analysis_results(result, "雙車手遙測比較分析"):
            return None
        
        # 11. 保存JSON結果（確保一定會保存）
        if result:
            self._save_json_result(result, driver1, driver2, display_lap1, display_lap2)
        
        # 12. 保存緩存
        if self.cache_enabled and result:
            self._save_cache(result, cache_key)
            print("💾 分析結果已緩存")
        
        return result
    
    def _perform_comparison_analysis(self, lap_data1, telemetry1, driver1, lap_data2, telemetry2, driver2, lap_number, lap_number1=None, lap_number2=None):
        """執行雙車手遙測比較分析"""
        print("📊 分析雙車手遙測數據...")
        
        # 處理雙圈數參數
        if lap_number1 is None:
            lap_number1 = lap_number
        if lap_number2 is None:
            lap_number2 = lap_number
        
        # 基本圈資訊
        lap_time1 = self._format_lap_time(lap_data1['LapTime'])
        lap_time2 = self._format_lap_time(lap_data2['LapTime'])
        
        # 確保距離數據存在
        if 'Distance' not in telemetry1.columns or 'Distance' not in telemetry2.columns:
            print("❌ 遙測數據中缺少距離資訊")
            return None
        
        # 計算加速度
        if 'Speed' in telemetry1.columns:
            speed_ms1 = telemetry1['Speed'] / 3.6
            time_diff1 = telemetry1['Time'].diff().dt.total_seconds()
            telemetry1['Acceleration'] = speed_ms1.diff() / time_diff1
        
        if 'Speed' in telemetry2.columns:
            speed_ms2 = telemetry2['Speed'] / 3.6
            time_diff2 = telemetry2['Time'].diff().dt.total_seconds()
            telemetry2['Acceleration'] = speed_ms2.diff() / time_diff2
        
        # 準備分析結果
        analysis_result = {
            'comparison_info': {
                'driver1': driver1,
                'driver2': driver2,
                'act_lap1_number': lap_number1,
                'act_lap2_number': lap_number2,
                'lap_time1': lap_time1,
                'lap_time2': lap_time2,
                'compound1': getattr(lap_data1, 'Compound', 'Unknown'),
                'compound2': getattr(lap_data2, 'Compound', 'Unknown'),
                'tyre_life1': getattr(lap_data1, 'TyreLife', 'Unknown'),
                'tyre_life2': getattr(lap_data2, 'TyreLife', 'Unknown')
            },
            'telemetry_comparison': {},
            'speed_difference': {},
            'distance_difference': {},
            'statistics': {},
            'charts_generated': []
        }
        
        # 分析各種遙測參數比較
        telemetry_params = {
            'Speed': '速度 (km/h)',
            'RPM': 'RPM',
            'Brake': '煞車 (%)',
            'nGear': '檔位',
            'Throttle': '油門開度 (%)',
            'Acceleration': '加速度 (m/s²)'
        }
        
        for param, param_name in telemetry_params.items():
            if param in telemetry1.columns and param in telemetry2.columns:
                param_data1 = telemetry1[param].dropna()
                param_data2 = telemetry2[param].dropna()
                
                if not param_data1.empty and not param_data2.empty:
                    # 插值到共同的距離基準
                    common_distance, interp_data1, interp_data2 = self._interpolate_to_common_distance(
                        telemetry1, telemetry2, param
                    )
                    
                    if common_distance is not None:
                        analysis_result['telemetry_comparison'][param] = {
                            'name': param_name,
                            'driver1_data': interp_data1.tolist(),
                            'driver2_data': interp_data2.tolist(),
                            'distance': common_distance.tolist()
                        }
                        
                        # 統計資訊
                        analysis_result['statistics'][param] = {
                            f'{driver1}_max': float(param_data1.max()),
                            f'{driver1}_min': float(param_data1.min()),
                            f'{driver1}_mean': float(param_data1.mean()),
                            f'{driver2}_max': float(param_data2.max()),
                            f'{driver2}_min': float(param_data2.min()),
                            f'{driver2}_mean': float(param_data2.mean())
                        }
        
        # 計算速度差分析
        speed_diff_analysis = self._calculate_speed_difference(telemetry1, telemetry2, driver1, driver2)
        if speed_diff_analysis:
            analysis_result['speed_difference'] = speed_diff_analysis
        
        # 計算賽道累積距離差分析
        print("🔍 檢查遙測數據完整性...")
        print(f"📊 {driver1} 遙測欄位: {list(telemetry1.columns)}")
        print(f"📊 {driver2} 遙測欄位: {list(telemetry2.columns)}")
        print(f"📊 {driver1} 數據形狀: {telemetry1.shape}")
        print(f"📊 {driver2} 數據形狀: {telemetry2.shape}")
        
        distance_diff_analysis = self._calculate_distance_difference(telemetry1, telemetry2, driver1, driver2)
        print(f"🔍 距離差分析結果: {type(distance_diff_analysis)}")
        if distance_diff_analysis:
            print(f"🔍 距離差分析內容鍵: {list(distance_diff_analysis.keys())}")
            analysis_result['distance_difference'] = distance_diff_analysis
        else:
            print("❌ 距離差分析返回 None 或空字典")
            analysis_result['distance_difference'] = {}
        
        # 生成比較圖表
        self._generate_comparison_charts(analysis_result, driver1, driver2, lap_number)
        
        # 顯示詳細資訊表格
        self._print_comparison_summary(analysis_result)
        
        return analysis_result
    
    def _interpolate_to_common_distance(self, telemetry1, telemetry2, param):
        """插值到共同的距離基準"""
        try:
            # 檢查原始數據
            print(f"🔍 插值參數: {param}")
            print(f"   車手1 {param} 範圍: {telemetry1[param].min():.2f} - {telemetry1[param].max():.2f}")
            print(f"   車手2 {param} 範圍: {telemetry2[param].min():.2f} - {telemetry2[param].max():.2f}")
            print(f"   車手1 距離範圍: {telemetry1['Distance'].min():.2f} - {telemetry1['Distance'].max():.2f}")
            print(f"   車手2 距離範圍: {telemetry2['Distance'].min():.2f} - {telemetry2['Distance'].max():.2f}")
            
            # 獲取共同的距離範圍
            min_distance = max(telemetry1['Distance'].min(), telemetry2['Distance'].min())
            max_distance = min(telemetry1['Distance'].max(), telemetry2['Distance'].max())
            
            print(f"   共同距離範圍: {min_distance:.2f} - {max_distance:.2f}")
            
            if min_distance >= max_distance:
                print(f"   ❌ 無有效的共同距離範圍")
                return None, None, None
            
            # 確保距離數據是遞增的
            if not telemetry1['Distance'].is_monotonic_increasing:
                print("   ⚠️ 車手1距離數據不是遞增的，正在排序...")
                telemetry1_sorted = telemetry1.sort_values('Distance')
            else:
                telemetry1_sorted = telemetry1
                
            if not telemetry2['Distance'].is_monotonic_increasing:
                print("   ⚠️ 車手2距離數據不是遞增的，正在排序...")
                telemetry2_sorted = telemetry2.sort_values('Distance')
            else:
                telemetry2_sorted = telemetry2
            
            # 創建共同的距離數組
            num_points = min(len(telemetry1), len(telemetry2), 500)  # 減少點數避免問題
            common_distance = np.linspace(min_distance, max_distance, num_points)
            
            # 插值 - 確保使用排序後的數據
            print(f"   🔧 開始插值計算...")
            print(f"      排序後車手1 {param} 範圍: {telemetry1_sorted[param].min():.2f} - {telemetry1_sorted[param].max():.2f}")
            print(f"      排序後車手2 {param} 範圍: {telemetry2_sorted[param].min():.2f} - {telemetry2_sorted[param].max():.2f}")
            print(f"      排序後車手1距離範圍: {telemetry1_sorted['Distance'].min():.2f} - {telemetry1_sorted['Distance'].max():.2f}")
            print(f"      排序後車手2距離範圍: {telemetry2_sorted['Distance'].min():.2f} - {telemetry2_sorted['Distance'].max():.2f}")
            print(f"      共同距離數組長度: {len(common_distance)}")
            print(f"      共同距離範圍: {common_distance[0]:.2f} - {common_distance[-1]:.2f}")
            
            # 檢查插值前的數據有效性
            valid_data1 = not telemetry1_sorted[param].isna().all()
            valid_data2 = not telemetry2_sorted[param].isna().all()
            print(f"      車手1 {param} 數據有效: {valid_data1}")
            print(f"      車手2 {param} 數據有效: {valid_data2}")
            
            if not valid_data1 or not valid_data2:
                print(f"   ❌ 存在無效數據，跳過插值")
                return None, None, None
            
            interp_data1 = np.interp(common_distance, telemetry1_sorted['Distance'], telemetry1_sorted[param])
            interp_data2 = np.interp(common_distance, telemetry2_sorted['Distance'], telemetry2_sorted[param])
            
            print(f"   ✅ 插值完成，輸出範圍:")
            print(f"      車手1: {interp_data1.min():.2f} - {interp_data1.max():.2f}")
            print(f"      車手2: {interp_data2.min():.2f} - {interp_data2.max():.2f}")
            print(f"      車手1前5個值: {interp_data1[:5]}")
            print(f"      車手2前5個值: {interp_data2[:5]}")
            
            return common_distance, interp_data1, interp_data2
            
        except Exception as e:
            print(f"⚠️ 插值計算失敗 ({param}): {e}")
            return None, None, None
    
    def _calculate_speed_difference(self, telemetry1, telemetry2, driver1, driver2):
        """計算速度差 vs 距離"""
        try:
            if 'Speed' not in telemetry1.columns or 'Speed' not in telemetry2.columns:
                return None
            
            if 'Distance' not in telemetry1.columns or 'Distance' not in telemetry2.columns:
                return None
            
            # 獲取兩個車手的距離範圍
            dist1_min, dist1_max = telemetry1['Distance'].min(), telemetry1['Distance'].max()
            dist2_min, dist2_max = telemetry2['Distance'].min(), telemetry2['Distance'].max()
            
            # 找出共同的距離範圍
            common_min = max(dist1_min, dist2_min)
            common_max = min(dist1_max, dist2_max)
            
            if common_min >= common_max:
                print(f"❌ 沒有共同的距離範圍: [{common_min}, {common_max}]")
                return None
            
            # 創建共同的距離數組
            common_distance = np.linspace(common_min, common_max, 500)
            
            # 插值速度數據到共同距離
            speed1_interp = np.interp(common_distance, telemetry1['Distance'], telemetry1['Speed'])
            speed2_interp = np.interp(common_distance, telemetry2['Distance'], telemetry2['Speed'])
            
            # 計算速度差
            speed_diff = speed1_interp - speed2_interp  # driver1 - driver2
            
            return {
                'distance': common_distance.tolist(),
                'speed_difference': speed_diff.tolist(),
                'max_diff': float(np.max(speed_diff)),
                'min_diff': float(np.min(speed_diff)),
                'mean_diff': float(np.mean(speed_diff)),
                'reference': f"{driver1} - {driver2}"
            }
            
        except Exception as e:
            print(f"⚠️ 速度差分析失敗: {e}")
            return None
            
            common_distance, speed1, speed2 = self._interpolate_to_common_distance(
                telemetry1, telemetry2, 'Speed'
            )
            
            if common_distance is None:
                return None
            
            speed_diff = speed1 - speed2  # driver1 - driver2
            
            return {
                'distance': common_distance.tolist(),
                'speed_difference': speed_diff.tolist(),
                'max_diff': float(np.max(speed_diff)),
                'min_diff': float(np.min(speed_diff)),
                'mean_diff': float(np.mean(speed_diff)),
                'reference': f"{driver1} - {driver2}"
            }
            
        except Exception as e:
            print(f"⚠️ 速度差計算失敗: {e}")
            return None
    
    def _interpolate_position_to_common_distance(self, telemetry1, telemetry2, distance_column='Distance'):
        """使用距離作為基準進行插值"""
        try:
            # 獲取兩個車手的距離範圍
            dist1_min, dist1_max = telemetry1[distance_column].min(), telemetry1[distance_column].max()
            dist2_min, dist2_max = telemetry2[distance_column].min(), telemetry2[distance_column].max()
            
            # 找出共同的距離範圍
            common_min = max(dist1_min, dist2_min)
            common_max = min(dist1_max, dist2_max)
            
            if common_min >= common_max:
                print(f"❌ 沒有共同的距離範圍: [{common_min}, {common_max}]")
                return None, None, None
            
            # 創建共同的距離數組
            common_distance = np.linspace(common_min, common_max, 500)
            
            # 插值位置數據 (X, Y 坐標) 到共同距離
            position1_x = np.interp(common_distance, telemetry1[distance_column], telemetry1['X'])
            position1_y = np.interp(common_distance, telemetry1[distance_column], telemetry1['Y'])
            
            position2_x = np.interp(common_distance, telemetry2[distance_column], telemetry2['X'])
            position2_y = np.interp(common_distance, telemetry2[distance_column], telemetry2['Y'])
            
            # 計算實際位置距離差（歐幾里得距離）
            position_diff = np.sqrt((position1_x - position2_x)**2 + (position1_y - position2_y)**2)
            
            # 計算累積距離差 (基於時間差異)
            time1_interp = np.interp(common_distance, telemetry1[distance_column], 
                                   telemetry1['Time'].dt.total_seconds())
            time2_interp = np.interp(common_distance, telemetry2[distance_column], 
                                   telemetry2['Time'].dt.total_seconds())
            
            # 使用時間差和速度估算距離差
            speed1_interp = np.interp(common_distance, telemetry1[distance_column], telemetry1['Speed'])
            speed2_interp = np.interp(common_distance, telemetry2[distance_column], telemetry2['Speed'])
            avg_speed = (speed1_interp + speed2_interp) / 2 * 1000 / 3600  # 轉換為 m/s
            
            time_diff = time1_interp - time2_interp
            cumulative_distance_diff = time_diff * avg_speed
            
            return common_distance, position_diff, cumulative_distance_diff
            
        except Exception as e:
            print(f"⚠️ 距離插值失敗: {e}")
            return None, None, None
    
    def _calculate_distance_difference(self, telemetry1, telemetry2, driver1, driver2):
        """計算賽道累積距離差 vs 距離"""
        try:
            print("🔍 開始計算賽道累積距離差...")
            
            # 檢查必要的數據欄位
            required_cols = ['Time', 'Distance', 'X', 'Y', 'Speed']
            for col in required_cols:
                if col not in telemetry1.columns or col not in telemetry2.columns:
                    print(f"❌ 遙測數據中缺少必要欄位: {col}")
                    return None
            
            print(f"📊 {driver1} 時間範圍: {telemetry1['Time'].min()} 到 {telemetry1['Time'].max()}")
            print(f"📊 {driver2} 時間範圍: {telemetry2['Time'].min()} 到 {telemetry2['Time'].max()}")
            
            # 使用改進的距離插值方法
            print("🔄 計算位置和累積距離差...")
            common_distance, position_diff, cumulative_distance_diff = self._interpolate_position_to_common_distance(
                telemetry1, telemetry2, 'Distance'
            )
            
            if common_distance is None:
                print("❌ 距離插值失敗")
                return None
            
            print(f"✅ 距離差計算完成，數據點數: {len(cumulative_distance_diff)}")
            print(f"📊 位置距離差統計: 最大={np.max(position_diff):.2f}m, 最小={np.min(position_diff):.2f}m, 平均={np.mean(position_diff):.2f}m")
            print(f"📊 累積距離差統計: 最大={np.max(cumulative_distance_diff):.2f}m, 最小={np.min(cumulative_distance_diff):.2f}m, 平均={np.mean(cumulative_distance_diff):.2f}m")
            
            return {
                'reference_distance': common_distance.tolist(),
                'position_difference': position_diff.tolist(),
                'cumulative_distance_difference': cumulative_distance_diff.tolist(),
                'position_diff_stats': {
                    'max_diff': float(np.max(position_diff)),
                    'min_diff': float(np.min(position_diff)),
                    'mean_diff': float(np.mean(position_diff))
                },
                'cumulative_diff_stats': {
                    'max_diff': float(np.max(cumulative_distance_diff)),
                    'min_diff': float(np.min(cumulative_distance_diff)),
                    'mean_diff': float(np.mean(cumulative_distance_diff))
                },
                'reference': f"{driver1} - {driver2}"
            }
            
        except Exception as e:
            print(f"⚠️ 賽道距離差計算失敗: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _generate_comparison_charts(self, analysis_result, driver1, driver2, lap_number):
        """生成雙車手比較圖表"""
        disable_charts = analysis_result.get('disable_charts', False)
        if disable_charts:
            print("📈 已禁用圖表生成")
            return
        
        print("📈 生成雙車手比較圖表...")
        
        telemetry_data = analysis_result['telemetry_comparison']
        speed_diff = analysis_result.get('speed_difference', {})
        distance_diff = analysis_result.get('distance_difference', {})
        
        if not telemetry_data and not speed_diff and not distance_diff:
            print("⚠️ 沒有可用的比較數據，跳過圖表生成")
            return
        
        # 創建圖表目錄
        chart_dir = "cache"
        os.makedirs(chart_dir, exist_ok=True)
        
        # 計算需要的子圖數量
        num_telemetry = len(telemetry_data)
        has_speed_diff = bool(speed_diff)
        has_distance_diff = bool(distance_diff)
        total_plots = num_telemetry + (1 if has_speed_diff else 0) + (1 if has_distance_diff else 0)
        
        if total_plots == 0:
            return
        
        # 計算子圖佈局
        if total_plots <= 4:
            rows, cols = 2, 2
            figsize = (15, 10)
        else:
            rows, cols = 3, 3
            figsize = (18, 12)
        
        fig, axes = plt.subplots(rows, cols, figsize=figsize)
        axes = axes.flatten() if rows * cols > 1 else [axes]
        
        # 顏色設定
        driver1_color = '#FF6B6B'
        driver2_color = '#4ECDC4'
        diff_color = '#96CEB4'
        
        plot_idx = 0
        
        # 繪製遙測參數比較
        for param, data_info in telemetry_data.items():
            if plot_idx >= len(axes):
                break
                
            ax = axes[plot_idx]
            
            ax.plot(data_info['distance'], data_info['driver1_data'], 
                   color=driver1_color, linewidth=2, alpha=0.8, label=driver1)
            ax.plot(data_info['distance'], data_info['driver2_data'], 
                   color=driver2_color, linewidth=2, alpha=0.8, label=driver2)
            
            ax.set_xlabel('距離 (m)')
            ax.set_ylabel(data_info['name'])
            ax.set_title(f'第{lap_number}圈 {data_info["name"]} 比較')
            ax.grid(True, alpha=0.3)
            ax.legend()
            
            # 設置y軸範圍
            if param == 'nGear':
                ax.set_ylim(0, 8)
            elif param in ['Brake', 'Throttle']:
                ax.set_ylim(0, 100)
            
            plot_idx += 1
        
        # 繪製速度差圖表
        if has_speed_diff and plot_idx < len(axes):
            ax = axes[plot_idx]
            ax.plot(speed_diff['distance'], speed_diff['speed_difference'], 
                   color=diff_color, linewidth=2, alpha=0.8)
            ax.set_xlabel('距離 (m)')
            ax.set_ylabel('速度差 (km/h)')
            ax.set_title(f'第{lap_number}圈 速度差 ({speed_diff["reference"]})')
            ax.grid(True, alpha=0.3)
            ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)
            plot_idx += 1
        
        # 繪製賽道累積距離差圖表
        if has_distance_diff and plot_idx < len(axes):
            ax = axes[plot_idx]
            
            # 檢查新的數據結構
            if 'cumulative_distance_difference' in distance_diff:
                # 使用新的累積距離差數據
                ax.plot(distance_diff['reference_distance'], distance_diff['cumulative_distance_difference'], 
                       color='#DDA0DD', linewidth=2, alpha=0.8, label='累積距離差')
                       
                # 可選：添加位置距離差
                if 'position_difference' in distance_diff:
                    ax2 = ax.twinx()
                    ax2.plot(distance_diff['reference_distance'], distance_diff['position_difference'], 
                           color='#FF6B6B', linewidth=1.5, alpha=0.6, label='位置距離差')
                    ax2.set_ylabel('位置距離差 (m)', color='#FF6B6B')
                    ax2.tick_params(axis='y', labelcolor='#FF6B6B')
                
            elif 'distance_difference' in distance_diff:
                # 向下兼容舊的數據結構
                ax.plot(distance_diff['reference_distance'], distance_diff['distance_difference'], 
                       color='#DDA0DD', linewidth=2, alpha=0.8)
            
            ax.set_xlabel('參考距離 (m)')
            ax.set_ylabel('累積距離差 (m)')
            ax.set_title(f'第{lap_number}圈 賽道累積距離差 ({distance_diff["reference"]})')
            ax.grid(True, alpha=0.3)
            ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)
            ax.legend()
            plot_idx += 1
        
        # 隱藏多餘的子圖
        for j in range(plot_idx, len(axes)):
            axes[j].set_visible(False)
        
        plt.tight_layout()
        
        # 保存圖表
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        chart_filename = f"comparison_telemetry_{driver1}_{driver2}_{self.year}_{self.race}_{self.session}_Lap{lap_number}_{timestamp}.png"
        chart_path = os.path.join(chart_dir, chart_filename)
        
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        analysis_result['charts_generated'].append(chart_path)
        print(f"📊 比較圖表已保存: {chart_path}")
    
    def _print_comparison_summary(self, analysis_result):
        """顯示雙車手比較摘要表格"""
        print("\n" + "="*80)
        print("📊 [詳細] 雙車手遙測比較數據摘要")
        print("="*80)
        
        # 基本資訊表格
        info_table = PrettyTable()
        info_table.field_names = ["項目", "車手1", "車手2"]
        info_table.align = "l"
        
        comp_info = analysis_result['comparison_info']
        info_table.add_row(["🏎️ 車手", comp_info['driver1'], comp_info['driver2']])
        info_table.add_row(["🏁 圈數", f"第 {comp_info['act_lap1_number']} 圈", f"第 {comp_info['act_lap2_number']} 圈"])
        info_table.add_row(["⏱️ 圈時間", comp_info['lap_time1'], comp_info['lap_time2']])
        info_table.add_row(["🛞 輪胎配方", comp_info['compound1'], comp_info['compound2']])
        info_table.add_row(["🔄 輪胎使用圈數", comp_info['tyre_life1'], comp_info['tyre_life2']])
        
        print(info_table)
        
        # 速度差分析
        if analysis_result.get('speed_difference'):
            speed_diff = analysis_result['speed_difference']
            print(f"\n📈 速度差分析 ({speed_diff['reference']}):")
            speed_table = PrettyTable()
            speed_table.field_names = ["統計項目", "數值 (km/h)"]
            speed_table.align = "l"
            speed_table.add_row(["最大速度差", f"{speed_diff['max_diff']:.2f}"])
            speed_table.add_row(["最小速度差", f"{speed_diff['min_diff']:.2f}"])
            speed_table.add_row(["平均速度差", f"{speed_diff['mean_diff']:.2f}"])
            print(speed_table)
        
        # 距離差分析
        if analysis_result.get('distance_difference'):
            dist_diff = analysis_result['distance_difference']
            reference = str(dist_diff.get('reference', 'N/A'))
            print(f"\n📍 賽道累積距離差分析 ({reference}):")
            
            # 位置距離差表格
            if 'position_diff_stats' in dist_diff:
                pos_table = PrettyTable()
                pos_table.field_names = ["統計項目", "數值 (m)"]
                pos_table.align = "l"
                pos_stats = dist_diff['position_diff_stats']
                pos_table.add_row(["最大位置差", f"{pos_stats['max_diff']:.2f}"])
                pos_table.add_row(["最小位置差", f"{pos_stats['min_diff']:.2f}"])
                pos_table.add_row(["平均位置差", f"{pos_stats['mean_diff']:.2f}"])
                print("📍 位置距離差:")
                print(pos_table)
            
            # 累積距離差表格  
            if 'cumulative_diff_stats' in dist_diff:
                cum_table = PrettyTable()
                cum_table.field_names = ["統計項目", "數值 (m)"]
                cum_table.align = "l"
                cum_stats = dist_diff['cumulative_diff_stats']
                cum_table.add_row(["最大累積距離差", f"{cum_stats['max_diff']:.2f}"])
                cum_table.add_row(["最小累積距離差", f"{cum_stats['min_diff']:.2f}"])
                cum_table.add_row(["平均累積距離差", f"{cum_stats['mean_diff']:.2f}"])
                print("📊 累積距離差:")
                print(cum_table)
            
            # 向下兼容：如果有舊格式數據
            if 'max_diff' in dist_diff and 'position_diff_stats' not in dist_diff:
                dist_table = PrettyTable()
                dist_table.field_names = ["統計項目", "數值 (m)"]
                dist_table.align = "l"
                dist_table.add_row(["最大距離差", f"{dist_diff['max_diff']:.2f}"])
                dist_table.add_row(["最小距離差", f"{dist_diff['min_diff']:.2f}"])
                dist_table.add_row(["平均距離差", f"{dist_diff['mean_diff']:.2f}"])
                print(dist_table)
        
        # 圖表資訊
        if analysis_result['charts_generated']:
            print(f"\n📊 生成圖表數量: {len(analysis_result['charts_generated'])}")
            for chart_path in analysis_result['charts_generated']:
                print(f"   • {os.path.basename(chart_path)}")
    
    def _save_json_result(self, analysis_result, driver1, driver2, lap_number1, lap_number2=None):
        """保存 JSON 結果 - 支援雙圈數命名"""
        try:
            # 創建 JSON 目錄
            json_dir = "json"
            os.makedirs(json_dir, exist_ok=True)
            
            # 準備 JSON 數據
            json_data = {
                "analysis_type": "two_driver_telemetry_comparison",
                "metadata": {
                    "year": self.year,
                    "race": self.race,
                    "session": self.session,
                    "driver1": driver1,
                    "driver2": driver2,
                    "lap_number1": lap_number1,
                    "lap_number2": lap_number2 if lap_number2 is not None else lap_number1,
                    "analysis_timestamp": datetime.now().isoformat()
                },
                "results": analysis_result
            }
            
            # 生成檔案名 - 統一使用完整格式，即使是同車手同圈數
            # 修改：始終使用 comparison_telemetry_{driver1}_{driver2}_{year}_{race}_{session}_Lap{lap1}_Lap{lap2}.json 格式
            filename = f"comparison_telemetry_{driver1}_{driver2}_{self.year}_{self.race}_{self.session}_Lap{lap_number1}_Lap{lap_number2}.json"
            
            filepath = os.path.join(json_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"\n💾 JSON 遙測比較結果已保存到: {filepath}")
            print(f"📄 檔案名: {filename}")
            print(f"🔄 使用統一命名格式: comparison_telemetry_{driver1}_{driver2}_{self.year}_{self.race}_{self.session}_Lap{lap_number1}_Lap{lap_number2}.json")
            
        except Exception as e:
            print(f"⚠️ JSON 保存失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _format_lap_time(self, lap_time):
        """格式化圈時間"""
        if pd.isna(lap_time):
            return "N/A"
        else:
            total_seconds = lap_time.total_seconds()
            minutes = int(total_seconds // 60)
            seconds = total_seconds % 60
            return f"{minutes}:{seconds:06.3f}"
    
    def _generate_cache_key(self, driver1, driver2, lap_number1, lap_number2=None, **kwargs):
        """生成緩存鍵值 - 支援雙圈數"""
        if lap_number2 is not None and lap_number2 != lap_number1:
            return f"comparison_telemetry_{self.year}_{self.race}_{self.session}_{driver1}_lap{lap_number1}_{driver2}_lap{lap_number2}"
        else:
            return f"comparison_telemetry_{self.year}_{self.race}_{self.session}_{driver1}_{driver2}_lap{lap_number1}"
    
    def _check_cache(self, cache_key):
        """檢查緩存"""
        cache_path = os.path.join("cache", f"{cache_key}.pkl")
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"⚠️ 緩存讀取失敗: {e}")
        return None
    
    def _save_cache(self, data, cache_key):
        """保存緩存"""
        try:
            os.makedirs("cache", exist_ok=True)
            cache_path = os.path.join("cache", f"{cache_key}.pkl")
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            print(f"⚠️ 緩存保存失敗: {e}")
    
    def _display_detailed_telemetry_tables(self, result):
        """顯示詳細的遙測比較表格"""
        print("\n" + "="*80)
        print("📊 [詳細] 雙車手遙測數據對比表格")
        print("="*80)
        
        # 基本資訊表格
        self._display_basic_info_table(result)
        
        # 遙測參數統計表格
        self._display_telemetry_statistics_table(result)
        
        # 遙測數據樣本表格（顯示前20個數據點）
        self._display_telemetry_sample_table(result)
        
        # 速度差和距離差詳細數據
        self._display_difference_analysis_table(result)
    
    def _display_basic_info_table(self, result):
        """顯示基本資訊表格"""
        from prettytable import PrettyTable
        
        info = result.get('comparison_info', {})
        table = PrettyTable()
        table.field_names = ["比較項目", f"車手1 ({info.get('driver1', 'N/A')})", f"車手2 ({info.get('driver2', 'N/A')})"]
        table.align = "l"
        
        table.add_row(["🏎️ 車手代號", info.get('driver1', 'N/A'), info.get('driver2', 'N/A')])
        table.add_row(["🏁 比較圈數", f"第 {info.get('lap_number', 'N/A')} 圈", f"第 {info.get('lap_number', 'N/A')} 圈"])
        table.add_row(["⏱️ 圈時間", info.get('lap_time1', 'N/A'), info.get('lap_time2', 'N/A')])
        table.add_row(["🛞 輪胎配方", info.get('compound1', 'N/A'), info.get('compound2', 'N/A')])
        table.add_row(["🔄 輪胎圈數", str(info.get('tyre_life1', 'N/A')), str(info.get('tyre_life2', 'N/A'))])
        
        print(f"\n📋 基本比較資訊:")
        print(table)
    
    def _display_telemetry_statistics_table(self, result):
        """顯示遙測參數統計表格"""
        from prettytable import PrettyTable
        
        stats = result.get('statistics', {})
        if not stats:
            return
        
        print(f"\n📊 遙測參數統計對比:")
        
        for param, param_stats in stats.items():
            if isinstance(param_stats, dict):
                table = PrettyTable()
                table.field_names = ["統計項目", f"車手1 ({result['comparison_info']['driver1']})", f"車手2 ({result['comparison_info']['driver2']})"]
                table.align = "c"
                
                driver1_max = param_stats.get(f"{result['comparison_info']['driver1']}_max", 'N/A')
                driver1_min = param_stats.get(f"{result['comparison_info']['driver1']}_min", 'N/A')
                driver1_mean = param_stats.get(f"{result['comparison_info']['driver1']}_mean", 'N/A')
                
                driver2_max = param_stats.get(f"{result['comparison_info']['driver2']}_max", 'N/A')
                driver2_min = param_stats.get(f"{result['comparison_info']['driver2']}_min", 'N/A')
                driver2_mean = param_stats.get(f"{result['comparison_info']['driver2']}_mean", 'N/A')
                
                # 格式化數值
                if isinstance(driver1_max, float):
                    driver1_max = f"{driver1_max:.2f}"
                if isinstance(driver1_min, float):
                    driver1_min = f"{driver1_min:.2f}"
                if isinstance(driver1_mean, float):
                    driver1_mean = f"{driver1_mean:.2f}"
                if isinstance(driver2_max, float):
                    driver2_max = f"{driver2_max:.2f}"
                if isinstance(driver2_min, float):
                    driver2_min = f"{driver2_min:.2f}"
                if isinstance(driver2_mean, float):
                    driver2_mean = f"{driver2_mean:.2f}"
                
                table.add_row(["最大值", driver1_max, driver2_max])
                table.add_row(["最小值", driver1_min, driver2_min])
                table.add_row(["平均值", driver1_mean, driver2_mean])
                
                print(f"\n🔧 {param} 統計:")
                print(table)
    
    def _display_telemetry_sample_table(self, result):
        """顯示遙測數據樣本表格（前20個數據點）"""
        from prettytable import PrettyTable
        
        telemetry = result.get('telemetry_comparison', {})
        if not telemetry:
            return
        
        print(f"\n📋 遙測數據樣本 (前20個數據點):")
        
        # 獲取第一個參數的數據長度作為參考
        first_param = next(iter(telemetry.values()), {})
        data_length = len(first_param.get('driver1_data', []))
        sample_size = min(20, data_length)
        
        if sample_size == 0:
            return
        
        table = PrettyTable()
        param_order = ['Speed', 'RPM', 'Brake', 'nGear', 'Throttle', 'Acceleration']
        header_names = ['Speed', 'RPM', 'Brake', 'nGear', 'Throttle', 'Acceleration']
        table.field_names = ["數據點"] + header_names
        table.align = "c"
        
        for i in range(sample_size):
            row = [f"#{i+1}"]
            for param_name in param_order:
                if param_name in telemetry:
                    param_data = telemetry[param_name]
                    driver1_data = param_data.get('driver1_data', [])
                    driver2_data = param_data.get('driver2_data', [])
                    
                    if i < len(driver1_data) and i < len(driver2_data):
                        # 檢查數據有效性並添加調試
                        if i == 0:  # 只在第一行顯示調試信息
                            print(f"🔍 調試 {param_name}: VER[0]={driver1_data[0]}, LEC[0]={driver2_data[0]}")
                        
                        val1 = driver1_data[i] if isinstance(driver1_data[i], (int, str)) else f"{driver1_data[i]:.1f}"
                        val2 = driver2_data[i] if isinstance(driver2_data[i], (int, str)) else f"{driver2_data[i]:.1f}"
                        row.append(f"{val1} / {val2}")
                    else:
                        row.append("N/A")
                else:
                    row.append("N/A")
            
            table.add_row(row)
        
        print(table)
        print(f"💡 格式: 車手1 / 車手2")
    
    def _display_difference_analysis_table(self, result):
        """顯示速度差和距離差分析表格"""
        from prettytable import PrettyTable
        
        # 速度差分析
        speed_diff = result.get('speed_difference', {})
        if speed_diff:
            print(f"\n🏃 速度差分析詳細數據 (前15個數據點):")
            table = PrettyTable()
            table.field_names = ["數據點", "賽道距離 (m)", "速度差 (km/h)", "說明"]
            table.align = "c"
            
            distance_data = speed_diff.get('distance', [])
            speed_diff_data = speed_diff.get('speed_difference', [])
            sample_size = min(15, len(distance_data), len(speed_diff_data))
            
            for i in range(sample_size):
                distance = f"{distance_data[i]:.1f}" if i < len(distance_data) else "N/A"
                diff = f"{speed_diff_data[i]:.2f}" if i < len(speed_diff_data) else "N/A"
                
                # 判斷誰更快
                explanation = ""
                if i < len(speed_diff_data):
                    if speed_diff_data[i] > 0:
                        explanation = f"{result['comparison_info']['driver1']} 較快"
                    elif speed_diff_data[i] < 0:
                        explanation = f"{result['comparison_info']['driver2']} 較快"
                    else:
                        explanation = "速度相同"
                
                table.add_row([f"#{i+1}", distance, diff, explanation])
            
            print(table)
        
        # 距離差分析
        distance_diff = result.get('distance_difference', {})
        if distance_diff:
            print(f"\n📍 賽道距離差分析:")
            table = PrettyTable()
            table.field_names = ["分析項目", "數值", "單位", "說明"]
            table.align = "l"
            
            pos_stats = distance_diff.get('position_diff_stats', {})
            cum_stats = distance_diff.get('cumulative_diff_stats', {})
            
            if pos_stats:
                max_val = pos_stats.get('max_diff', 'N/A')
                min_val = pos_stats.get('min_diff', 'N/A')
                mean_val = pos_stats.get('mean_diff', 'N/A')
                
                max_str = f"{max_val:.2f}" if isinstance(max_val, (int, float)) else str(max_val)
                min_str = f"{min_val:.2f}" if isinstance(min_val, (int, float)) else str(min_val)
                mean_str = f"{mean_val:.2f}" if isinstance(mean_val, (int, float)) else str(mean_val)
                
                table.add_row(["位置距離差 - 最大", max_str, "公尺", "兩車最大分離距離"])
                table.add_row(["位置距離差 - 最小", min_str, "公尺", "兩車最小分離距離"])
                table.add_row(["位置距離差 - 平均", mean_str, "公尺", "平均分離距離"])
            
            if cum_stats:
                max_val = cum_stats.get('max_diff', 'N/A')
                min_val = cum_stats.get('min_diff', 'N/A')
                mean_val = cum_stats.get('mean_diff', 'N/A')
                
                max_str = f"{max_val:.2f}" if isinstance(max_val, (int, float)) else str(max_val)
                min_str = f"{min_val:.2f}" if isinstance(min_val, (int, float)) else str(min_val)
                mean_str = f"{mean_val:.2f}" if isinstance(mean_val, (int, float)) else str(mean_val)
                
                table.add_row(["累積距離差 - 最大", max_str, "公尺", "最大領先距離"])
                table.add_row(["累積距離差 - 最小", min_str, "公尺", "最大落後距離"])
                table.add_row(["累積距離差 - 平均", mean_str, "公尺", "平均距離差"])
            
            print(table)
    
    def _report_analysis_results(self, data, analysis_type="analysis"):
        """報告分析結果狀態"""
        if not data:
            print(f"❌ {analysis_type}失敗：無可用數據")
            return False
        
        # 檢查比較數據
        telemetry_count = len(data.get('telemetry_comparison', {}))
        charts_count = len(data.get('charts_generated', []))
        has_speed_diff = bool(data.get('speed_difference'))
        has_distance_diff = bool(data.get('distance_difference'))
        
        print(f"📊 {analysis_type}結果摘要：")
        print(f"   • 遙測參數比較數量: {telemetry_count}")
        print(f"   • 速度差分析: {'✅ 完成' if has_speed_diff else '❌ 未完成'}")
        print(f"   • 距離差分析: {'✅ 完成' if has_distance_diff else '❌ 未完成'}")
        print(f"   • 生成圖表數量: {charts_count}")
        print(f"   • 數據完整性: {'✅ 良好' if telemetry_count > 0 else '❌ 不足'}")
        
        print(f"✅ {analysis_type}分析完成！")
        return True


def run_two_driver_telemetry_comparison_analysis(data_loader, year, race, session, driver, driver2, lap_number=1, lap1=None, lap2=None, lap1_original=None, lap2_original=None, **kwargs):
    """運行雙車手遙測比較分析的入口函數"""
    
    # 支援雙圈數參數
    if lap1 is not None and lap2 is not None:
        # 使用 lap1 和 lap2 進行分析
        lap_number1 = lap1
        lap_number2 = lap2
        print(f"[DEBUG] 使用雙圈數參數: lap1={lap1}, lap2={lap2}")
    else:
        # 使用原有的 lap_number 參數
        lap_number1 = lap_number
        lap_number2 = lap_number
        print(f"[DEBUG] 使用傳統圈數參數: lap_number={lap_number}")
    
    # 處理檔案命名用的圈數（保留原始輸入，如99表示最速圈）
    if lap1_original is not None and lap2_original is not None:
        file_lap1 = lap1_original
        file_lap2 = lap2_original
        print(f"[DEBUG] 檔案命名使用原始參數: lap1_original={lap1_original}, lap2_original={lap2_original}")
    else:
        file_lap1 = lap_number1
        file_lap2 = lap_number2
    
    analyzer = TwoDriverTelemetryComparison(
        data_loader=data_loader,
        year=year,
        race=race,
        session=session
    )
    
    result = analyzer.analyze(
        driver1=driver, 
        driver2=driver2, 
        lap_number1=lap_number1, 
        lap_number2=lap_number2,
        lap1=lap1, 
        lap2=lap2,
        file_lap1=file_lap1,
        file_lap2=file_lap2,
        **kwargs
    )
    
    # 包裝結果以符合 function_mapper 的期望格式
    if result:
        return {
            "success": True, 
            "message": f"雙車手遙測比較分析完成 (車手: {driver} vs {driver2}, 圈數: {lap_number1} vs {lap_number2})", 
            "data": result,
            "function_id": "13"
        }
    else:
        return {
            "success": False, 
            "message": "雙車手遙測比較分析失敗", 
            "function_id": "13"
        }
