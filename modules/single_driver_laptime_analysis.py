#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
單一車手圈速分析模組
提供車手圈速表現的深度分析
"""

import os
import json
import pickle
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional, List
from prettytable import PrettyTable

class SingleDriverLaptimeAnalysis:
    """單一車手圈速分析器"""
    
    def __init__(self, data_loader, year: int, race: str, session: str):
        self.data_loader = data_loader
        self.year = year
        self.race = race
        self.session = session
        self.cache_dir = "cache"
        
        # 確保緩存目錄存在
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def analyze_lap_times(self, driver: str, **kwargs) -> Dict[str, Any]:
        """分析車手圈速表現
        
        Args:
            driver: 車手代碼 (如 'VER', 'LEC')
            
        Returns:
            Dict: 包含圈速分析結果的字典
        """
        print(f"⏱️ 開始分析車手 {driver} 的圈速表現...")
        
        try:
            # 生成緩存鍵
            cache_key = f"laptime_analysis_{self.year}_{self.race}_{self.session}_{driver}"
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
            
            # 檢查緩存
            if os.path.exists(cache_file):
                print("📦 從緩存載入圈速分析數據...")
                with open(cache_file, 'rb') as f:
                    cached_result = pickle.load(f)
                
                # 顯示對應的 JSON 檔案路徑
                json_file = cache_file.replace('.pkl', '.json')
                if os.path.exists(json_file):
                    print(f"📄 對應 JSON 檔案: {json_file}")
                
                # 顯示圈速分析表格
                self._display_laptime_analysis_table(cached_result, driver)
                
                print("✅ 圈速分析完成 (使用緩存)")
                return cached_result
            
            # 載入賽事數據
            session_data = self.data_loader.get_loaded_data()
            
            if session_data is None:
                raise ValueError("無法載入賽事數據")
            
            # 從數據字典中獲取圈速數據
            if isinstance(session_data, dict):
                laps_data = session_data.get('laps')
                if laps_data is None:
                    raise ValueError("無法找到圈速數據")
            else:
                laps_data = getattr(session_data, 'laps', None)
                if laps_data is None:
                    raise ValueError("無法找到圈速數據")
            
            # 獲取車手數據
            driver_data = laps_data.pick_driver(driver)
            
            if driver_data.empty:
                raise ValueError(f"找不到車手 {driver} 的數據")
            
            # 分析圈速
            result = {
                "success": True,
                "driver": driver,
                "year": self.year,
                "race": self.race,
                "session": self.session,
                "analysis_timestamp": datetime.now().isoformat(),
                "lap_time_analysis": {
                    "basic_statistics": self._calculate_basic_statistics(driver_data),
                    "fastest_laps": self._find_fastest_laps(driver_data),
                    "consistency_analysis": self._analyze_consistency(driver_data),
                    "sector_analysis": self._analyze_sectors(driver_data),
                    "performance_trends": self._analyze_performance_trends(driver_data),
                    "comparative_analysis": self._compare_with_session_average(driver_data, laps_data),
                    "pace_analysis": self._analyze_race_pace(driver_data)
                }
            }
            
            # 保存到緩存
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)
            
            # 同時保存為 JSON
            json_file = cache_file.replace('.pkl', '.json')
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"💾 JSON 分析結果已保存: {json_file}")
            
            # 顯示圈速分析表格
            self._display_laptime_analysis_table(result, driver)
            
            print("✅ 車手圈速分析完成")
            return result
            
        except Exception as e:
            print(f"❌ 圈速分析失敗: {e}")
            return {
                "success": False,
                "error": str(e),
                "driver": driver,
                "analysis_timestamp": datetime.now().isoformat()
            }
    
    def _calculate_basic_statistics(self, driver_data) -> Dict[str, Any]:
        """計算基本圈速統計"""
        try:
            lap_times = driver_data['LapTime'].dropna()
            
            if lap_times.empty:
                return {"error": "無有效圈速數據"}
            
            # 轉換為秒數進行計算
            times_seconds = [t.total_seconds() for t in lap_times]
            
            return {
                "total_laps": len(driver_data),
                "valid_laps": len(lap_times),
                "fastest_lap": min(times_seconds),
                "slowest_lap": max(times_seconds),
                "average_lap_time": np.mean(times_seconds),
                "median_lap_time": np.median(times_seconds),
                "lap_time_range": max(times_seconds) - min(times_seconds),
                "standard_deviation": np.std(times_seconds)
            }
        except Exception as e:
            return {"error": f"統計計算失敗: {e}"}
    
    def _find_fastest_laps(self, driver_data, top_n: int = 5) -> List[Dict[str, Any]]:
        """找出最快的幾圈"""
        try:
            valid_laps = driver_data[driver_data['LapTime'].notna()].copy()
            
            if valid_laps.empty:
                return []
            
            # 按圈速排序
            valid_laps = valid_laps.sort_values('LapTime')
            fastest_laps = []
            
            for i, (_, lap) in enumerate(valid_laps.head(top_n).iterrows()):
                fastest_laps.append({
                    "rank": i + 1,
                    "lap_number": int(lap['LapNumber']),
                    "lap_time": lap['LapTime'].total_seconds(),
                    "compound": lap.get('Compound', 'Unknown'),
                    "tyre_life": lap.get('TyreLife', 'Unknown'),
                    "position": int(lap.get('Position', 0))
                })
            
            return fastest_laps
        except Exception as e:
            return [{"error": f"無法分析最快圈: {e}"}]
    
    def _analyze_consistency(self, driver_data) -> Dict[str, Any]:
        """分析圈速一致性"""
        try:
            lap_times = driver_data['LapTime'].dropna()
            
            if len(lap_times) < 3:
                return {"error": "數據不足以分析一致性"}
            
            times_seconds = [t.total_seconds() for t in lap_times]
            mean_time = np.mean(times_seconds)
            std_dev = np.std(times_seconds)
            
            # 計算變異係數 (CV)
            coefficient_of_variation = (std_dev / mean_time) * 100
            
            # 計算在平均時間±2秒內的圈數百分比
            within_2_seconds = sum(1 for t in times_seconds if abs(t - mean_time) <= 2.0)
            consistency_percentage = (within_2_seconds / len(times_seconds)) * 100
            
            return {
                "coefficient_of_variation": coefficient_of_variation,
                "consistency_percentage": consistency_percentage,
                "standard_deviation": std_dev,
                "outlier_laps": self._find_outlier_laps(driver_data, times_seconds, mean_time, std_dev)
            }
        except Exception as e:
            return {"error": f"一致性分析失敗: {e}"}
    
    def _find_outlier_laps(self, driver_data, times_seconds: List[float], mean_time: float, std_dev: float) -> List[Dict[str, Any]]:
        """找出異常圈速"""
        try:
            outliers = []
            threshold = 2 * std_dev  # 2個標準差
            
            lap_times = driver_data['LapTime'].dropna()
            
            for i, (lap_time, (_, lap)) in enumerate(zip(times_seconds, lap_times.items())):
                if abs(lap_time - mean_time) > threshold:
                    lap_data = driver_data.loc[lap]
                    outliers.append({
                        "lap_number": int(lap_data['LapNumber']),
                        "lap_time": lap_time,
                        "deviation_from_mean": lap_time - mean_time,
                        "reason": "Significantly slower" if lap_time > mean_time else "Significantly faster"
                    })
            
            return outliers
        except:
            return []
    
    def _analyze_sectors(self, driver_data) -> Dict[str, Any]:
        """分析分段時間"""
        try:
            sector_analysis = {}
            
            # 檢查是否有分段時間數據
            sector_columns = ['Sector1Time', 'Sector2Time', 'Sector3Time']
            available_sectors = [col for col in sector_columns if col in driver_data.columns]
            
            if not available_sectors:
                return {"error": "無分段時間數據"}
            
            for sector_col in available_sectors:
                sector_data = driver_data[sector_col].dropna()
                
                if not sector_data.empty:
                    sector_times = [t.total_seconds() for t in sector_data]
                    sector_num = sector_col.replace('Sector', '').replace('Time', '')
                    
                    sector_analysis[f"sector_{sector_num}"] = {
                        "fastest_time": min(sector_times),
                        "average_time": np.mean(sector_times),
                        "consistency": np.std(sector_times),
                        "improvement_potential": max(sector_times) - min(sector_times)
                    }
            
            return sector_analysis
        except Exception as e:
            return {"error": f"分段分析失敗: {e}"}
    
    def _analyze_performance_trends(self, driver_data) -> Dict[str, Any]:
        """分析表現趨勢"""
        try:
            lap_times = driver_data['LapTime'].dropna()
            
            if len(lap_times) < 5:
                return {"error": "數據不足以分析趨勢"}
            
            times_seconds = [t.total_seconds() for t in lap_times]
            lap_numbers = range(1, len(times_seconds) + 1)
            
            # 計算趨勢線斜率
            trend_slope = np.polyfit(lap_numbers, times_seconds, 1)[0]
            
            # 分析前半段 vs 後半段
            mid_point = len(times_seconds) // 2
            first_half_avg = np.mean(times_seconds[:mid_point])
            second_half_avg = np.mean(times_seconds[mid_point:])
            
            return {
                "trend_slope": trend_slope,
                "trending": "Improving" if trend_slope < -0.1 else "Degrading" if trend_slope > 0.1 else "Stable",
                "first_half_average": first_half_avg,
                "second_half_average": second_half_avg,
                "race_degradation": second_half_avg - first_half_avg,
                "strongest_stint": self._find_strongest_stint(times_seconds)
            }
        except Exception as e:
            return {"error": f"趨勢分析失敗: {e}"}
    
    def _find_strongest_stint(self, times_seconds: List[float]) -> Dict[str, Any]:
        """找出表現最好的連續段落"""
        try:
            if len(times_seconds) < 5:
                return {"error": "數據不足"}
            
            stint_length = 5  # 分析5圈的連續段落
            best_stint = None
            best_average = float('inf')
            
            for i in range(len(times_seconds) - stint_length + 1):
                stint_times = times_seconds[i:i + stint_length]
                stint_average = np.mean(stint_times)
                
                if stint_average < best_average:
                    best_average = stint_average
                    best_stint = {
                        "start_lap": i + 1,
                        "end_lap": i + stint_length,
                        "average_time": stint_average,
                        "consistency": np.std(stint_times)
                    }
            
            return best_stint or {"error": "無法找到最佳段落"}
        except:
            return {"error": "分析失敗"}
    
    def _compare_with_session_average(self, driver_data, laps_data) -> Dict[str, Any]:
        """與全場平均比較"""
        try:
            driver_times = driver_data['LapTime'].dropna()
            session_times = laps_data['LapTime'].dropna()
            
            if driver_times.empty or session_times.empty:
                return {"error": "無足夠數據進行比較"}
            
            driver_avg = np.mean([t.total_seconds() for t in driver_times])
            session_avg = np.mean([t.total_seconds() for t in session_times])
            
            return {
                "driver_average": driver_avg,
                "session_average": session_avg,
                "gap_to_average": driver_avg - session_avg,
                "relative_performance": "Above Average" if driver_avg < session_avg else "Below Average",
                "percentile_rank": self._calculate_percentile_rank(driver_avg, session_times)
            }
        except Exception as e:
            return {"error": f"比較分析失敗: {e}"}
    
    def _calculate_percentile_rank(self, driver_avg: float, session_times) -> float:
        """計算車手在全場的百分位排名"""
        try:
            all_times = [t.total_seconds() for t in session_times]
            better_count = sum(1 for t in all_times if t < driver_avg)
            return (better_count / len(all_times)) * 100
        except:
            return 0.0
    
    def _analyze_race_pace(self, driver_data) -> Dict[str, Any]:
        """分析比賽節奏"""
        try:
            # 排除前3圈和最後2圈以獲得純比賽節奏
            race_laps = driver_data.iloc[3:-2] if len(driver_data) > 5 else driver_data
            race_times = race_laps['LapTime'].dropna()
            
            if race_times.empty:
                return {"error": "無足夠比賽節奏數據"}
            
            times_seconds = [t.total_seconds() for t in race_times]
            
            return {
                "pure_race_pace": np.mean(times_seconds),
                "race_pace_consistency": np.std(times_seconds),
                "pace_rating": self._rate_pace_consistency(np.std(times_seconds)),
                "fuel_corrected_pace": self._estimate_fuel_corrected_pace(times_seconds)
            }
        except Exception as e:
            return {"error": f"比賽節奏分析失敗: {e}"}
    
    def _rate_pace_consistency(self, std_dev: float) -> str:
        """評估節奏一致性等級"""
        if std_dev < 0.5:
            return "Excellent"
        elif std_dev < 1.0:
            return "Good"
        elif std_dev < 1.5:
            return "Average"
        elif std_dev < 2.0:
            return "Below Average"
        else:
            return "Poor"
    
    def _estimate_fuel_corrected_pace(self, times_seconds: List[float]) -> Optional[float]:
        """估算燃油修正後的節奏 (簡化版)"""
        try:
            if len(times_seconds) < 10:
                return None
            
            # 簡化的燃油修正：假設每圈節省0.05秒燃油重量
            fuel_correction_per_lap = 0.05
            corrected_times = []
            
            for i, lap_time in enumerate(times_seconds):
                fuel_correction = i * fuel_correction_per_lap
                corrected_times.append(lap_time - fuel_correction)
            
            return np.mean(corrected_times)
        except:
            return None
    
    def _display_laptime_analysis_table(self, result: Dict[str, Any], driver: str):
        """顯示圈速分析結果表格"""
        try:
            laptime_data = result.get('lap_time_analysis', {})
            
            print(f"\n⏱️ 車手 {driver} 圈速分析結果")
            print("=" * 80)
            
            # 基本統計表格
            basic_stats = laptime_data.get('basic_statistics', {})
            if basic_stats and not basic_stats.get('error'):
                stats_table = PrettyTable()
                stats_table.field_names = ["統計項目", "圈速", "說明"]
                stats_table.align["統計項目"] = "l"
                stats_table.align["說明"] = "l"
                
                fastest = basic_stats.get('fastest_lap', 0)
                slowest = basic_stats.get('slowest_lap', 0)
                average = basic_stats.get('average_lap_time', 0)
                median = basic_stats.get('median_lap_time', 0)
                std_dev = basic_stats.get('standard_deviation', 0)
                total_laps = basic_stats.get('total_laps', 0)
                valid_laps = basic_stats.get('valid_laps', 0)
                
                def format_time(seconds):
                    if seconds > 0:
                        return f"{int(seconds//60)}:{seconds%60:06.3f}"
                    return "N/A"
                
                stats_table.add_row(["最快圈速", format_time(fastest), "單圈最快時間"])
                stats_table.add_row(["最慢圈速", format_time(slowest), "單圈最慢時間"])
                stats_table.add_row(["平均圈速", format_time(average), "所有有效圈速的平均"])
                stats_table.add_row(["中位數圈速", format_time(median), "圈速分布的中位數"])
                stats_table.add_row(["標準差", f"{std_dev:.3f}s", "圈速一致性指標"])
                stats_table.add_row(["總圈數", f"{total_laps} 圈", "完成的總圈數"])
                stats_table.add_row(["有效圈數", f"{valid_laps} 圈", f"有效圈速數量 ({valid_laps/total_laps*100:.1f}%)" if total_laps > 0 else "有效圈速數量"])
                
                print(f"\n📊 基本圈速統計:")
                print(stats_table)
            
            # 最快圈數表格
            fastest_laps = laptime_data.get('fastest_laps', [])
            if fastest_laps and not any(lap.get('error') for lap in fastest_laps):
                fastest_table = PrettyTable()
                fastest_table.field_names = ["排名", "圈數", "圈速", "輪胎配方", "輪胎壽命", "位置"]
                fastest_table.align["輪胎配方"] = "c"
                
                for lap in fastest_laps[:5]:  # 顯示前5快
                    rank = lap.get('rank', 0)
                    lap_num = lap.get('lap_number', 0)
                    lap_time = lap.get('lap_time', 0)
                    compound = lap.get('compound', 'Unknown')
                    tyre_life = lap.get('tyre_life', 'Unknown')
                    position = lap.get('position', 0)
                    
                    time_str = f"{int(lap_time//60)}:{lap_time%60:06.3f}" if lap_time > 0 else "N/A"
                    
                    fastest_table.add_row([f"第 {rank} 快", f"第 {lap_num} 圈", time_str, compound, f"{tyre_life} 圈" if isinstance(tyre_life, (int, float)) else tyre_life, f"P{position}"])
                
                print(f"\n🏆 最快圈速排行:")
                print(fastest_table)
            
            # 一致性分析表格
            consistency = laptime_data.get('consistency_analysis', {})
            if consistency and not consistency.get('error'):
                consistency_table = PrettyTable()
                consistency_table.field_names = ["一致性指標", "數值", "評估", "說明"]
                consistency_table.align["一致性指標"] = "l"
                consistency_table.align["說明"] = "l"
                
                cv = consistency.get('coefficient_of_variation', 0)
                consistency_pct = consistency.get('consistency_percentage', 0)
                std_dev = consistency.get('standard_deviation', 0)
                outliers = consistency.get('outlier_laps', [])
                
                cv_rating = "優秀" if cv < 1.0 else "良好" if cv < 2.0 else "一般" if cv < 3.0 else "需改善"
                consistency_rating = "優秀" if consistency_pct > 90 else "良好" if consistency_pct > 80 else "一般" if consistency_pct > 70 else "需改善"
                
                consistency_table.add_row(["變異係數", f"{cv:.2f}%", cv_rating, "越低越一致"])
                consistency_table.add_row(["一致性百分比", f"{consistency_pct:.1f}%", consistency_rating, "在±2秒內的圈數百分比"])
                consistency_table.add_row(["標準差", f"{std_dev:.3f}s", "標準", "圈速離散程度"])
                consistency_table.add_row(["異常圈數", f"{len(outliers)} 圈", "偵測", "明顯偏離平均的圈數"])
                
                print(f"\n📈 圈速一致性分析:")
                print(consistency_table)
            
            # 表現趨勢表格
            trends = laptime_data.get('performance_trends', {})
            if trends and not trends.get('error'):
                trends_table = PrettyTable()
                trends_table.field_names = ["趨勢項目", "數值", "評估", "說明"]
                trends_table.align["趨勢項目"] = "l"
                trends_table.align["說明"] = "l"
                
                trend_slope = trends.get('trend_slope', 0)
                trending = trends.get('trending', 'Unknown')
                first_half = trends.get('first_half_average', 0)
                second_half = trends.get('second_half_average', 0)
                degradation = trends.get('race_degradation', 0)
                
                def format_time_short(seconds):
                    if seconds > 0:
                        return f"{int(seconds//60)}:{seconds%60:06.3f}"
                    return "N/A"
                
                trend_desc = "表現提升" if trend_slope < -0.1 else "表現下降" if trend_slope > 0.1 else "表現穩定"
                degradation_desc = "前半段較快" if degradation < 0 else "後半段較快" if degradation > 0 else "前後一致"
                
                trends_table.add_row(["趨勢斜率", f"{trend_slope:.4f}", trending, trend_desc])
                trends_table.add_row(["前半段平均", format_time_short(first_half), "基準", "比賽前半段平均圈速"])
                trends_table.add_row(["後半段平均", format_time_short(second_half), "比較", "比賽後半段平均圈速"])
                trends_table.add_row(["圈速衰退", f"{degradation:+.3f}s", degradation_desc, "後半段相對前半段的變化"])
                
                print(f"\n📊 表現趨勢分析:")
                print(trends_table)
            
            # 比賽節奏分析
            pace_analysis = laptime_data.get('pace_analysis', {})
            if pace_analysis and not pace_analysis.get('error'):
                pace_table = PrettyTable()
                pace_table.field_names = ["節奏指標", "數值", "評級", "說明"]
                pace_table.align["節奏指標"] = "l"
                pace_table.align["說明"] = "l"
                
                race_pace = pace_analysis.get('pure_race_pace', 0)
                pace_consistency = pace_analysis.get('race_pace_consistency', 0)
                pace_rating = pace_analysis.get('pace_rating', 'Unknown')
                fuel_corrected = pace_analysis.get('fuel_corrected_pace')
                
                def format_time_short(seconds):
                    if seconds > 0:
                        return f"{int(seconds//60)}:{seconds%60:06.3f}"
                    return "N/A"
                
                pace_table.add_row(["純比賽節奏", format_time_short(race_pace), "基準", "排除開頭和結尾圈的平均圈速"])
                pace_table.add_row(["節奏一致性", f"{pace_consistency:.3f}s", pace_rating, "比賽節奏的穩定程度"])
                
                if fuel_corrected:
                    pace_table.add_row(["燃油修正節奏", format_time_short(fuel_corrected), "估算", "考慮燃油重量後的理論節奏"])
                
                print(f"\n🏃 比賽節奏分析:")
                print(pace_table)
            
            print("=" * 80)
            
        except Exception as e:
            print(f"❌ 顯示圈速分析表格失敗: {e}")
            # 顯示基本信息作為備用
            print(f"\n⏱️ 車手 {driver} 圈速分析結果 (簡化版)")
            print(f"分析時間: {result.get('analysis_timestamp', 'Unknown')}")
            print(f"分析狀態: {'成功' if result.get('success') else '失敗'}")

    def analyze_fastest_lap(self, driver: str, **kwargs) -> Dict[str, Any]:
        """Function 26: 分析車手最速圈速表現
        
        Args:
            driver: 車手代碼 (如 'VER', 'LEC')
            
        Returns:
            Dict: 包含最速圈分析結果的字典
        """
        print(f"⚡ 開始分析車手 {driver} 的最速圈表現...")
        
        try:
            # 生成緩存鍵
            cache_key = f"fastest_lap_analysis_{self.year}_{self.race}_{self.session}_{driver}"
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
            
            # 檢查緩存
            if os.path.exists(cache_file):
                print("📦 從緩存載入最速圈分析數據...")
                with open(cache_file, 'rb') as f:
                    cached_result = pickle.load(f)
                
                # 顯示結果
                self._display_fastest_lap_analysis(driver, cached_result)
                return cached_result
            
            # 獲取數據
            data = self.data_loader.get_loaded_data()
            if not data:
                return {"error": "無法獲取數據"}
            
            laps = data['laps']
            driver_data = laps[laps['Driver'] == driver].copy()
            
            if driver_data.empty:
                return {"error": f"車手 {driver} 無數據"}
            
            # 執行最速圈分析
            result = self._analyze_fastest_lap_performance(driver, driver_data)
            
            # 保存緩存
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)
            
            # 保存JSON
            json_file = f"fastest_lap_analysis_{self.year}_{self.race}_{self.session}_{driver}.json"
            json_path = os.path.join("json", json_file)
            os.makedirs("json", exist_ok=True)
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"📄 JSON 分析報告已保存: {json_path}")
            
            # 顯示結果
            self._display_fastest_lap_analysis(driver, result)
            
            return result
            
        except Exception as e:
            print(f"❌ 最速圈分析失敗: {e}")
            return {"error": str(e)}
    
    def _analyze_fastest_lap_performance(self, driver: str, driver_data) -> Dict[str, Any]:
        """分析最速圈表現"""
        try:
            valid_laps = driver_data[driver_data['LapTime'].notna()].copy()
            
            if valid_laps.empty:
                return {"error": "無有效圈速數據"}
            
            # 找出最快圈
            fastest_lap_idx = valid_laps['LapTime'].idxmin()
            fastest_lap = valid_laps.loc[fastest_lap_idx]
            
            # 基本信息
            fastest_time = fastest_lap['LapTime'].total_seconds()
            lap_number = int(fastest_lap['LapNumber'])
            
            # 輪胎信息
            compound = fastest_lap.get('Compound', 'Unknown')
            tyre_life = fastest_lap.get('TyreLife', 'Unknown')
            
            # 分段時間
            sector_times = {
                'sector_1': fastest_lap.get('Sector1Time'),
                'sector_2': fastest_lap.get('Sector2Time'),
                'sector_3': fastest_lap.get('Sector3Time')
            }
            
            # 位置信息
            position = fastest_lap.get('Position', 'Unknown')
            
            # 與平均圈速比較
            avg_lap_time = valid_laps['LapTime'].mean().total_seconds()
            improvement = avg_lap_time - fastest_time
            
            result = {
                "driver": driver,
                "fastest_lap": {
                    "lap_number": lap_number,
                    "lap_time_seconds": fastest_time,
                    "lap_time_formatted": self._format_time_seconds(fastest_time),
                    "compound": compound,
                    "tyre_life": tyre_life,
                    "position": position
                },
                "sector_times": {
                    "sector_1": self._format_time_delta(sector_times['sector_1']),
                    "sector_2": self._format_time_delta(sector_times['sector_2']),
                    "sector_3": self._format_time_delta(sector_times['sector_3'])
                },
                "comparison": {
                    "average_lap_time": self._format_time_seconds(avg_lap_time),
                    "improvement_from_average": self._format_time_seconds(improvement),
                    "percentage_improvement": (improvement / avg_lap_time) * 100
                },
                "session_stats": {
                    "total_laps": len(driver_data),
                    "valid_laps": len(valid_laps),
                    "fastest_lap_rank": self._get_fastest_lap_rank(driver_data, fastest_time)
                },
                "analysis_timestamp": datetime.now().isoformat(),
                "success": True
            }
            
            return result
            
        except Exception as e:
            return {"error": f"最速圈分析失敗: {e}", "success": False}
    
    def _get_fastest_lap_rank(self, driver_data, fastest_time: float) -> int:
        """獲取最快圈在所有圈中的排名"""
        try:
            valid_times = driver_data['LapTime'].dropna()
            times_seconds = [t.total_seconds() for t in valid_times]
            times_seconds.sort()
            
            rank = times_seconds.index(fastest_time) + 1
            return rank
        except:
            return 1
    
    def _format_time_seconds(self, seconds: float) -> str:
        """格式化秒數為時間格式"""
        if pd.isna(seconds):
            return "N/A"
        
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}:{secs:06.3f}"
    
    def _format_time_delta(self, time_delta) -> str:
        """格式化時間差"""
        if pd.isna(time_delta) or time_delta is None:
            return "N/A"
        
        if hasattr(time_delta, 'total_seconds'):
            seconds = time_delta.total_seconds()
            return f"{seconds:.3f}s"
        
        return str(time_delta)
    
    def _display_fastest_lap_analysis(self, driver: str, result: Dict[str, Any]):
        """顯示最速圈分析結果"""
        try:
            if result.get('error'):
                print(f"❌ 分析錯誤: {result['error']}")
                return
            
            print(f"\n⚡ {driver} 最速圈分析結果:")
            print("=" * 60)
            
            fastest_lap = result.get('fastest_lap', {})
            
            # 基本信息表格
            info_table = PrettyTable()
            info_table.field_names = ["項目", "數值"]
            info_table.align = "l"
            
            info_table.add_row(["🏁 最快圈圈數", f"第 {fastest_lap.get('lap_number', 'N/A')} 圈"])
            info_table.add_row(["⏱️ 最快圈時間", fastest_lap.get('lap_time_formatted', 'N/A')])
            info_table.add_row(["🛞 使用輪胎", fastest_lap.get('compound', 'N/A')])
            info_table.add_row(["🔄 輪胎壽命", f"{fastest_lap.get('tyre_life', 'N/A')} 圈"])
            info_table.add_row(["📍 當時位置", f"P{fastest_lap.get('position', 'N/A')}"])
            
            print(info_table)
            
            # 分段時間表格
            sector_times = result.get('sector_times', {})
            if any(sector_times.values()):
                print("\n🏁 分段時間:")
                sector_table = PrettyTable()
                sector_table.field_names = ["分段", "時間"]
                sector_table.align = "l"
                
                sector_table.add_row(["Sector 1", sector_times.get('sector_1', 'N/A')])
                sector_table.add_row(["Sector 2", sector_times.get('sector_2', 'N/A')])
                sector_table.add_row(["Sector 3", sector_times.get('sector_3', 'N/A')])
                
                print(sector_table)
            
            # 比較分析
            comparison = result.get('comparison', {})
            if comparison:
                print("\n📊 表現比較:")
                comp_table = PrettyTable()
                comp_table.field_names = ["比較項目", "數值"]
                comp_table.align = "l"
                
                comp_table.add_row(["平均圈速", comparison.get('average_lap_time', 'N/A')])
                comp_table.add_row(["較平均快", comparison.get('improvement_from_average', 'N/A')])
                
                improvement_pct = comparison.get('percentage_improvement', 0)
                if improvement_pct > 0:
                    comp_table.add_row(["改善幅度", f"{improvement_pct:.2f}%"])
                
                print(comp_table)
            
            print("=" * 60)
            print("✅ 最速圈分析完成！")
            
        except Exception as e:
            print(f"❌ 顯示最速圈分析失敗: {e}")
            print(f"車手 {driver} 最速圈分析結果 (簡化版)")
            print(f"分析狀態: {'成功' if result.get('success') else '失敗'}")
