#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
動態彎道檢測分析模組
Dynamic Corner Detection Analysis Module

功能：基於遙測數據自動檢測賽道彎道位置
- 速度變化檢測
- 方向角變化檢測  
- 彎道信心度評分
- 彎道特徵分析
- 支援所有賽道的通用檢測

版本: 1.0
作者: F1 Analysis Team
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
import json
import pickle
from math import atan2, degrees
from prettytable import PrettyTable

# 確保能夠導入基礎模組
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from base import initialize_data_loader, setup_matplotlib_chinese


class DynamicCornerDetectionAnalysis:
    """動態彎道檢測分析類"""
    
    def __init__(self, data_loader=None, year=None, race=None, session='R'):
        """
        初始化動態彎道檢測分析
        
        Args:
            data_loader: 數據載入器
            year: 賽季年份
            race: 賽事名稱
            session: 賽段 ('R'=正賽, 'Q'=排位賽, 'P'=練習賽)
        """
        self.data_loader = initialize_data_loader(data_loader)
        self.year = year
        self.race = race
        self.session = session
        self.cache_enabled = True
        
        # 設置中文字體
        setup_matplotlib_chinese()
        
        # 檢測參數 - 針對不同賽道可調整
        self.detection_params = {
            'speed_threshold': 12,      # 速度下降閾值 (km/h)
            'direction_threshold': 20,  # 方向角變化閾值 (度)
            'min_corner_distance': 80,  # 彎道最小間隔 (m)
            'window_size': 15,          # 滑動窗口大小
            'confidence_threshold': 0.5 # 最低信心度閾值
        }
    
    def analyze(self, driver='VER', show_detailed_output=True, export_json=True, **kwargs):
        """
        執行動態彎道檢測分析
        
        Args:
            driver: 車手代碼
            show_detailed_output: 是否顯示詳細輸出
            export_json: 是否導出JSON
            **kwargs: 其他參數
        """
        print(f"🚀 開始執行動態彎道檢測分析...")
        
        # 檢查緩存
        cache_key = self._generate_cache_key(driver, **kwargs)
        if self.cache_enabled:
            cached_result = self._check_cache(cache_key)
            if cached_result and not show_detailed_output:
                print("📦 使用緩存數據")
                self._report_analysis_results(cached_result, "動態彎道檢測")
                return cached_result
            elif cached_result and show_detailed_output:
                print("📦 使用緩存數據 + 📊 顯示詳細分析結果")
                self._display_detailed_output(cached_result, driver)
                return cached_result
        
        print("🔄 重新計算 - 開始動態彎道檢測...")
        
        # 載入遙測數據
        telemetry_data = self._load_telemetry_data(driver)
        if telemetry_data is None:
            print("❌ 無法載入遙測數據")
            return None
        
        # 執行動態檢測
        corners_data = self._perform_corner_detection(telemetry_data, driver)
        if not corners_data:
            print("❌ 彎道檢測失敗")
            return None
        
        # 分析彎道特徵
        analysis_result = self._analyze_corner_features(corners_data, driver)
        
        # 顯示結果
        if show_detailed_output:
            self._display_detailed_output(analysis_result, driver)
        
        # 導出JSON
        if export_json:
            self._export_json(analysis_result, driver)
        
        # 緩存結果
        if self.cache_enabled and analysis_result:
            self._save_cache(analysis_result, cache_key)
            print("💾 分析結果已緩存")
        
        # 報告結果
        if not self._report_analysis_results(analysis_result, "動態彎道檢測"):
            return None
        
        return analysis_result
    
    def _load_telemetry_data(self, driver):
        """載入車手遙測數據"""
        try:
            print(f"📥 載入 {driver} 車手遙測數據...")
            
            if self.data_loader is None:
                print("❌ 數據載入器未初始化")
                return None
            
            # 檢查是否有有效的會話數據
            if not hasattr(self.data_loader, 'session') or self.data_loader.session is None:
                print("❌ 會話數據不可用")
                return None
            
            # 檢查是否有圈數數據
            if not hasattr(self.data_loader, 'laps') or self.data_loader.laps is None:
                print("❌ 圈數數據不可用")
                return None
                
            # 獲取車手最快圈
            driver_laps = self.data_loader.laps.pick_drivers([driver])
            if driver_laps.empty:
                print(f"❌ 找不到車手 {driver} 的圈數數據")
                return None
            
            fastest_lap = driver_laps.pick_fastest()
            telemetry = fastest_lap.get_telemetry()
            
            print(f"✅ 遙測數據載入成功: {len(telemetry)} 個數據點")
            return telemetry
            
        except Exception as e:
            print(f"❌ 載入遙測數據失敗: {e}")
            return None
    
    def _perform_corner_detection(self, telemetry, driver):
        """執行動態彎道檢測"""
        try:
            print(f"🔍 開始檢測 {driver} 的彎道...")
            
            corners = self.detect_corners_by_speed_and_direction(
                telemetry,
                speed_threshold=self.detection_params['speed_threshold'],
                direction_threshold=self.detection_params['direction_threshold'],
                min_corner_distance=self.detection_params['min_corner_distance']
            )
            
            if not corners:
                print("⚠️ 未檢測到任何彎道")
                return None
            
            # 過濾低信心度的彎道
            filtered_corners = [
                corner for corner in corners 
                if corner['confidence_score'] >= self.detection_params['confidence_threshold']
            ]
            
            print(f"🎯 檢測到 {len(corners)} 個彎道候選點")
            print(f"✅ 過濾後剩餘 {len(filtered_corners)} 個高信心度彎道")
            
            return filtered_corners
            
        except Exception as e:
            print(f"❌ 彎道檢測失敗: {e}")
            return None
    
    def detect_corners_by_speed_and_direction(self, telemetry, speed_threshold=12, direction_threshold=20, min_corner_distance=80):
        """
        基於速度變化和方向角變化的動態彎道檢測
        """
        corners = []
        
        # 檢查必要的欄位
        required_cols = ['Speed', 'Distance']
        if not all(col in telemetry.columns for col in required_cols):
            print(f"⚠️ 缺少必要欄位: {required_cols}")
            return corners
        
        # 計算方向角（如果有 X/Y 數據）
        heading_angles = []
        if all(col in telemetry.columns for col in ['X', 'Y']):
            heading_angles = self.calculate_heading_angle(telemetry)
        
        # 檢測速度明顯下降的區域
        window_size = self.detection_params['window_size']
        for i in range(window_size, len(telemetry) - window_size):
            window_start = i - window_size
            window_end = i + window_size
            
            # 計算速度變化
            speed_window = telemetry['Speed'].iloc[window_start:window_end]
            max_speed = speed_window.max()
            min_speed = speed_window.min()
            speed_drop = max_speed - min_speed
            
            # 速度下降檢查
            if speed_drop < speed_threshold:
                continue
            
            # 方向角變化檢查（如果有數據）
            direction_change = 0
            if heading_angles:
                angle_window = heading_angles[window_start:window_end]
                if angle_window:
                    direction_change = max(angle_window) - min(angle_window)
                    # 處理角度跨越邊界的情況
                    if direction_change > 180:
                        direction_change = 360 - direction_change
            
            # 如果有方向數據，檢查方向變化
            if heading_angles and direction_change < direction_threshold:
                continue
            
            # 找到窗口內的最低速度點作為彎道頂點
            min_speed_idx = speed_window.idxmin()
            corner_point = telemetry.loc[min_speed_idx]
            
            # 計算彎道開始和結束距離
            start_distance = telemetry['Distance'].iloc[window_start]
            end_distance = telemetry['Distance'].iloc[window_end]
            
            # 計算信心分數
            confidence_score = min(1.0, (speed_drop / 50) * 0.6 + (direction_change / 90) * 0.4)
            
            corner_data = {
                'distance': corner_point['Distance'],
                'start_distance': start_distance,
                'end_distance': end_distance,
                'min_speed': min_speed,
                'max_speed': max_speed,
                'speed_drop': speed_drop,
                'direction_change': direction_change,
                'confidence_score': confidence_score
            }
            
            corners.append(corner_data)
        
        # 去除重複的彎道並按距離排序
        corners = self.cluster_corner_candidates(corners, min_corner_distance)
        corners.sort(key=lambda x: x['distance'])
        
        return corners
    
    def calculate_heading_angle(self, telemetry):
        """計算每個點的行車方向角"""
        angles = []
        for i in range(1, len(telemetry)):
            prev_point = telemetry.iloc[i-1]
            curr_point = telemetry.iloc[i]
            
            dx = curr_point['X'] - prev_point['X']
            dy = curr_point['Y'] - prev_point['Y']
            
            if dx != 0 or dy != 0:
                angle = degrees(atan2(dy, dx))
                # 標準化角度到 0-360 範圍
                if angle < 0:
                    angle += 360
                angles.append(angle)
            else:
                # 如果沒有移動，使用前一個角度
                angles.append(angles[-1] if angles else 0)
        
        return angles
    
    def cluster_corner_candidates(self, corners, min_distance=80):
        """聚合相近的彎道候選點"""
        if not corners:
            return []
        
        # 按距離排序
        corners.sort(key=lambda x: x['distance'])
        
        clustered = []
        current_cluster = [corners[0]]
        
        for corner in corners[1:]:
            # 檢查與當前聚類的距離
            cluster_center = sum(c['distance'] for c in current_cluster) / len(current_cluster)
            
            if abs(corner['distance'] - cluster_center) <= min_distance:
                # 加入當前聚類
                current_cluster.append(corner)
            else:
                # 完成當前聚類，開始新聚類
                # 選擇信心分數最高的作為代表
                best_corner = max(current_cluster, key=lambda x: x['confidence_score'])
                clustered.append(best_corner)
                current_cluster = [corner]
        
        # 處理最後一個聚類
        if current_cluster:
            best_corner = max(current_cluster, key=lambda x: x['confidence_score'])
            clustered.append(best_corner)
        
        return clustered
    
    def _analyze_corner_features(self, corners_data, driver):
        """分析彎道特徵"""
        try:
            print("📊 分析彎道特徵...")
            
            # 計算統計數據
            total_corners = len(corners_data)
            avg_speed = np.mean([c['min_speed'] for c in corners_data])
            avg_speed_drop = np.mean([c['speed_drop'] for c in corners_data])
            avg_confidence = np.mean([c['confidence_score'] for c in corners_data])
            
            # 找出最慢和最快的彎道
            slowest_corner = min(corners_data, key=lambda x: x['min_speed'])
            fastest_corner = max(corners_data, key=lambda x: x['min_speed'])
            
            # 找出最大速度下降的彎道
            max_drop_corner = max(corners_data, key=lambda x: x['speed_drop'])
            
            # 彎道分類
            slow_corners = [c for c in corners_data if c['min_speed'] < 150]
            medium_corners = [c for c in corners_data if 150 <= c['min_speed'] < 250]
            fast_corners = [c for c in corners_data if c['min_speed'] >= 250]
            
            analysis_result = {
                'driver': driver,
                'race_info': {
                    'year': self.year,
                    'race': self.race,
                    'session': self.session
                },
                'corners_data': corners_data,
                'statistics': {
                    'total_corners': total_corners,
                    'average_speed': avg_speed,
                    'average_speed_drop': avg_speed_drop,
                    'average_confidence': avg_confidence,
                    'slowest_corner': slowest_corner,
                    'fastest_corner': fastest_corner,
                    'max_drop_corner': max_drop_corner
                },
                'classification': {
                    'slow_corners': len(slow_corners),
                    'medium_corners': len(medium_corners),
                    'fast_corners': len(fast_corners)
                },
                'detection_params': self.detection_params.copy(),
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"✅ 彎道特徵分析完成")
            return analysis_result
            
        except Exception as e:
            print(f"❌ 彎道特徵分析失敗: {e}")
            return None
    
    def _display_detailed_output(self, analysis_result, driver):
        """顯示詳細分析結果"""
        print(f"\n📊 [LIST] 動態彎道檢測結果 - {driver}")
        
        corners_data = analysis_result['corners_data']
        stats = analysis_result['statistics']
        classification = analysis_result['classification']
        
        # 顯示彎道列表
        table = PrettyTable()
        table.field_names = ["彎道", "距離(m)", "最低速度(km/h)", "速度下降(km/h)", "方向變化(度)", "信心度", "類型"]
        
        for i, corner in enumerate(corners_data):
            corner_type = "慢速" if corner['min_speed'] < 150 else ("中速" if corner['min_speed'] < 250 else "高速")
            
            table.add_row([
                f"T{i+1}",
                f"{corner['distance']:.0f}",
                f"{corner['min_speed']:.1f}",
                f"{corner['speed_drop']:.1f}",
                f"{corner['direction_change']:.1f}",
                f"{corner['confidence_score']:.2f}",
                corner_type
            ])
        
        print(table)
        
        # 顯示統計摘要
        summary_table = PrettyTable()
        summary_table.field_names = ["統計項目", "數值"]
        summary_table.add_row(["檢測到的彎道總數", f"{stats['total_corners']} 個"])
        summary_table.add_row(["平均彎道速度", f"{stats['average_speed']:.1f} km/h"])
        summary_table.add_row(["平均速度下降", f"{stats['average_speed_drop']:.1f} km/h"])
        summary_table.add_row(["平均信心度", f"{stats['average_confidence']:.2f}"])
        summary_table.add_row(["最慢彎道", f"T{corners_data.index(stats['slowest_corner'])+1} ({stats['slowest_corner']['min_speed']:.1f} km/h)"])
        summary_table.add_row(["最快彎道", f"T{corners_data.index(stats['fastest_corner'])+1} ({stats['fastest_corner']['min_speed']:.1f} km/h)"])
        summary_table.add_row(["最大速度下降", f"T{corners_data.index(stats['max_drop_corner'])+1} ({stats['max_drop_corner']['speed_drop']:.1f} km/h)"])
        
        print(f"\n📊 統計摘要:")
        print(summary_table)
        
        # 顯示彎道分類
        class_table = PrettyTable()
        class_table.field_names = ["彎道類型", "數量", "佔比"]
        class_table.add_row(["慢速彎道 (<150 km/h)", f"{classification['slow_corners']} 個", f"{classification['slow_corners']/stats['total_corners']*100:.1f}%"])
        class_table.add_row(["中速彎道 (150-250 km/h)", f"{classification['medium_corners']} 個", f"{classification['medium_corners']/stats['total_corners']*100:.1f}%"])
        class_table.add_row(["高速彎道 (>250 km/h)", f"{classification['fast_corners']} 個", f"{classification['fast_corners']/stats['total_corners']*100:.1f}%"])
        
        print(f"\n📈 彎道分類:")
        print(class_table)
    
    def _export_json(self, analysis_result, driver):
        """導出JSON格式結果"""
        try:
            os.makedirs("json", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"json/dynamic_corner_detection_{driver}_{self.year}_{self.race}_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, ensure_ascii=False, indent=2)
            
            print(f"📄 JSON 文件已導出: {filename}")
            
        except Exception as e:
            print(f"❌ JSON 導出失敗: {e}")
    
    def _generate_cache_key(self, driver, **kwargs):
        """生成緩存鍵值"""
        return f"dynamic_corner_detection_{driver}_{self.year}_{self.race}_{self.session}"
    
    def _check_cache(self, cache_key):
        """檢查緩存"""
        cache_path = os.path.join("cache", f"{cache_key}.pkl")
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
            except:
                pass
        return None
    
    def _save_cache(self, data, cache_key):
        """保存緩存"""
        os.makedirs("cache", exist_ok=True)
        cache_path = os.path.join("cache", f"{cache_key}.pkl")
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            print(f"⚠️ 緩存保存失敗: {e}")
    
    def _report_analysis_results(self, data, analysis_type="動態彎道檢測"):
        """報告分析結果狀態"""
        if not data:
            print(f"❌ {analysis_type}失敗：無可用數據")
            return False
        
        corners_count = len(data.get('corners_data', []))
        print(f"📊 {analysis_type}結果摘要：")
        print(f"   • 檢測到彎道數量: {corners_count}")
        print(f"   • 平均信心度: {data.get('statistics', {}).get('average_confidence', 0):.2f}")
        print(f"   • 數據完整性: {'✅ 良好' if corners_count > 0 else '❌ 不足'}")
        
        print(f"✅ {analysis_type}分析完成！")
        return True


def run_dynamic_corner_detection_analysis(data_loader=None, year=2025, race="Japan", session="R", 
                                         driver="VER", show_detailed_output=True, export_json=True):
    """
    運行動態彎道檢測分析的主函數
    
    Args:
        data_loader: 數據載入器
        year: 年份
        race: 賽事
        session: 賽段
        driver: 車手代碼
        show_detailed_output: 是否顯示詳細輸出
        export_json: 是否導出JSON
    
    Returns:
        分析結果字典
    """
    analyzer = DynamicCornerDetectionAnalysis(
        data_loader=data_loader,
        year=year,
        race=race,
        session=session
    )
    
    return analyzer.analyze(
        driver=driver,
        show_detailed_output=show_detailed_output,
        export_json=export_json
    )


if __name__ == "__main__":
    # 測試運行
    result = run_dynamic_corner_detection_analysis(
        year=2025,
        race="Japan",
        session="R",
        driver="VER",
        show_detailed_output=True
    )
    
    if result:
        print("🎉 動態彎道檢測分析完成！")
    else:
        print("❌ 動態彎道檢測分析失敗！")
