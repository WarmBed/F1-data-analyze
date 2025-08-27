#!/usr/bin/env python3
"""
單一車手指定賽事全部彎道詳細分析模組
Single Driver All Corners Detailed Analysis Module

功能：分析單一車手在該賽事的每個彎道的穩定度評分及表現評分及車手速度
作者：F1 Analysis Team
版本：2.0 - 採用與功能13相同的彎道檢測和評分演算法
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from datetime import datetime
from prettytable import PrettyTable
import warnings
import traceback
import json
import pickle
from driver_selection_utils import get_user_driver_selection

# 設定中文字體和忽略警告
matplotlib.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
matplotlib.rcParams['axes.unicode_minus'] = False
warnings.filterwarnings("ignore")

def run_single_driver_all_corners_detailed_analysis(data_loader, f1_analysis_instance=None, show_detailed_output=True, driver=None):
    """
    執行單一車手指定賽事全部彎道詳細分析
    
    Args:
        data_loader: 數據載入器實例
        f1_analysis_instance: F1分析實例（可選）
        show_detailed_output: 是否顯示詳細輸出（默認True）
        driver: 指定車手代碼（可選，如 'VER'）
    """
    print("\n[INFO] 單一車手指定賽事全部彎道詳細分析")
    print("=" * 60)
    
    try:
        # 初始化分析器
        analyzer = SingleDriverCornerAnalyzer()
        return analyzer.analyze(data_loader, f1_analysis_instance, show_detailed_output=show_detailed_output, driver=driver)
        
    except Exception as e:
        print(f"[ERROR] 分析過程中發生錯誤: {e}")
        traceback.print_exc()
        return False

class SingleDriverCornerAnalyzer:
    """單一車手彎道分析器"""
    
    def __init__(self):
        """初始化分析器"""
        # 設定暫存目錄
        self.cache_dir = "corner_analysis_cache"
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def _get_cache_filename(self, year, race_name, driver_name):
        """生成暫存檔案名稱"""
        safe_race_name = "".join(c for c in race_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_race_name = safe_race_name.replace(' ', '_')
        return os.path.join(self.cache_dir, f"single_driver_corner_analysis_{year}_{safe_race_name}_{driver_name}.pkl")
    
    def _save_to_cache(self, data, year, race_name, driver_name):
        """儲存分析結果到暫存檔"""
        try:
            cache_filename = self._get_cache_filename(year, race_name, driver_name)
            cache_data = {
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'year': year,
                'race_name': race_name,
                'driver_name': driver_name
            }
            
            with open(cache_filename, 'wb') as f:
                pickle.dump(cache_data, f)
            
            print(f"💾 分析結果已儲存到暫存: {os.path.basename(cache_filename)}")
            return True
        except Exception as e:
            print(f"[WARNING] 儲存暫存檔失敗: {e}")
            return False
    
    def _load_from_cache(self, year, race_name, driver_name):
        """從暫存檔讀取分析結果"""
        try:
            cache_filename = self._get_cache_filename(year, race_name, driver_name)
            
            if not os.path.exists(cache_filename):
                return None
            
            with open(cache_filename, 'rb') as f:
                cache_data = pickle.load(f)
            
            # 檢查暫存檔是否是同一賽事的
            if (cache_data.get('year') == year and 
                cache_data.get('race_name') == race_name and 
                cache_data.get('driver_name') == driver_name):
                
                print(f"📂 從暫存載入分析結果: {os.path.basename(cache_filename)}")
                return cache_data['data']
            
            return None
            
        except Exception as e:
            print(f"[WARNING] 讀取暫存檔失敗: {e}")
            return None
    
    def _get_cache_filename(self, year, race_name, driver_name):
        """生成暫存檔案名稱"""
        safe_race_name = "".join(c for c in race_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_race_name = safe_race_name.replace(' ', '_')
        return os.path.join(self.cache_dir, f"single_driver_corner_analysis_{year}_{safe_race_name}_{driver_name}.pkl")
    
    def _save_to_cache(self, data, year, race_name, driver_name):
        """儲存分析結果到暫存檔"""
        try:
            cache_filename = self._get_cache_filename(year, race_name, driver_name)
            cache_data = {
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'year': year,
                'race_name': race_name,
                'driver_name': driver_name
            }
            
            with open(cache_filename, 'wb') as f:
                pickle.dump(cache_data, f)
            
            print(f"💾 分析結果已儲存到暫存: {cache_filename}")
            return True
        except Exception as e:
            print(f"[WARNING] 儲存暫存檔失敗: {e}")
            return False
    
    def _load_from_cache(self, year, race_name, driver_name):
        """從暫存檔讀取分析結果"""
        try:
            cache_filename = self._get_cache_filename(year, race_name, driver_name)
            
            if not os.path.exists(cache_filename):
                return None
            
            with open(cache_filename, 'rb') as f:
                cache_data = pickle.load(f)
            
            # 檢查暫存檔是否是今天的
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            current_time = datetime.now()
            
            # 如果暫存檔超過24小時，視為過期
            if (current_time - cache_time).total_seconds() > 86400:  # 24小時 = 86400秒
                print(f"[WARNING] 暫存檔已過期，將重新分析")
                return None
            
            print(f"📂 從暫存載入分析結果: {cache_filename}")
            print(f"📅 暫存時間: {cache_time.strftime('%Y-%m-%d %H:%M:%S')}")
            return cache_data['data']
            
        except Exception as e:
            print(f"[WARNING] 讀取暫存檔失敗: {e}")
            return None
    
    def analyze(self, data_loader, f1_analysis_instance=None, show_detailed_output=True, driver=None):
        """執行分析
        
        Args:
            data_loader: 數據載入器實例
            f1_analysis_instance: F1分析實例（可選）
            show_detailed_output: 是否顯示詳細輸出（默認True）
            driver: 指定車手代碼（可選，如 'VER'）
        """
        try:
            # 檢查數據載入器
            if not data_loader or not hasattr(data_loader, 'session') or data_loader.session is None:
                print("[ERROR] 數據載入器未正確初始化，請先載入賽事數據")
                return False
            
            session = data_loader.session
            
            # 獲取賽事信息
            race_name = getattr(session.event, 'EventName', 'Unknown Race')
            year = getattr(session.event, 'year', 'Unknown Year')
            
            print(f"[INFO] 分析賽事: {year} {race_name}")
            
            # 獲取所有圈數數據
            try:
                laps = session.laps
                if laps.empty:
                    print("[ERROR] 無法獲取圈數數據")
                    return False
            except Exception as e:
                print(f"[ERROR] 獲取圈數數據失敗: {e}")
                return False
            
            # 獲取可用車手列表
            all_drivers = laps['Driver'].unique().tolist()
            if not all_drivers:
                print("[ERROR] 無法獲取車手列表")
                return False

            # 車手選擇邏輯 - 符合開發核心原則
            if driver:
                # 參數化模式：使用指定的車手
                if driver in all_drivers:
                    selected_driver = driver
                    print(f"🎯 參數模式：使用指定車手 {driver}")
                else:
                    print(f"❌ 指定車手 {driver} 不在賽事中，可用車手: {all_drivers}")
                    return False
            else:
                # 交互模式：讓用戶選擇車手
                selected_driver = get_user_driver_selection(session, all_drivers)
                if not selected_driver:
                    return False
            
            print(f"\n[SUCCESS] 已選擇車手: {selected_driver}")
            
            # 嘗試從暫存載入
            print(f"\n[DEBUG] 檢查暫存檔...")
            cached_data = self._load_from_cache(year, race_name, selected_driver)
            
            if cached_data:
                print("📦 使用緩存數據")
                if show_detailed_output:
                    print("📊 顯示詳細分析結果")
                    # 直接顯示結果和視覺化
                    self._generate_analysis_report(cached_data, selected_driver, race_name, year)
                    self._generate_visualization(cached_data, selected_driver, race_name, year)
                else:
                    print("📋 緩存模式：僅顯示摘要")
                    self._display_summary_only(cached_data, selected_driver)
                return True
            
            print("🔄 重新計算 - 開始數據分析...")
            print("[INFO] 暫存檔不存在，開始重新分析...")
            
            if cached_data:
                print(f"[START] 使用暫存數據，跳過重複分析")
                # 生成報告和視覺化
                self._generate_analysis_report(cached_data, selected_driver, race_name, year)
                self._generate_visualization(cached_data, selected_driver, race_name, year)
                return True
            
            print(f"[INFO] 開始新的分析...")
            
            # 首先獲取賽道彎道資訊（使用與功能13相同的方法）
            print(f"\n[DEBUG] 分析賽道彎道配置...")
            # 使用排名較前的車手來檢測彎道（更可靠的遙測數據）
            reference_driver = all_drivers[0]
            corners_data = self._extract_race_corners_info(session, laps, reference_driver)
            if not corners_data:
                # 如果第一個車手失敗，嘗試前幾個車手
                for backup_driver in all_drivers[1:min(5, len(all_drivers))]:
                    corners_data = self._extract_race_corners_info(session, laps, backup_driver)
                    if corners_data:
                        reference_driver = backup_driver
                        break
                
            if not corners_data:
                print(f"[ERROR] 無法獲取賽道彎道資訊")
                return False
            
            print(f"[SUCCESS] 識別到 {len(corners_data)} 個彎道")
            
            # 分類彎道類型
            corner_types = self._classify_corner_types(corners_data)
            self._display_corner_types_summary(corner_types)
            
            # 獲取所有車手的彎道速度數據（用於評分基準）
            print(f"\n[INFO] 收集全部車手彎道數據作為評分基準...")
            all_drivers_corner_speeds = self._collect_all_drivers_corner_speeds(
                session, laps, all_drivers, corners_data
            )
            
            # 分析選定車手的彎道表現
            print(f"\n[INFO] 分析車手 {selected_driver} 的彎道表現...")
            driver_analysis = self._analyze_single_driver_corners(
                session, laps, selected_driver, corners_data, corner_types
            )
            
            if not driver_analysis:
                print(f"[ERROR] 車手 {selected_driver} 分析失敗")
                return False
            
            # 計算評分（使用全部車手數據作為基準）
            print(f"\n🔄 計算表現評分（使用全部車手基準）...")
            performance_scores = self._calculate_corner_scores(
                driver_analysis['corner_statistics'], 
                all_drivers_corner_speeds
            )
            
            driver_analysis['performance_scores'] = performance_scores
            
            # 計算整體指標
            overall_metrics = self._calculate_overall_metrics(
                performance_scores, driver_analysis['corner_type_scores']
            )
            driver_analysis['overall_metrics'] = overall_metrics
            
            # 儲存到暫存
            self._save_to_cache(driver_analysis, year, race_name, selected_driver)
            
            # 生成報告和視覺化
            self._generate_analysis_report(driver_analysis, selected_driver, race_name, year)
            self._generate_visualization(driver_analysis, selected_driver, race_name, year)
            
            print(f"\n[SUCCESS] 單一車手指定賽事全部彎道詳細分析完成！")
            return True
            
        except Exception as e:
            print(f"[ERROR] 分析過程中發生錯誤: {e}")
            traceback.print_exc()
            return False
    
    def _select_driver(self, all_drivers):
        """選擇車手"""
        while True:
            try:
                choice = input(f"\n請選擇車手編號 (1-{len(all_drivers)}) 或直接輸入車手縮寫: ").strip()
                
                if choice.isdigit():
                    idx = int(choice)
                    if 1 <= idx <= len(all_drivers):
                        return all_drivers[idx - 1]
                    else:
                        print(f"[ERROR] 請輸入有效的編號 (1-{len(all_drivers)})")
                        continue
                else:
                    # 直接輸入車手縮寫
                    choice_upper = choice.upper()
                    if choice_upper in all_drivers:
                        return choice_upper
                    else:
                        print(f"[ERROR] 車手縮寫 '{choice}' 不存在，請重新輸入")
                        continue
                        
            except KeyboardInterrupt:
                print("\n[WARNING] 用戶取消操作")
                return None
            except EOFError:
                print("\n[WARNING] 輸入終止，使用第一個車手")
                return all_drivers[0]
            except Exception as e:
                print(f"[ERROR] 輸入處理錯誤: {e}")
                continue
    
    def _extract_race_corners_info(self, session, laps, reference_driver):
        """提取比賽賽道彎道資訊 - 優先使用FastF1官方彎道資訊"""
        try:
            print(f"   [DEBUG] 正在分析車手 {reference_driver} 的彎道資訊...")
            
            # 方法1: 嘗試使用FastF1官方彎道資訊
            try:
                circuit_info = session.get_circuit_info()
                if hasattr(circuit_info, 'corners') and circuit_info.corners is not None:
                    official_corners = circuit_info.corners
                    if len(official_corners) > 0:
                        print(f"   [SUCCESS] 使用官方彎道資訊，共 {len(official_corners)} 個彎道")
                        
                        # 轉換為標準格式
                        corners_data = {}
                        for i, (idx, corner) in enumerate(official_corners.iterrows(), 1):
                            corners_data[i] = {
                                'corner_number': i,
                                'distance': corner.get('Distance', i * 1000),
                                'x': corner.get('X', 0),
                                'y': corner.get('Y', 0),
                                'corner_type': 'official',
                                'start_distance': corner.get('Distance', i * 1000),
                                'end_distance': corner.get('Distance', i * 1000) + 100,
                                'min_speed': 100.0,
                                'max_speed': 200.0,
                                'avg_speed': 150.0,
                                'speed_drop': 50.0
                            }
                        return corners_data
            except Exception as e:
                print(f"   [WARNING] 無法使用官方彎道資訊: {e}")
            
            # 方法2: 使用遙測數據檢測彎道（後備方案）
            print(f"   🔄 使用遙測數據檢測彎道...")
            
            # 找到參考車手的最速圈
            driver_laps = laps[laps['Driver'] == reference_driver].copy()
            if driver_laps.empty:
                return None
            
            valid_laps = driver_laps[driver_laps['LapTime'].notna()].copy()
            if valid_laps.empty:
                return None
            
            print(f"   [INFO] 使用圈數: {len(valid_laps)}")
            
            # 找最速圈
            fastest_lap = valid_laps.loc[valid_laps['LapTime'].idxmin()]
            
            try:
                # 獲取遙測數據
                telemetry = fastest_lap.get_car_data().add_distance()
                
                if telemetry.empty or 'Speed' not in telemetry.columns:
                    print(f"[WARNING] {reference_driver} 遙測數據不完整")
                    return None
                
                # 基於速度變化識別彎道
                corners_data = self._identify_corners_from_speed(telemetry)
                if corners_data:
                    print(f"   [SUCCESS] 從遙測數據檢測到 {len(corners_data)} 個彎道")
                return corners_data
                
            except Exception as e:
                print(f"[WARNING] 獲取 {reference_driver} 遙測數據失敗: {e}")
                return None
                
        except Exception as e:
            print(f"[ERROR] 提取彎道資訊失敗: {e}")
            return None
    
    def _identify_corners_from_speed(self, telemetry):
        """從速度變化識別彎道 - 與功能13完全相同"""
        try:
            speeds = telemetry['Speed'].values
            distances = telemetry['Distance'].values
            
            # 計算速度變化率
            speed_changes = np.diff(speeds)
            
            # 找到速度大幅下降的點（彎道入口）
            decel_threshold = -10  # km/h per data point
            corner_starts = []
            
            for i in range(len(speed_changes)):
                if speed_changes[i] < decel_threshold:
                    corner_starts.append(i)
            
            # 合併相近的彎道點
            corners_data = {}
            corner_num = 1
            
            i = 0
            while i < len(corner_starts):
                start_idx = corner_starts[i]
                
                # 尋找這個彎道的結束點
                end_idx = start_idx
                while (end_idx < len(speeds) - 1 and 
                       speeds[end_idx] < speeds[start_idx] * 1.1):
                    end_idx += 1
                
                # 計算彎道統計
                corner_speeds = speeds[start_idx:end_idx+1]
                if len(corner_speeds) > 5:  # 過濾太短的彎道
                    corners_data[corner_num] = {
                        'start_distance': distances[start_idx],
                        'end_distance': distances[end_idx],
                        'min_speed': np.min(corner_speeds),
                        'max_speed': np.max(corner_speeds),
                        'avg_speed': np.mean(corner_speeds),
                        'speed_drop': speeds[start_idx] - np.min(corner_speeds)
                    }
                    corner_num += 1
                
                # 跳過相近的點
                while (i < len(corner_starts) - 1 and 
                       corner_starts[i + 1] - start_idx < 50):  # 50個數據點的間隔
                    i += 1
                i += 1
            
            return corners_data
            
        except Exception as e:
            print(f"[ERROR] 識別彎道失敗: {e}")
            return {}
    
    def _classify_corner_types(self, corners_data):
        """分類彎道類型 - 適應官方彎道資訊和遙測檢測"""
        corner_types = {
            'high_speed': {'count': 0, 'corners': [], 'description': '高速彎道 (>200 km/h)'},
            'medium_speed': {'count': 0, 'corners': [], 'description': '中速彎道 (100-200 km/h)'},
            'low_speed': {'count': 0, 'corners': [], 'description': '低速彎道 (<100 km/h)'},
            'hairpin': {'count': 0, 'corners': [], 'description': '髮夾彎 (速度降幅>100 km/h)'}
        }
        
        for corner_num, corner_info in corners_data.items():
            # 檢查是否為官方彎道資訊
            if corner_info.get('corner_type') == 'official':
                # 官方彎道資訊，使用預設分類
                if corner_num <= 6:  # 前6個彎道通常是高速彎
                    corner_types['high_speed']['count'] += 1
                    corner_types['high_speed']['corners'].append(corner_num)
                elif corner_num <= 12:  # 中間彎道通常是中速彎
                    corner_types['medium_speed']['count'] += 1
                    corner_types['medium_speed']['corners'].append(corner_num)
                else:  # 後面彎道通常是低速彎
                    corner_types['low_speed']['count'] += 1
                    corner_types['low_speed']['corners'].append(corner_num)
            else:
                # 遙測檢測的彎道，使用速度分類
                min_speed = corner_info.get('min_speed', 100)
                speed_drop = corner_info.get('speed_drop', 0)
                
                # 髮夾彎判斷
                if speed_drop > 100:
                    corner_types['hairpin']['count'] += 1
                    corner_types['hairpin']['corners'].append(corner_num)
                # 速度分類
                elif min_speed > 200:
                    corner_types['high_speed']['count'] += 1
                    corner_types['high_speed']['corners'].append(corner_num)
                elif min_speed > 100:
                    corner_types['medium_speed']['count'] += 1
                    corner_types['medium_speed']['corners'].append(corner_num)
                else:
                    corner_types['low_speed']['count'] += 1
                    corner_types['low_speed']['corners'].append(corner_num)
        
        return corner_types
    
    def _display_corner_types_summary(self, corner_types):
        return corner_types
    
    def _display_corner_types_summary(self, corner_types):
        """顯示彎道類型統計 - 與功能13完全相同"""
        print(f"\n[FINISH] 賽道彎道類型分析:")
        for type_name, type_info in corner_types.items():
            if type_info['count'] > 0:
                corner_list = ', '.join([f'T{c}' for c in type_info['corners']])
                print(f"   {type_info['description']}: {type_info['count']}個 ({corner_list})")
    
    def _collect_all_drivers_corner_speeds(self, session, laps, all_drivers, corners_data):
        """收集所有車手的彎道速度數據（用於評分基準）- 改進版本"""
        all_drivers_corner_speeds = {}
        
        print(f"   [INFO] 正在收集 {len(all_drivers)} 位車手的彎道數據...")
        
        for driver in all_drivers:
            try:
                driver_laps = laps[laps['Driver'] == driver].copy()
                
                # 使用與功能13相同的圈數過濾
                valid_laps, _ = self._filter_valid_laps_enhanced(driver_laps)
                
                if len(valid_laps) < 3:
                    continue
                
                # 分析每個彎道
                for corner_num in corners_data.keys():
                    corner_speeds = []
                    corner_info = corners_data[corner_num]
                    
                    # 檢查是否為官方彎道資訊
                    if corner_info.get('corner_type') == 'official':
                        # 對於官方彎道，使用更智能的方法收集速度數據
                        corner_speeds = self._collect_corner_speeds_smart(valid_laps, corner_num, len(corners_data))
                    else:
                        # 對於遙測檢測的彎道，使用原有方法
                        corner_speeds = self._collect_corner_speeds_by_distance(valid_laps, corner_info)
                    
                    # 添加到全部車手數據中
                    if len(corner_speeds) > 5:
                        if corner_num not in all_drivers_corner_speeds:
                            all_drivers_corner_speeds[corner_num] = []
                        all_drivers_corner_speeds[corner_num].extend(corner_speeds)
                        
            except Exception as e:
                continue
        
        print(f"   [SUCCESS] 收集完成，共處理 {len(all_drivers_corner_speeds)} 個彎道")
        return all_drivers_corner_speeds
    
    def _collect_corner_speeds_smart(self, valid_laps, corner_num, total_corners):
        """智能收集彎道速度（用於官方彎道資訊）"""
        corner_speeds = []
        
        for lap_idx, lap in valid_laps.iterrows():
            try:
                telemetry = lap.get_car_data().add_distance()
                if telemetry.empty or 'Speed' not in telemetry.columns:
                    continue
                
                # 根據彎道編號估算位置（平均分配）
                total_distance = telemetry['Distance'].max()
                section_length = total_distance / total_corners
                
                # 計算該彎道的大概位置
                start_pos = (corner_num - 1) * section_length
                end_pos = start_pos + section_length * 0.3  # 彎道佔30%的區段長度
                
                # 獲取該區段的速度數據
                corner_mask = ((telemetry['Distance'] >= start_pos) & 
                             (telemetry['Distance'] <= end_pos))
                corner_telemetry = telemetry[corner_mask]
                
                if not corner_telemetry.empty:
                    # 取該區段的最低速度（彎道通常是最慢的）
                    min_speeds = corner_telemetry.nsmallest(5, 'Speed')['Speed'].tolist()
                    corner_speeds.extend(min_speeds)
            
            except Exception as e:
                continue
        
        return corner_speeds
    
    def _collect_corner_speeds_by_distance(self, valid_laps, corner_info):
        """根據距離範圍收集彎道速度（用於遙測檢測的彎道）"""
        corner_speeds = []
        
        for lap_idx, lap in valid_laps.iterrows():
            try:
                telemetry = lap.get_car_data().add_distance()
                if telemetry.empty or 'Speed' not in telemetry.columns:
                    continue
                
                # 使用精確的距離範圍
                start_dist = corner_info['start_distance']
                end_dist = corner_info['end_distance']
                
                # 獲取彎道範圍內的遙測數據
                corner_mask = ((telemetry['Distance'] >= start_dist) & 
                             (telemetry['Distance'] <= end_dist))
                corner_telemetry = telemetry[corner_mask]
                
                if not corner_telemetry.empty:
                    corner_speeds.extend(corner_telemetry['Speed'].tolist())
            
            except Exception as e:
                continue
        
        return corner_speeds
    
    def _collect_single_lap_corner_speeds_smart(self, telemetry, corner_num, total_corners):
        """為單圈智能收集彎道速度（用於官方彎道資訊）"""
        # 根據彎道編號估算位置（平均分配）
        total_distance = telemetry['Distance'].max()
        section_length = total_distance / total_corners
        
        # 計算該彎道的大概位置
        start_pos = (corner_num - 1) * section_length
        end_pos = start_pos + section_length * 0.3  # 彎道佔30%的區段長度
        
        # 獲取該區段的速度數據
        corner_mask = ((telemetry['Distance'] >= start_pos) & 
                     (telemetry['Distance'] <= end_pos))
        corner_telemetry = telemetry[corner_mask]
        
        if not corner_telemetry.empty:
            # 取該區段的最低速度（彎道通常是最慢的）
            min_speeds = corner_telemetry.nsmallest(5, 'Speed')['Speed'].tolist()
            return min_speeds
        
        return []
    
    def _collect_single_lap_corner_speeds_by_distance(self, telemetry, corner_info):
        """為單圈根據距離範圍收集彎道速度"""
        start_dist = corner_info['start_distance']
        end_dist = corner_info['end_distance']
        
        # 獲取彎道範圍內的遙測數據
        corner_mask = ((telemetry['Distance'] >= start_dist) & 
                     (telemetry['Distance'] <= end_dist))
        corner_telemetry = telemetry[corner_mask]
        
        if not corner_telemetry.empty:
            return corner_telemetry['Speed'].tolist()
        
        return []
    
    def _filter_valid_laps_enhanced(self, driver_laps):
        """增強的有效圈過濾 - 與功能13完全相同"""
        filtering_stats = {
            'slow_laps': 0,
            'flag_laps': 0,
            'outlier_laps': 0
        }
        
        if driver_laps.empty:
            return driver_laps, filtering_stats
        
        # 移除無圈時的圈
        valid_laps = driver_laps[driver_laps['LapTime'].notna()].copy()
        
        if len(valid_laps) < 3:
            return valid_laps, filtering_stats
        
        # 計算圈時統計
        lap_times = valid_laps['LapTime'].dt.total_seconds()
        median_time = lap_times.median()
        std_time = lap_times.std()
        
        # 過濾明顯過慢的圈（超过中位數的130%）
        slow_threshold = median_time * 1.3
        slow_mask = lap_times > slow_threshold
        filtering_stats['slow_laps'] = slow_mask.sum()
        
        # 過濾異常值（超過2個標準差）
        if std_time > 0:
            outlier_mask = np.abs(lap_times - median_time) > 2 * std_time
            filtering_stats['outlier_laps'] = outlier_mask.sum()
        else:
            outlier_mask = pd.Series([False] * len(valid_laps), index=valid_laps.index)
        
        # 合併過濾條件
        final_mask = ~(slow_mask | outlier_mask)
        filtered_laps = valid_laps[final_mask]
        
        return filtered_laps, filtering_stats
    
    def _analyze_single_driver_corners(self, session, laps, driver, corners_data, corner_types):
        """分析單一車手的彎道表現 - 基於功能13但專注於單一車手"""
        try:
            # 獲取車手圈數數據
            driver_laps = laps[laps['Driver'] == driver].copy()
            
            # 使用增強過濾
            valid_laps, filtering_stats = self._filter_valid_laps_enhanced(driver_laps)
            
            if len(valid_laps) < 3:
                print(f"   [WARNING] {driver} 有效圈數不足 ({len(valid_laps)})")
                return None
            
            print(f"   [INFO] {driver}: 總圈數 {len(driver_laps)}, 有效圈數 {len(valid_laps)}")
            
            # 分析結果容器
            driver_analysis = {
                'driver_name': driver,
                'analyzed_laps': len(valid_laps),
                'valid_laps_count': len(valid_laps),
                'corner_statistics': {},
                'corner_type_scores': {},
                'lap_by_lap_data': []  # 新增：每圈的彎道表現數據
            }
            
            # 分析每個彎道
            corner_statistics = {}
            lap_by_lap_data = []
            
            # 收集每圈數據
            for lap_num, (lap_idx, lap) in enumerate(valid_laps.iterrows(), 1):
                lap_data = {'lap_number': lap_num, 'corners': {}}
                
                try:
                    telemetry = lap.get_car_data().add_distance()
                    if telemetry.empty or 'Speed' not in telemetry.columns:
                        continue
                    
                    # 分析該圈每個彎道
                    for corner_num in corners_data.keys():
                        corner_info = corners_data[corner_num]
                        
                        # 根據彎道類型選擇收集方法
                        if corner_info.get('corner_type') == 'official':
                            # 官方彎道使用智能收集
                            corner_speeds = self._collect_single_lap_corner_speeds_smart(
                                telemetry, corner_num, len(corners_data)
                            )
                        else:
                            # 遙測彎道使用距離範圍
                            corner_speeds = self._collect_single_lap_corner_speeds_by_distance(
                                telemetry, corner_info
                            )
                        
                        if corner_speeds:
                            avg_speed = np.mean(corner_speeds)
                            max_speed = np.max(corner_speeds)
                            
                            lap_data['corners'][corner_num] = {
                                'avg_speed': avg_speed,
                                'max_speed': max_speed,
                                'speeds': corner_speeds
                            }
                            
                            # 累積到彎道統計中
                            if corner_num not in corner_statistics:
                                corner_statistics[corner_num] = {
                                    'speeds': [],
                                    'lap_count': 0
                                }
                            
                            corner_statistics[corner_num]['speeds'].extend(corner_speeds)
                            corner_statistics[corner_num]['lap_count'] += 1
                
                except Exception as e:
                    continue
                
                lap_by_lap_data.append(lap_data)
            
            # 計算每個彎道的統計數據
            for corner_num, stats in corner_statistics.items():
                if len(stats['speeds']) > 5:
                    corner_statistics[corner_num].update({
                        'avg_speed': np.mean(stats['speeds']),
                        'max_speed': np.max(stats['speeds']),
                        'median_speed': np.median(stats['speeds']),
                        'std_deviation': np.std(stats['speeds']),
                    })
            
            driver_analysis['corner_statistics'] = corner_statistics
            driver_analysis['lap_by_lap_data'] = lap_by_lap_data
            
            # 計算彎道類型得分
            corner_type_scores = self._calculate_corner_type_scores(corner_statistics, corner_types)
            driver_analysis['corner_type_scores'] = corner_type_scores
            
            if len(corner_statistics) == 0:
                print(f"   [ERROR] {driver} 沒有有效的彎道數據")
                return None
            
            print(f"   [SUCCESS] {driver} 成功分析 {len(corner_statistics)} 個彎道")
            return driver_analysis
            
        except Exception as e:
            print(f"   [ERROR] {driver} 分析失敗: {e}")
            return None
    
    def _calculate_corner_type_scores(self, corner_statistics, corner_types):
        """計算彎道類型評分 - 與功能13完全相同"""
        corner_type_scores = {}
        
        for type_name, type_info in corner_types.items():
            if type_info['count'] == 0:
                continue
            
            type_speeds = []
            type_corners = []
            
            for corner_num in type_info['corners']:
                if corner_num in corner_statistics:
                    corner_data = corner_statistics[corner_num]
                    type_speeds.extend(corner_data['speeds'])
                    type_corners.append(corner_num)
            
            if type_speeds:
                corner_type_scores[type_name] = {
                    'avg_speed': np.mean(type_speeds),
                    'max_speed': np.max(type_speeds),
                    'stability': 1 / (1 + np.std(type_speeds) / np.mean(type_speeds)) if np.mean(type_speeds) > 0 else 0,
                    'corner_count': len(type_corners),
                    'avg_performance_score': np.mean(type_speeds) / 3.0,  # 簡單的性能評分
                    'stability_score': 100 * (1 / (1 + np.std(type_speeds) / np.mean(type_speeds))) if np.mean(type_speeds) > 0 else 0
                }
        
        return corner_type_scores
    
    def _calculate_corner_scores(self, corner_statistics, all_drivers_corner_speeds):
        """計算彎道評分（使用與功能13完全相同的評分標準）"""
        performance_scores = {}
        
        for corner_num, corner_stats in corner_statistics.items():
            if corner_num not in all_drivers_corner_speeds:
                continue
            
            # 該車手在該彎道的表現
            driver_avg_speed = corner_stats['avg_speed']
            driver_max_speed = corner_stats['max_speed']
            driver_speeds = corner_stats['speeds']
            
            # 全部車手在該彎道的速度分佈
            all_speeds = all_drivers_corner_speeds[corner_num]
            if len(all_speeds) == 0:
                continue
            
            # 計算中位數作為基準（與功能13相同）
            median_speed = np.median(all_speeds)
            
            # 表現評分計算：使用與功能13相同的方法
            # (車手速度 / 中位數速度) * 100，限制在0-150之間
            speed_performance = (driver_avg_speed / median_speed) * 100 if median_speed > 0 else 0
            speed_performance = min(max(speed_performance, 0), 150)  # 限制範圍0-150
            
            # 最終表現評分：轉換到0-100範圍
            # 100分對應速度比中位數快25%，即speed_performance = 125
            final_performance = min((speed_performance / 125) * 100, 100)
            
            # 穩定度評分：使用與功能13相同的一致性計算
            if len(driver_speeds) > 1:
                # 計算一致性分數（與功能13相同）
                driver_consistency = 100 * (1 / (1 + np.std(driver_speeds) / np.mean(driver_speeds))) if np.mean(driver_speeds) > 0 else 0
                stability_score = min(max(driver_consistency, 0), 100)
            else:
                stability_score = 0
            
            performance_scores[corner_num] = {
                'performance_score': final_performance,
                'stability_score': stability_score,
                'avg_speed': driver_avg_speed,
                'max_speed': driver_max_speed,
                'median_reference': median_speed,
                'raw_speed_ratio': speed_performance
            }
        
        return performance_scores
    
    def _calculate_overall_metrics(self, performance_scores, corner_type_scores):
        """計算車手整體指標（使用與功能13完全相同的方法）"""
        try:
            if not performance_scores:
                return {
                    'overall_performance_score': 0,
                    'overall_stability_score': 0,
                    'analyzed_corners': 0,
                    'total_corner_types': 0
                }
            
            # 收集所有評分（與功能13相同）
            speed_scores = [score['performance_score'] for score in performance_scores.values()]
            consistency_scores = [score['stability_score'] for score in performance_scores.values()]
            
            overall_metrics = {
                'overall_performance_score': min(np.mean(speed_scores), 100) if speed_scores else 0,
                'overall_stability_score': min(np.mean(consistency_scores), 100) if consistency_scores else 0,
                'analyzed_corners': len(performance_scores),
                'total_corner_types': len(corner_type_scores) if corner_type_scores else 0
            }
            
            return overall_metrics
            
        except Exception as e:
            print(f"   [ERROR] 計算整體指標失敗: {e}")
            return {
                'overall_performance_score': 0,
                'overall_stability_score': 0,
                'analyzed_corners': 0,
                'total_corner_types': 0
            }
    
    def _generate_analysis_report(self, driver_analysis, driver_name, race_name, year):
        """生成分析報告"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            print(f"\n[INFO] 生成 {driver_name} 彎道表現分析報告...")
            
            # 彎道表現摘要表
            print(f"\n[LIST] 彎道表現摘要表")
            summary_table = PrettyTable()
            summary_table.field_names = ["彎道", "平均速度", "最高速度", "中位速度", "最低速度", "表現評分", "穩定度評分"]
            summary_table.align = "c"
            
            performance_scores = driver_analysis.get('performance_scores', {})
            corner_statistics = driver_analysis.get('corner_statistics', {})
            
            for corner_num in sorted(corner_statistics.keys()):
                if corner_num in performance_scores:
                    scores = performance_scores[corner_num]
                    stats = corner_statistics[corner_num]
                    
                    # 計算中位速度和最低速度
                    speeds = stats.get('speeds', [])
                    filtered_speeds = [s for s in speeds if s >= 50]  # 過濾低於50的速度
                    median_speed = np.median(filtered_speeds) if filtered_speeds else 0
                    min_speed = np.min(filtered_speeds) if filtered_speeds else 0
                    
                    summary_table.add_row([
                        f"T{corner_num}",
                        f"{scores['avg_speed']:.1f}",
                        f"{scores['max_speed']:.1f}",
                        f"{median_speed:.1f}",
                        f"{min_speed:.1f}",
                        f"{scores['performance_score']:.1f}",
                        f"{scores['stability_score']:.1f}"
                    ])
            
            print(summary_table)
            
            # 整體表現統計
            overall_metrics = driver_analysis.get('overall_metrics', {})
            print(f"\n[STATS] 整體表現統計")
            print(f"   整體表現評分: {overall_metrics.get('overall_performance_score', 0):.1f}/100")
            print(f"   整體穩定度評分: {overall_metrics.get('overall_stability_score', 0):.1f}/100")
            print(f"   分析彎道數: {overall_metrics.get('analyzed_corners', 0)}")
            print(f"   有效圈數: {driver_analysis.get('analyzed_laps', 0)}")
            
            print(f"[SUCCESS] 分析報告生成完成")
            
        except Exception as e:
            print(f"[ERROR] 生成報告時發生錯誤: {e}")
    
    def _generate_visualization(self, driver_analysis, driver_name, race_name, year):
        """生成視覺化圖表 - 使用plt.show()"""
        try:
            print(f"\n[STATS] 生成 {driver_name} 彎道表現視覺化圖表...")
            
            # 設置中文字體
            plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
            plt.rcParams['axes.unicode_minus'] = False
            
            performance_scores = driver_analysis.get('performance_scores', {})
            
            if not performance_scores:
                print("[WARNING] 沒有可視化的數據")
                return
            
            # 創建圖表布局（3x2）
            fig = plt.figure(figsize=(18, 15))
            fig.suptitle(f'{driver_name} - {race_name} 彎道表現分析', fontsize=16)
            
            # 1. 彎道速度Box-and-Whisker圖
            ax1 = plt.subplot(3, 2, 1)
            corner_nums = sorted(performance_scores.keys())
            
            # 收集每個彎道的所有速度數據（用於箱線圖），過濾低於50的速度
            corner_speed_data = []
            corner_labels = []
            
            for corner_num in corner_nums:
                if corner_num in driver_analysis['corner_statistics']:
                    speeds = driver_analysis['corner_statistics'][corner_num]['speeds']
                    # 過濾低於50的速度
                    filtered_speeds = [s for s in speeds if s >= 50]
                    if filtered_speeds:
                        corner_speed_data.append(filtered_speeds)
                        corner_labels.append(f'T{corner_num}')
            
            if corner_speed_data:
                # 創建箱線圖
                box_plot = ax1.boxplot(corner_speed_data, labels=corner_labels, patch_artist=True)
                
                # 美化箱線圖
                for patch in box_plot['boxes']:
                    patch.set_facecolor('skyblue')
                    patch.set_alpha(0.7)
                
                for whisker in box_plot['whiskers']:
                    whisker.set_color('navy')
                    whisker.set_linewidth(1.5)
                
                for cap in box_plot['caps']:
                    cap.set_color('navy')
                    cap.set_linewidth(1.5)
                
                for median in box_plot['medians']:
                    median.set_color('red')
                    median.set_linewidth(2)
                
                # 設置離群值樣式
                for flier in box_plot['fliers']:
                    flier.set_marker('o')
                    flier.set_markerfacecolor('red')
                    flier.set_markersize(4)
                    flier.set_alpha(0.6)
                
                ax1.set_xlabel('彎道')
                ax1.set_ylabel('速度 (km/h)')
                ax1.set_title('各彎道速度分布 (箱線圖)')
                ax1.grid(True, axis='y', alpha=0.3)
                
                # 旋轉x軸標籤以避免重疊
                plt.setp(ax1.get_xticklabels(), rotation=45)
            else:
                ax1.text(0.5, 0.5, '無速度數據', transform=ax1.transAxes, ha='center', va='center')
                ax1.set_title('各彎道速度分布')
            
            # 2. 表現評分與穩定度評分
            ax2 = plt.subplot(3, 2, 2)
            performance_vals = [performance_scores[c]['performance_score'] for c in corner_nums]
            stability_vals = [performance_scores[c]['stability_score'] for c in corner_nums]
            
            x_pos = range(len(corner_nums))
            ax2.plot(x_pos, performance_vals, 'o-', label='表現評分', linewidth=2, markersize=6)
            ax2.plot(x_pos, stability_vals, 's-', label='穩定度評分', linewidth=2, markersize=6)
            ax2.set_xlabel('彎道')
            ax2.set_ylabel('評分')
            ax2.set_title('彎道表現與穩定度評分')
            ax2.set_xticks(x_pos)
            ax2.set_xticklabels([f'T{c}' for c in corner_nums])
            ax2.set_ylim(0, 100)
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            plt.setp(ax2.get_xticklabels(), rotation=45)
            
            # 3. 彎道表現雷達圖（顯示全部彎道編號）
            ax3 = plt.subplot(3, 2, 3, projection='polar')
            if len(corner_nums) > 0:
                radar_corners = corner_nums
                radar_scores = [performance_scores[c]['performance_score'] for c in radar_corners]
                
                # 創建雷達圖
                angles = np.linspace(0, 2 * np.pi, len(radar_corners), endpoint=False)
                radar_scores_plot = radar_scores + [radar_scores[0]]  # 閉合圖形
                angles_plot = np.concatenate((angles, [angles[0]]))
                
                ax3.plot(angles_plot, radar_scores_plot, 'o-', linewidth=2, markersize=4)
                ax3.fill(angles_plot, radar_scores_plot, alpha=0.25)
                ax3.set_xticks(angles)
                
                # 顯示所有彎道編號，但調整字體大小以避免重疊
                labels = [f'T{c}' for c in radar_corners]
                ax3.set_xticklabels(labels, fontsize=max(6, 12 - len(radar_corners) // 3))
                ax3.set_ylim(0, 100)
                ax3.set_title(f'彎道表現雷達圖 ({len(radar_corners)}個彎道)', y=1.08)
                ax3.grid(True)
            
            # 4. 速度分布與穩定度複合圖
            ax4 = plt.subplot(3, 2, 4)
            
            # 收集每個彎道的速度數據和穩定度評分
            corner_speed_data = []  # 用於箱線圖的速度數據
            stability_scores = []
            corner_names = []
            corner_positions = []
            
            for i, corner_num in enumerate(corner_nums):
                if corner_num in driver_analysis['corner_statistics']:
                    speeds = driver_analysis['corner_statistics'][corner_num]['speeds']
                    filtered_speeds = [s for s in speeds if s >= 50]  # 過濾低於50的速度
                    if filtered_speeds and len(filtered_speeds) >= 3:  # 確保有足夠數據繪製箱線圖
                        stability_score = performance_scores[corner_num]['stability_score']
                        
                        corner_speed_data.append(filtered_speeds)
                        stability_scores.append(stability_score)
                        corner_names.append(f'T{corner_num}')
                        corner_positions.append(i + 1)  # 箱線圖位置從1開始
            
            if corner_speed_data:
                # 創建雙軸圖
                ax4_twin = ax4.twinx()
                
                # 速度箱線圖
                bp = ax4.boxplot(corner_speed_data, positions=corner_positions, 
                               patch_artist=True, widths=0.6)
                
                # 設置箱線圖樣式
                for patch in bp['boxes']:
                    patch.set_facecolor('skyblue')
                    patch.set_alpha(0.7)
                for whisker in bp['whiskers']:
                    whisker.set_color('navy')
                    whisker.set_linewidth(2)
                for cap in bp['caps']:
                    cap.set_color('navy')
                    cap.set_linewidth(2)
                for median in bp['medians']:
                    median.set_color('red')
                    median.set_linewidth(2)
                for flier in bp['fliers']:
                    flier.set_marker('o')
                    flier.set_markerfacecolor('red')
                    flier.set_markersize(4)
                    flier.set_alpha(0.7)
                
                # 穩定度折線圖
                line = ax4_twin.plot(corner_positions, stability_scores, 'ro-', 
                                   linewidth=2, markersize=6, label='穩定度評分')
                
                ax4.set_xlabel('彎道')
                ax4.set_ylabel('速度分布 (km/h)', color='blue')
                ax4_twin.set_ylabel('穩定度評分', color='red')
                ax4.set_title('速度分布箱線圖與穩定度複合圖')
                ax4.set_xticks(corner_positions)
                ax4.set_xticklabels(corner_names)
                ax4_twin.set_ylim(0, 100)
                
                # 添加圖例
                ax4.plot([], [], 's', color='skyblue', alpha=0.7, label='速度分布')
                lines2, labels2 = ax4_twin.get_legend_handles_labels()
                ax4.legend(loc='upper left')
                ax4_twin.legend(loc='upper right')
                
                ax4.grid(True, alpha=0.3)
                plt.setp(ax4.get_xticklabels(), rotation=45)
            
            # 5. 彎道類型分析
            ax5 = plt.subplot(3, 2, 5)
            
            # 統計不同類型彎道的表現
            corner_types = driver_analysis.get('corner_type_scores', {})
            if corner_types:
                type_names = []
                type_scores = []
                type_counts = []
                
                for type_name, type_data in corner_types.items():
                    if type_data.get('avg_performance_score', 0) > 0:
                        type_names.append(type_name.replace('_', ' ').title())
                        type_scores.append(type_data['avg_performance_score'])
                        type_counts.append(type_data['corner_count'])
                
                if type_names:
                    bars = ax5.bar(type_names, type_scores, color=['lightcoral', 'lightblue', 'lightgreen', 'lightyellow'][:len(type_names)])
                    
                    # 在條形圖上添加彎道數量
                    for i, (bar, count) in enumerate(zip(bars, type_counts)):
                        ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                                f'{count}個彎道', ha='center', va='bottom', fontsize=10)
                    
                    ax5.set_ylabel('平均表現評分')
                    ax5.set_title('彎道類型表現分析')
                    ax5.set_ylim(0, 100)
                    ax5.grid(True, axis='y', alpha=0.3)
            
            # 6. 整體表現統計
            ax6 = plt.subplot(3, 2, 6)
            overall_metrics = driver_analysis.get('overall_metrics', {})
            ax6.text(0.5, 0.7, f"整體表現評分\n{overall_metrics.get('overall_performance_score', 0):.1f}/100", 
                    transform=ax6.transAxes, ha='center', va='center', fontsize=18,
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue"))
            ax6.text(0.5, 0.3, f"整體穩定度評分\n{overall_metrics.get('overall_stability_score', 0):.1f}/100", 
                    transform=ax6.transAxes, ha='center', va='center', fontsize=18,
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen"))
            ax6.text(0.5, 0.1, f"分析彎道數: {overall_metrics.get('analyzed_corners', 0)}", 
                    transform=ax6.transAxes, ha='center', va='center', fontsize=14)
            ax6.set_title('整體表現統計')
            ax6.axis('off')
            
            plt.tight_layout()
            # plt.show()  # 圖表顯示已禁用 - 直接顯示而不保存文件
            
            print("[SUCCESS] 視覺化圖表生成已完成（顯示已禁用）")
            
        except Exception as e:
            print(f"[ERROR] 生成視覺化圖表時發生錯誤: {e}")
            traceback.print_exc()
    
    def _display_summary_only(self, driver_analysis, driver_name):
        """顯示緩存數據的摘要 - 符合開發核心原則"""
        try:
            overall_metrics = driver_analysis.get('overall_metrics', {})
            corner_data = driver_analysis.get('corner_data', {})
            
            print(f"\n📊 {driver_name} 彎道表現摘要（來自緩存）:")
            print(f"   • 整體表現評分: {overall_metrics.get('overall_performance_score', 0):.1f}/100")
            print(f"   • 整體穩定度評分: {overall_metrics.get('overall_stability_score', 0):.1f}/100")
            print(f"   • 分析彎道數: {overall_metrics.get('analyzed_corners', 0)}")
            print(f"   • 有效圈數: {overall_metrics.get('total_laps', 0)}")
            
            if corner_data:
                best_performance = max(corner_data.values(), key=lambda x: x.get('performance_score', 0))
                best_stability = max(corner_data.values(), key=lambda x: x.get('stability_score', 0))
                
                print(f"   • 最佳表現彎道: {best_performance.get('corner_name', 'N/A')} ({best_performance.get('performance_score', 0):.1f}分)")
                print(f"   • 最穩定彎道: {best_stability.get('corner_name', 'N/A')} ({best_stability.get('stability_score', 0):.1f}分)")
            
            print("💾 詳細數據已從緩存載入，使用 --show-detailed-output 查看完整表格")
            
        except Exception as e:
            print(f"[WARNING] 摘要顯示失敗: {e}")

# 模組測試
if __name__ == "__main__":
    print("🧪 單一車手指定賽事全部彎道詳細分析模組測試")
    print("此模組需要在完整的F1分析系統中運行")
