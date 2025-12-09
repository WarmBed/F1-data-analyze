#!/usr/bin/env python3
"""
F1 進站策略分析模組 - 完全復刻版本
F1 Pitstop Strategy Analysis Module - Complete Recreation

基於 f1_analysis_cli_new.py 的進站策略分析功能
優先使用 OpenF1 API 獲取準確的進站時間數據
支援 OpenF1 API 和 FastF1 兩種數據源
完全獨立的模組化設計，符合 copilot-instructions 開發核心要求

版本: 2.0
作者: F1 Analysis Team
"""

import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import pickle
from datetime import datetime, timedelta
from prettytable import PrettyTable
import json
import logging

from core.logger import get_logger

logger = get_logger("pitstop_analysis_complete", component="gui")

# 確保能夠導入基礎模組
# 確保可導入基礎模組
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

try:
    from CLI_modules.cli.core.base import F1AnalysisBase
except ImportError:
    logger.error("[ERROR] 無法導入基礎模組 F1AnalysisBase")
    F1AnalysisBase = object

# 導入 OpenF1 分析器 - 優先使用 OpenF1 API
try:
    from CLI_modules.cli.core.openf1_data_analyzer import F1OpenDataAnalyzer
except ImportError:
    logger.warning("[WARNING] 無法導入 OpenF1 數據分析器，將只使用 FastF1 分析")
    F1OpenDataAnalyzer = None


def format_time(time_obj):
    """標準時間格式化函數 - 禁止包含 day 或 days"""
    if pd.isna(time_obj) or time_obj is None:
        return "N/A"
    
    # 轉換為字符串並移除 days
    time_str = str(time_obj)
    
    # 移除 "0 days " 和任何 "days " 前綴
    if "days" in time_str:
        time_str = time_str.split("days ")[-1]
    
    # 處理數值型時間（秒）
    if isinstance(time_obj, (int, float)):
        return f"{time_obj:.3f}s"
    
    return time_str


def check_cache(cache_key):
    """檢查緩存是否存在"""
    cache_dir = "cache"
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f"{cache_key}.pkl")
    
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.warning("[WARNING] 緩存載入失敗: %s", e)
            return None
    return None


def save_cache(data, cache_key):
    """保存數據到緩存"""
    cache_dir = "cache"
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f"{cache_key}.pkl")
    
    try:
        with open(cache_path, 'wb') as f:
            pickle.dump(data, f)
    except Exception as e:
        logger.warning("[WARNING] 緩存保存失敗: %s", e)


def report_analysis_results(data, analysis_type="analysis"):
    """報告分析結果狀態"""
    if not data:
        logger.error("❌ %s失敗：無可用數據", analysis_type)
        return False
    
    # 正確計算進站分析的數據數量
    data_count = 0
    if isinstance(data, dict):
        if 'pitstop_summary' in data:
            data_count = data['pitstop_summary'].get('total_pitstops', 0)
        elif 'pitstops' in data:
            data_count = len(data['pitstops'])
        else:
            data_count = len(data)
    elif isinstance(data, list):
        data_count = len(data)
    
    logger.info("📊 %s結果摘要：", analysis_type)
    logger.info("   • 數據項目數量: %s", data_count)
    logger.info("   • 數據完整性: %s", '✅ 良好' if data_count > 0 else '❌ 不足')
    
    # 顯示進站分析特有信息
    if isinstance(data, dict) and 'pitstop_summary' in data:
        drivers_count = data['pitstop_summary'].get('drivers_with_pitstops', 0)
        avg_time = data['pitstop_summary'].get('average_pitstop_time', 0)
        logger.info("   • 參與進站車手數: %s", drivers_count)
        if avg_time > 0:
            logger.info("   • 平均進站時間: %.1f秒", avg_time)
    
    logger.info("✅ %s分析完成！", analysis_type)
    return True


class F1PitstopAnalyzer(F1AnalysisBase):
    """F1進站策略分析器 - 優先使用 OpenF1 API"""
    
    def __init__(self, data_loader=None):
        super().__init__()  # 基礎類不需要參數
        self.data_loader = data_loader
        self.title = "F1 進站策略分析"
        self.version = "2.0"
        self.pitstops_data = []
        self.cache_enabled = True
        self.drivers_pitstops = {}
        self.strategy_stats = {}
        
    def run_analysis(self, f1_analysis_instance=None):
        """執行進站策略分析"""
        logger.info("⏱️ 執行進站策略分析...")
        
        if not self.data_loader or not self.data_loader.session_loaded:
            logger.error("[ERROR] 數據載入器未初始化或未載入賽事數據")
            return False
            
        try:
            # 獲取載入的數據
            data = self.data_loader.get_loaded_data()
            metadata = data.get('metadata', {})
            
            logger.info("[CONFIG] 分析 %s %s 進站資料...", metadata.get('year', 'Unknown'), metadata.get('race_name', 'Unknown'))
            
            # 嘗試使用 OpenF1 API 分析
            if self._try_openf1_analysis(metadata):
                logger.info("[SUCCESS] OpenF1 進站分析完成！")
                return True
            else:
                logger.info("🔄 切換到 FastF1 資料分析...")
                return self._run_fastf1_analysis(data)
                
        except Exception as e:
            logger.exception("[ERROR] 進站分析執行失敗: %s", e)
            return False
    
    def _try_openf1_analysis(self, metadata):
        """嘗試使用 OpenF1 API 進行分析"""
        if F1OpenDataAnalyzer is None:
            logger.error("[ERROR] OpenF1 數據分析器未可用")
            return False
            
        try:
            # 創建 OpenF1 分析器
            openf1_analyzer = F1OpenDataAnalyzer()
            
            # 根據年份和比賽名稱找到對應的 session_key
            race_session = openf1_analyzer.find_race_session_by_name(
                metadata.get('year'), metadata.get('race_name')
            )
            
            if not race_session:
                logger.error("[ERROR] 無法找到對應的比賽會話")
                return False
            
            session_key = race_session.get('session_key')
            if not session_key:
                logger.error("[ERROR] 無法獲取會話金鑰")
                return False
            
            # 獲取 OpenF1 進站數據
            logger.info("📡 從 OpenF1 API 獲取進站數據 (session_key: %s)...", session_key)
            enhanced_pitstops = openf1_analyzer.get_enhanced_pit_stops(session_key)
            
            if not enhanced_pitstops:
                logger.error("[ERROR] OpenF1 API 未返回進站數據")
                return False
            
            # 分析 OpenF1 進站數據
            self._analyze_openf1_pitstops(enhanced_pitstops)
            
            # 保存進站數據到快取
            cache_file = openf1_analyzer.save_pitstop_data_to_cache(
                enhanced_pitstops, metadata.get('year'), metadata.get('race_name')
            )
            if cache_file:
                logger.info("[SUCCESS] 進站數據已快取到: %s", cache_file)
            
            return True
            
        except Exception as e:
            logger.exception("[ERROR] OpenF1 進站分析失敗: %s", e)
            return False
    
    def _analyze_openf1_pitstops(self, enhanced_pitstops):
        """分析 OpenF1 進站數據"""
        logger.info("[INFO] OpenF1 進站數據分析結果")
        logger.info("=" * 80)
        
        if not enhanced_pitstops:
            logger.error("[ERROR] 沒有進站數據可供分析")
            return
        
        # 處理進站時間數據
        valid_pitstops = []
        for stop in enhanced_pitstops:
            try:
                pit_duration = stop.get('pit_duration')
                if pit_duration is not None and pit_duration > 0:
                    valid_pitstops.append({
                        'driver_number': stop.get('driver_number'),
                        'driver_name': stop.get('driver_info', {}).get('full_name', f"Driver #{stop.get('driver_number')}"),
                        'driver_acronym': stop.get('driver_info', {}).get('name_acronym', 'UNK'),
                        'team_name': stop.get('driver_info', {}).get('team_name', 'Unknown Team'),
                        'lap_number': stop.get('lap_number'),
                        'pit_duration': float(pit_duration)
                    })
            except (ValueError, TypeError):
                continue
        
        if not valid_pitstops:
            logger.error("[ERROR] 沒有有效的進站時間數據")
            return
        
        self.pitstops_data = valid_pitstops
        
        # 1. 車手最快進站時間排行榜
        self._display_driver_fastest_pitstops(valid_pitstops)
        
        # 2. 車隊進站時間排行榜
        self._display_team_pitstop_rankings(valid_pitstops)
        
        # 3. 進站策略分析
        self._display_pitstop_strategy_analysis(valid_pitstops)
        
        # 4. 進站時間分佈分析
        self._display_pitstop_time_distribution(valid_pitstops)
    
    def _display_driver_fastest_pitstops(self, valid_pitstops):
        """顯示車手最快進站時間排行榜"""
        # 每位車手只顯示一次，最快時間
        driver_best_times = {}
        for stop in valid_pitstops:
            driver = stop['driver_acronym']
            if driver not in driver_best_times or stop['pit_duration'] < driver_best_times[driver]['pit_duration']:
                driver_best_times[driver] = stop
        
        # 按最快時間排序
        sorted_drivers = sorted(driver_best_times.values(), key=lambda x: x['pit_duration'])
        
        logger.info("[STATS] 總計有進站記錄的車手: %s", len(sorted_drivers))
        logger.info("⚡ 全場最快進站: %.1f秒 (%s)", sorted_drivers[0]['pit_duration'], sorted_drivers[0]['driver_acronym'])
        logger.info("🐌 全場最慢進站: %.1f秒 (%s)", sorted_drivers[-1]['pit_duration'], sorted_drivers[-1]['driver_acronym'])
        
        logger.info("🏆 車手最快進站時間排行榜:")
        time_table = PrettyTable()
        time_table.field_names = ["排名", "車手", "車隊", "最快進站時間", "圈數"]
        time_table.align = "l"
        
        for i, driver_data in enumerate(sorted_drivers, 1):
            time_table.add_row([
                i,
                driver_data['driver_acronym'],
                driver_data['team_name'][:18],
                f"{driver_data['pit_duration']:.1f}秒",
                driver_data['lap_number']
            ])
        
        logger.info("\n%s", time_table)
    
    def _display_team_pitstop_rankings(self, valid_pitstops):
        """顯示車隊進站時間排行榜"""
        team_stats = {}
        for stop in valid_pitstops:
            team = stop['team_name']
            if team not in team_stats:
                team_stats[team] = []
            team_stats[team].append(stop['pit_duration'])
        
        # 計算車隊最快時間並排序
        team_rankings = []
        for team, times in team_stats.items():
            fastest_time = min(times)
            team_rankings.append({
                'team': team,
                'fastest_time': fastest_time,
                'total_stops': len(times)
            })
        
        team_rankings.sort(key=lambda x: x['fastest_time'])
        
        logger.info("[FINISH] 車隊進站時間排行榜:")
        team_table = PrettyTable()
        team_table.field_names = ["排名", "車隊", "最快時間", "進站次數"]
        team_table.align = "l"
        
        for i, team_data in enumerate(team_rankings, 1):
            team_table.add_row([
                i,
                team_data['team'][:18],
                f"{team_data['fastest_time']:.1f}秒",
                team_data['total_stops']
            ])
        
        logger.info("\n%s", team_table)
    
    def _display_pitstop_strategy_analysis(self, valid_pitstops):
        """顯示進站策略分析"""
        logger.info("[INFO] 進站策略分析:")
        
        # 整理每位車手的所有進站記錄
        driver_pitstop_records = {}
        for stop in valid_pitstops:
            driver = stop['driver_acronym']
            if driver not in driver_pitstop_records:
                driver_pitstop_records[driver] = {
                    'team': stop['team_name'],
                    'stops': []
                }
            driver_pitstop_records[driver]['stops'].append({
                'lap': stop['lap_number'],
                'time': stop['pit_duration']
            })
        
        strategy_stats = {}
        for driver, data in driver_pitstop_records.items():
            stop_count = len(data['stops'])
            strategy_name = f"{stop_count}停"
            
            if strategy_name not in strategy_stats:
                strategy_stats[strategy_name] = {
                    'count': 0,
                    'drivers': [],
                    'times': []
                }
            
            strategy_stats[strategy_name]['count'] += 1
            strategy_stats[strategy_name]['drivers'].append(driver)
            strategy_stats[strategy_name]['times'].extend([stop['time'] for stop in data['stops']])
        
        self.strategy_stats = strategy_stats
        self.drivers_pitstops = driver_pitstop_records
        
        strategy_table = PrettyTable()
        strategy_table.field_names = ["策略", "車手數", "車手列表", "時間範圍"]
        strategy_table.align = "l"
        
        for stop_count in sorted(strategy_stats.keys(), key=lambda x: int(x[0])):
            stats = strategy_stats[stop_count]
            drivers_str = ', '.join(stats['drivers'][:6])  # 最多顯示6個車手
            if len(stats['drivers']) > 6:
                drivers_str += f"... (+{len(stats['drivers']) - 6})"
            
            if stats['times']:
                time_range = f"{min(stats['times']):.1f}s - {max(stats['times']):.1f}s"
            else:
                time_range = "N/A"
            
            strategy_table.add_row([
                stop_count,
                stats['count'],
                drivers_str,
                time_range
            ])
        
        logger.info("\n%s", strategy_table)
    
    def _display_pitstop_time_distribution(self, valid_pitstops):
        """顯示進站時間分佈分析"""
        logger.info("⏱️ 進站時間分佈分析:")
        
        # 計算所有進站時間的中位數
        all_pit_times = [stop['pit_duration'] for stop in valid_pitstops]
        median_time = sorted(all_pit_times)[len(all_pit_times) // 2]
        
        logger.info("[INFO] 本場比賽進站時間中位數: %.2f秒", median_time)
        
        # 基於中位數劃分時間範圍
        time_ranges = [
            (0, median_time, f"快速 (<{median_time:.1f}s)"),
            (median_time, float('inf'), f"較慢 (≥{median_time:.1f}s)")
        ]
        
        distribution_table = PrettyTable()
        distribution_table.field_names = ["時間範圍", "進站次數", "百分比", "代表車手 (時間)"]
        distribution_table.align = "l"
        
        total_stops = len(valid_pitstops)
        
        for min_time, max_time, range_name in time_ranges:
            if max_time == float('inf'):
                stops_in_range = [stop for stop in valid_pitstops if stop['pit_duration'] >= min_time]
            else:
                stops_in_range = [stop for stop in valid_pitstops if min_time <= stop['pit_duration'] < max_time]
            
            if stops_in_range:
                count = len(stops_in_range)
                percentage = (count / total_stops) * 100
                
                # 找出該範圍內最具代表性的進站（最接近該範圍中位數的）
                range_times = [stop['pit_duration'] for stop in stops_in_range]
                range_median = sorted(range_times)[len(range_times) // 2]
                representative_stop = min(stops_in_range, key=lambda x: abs(x['pit_duration'] - range_median))
                rep_str = f"{representative_stop['driver_acronym']} ({representative_stop['pit_duration']:.1f}s)"
                
                distribution_table.add_row([
                    range_name,
                    count,
                    f"{percentage:.1f}%",
                    rep_str
                ])
            else:
                distribution_table.add_row([range_name, 0, "0.0%", "無"])
        
        logger.info("\n%s", distribution_table)
    
    def _run_fastf1_analysis(self, data):
        """使用 FastF1 數據進行進站分析"""
        logger.info("🔄 執行 FastF1 進站分析...")
        
        try:
            laps = data.get('laps')
            if laps is None or laps.empty:
                logger.error("[ERROR] 沒有圈速數據")
                return False
            
            # 分析進站資料
            pitstops = []
            drivers_pitstops = {}
            
            for _, lap in laps.iterrows():
                driver = lap['Driver']
                
                # 檢查是否有進站時間資料
                if pd.notna(lap.get('PitInTime')) and pd.notna(lap.get('PitOutTime')):
                    pit_time = lap['PitOutTime'] - lap['PitInTime']
                    pit_duration = pit_time.total_seconds()
                    
                    pitstop_info = {
                        'driver': driver,
                        'lap': int(lap['LapNumber']),
                        'pit_time': pit_duration,
                        'compound_before': lap.get('Compound', 'Unknown'),
                        'tyre_life': lap.get('TyreLife', 0)
                    }
                    
                    pitstops.append(pitstop_info)
                    
                    if driver not in drivers_pitstops:
                        drivers_pitstops[driver] = []
                    drivers_pitstops[driver].append(pitstop_info)
            
            if not pitstops:
                logger.error("[ERROR] 沒有找到有效的進站資料")
                return False
            
            self.pitstops_data = pitstops
            self.drivers_pitstops = drivers_pitstops
            
            # 顯示分析結果
            self._display_fastf1_pitstop_rankings(pitstops)
            self._display_fastf1_driver_details(drivers_pitstops)
            self._display_fastf1_strategy_analysis(drivers_pitstops)
            self._display_fastf1_time_distribution(pitstops)
            self._display_fastf1_summary(pitstops)
            
            return True
            
        except Exception as e:
            logger.exception("[ERROR] FastF1 進站分析失敗: %s", e)
            return False
    
    def _display_fastf1_pitstop_rankings(self, pitstops):
        """顯示 FastF1 進站時間排行榜"""
        # 按進站時間排序
        pitstops.sort(key=lambda x: x['pit_time'])
        
        logger.info("🏆 所有車手進站時間排行榜:")
        time_table = PrettyTable()
        time_table.field_names = ["排名", "車手", "進站時間", "圈數", "輪胎"]
        time_table.align = "l"
        
        for i, ps in enumerate(pitstops, 1):
            time_table.add_row([
                i,
                ps['driver'],
                f"{ps['pit_time']:.1f}s",
                ps['lap'],
                str(ps['compound_before'])[:8]
            ])
        
        logger.info("\n%s", time_table)
    
    def _display_fastf1_driver_details(self, drivers_pitstops):
        """顯示車手進站詳細統計"""
        logger.info("👤 車手進站詳細統計:")
        
        for driver in sorted(drivers_pitstops.keys()):
            stops = drivers_pitstops[driver]
            stops.sort(key=lambda x: x['pit_time'])  # 按時間排序
            
            logger.info("🏎️ %s:", driver)
            driver_table = PrettyTable()
            driver_table.field_names = ["進站順序", "進站時間", "圈數", "輪胎", "胎齡"]
            driver_table.align = "l"
            
            for i, stop in enumerate(stops, 1):
                driver_table.add_row([
                    f"第{i}站",
                    f"{stop['pit_time']:.1f}s",
                    stop['lap'],
                    str(stop['compound_before'])[:8],
                    stop['tyre_life'] if stop['tyre_life'] else 'N/A'
                ])
            
            logger.info("\n%s", driver_table)
    
    def _display_fastf1_strategy_analysis(self, drivers_pitstops):
        """顯示 FastF1 進站策略分析"""
        logger.info("[INFO] 進站策略分析:")
        
        strategy_stats = {}
        for driver, stops in drivers_pitstops.items():
            stop_count = len(stops)
            if stop_count not in strategy_stats:
                strategy_stats[stop_count] = []
            strategy_stats[stop_count].append({
                'driver': driver,
                'times': [stop['pit_time'] for stop in stops]
            })
        
        strategy_table = PrettyTable()
        strategy_table.field_names = ["策略", "車手數", "車手列表", "時間範圍"]
        strategy_table.align = "l"
        
        for stop_count in sorted(strategy_stats.keys()):
            drivers_data = strategy_stats[stop_count]
            driver_names = [d['driver'] for d in drivers_data]
            
            # 計算該策略的時間範圍
            all_times = []
            for d in drivers_data:
                all_times.extend(d['times'])
            
            if all_times:
                min_time = min(all_times)
                max_time = max(all_times)
                time_range = f"{min_time:.1f}s - {max_time:.1f}s"
            else:
                time_range = "N/A"
            
            strategy_name = f"{stop_count}停策略"
            strategy_table.add_row([
                strategy_name,
                len(drivers_data),
                ", ".join(driver_names),
                time_range
            ])
        
        logger.info("\n%s", strategy_table)
    
    def _display_fastf1_time_distribution(self, pitstops):
        """顯示 FastF1 進站時間分佈分析"""
        logger.info("⏱️ 進站時間分佈分析:")
        
        time_ranges = [
            (0, 3.0, "超快 (≤3.0s)"),
            (3.0, 4.0, "快速 (3.0-4.0s)"),
            (4.0, 5.0, "正常 (4.0-5.0s)"),
            (5.0, 6.0, "較慢 (5.0-6.0s)"),
            (6.0, float('inf'), "很慢 (>6.0s)")
        ]
        
        distribution_table = PrettyTable()
        distribution_table.field_names = ["時間範圍", "進站次數", "百分比", "車手 (最快時間)"]
        distribution_table.align = "l"
        
        for min_time, max_time, range_name in time_ranges:
            stops_in_range = [
                stop for stop in pitstops 
                if min_time <= stop['pit_time'] < max_time or 
                (max_time == float('inf') and stop['pit_time'] >= min_time)
            ]
            
            count = len(stops_in_range)
            percentage = (count / len(pitstops)) * 100 if pitstops else 0
            
            if stops_in_range:
                # 找出該範圍內最快的車手
                fastest_in_range = min(stops_in_range, key=lambda x: x['pit_time'])
                fastest_info = f"{fastest_in_range['driver']} ({fastest_in_range['pit_time']:.1f}s)"
            else:
                fastest_info = "-"
            
            distribution_table.add_row([
                range_name,
                count,
                f"{percentage:.1f}%",
                fastest_info
            ])
        
        logger.info("\n%s", distribution_table)
    
    def _display_fastf1_summary(self, pitstops):
        """顯示 FastF1 分析總覽"""
        logger.info("[STATS] 進站分析總覽:")
        summary_table = PrettyTable()
        summary_table.field_names = ["統計項目", "數值"]
        summary_table.align = "l"
        
        avg_time = sum(p['pit_time'] for p in pitstops) / len(pitstops)
        min_time = min(p['pit_time'] for p in pitstops)
        max_time = max(p['pit_time'] for p in pitstops)
        
        summary_table.add_row(["總進站次數", len(pitstops)])
        summary_table.add_row(["平均進站時間", f"{avg_time:.1f}s"])
        summary_table.add_row(["最快進站時間", f"{min_time:.1f}s"])
        summary_table.add_row(["最慢進站時間", f"{max_time:.1f}s"])
        
        logger.info("\n%s", summary_table)
    
    def get_analysis_summary(self):
        """獲取分析摘要 - 返回結構化數據"""
        if not self.pitstops_data:
            return {
                "pitstop_summary": {
                    "total_pitstops": 0,
                    "drivers_with_pitstops": 0,
                    "average_pitstop_time": 0,
                    "message": "沒有進站數據可用於分析"
                },
                "driver_pitstops": {},
                "strategy_analysis": {
                    "strategies_used": 0,
                    "most_common_strategy": "N/A"
                }
            }
        
        total_stops = len(self.pitstops_data)
        strategy_count = len(self.strategy_stats)
        
        # 計算平均進站時間
        avg_time = 0
        if self.pitstops_data:
            total_time = sum(float(stop.get('Duration', 0)) for stop in self.pitstops_data if stop.get('Duration'))
            avg_time = total_time / len(self.pitstops_data) if self.pitstops_data else 0
        
        # 統計每個車手的進站次數
        driver_pitstops = {}
        for stop in self.pitstops_data:
            driver = stop.get('DriverCode', 'Unknown')
            if driver not in driver_pitstops:
                driver_pitstops[driver] = {
                    "pitstop_count": 0,
                    "total_time": 0,
                    "pitstops": []
                }
            driver_pitstops[driver]["pitstop_count"] += 1
            driver_pitstops[driver]["total_time"] += float(stop.get('Duration', 0))
            driver_pitstops[driver]["pitstops"].append({
                "lap": stop.get('Lap', 'N/A'),
                "time": stop.get('Time', 'N/A'),
                "duration": stop.get('Duration', 'N/A')
            })
        
        return {
            "pitstop_summary": {
                "total_pitstops": total_stops,
                "drivers_with_pitstops": len(driver_pitstops),
                "average_pitstop_time": round(avg_time, 3),
                "message": f"進站分析完成：共記錄 {total_stops} 次進站，{strategy_count} 種不同策略"
            },
            "driver_pitstops": driver_pitstops,
            "strategy_analysis": {
                "strategies_used": strategy_count,
                "most_common_strategy": list(self.strategy_stats.keys())[0] if self.strategy_stats else "N/A",
                "strategy_details": self.strategy_stats
            }
        }


def run_pitstop_analysis(data_loader, dynamic_team_mapping=None, f1_analysis_instance=None):
    """執行進站策略分析 - 模組入口函數"""
    logger.info("⏱️ 執行進站策略分析模組...")
    
    try:
        # 創建進站分析器
        analyzer = F1PitstopAnalyzer(data_loader)
        
        # 執行分析
        success = analyzer.run_analysis(f1_analysis_instance)
        
        if success:
            logger.info("[SUCCESS] 進站策略分析完成")
            return True
        else:
            logger.error("[ERROR] 進站策略分析失敗")
            return False
            
    except Exception as e:
        logger.exception("[ERROR] 進站策略分析模組執行錯誤: %s", e)
        return False


def run_pitstop_analysis_json(data_loader, dynamic_team_mapping=None, f1_analysis_instance=None, enable_debug=False):
    """執行進站策略分析並返回JSON格式結果 - API專用，優先使用 OpenF1 API"""
    logger.info("🚀 開始執行進站策略分析...")
    if enable_debug:
        logger.info("⏱️ 執行進站策略分析模組 (JSON輸出版)...")
    
    try:
        # 獲取基本賽事資訊
        session_info = {}
        cache_key = ""
        
        if hasattr(data_loader, 'session') and data_loader.session is not None:
            session_info = {
                "event_name": getattr(data_loader.session, 'event', {}).get('EventName', 'Unknown'),
                "circuit_name": getattr(data_loader.session, 'event', {}).get('Location', 'Unknown'),
                "session_type": getattr(data_loader.session, 'session_info', {}).get('Type', 'Unknown'),
                "year": getattr(data_loader.session, 'event', {}).get('year', 2024)
            }
            cache_key = f"pitstop_{session_info.get('year')}_{session_info.get('event_name', 'Unknown').replace(' ', '_')}"
        
        # 檢查緩存
        cached_data = check_cache(cache_key) if cache_key else None
        
        if cached_data:
            logger.info("📦 使用緩存數據")
            pitstop_data = cached_data
        else:
            logger.info("🔄 重新計算 - 開始數據分析...")
            
            # 創建進站分析器
            analyzer = F1PitstopAnalyzer(data_loader)
            
            # 執行進站分析並捕獲結果
            analyzer.run_analysis(f1_analysis_instance)
            pitstop_data = analyzer.get_analysis_summary()
            
            if pitstop_data and cache_key:
                # 保存緩存
                save_cache(pitstop_data, cache_key)
                logger.info("💾 分析結果已緩存")
        
        # 結果驗證和反饋
        if not report_analysis_results(pitstop_data, "進站策略分析"):
            return {
                "success": False,
                "message": "進站策略分析失敗：無可用數據",
                "data": None,
                "timestamp": datetime.now().isoformat()
            }
        
        if pitstop_data:
            result = {
                "success": True,
                "message": "成功執行 進站策略分析",
                "data": {
                    "function_id": 3,
                    "function_name": "Pitstop Strategy Analysis",
                    "function_description": "進站策略分析 (優先使用 OpenF1 API)",
                    "category": "基礎分析",
                    "analysis_type": "detailed_pitstop_analysis",
                    "metadata": {
                        "analysis_type": "pitstop_strategy_analysis",
                        "function_name": "Pitstop Strategy Analysis",
                        "generated_at": datetime.now().isoformat(),
                        "version": "2.0",
                        "data_source": "OpenF1 API (優先) + FastF1 (備用)",
                        "cache_used": cached_data is not None,
                        **session_info
                    },
                    "pitstop_analysis": pitstop_data
                },
                "timestamp": datetime.now().isoformat()
            }
            
            if enable_debug:
                logger.info("[SUCCESS] 進站策略分析完成 (JSON)")
            return result
        else:
            return {
                "success": False,
                "message": "進站策略分析執行失敗 - 無可用數據",
                "data": None,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        if enable_debug:
            logger.exception("[ERROR] 進站策略分析模組執行錯誤: %s", e)
        return {
            "success": False,
            "message": f"進站策略分析執行錯誤: {str(e)}",
            "data": None,
            "timestamp": datetime.now().isoformat()
        }


# 測試用主函數
def main():
    """測試用主函數"""
    logger.info("F1 進站策略分析模組 - 獨立測試")
    logger.info("需要數據載入器才能運行完整測試")

if __name__ == "__main__":
    main()
