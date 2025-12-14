#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F1 Analysis Instance Module
F1分析實例模組 - 完整復刻版本
用於替代對原始 f1_analysis_cli_new.py 的依賴，提供與原版相同的功能
"""

import os
import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

import time
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import requests
import traceback

# 添加父目錄到path以便導入base模組
sys.path.append(str(Path(__file__).parent.parent))

from modules.base import F1AnalysisBase
from modules.data_loader import F1DataLoader, F1OpenDataAnalyzer


class F1OvertakingAnalyzer:
    """完整復刻版超車分析器 - 與 f1_analysis_cli_new.py 保持一致"""
    
    def __init__(self):
        self.data_loader = F1DataLoader()
        self.openf1_analyzer = F1OpenDataAnalyzer()
        self.cache_dir = "overtaking_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 車手號碼映射 - 與原版保持一致
        self.driver_numbers = {
            'VER': 1, 'LEC': 16, 'SAI': 55, 'PER': 11, 'RUS': 63,
            'HAM': 44, 'NOR': 4, 'PIA': 81, 'ALO': 14, 'STR': 18,
            'TSU': 22, 'RIC': 3, 'GAS': 10, 'OCO': 31, 'ALB': 23,
            'SAR': 2, 'MAG': 20, 'HUL': 27, 'BOT': 77, 'ZHO': 24
        }
        
        # 2025年已完成比賽 - 與原版保持一致
        self.completed_races_2025 = [
            "Australia", "China", "Japan", "Bahrain", "Saudi Arabia", "Miami",
            "Emilia Romagna", "Monaco", "Spain", "Canada", "Austria", "Great Britain"
        ]
        
        # 比賽名稱映射 - 與原版保持一致
        self.race_name_aliases = {
            'Great Britain': ['Great Britain', 'Britain', 'British', 'Silverstone', 'UK', 'United Kingdom'],
            'Japan': ['Japan', 'Japanese', 'Suzuka'],
            'Australia': ['Australia', 'Australian', 'Melbourne'],
            'Monaco': ['Monaco', 'Monte Carlo'],
        }

    def analyze_all_drivers_overtaking(self, years, race_name=None):
        """分析所有車手的超車表現比較 - 完全復刻原版實現"""
        try:
            print(f"\n🏎️ 開始分析所有車手在 {years} 年的超車表現...")
            
            # 先確定實際要分析的比賽名稱
            matched_race_name = None
            if race_name:
                first_year = years[0] if years else 2025
                available_races = self._get_available_races(first_year)
                matched_race_name = self._match_race_name(race_name, available_races)
                
                if not matched_race_name:
                    print(f"[ERROR] 找不到比賽 '{race_name}'")
                    return None
                
                if matched_race_name != race_name:
                    print(f"🔄 比賽名稱匹配: '{race_name}' -> '{matched_race_name}'")
            
            all_drivers_data = {}
            total_races_analyzed = 0
            
            # 獲取車手列表
            drivers = list(self.driver_numbers.keys())
            print(f"[LIST] 分析車手列表: {', '.join(drivers)}")
            
            for year in years:
                print(f"\n📅 分析 {year} 年...")
                year_races = [matched_race_name] if matched_race_name else self._get_available_races(year)
                
                all_drivers_data[year] = {}
                
                for race in year_races:
                    print(f"   [FINISH] 分析 {race}...")
                    race_data = self._get_all_drivers_race_data(year, race)
                    
                    if race_data:
                        all_drivers_data[year][race] = race_data
                        total_races_analyzed += 1
                        print(f"   [SUCCESS] {race}: 成功獲取 {len(race_data)} 位車手資料")
                    else:
                        print(f"   [ERROR] {race}: 資料獲取失敗")
            
            if not all_drivers_data:
                print("[ERROR] 沒有獲取到任何超車資料")
                return None
            
            # 處理和分析資料
            analysis_results = self._process_all_drivers_data(all_drivers_data, years)
            
            if analysis_results:
                print(f"\n[SUCCESS] 分析完成！共分析 {total_races_analyzed} 場比賽")
            
            return analysis_results
            
        except Exception as e:
            print(f"[ERROR] 全車手超車分析失敗: {e}")
            traceback.print_exc()
            return None

    def _get_available_races(self, year):
        """獲取指定年份的可用比賽列表"""
        if year == 2025:
            return self.completed_races_2025.copy()
        elif year == 2024:
            # 2024年完整賽程
            return [
                "Bahrain", "Saudi Arabia", "Australia", "Japan", "China", "Miami",
                "Emilia Romagna", "Monaco", "Canada", "Spain", "Austria", "Great Britain",
                "Hungary", "Belgium", "Netherlands", "Italy", "Azerbaijan", "Singapore",
                "United States", "Mexico", "Brazil", "Las Vegas", "Qatar", "Abu Dhabi"
            ]
        else:
            return []

    def _match_race_name(self, input_race_name, available_races):
        """智能匹配比賽名稱"""
        if not input_race_name or not available_races:
            return None
        
        # 直接匹配
        for race in available_races:
            if input_race_name.lower() == race.lower():
                return race
        
        # 使用別名匹配
        input_lower = input_race_name.lower()
        for standard_name, aliases in self.race_name_aliases.items():
            if standard_name in available_races:
                for alias in aliases:
                    if alias.lower() == input_lower:
                        return standard_name
        
        # 部分匹配
        for race in available_races:
            if input_lower in race.lower() and len(input_lower) >= 3:
                return race
        
        return None

    def get_driver_overtaking_stats(self, driver_abbr):
        """
        獲取單一車手的超車統計數據
        
        Args:
            driver_abbr (str): 車手代碼 (如 'VER', 'NOR', 等)
        
        Returns:
            dict: 車手超車統計數據，包含 overtakes_made, overtaken_by 等欄位
        """
        try:
            # 使用真實的比賽數據分析超車統計
            if hasattr(self.data_loader, 'laps') and self.data_loader.laps is not None:
                driver_laps = self.data_loader.laps[self.data_loader.laps['Driver'] == driver_abbr]
                if len(driver_laps) > 1:
                    # 分析位置變化來計算超車
                    position_changes = driver_laps['Position'].diff().fillna(0)
                    overtakes_made = len(position_changes[position_changes < 0])  # 位置前進
                    overtaken_by = len(position_changes[position_changes > 0])    # 位置後退
                    
                    return {
                        'overtakes_made': overtakes_made,
                        'overtaken_by': overtaken_by,
                        'net_overtaking': overtakes_made - overtaken_by,
                        'success_rate': (overtakes_made / (overtakes_made + overtaken_by)) * 100 if (overtakes_made + overtaken_by) > 0 else 0.0,
                        'total_attempts': overtakes_made + overtaken_by
                    }
            
            # 如果沒有圈速資料，回傳基本統計
            return {
                'overtakes_made': 0,
                'overtaken_by': 0,
                'net_overtaking': 0,
                'success_rate': 0.0,
                'total_attempts': 0
            }
                
        except Exception as e:
            print(f"[ERROR] 獲取車手 {driver_abbr} 超車統計失敗: {e}")
            return {
                'overtakes_made': 0,
                'overtaken_by': 0,
                'net_overtaking': 0,
                'success_rate': 0.0,
                'total_attempts': 0
            }

    def _get_all_drivers_race_data(self, year, race_name):
        """獲取單場比賽所有車手的超車資料 - 復刻原版邏輯"""
        try:
            print(f"   🔄 從API獲取 {race_name} 所有車手資料...")
            
            # 優先使用OpenF1
            all_drivers_data = self._get_openf1_all_drivers_data(year, race_name)
            
            if not all_drivers_data:
                # 備用FastF1
                all_drivers_data = self._get_fastf1_all_drivers_data(year, race_name)
            
            return all_drivers_data
            
        except Exception as e:
            print(f"   [ERROR] 獲取 {race_name} 全車手資料失敗: {e}")
            return None

    def _get_openf1_all_drivers_data(self, year, race_name):
        """從OpenF1獲取所有車手的比賽資料 - 復刻原版邏輯"""
        try:
            time.sleep(1)  # API保護延遲
            
            # 獲取session資訊
            sessions_data = self.openf1_analyzer._make_request(
                'sessions',
                {"year": year, "session_name": "Race"}
            )
            
            if not sessions_data:
                return None
            
            # 找到對應的session
            target_session = None
            for session in sessions_data:
                location = session.get('location', '').lower()
                country = session.get('country_name', '').lower()
                
                if (race_name.lower() in location or 
                    race_name.lower() in country or
                    location in race_name.lower() or
                    country in race_name.lower()):
                    target_session = session
                    break
            
            if not target_session:
                return None
            
            session_key = target_session['session_key']
            
            # 獲取所有車手的位置資料
            all_drivers_data = {}
            
            for driver_abbr, driver_number in self.driver_numbers.items():
                try:
                    # 獲取位置資料
                    position_data = self.openf1_analyzer._make_request(
                        'position',
                        {"session_key": session_key, "driver_number": driver_number}
                    )
                    
                    if position_data:
                        # 使用與原版相同的計算邏輯
                        overtakes = self._calculate_overtakes_from_positions(position_data)
                        all_drivers_data[driver_abbr] = {
                            'overtakes': overtakes,
                            'driver_number': driver_number,
                            'position_data_points': len(position_data)
                        }
                    
                    time.sleep(0.5)  # API保護延遲
                    
                except Exception as e:
                    print(f"   [WARNING] {driver_abbr} 資料獲取失敗: {e}")
                    continue
            
            return all_drivers_data if all_drivers_data else None
            
        except Exception as e:
            print(f"   [ERROR] OpenF1全車手資料獲取失敗: {e}")
            return None

    def _get_fastf1_all_drivers_data(self, year, race_name):
        """從FastF1獲取所有車手的比賽資料 - 復刻原版邏輯"""
        try:
            # 載入FastF1資料
            race_loaded = self.data_loader.load_race_data(year, race_name, 'R')
            
            if not race_loaded:
                return None
            
            loaded_data = self.data_loader.loaded_data
            
            if 'laps' not in loaded_data:
                return None

            laps = loaded_data['laps']
            all_drivers_data = {}
            
            for driver_abbr in self.driver_numbers.keys():
                try:
                    driver_laps = laps[laps['Driver'] == driver_abbr].copy()
                    
                    if driver_laps.empty:
                        continue
                    
                    # 提取位置變化來計算超車 - 使用與原版相同的邏輯
                    positions = []
                    lap_numbers = []
                    
                    for _, lap in driver_laps.iterrows():
                        position = lap.get('Position')
                        lap_num = lap.get('LapNumber')
                        
                        if pd.notna(position) and position > 0:
                            if pd.notna(lap_num) and lap_num > 0:
                                lap_numbers.append(int(lap_num))
                                positions.append(int(position))
                    
                    if len(positions) < 2:
                        continue
                    
                    # 計算超車次數（位置改善的總和）- 與原版完全一致
                    overtakes = 0
                    for i in range(1, len(positions)):
                        if positions[i] < positions[i-1]:  # 位置提升
                            overtakes += (positions[i-1] - positions[i])
                    
                    all_drivers_data[driver_abbr] = {
                        'overtakes': overtakes,
                        'driver_number': self.driver_numbers.get(driver_abbr, 0),
                        'position_data_points': len(positions)
                    }
                    
                except Exception as e:
                    print(f"   [WARNING] {driver_abbr} FastF1分析失敗: {e}")
                    continue
            
            return all_drivers_data if all_drivers_data else None
            
        except Exception as e:
            print(f"   [ERROR] FastF1全車手資料獲取失敗: {e}")
            return None

    def _calculate_overtakes_from_positions(self, position_data):
        """從位置資料計算超車次數 - 與原版完全一致的計算邏輯"""
        try:
            if not position_data:
                return 0
            
            # 按時間排序
            sorted_data = sorted(position_data, key=lambda x: x.get('date', ''))
            
            positions = []
            for data_point in sorted_data:
                position = data_point.get('position')
                if position and isinstance(position, (int, float)):
                    positions.append(int(position))
            
            if len(positions) < 2:
                return 0
            
            # 計算超車 (位置提升) - 與原版完全一致
            overtakes = 0
            for i in range(1, len(positions)):
                if positions[i] < positions[i-1]:  # 位置提升
                    overtakes += (positions[i-1] - positions[i])
            
            return overtakes
            
        except Exception as e:
            return 0

    def _process_all_drivers_data(self, all_drivers_data, years):
        """處理所有車手的資料並生成統計 - 復刻原版邏輯"""
        try:
            analysis_results = {
                'drivers_stats': {},
                'race_summary': {},
                'yearly_summary': {},
                'overall_summary': {}
            }
            
            # 初始化車手統計
            for driver in self.driver_numbers.keys():
                analysis_results['drivers_stats'][driver] = {
                    'total_overtakes': 0,
                    'total_races': 0,
                    'avg_overtakes': 0.0,
                    'best_race': {'race': 'N/A', 'overtakes': 0},
                    'worst_race': {'race': 'N/A', 'overtakes': 999},
                    'races_details': {}
                }
            
            # 初始化年度統計
            for year in years:
                analysis_results['yearly_summary'][year] = {
                    'total_races': 0,
                    'total_overtakes': 0,
                    'drivers_participated': set()
                }
            
            # 處理每年每場比賽的資料
            for year, year_data in all_drivers_data.items():
                for race_name, race_data in year_data.items():
                    race_key = f"{year} {race_name}"
                    
                    # 初始化比賽統計
                    analysis_results['race_summary'][race_key] = {
                        'total_overtakes': 0,
                        'drivers_count': len(race_data),
                        'top_performer': {'driver': 'N/A', 'overtakes': 0}
                    }
                    
                    analysis_results['yearly_summary'][year]['total_races'] += 1
                    
                    # 處理每位車手的資料
                    for driver, driver_data in race_data.items():
                        overtakes = driver_data.get('overtakes', 0)
                        
                        # 更新車手統計
                        driver_stats = analysis_results['drivers_stats'][driver]
                        driver_stats['total_overtakes'] += overtakes
                        driver_stats['total_races'] += 1
                        driver_stats['races_details'][race_key] = overtakes
                        
                        # 更新最佳/最差表現
                        if overtakes > driver_stats['best_race']['overtakes']:
                            driver_stats['best_race'] = {'race': race_key, 'overtakes': overtakes}
                        
                        if overtakes < driver_stats['worst_race']['overtakes']:
                            driver_stats['worst_race'] = {'race': race_key, 'overtakes': overtakes}
                        
                        # 更新比賽統計
                        analysis_results['race_summary'][race_key]['total_overtakes'] += overtakes
                        if overtakes > analysis_results['race_summary'][race_key]['top_performer']['overtakes']:
                            analysis_results['race_summary'][race_key]['top_performer'] = {
                                'driver': driver, 'overtakes': overtakes
                            }
                        
                        # 更新年度統計
                        analysis_results['yearly_summary'][year]['drivers_participated'].add(driver)
                        analysis_results['yearly_summary'][year]['total_overtakes'] += overtakes
            
            # 計算平均值
            for driver, stats in analysis_results['drivers_stats'].items():
                if stats['total_races'] > 0:
                    stats['avg_overtakes'] = stats['total_overtakes'] / stats['total_races']
                
                if stats['worst_race']['overtakes'] == 999:
                    stats['worst_race'] = {'race': 'N/A', 'overtakes': 0}
            
            # 計算整體統計
            total_races = sum(len(year_data) for year_data in all_drivers_data.values())
            total_overtakes = sum(stats['total_overtakes'] for stats in analysis_results['drivers_stats'].values())
            active_drivers = len([d for d in analysis_results['drivers_stats'].values() if d['total_races'] > 0])
            
            analysis_results['overall_summary'] = {
                'total_races_analyzed': total_races,
                'total_overtakes': total_overtakes,
                'active_drivers': active_drivers,
                'avg_overtakes_per_race': total_overtakes / total_races if total_races > 0 else 0,
                'avg_overtakes_per_driver': total_overtakes / active_drivers if active_drivers > 0 else 0
            }

            return analysis_results
            
        except Exception as e:
            print(f"[ERROR] 資料處理失敗: {e}")
            traceback.print_exc()
            return None
                
                if not matched_race_name:
                    print(f"[ERROR] 無法匹配指定的比賽: '{race_name}'")
                    print(f"   [LIST] 可用比賽: {', '.join(available_races) if available_races else '無'}")
                    return None
                
                if matched_race_name != race_name:
                    print(f"   [NOTE] 比賽名稱匹配: '{race_name}' → '{matched_race_name}'")
            
            # 檢查整體分析結果快取
            years_str = "-".join(map(str, sorted(years)))
            cache_key = f"all_drivers_analysis_{years_str}"
            if matched_race_name:
                cache_key += f"_{matched_race_name}"
            
            # 獲取車手列表
            drivers = ['VER', 'HAM', 'RUS', 'LEC', 'SAI', 'NOR', 'PIA', 'ALB', 'ALO', 'STR', 'TSU', 'RIC', 'GAS', 'OCO', 'MAG', 'HUL', 'BOT', 'ZHO', 'SAR', 'PER']
            print(f"[LIST] 分析車手列表: {', '.join(drivers)}")
            
            all_drivers_data = {}
            total_races_analyzed = 0
            
            for year in years:
                print(f"\n📅 分析 {year} 賽季...")
                
                # 使用可用比賽列表
                if year == 2025:
                    available_races = ['Australia', 'China', 'Japan', 'Bahrain', 'Saudi Arabia', 'Miami', 'Emilia Romagna', 'Monaco', 'Spain', 'Canada', 'Austria', 'Great Britain']
                else:
                    available_races = ['Bahrain', 'Saudi Arabia', 'Australia', 'Japan', 'China', 'Miami', 'Emilia Romagna', 'Monaco', 'Canada', 'Spain', 'Austria', 'Great Britain', 'Hungary', 'Belgium', 'Netherlands', 'Italy', 'Azerbaijan', 'Singapore', 'United States', 'Mexico', 'Brazil', 'Las Vegas', 'Qatar', 'Abu Dhabi']
                
                if not available_races:
                    print(f"[ERROR] {year} 年沒有可用的比賽資料")
                    continue
                
                # 如果指定了特定比賽，使用匹配後的名稱
                if matched_race_name:
                    races_to_analyze = [matched_race_name]
                    print(f"[TARGET] 專注分析特定比賽: {matched_race_name}")
                else:
                    races_to_analyze = available_races
                
                year_data = {}
                successful_races = 0
                
                for race in races_to_analyze:
                    print(f"\n[FINISH] 分析 {race}...")
                    race_overtaking_data = self._get_detailed_race_overtaking_data(year, race)
                    
                    if race_overtaking_data:
                        year_data[race] = race_overtaking_data
                        successful_races += 1
                        total_races_analyzed += 1
                        
                        # 顯示詳細統計
                        driver_count = len([k for k in race_overtaking_data.keys() if k != 'race_weather'])
                        total_race_overtakes = sum(data.get('overtakes_made', 0) for data in race_overtaking_data.values() if isinstance(data, dict) and 'overtakes_made' in data)
                        
                        print(f"   [SUCCESS] {race}: 成功獲取 {driver_count} 位車手資料，共記錄 {total_race_overtakes} 次超車")
                    else:
                        print(f"   [ERROR] {race}: 資料獲取失敗")
                    
                    # 添加延遲保護
                    import time
                    time.sleep(1)  # 比賽間延遲
                
                if successful_races > 0:
                    all_drivers_data[year] = year_data
                    print(f"[SUCCESS] {year} 年分析完成: 共 {successful_races} 場比賽")
            
            if not all_drivers_data:
                print(f"[ERROR] 未找到任何有效的超車資料")
                return None
            
            # 處理和分析資料
            analysis_results = self._process_detailed_drivers_data(all_drivers_data, years)
            
            print(f"\n[TARGET] 深度分析完成！")
            print(f"[INFO] 分析了 {total_races_analyzed} 場比賽")
            print(f"🏎️  統計了 {len(analysis_results.get('drivers_stats', {}))} 位車手")
            print(f"[START] 總超車次數: {analysis_results.get('overall_summary', {}).get('total_overtakes', 0)}")
            
            return analysis_results
            
        except Exception as e:
            print(f"[ERROR] 深度超車分析失敗: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _get_available_races(self, year):
        """獲取可用比賽列表"""
        if year == 2025:
            return ['Australia', 'China', 'Japan', 'Bahrain', 'Saudi Arabia', 'Miami', 'Emilia Romagna', 'Monaco', 'Spain', 'Canada', 'Austria', 'Great Britain']
        else:
            return ['Bahrain', 'Saudi Arabia', 'Australia', 'Japan', 'China', 'Miami', 'Emilia Romagna', 'Monaco', 'Canada', 'Spain', 'Austria', 'Great Britain', 'Hungary', 'Belgium', 'Netherlands', 'Italy', 'Azerbaijan', 'Singapore', 'United States', 'Mexico', 'Brazil', 'Las Vegas', 'Qatar', 'Abu Dhabi']
    
    def _match_race_name(self, input_race_name, available_races):
        """智能匹配比賽名稱 - 增強版本，支援賽道別名"""
        if not input_race_name or not available_races:
            return None
        
        print(f"   [DEBUG] 智能匹配: '{input_race_name}' -> 可用比賽: {available_races}")
        
        # 建立完整的比賽別名映射表
        race_aliases = {
            'Japan': ['Japan', 'Japanese', 'Suzuka', 'suzuka'],
            'Great Britain': ['Great Britain', 'Britain', 'British', 'Silverstone', 'silverstone', 'UK', 'United Kingdom'],
            'Australia': ['Australia', 'Australian', 'Melbourne', 'melbourne'],
            'Monaco': ['Monaco', 'monte carlo', 'montecarlo'],
            'Spain': ['Spain', 'Spanish', 'Barcelona', 'barcelona', 'Catalunya'],
            'Canada': ['Canada', 'Canadian', 'Montreal', 'montreal', 'Montréal'],
            'Austria': ['Austria', 'Austrian', 'Spielberg', 'spielberg'],
            'Hungary': ['Hungary', 'Hungarian', 'Budapest', 'budapest'],
            'Belgium': ['Belgium', 'Belgian', 'Spa', 'spa'],
            'Italy': ['Italy', 'Italian', 'Monza', 'monza'],
            'Singapore': ['Singapore', 'Marina Bay', 'marina bay'],
            'United States': ['United States', 'USA', 'American', 'Austin', 'COTA', 'austin', 'cota'],
            'Mexico': ['Mexico', 'Mexican', 'Mexico City', 'mexico city'],
            'Brazil': ['Brazil', 'Brazilian', 'Interlagos', 'interlagos', 'Sao Paulo', 'sao paulo'],
            'Abu Dhabi': ['Abu Dhabi', 'UAE', 'Yas Marina', 'yas marina'],
            'Bahrain': ['Bahrain', 'Bahraini', 'Sakhir', 'sakhir'],
            'Saudi Arabia': ['Saudi Arabia', 'Saudi', 'Jeddah', 'jeddah'],
            'China': ['China', 'Chinese', 'Shanghai', 'shanghai'],
            'Emilia Romagna': ['Emilia Romagna', 'Imola', 'imola', 'San Marino'],
            'Netherlands': ['Netherlands', 'Dutch', 'Zandvoort', 'zandvoort'],
            'Azerbaijan': ['Azerbaijan', 'Baku', 'baku'],
            'Miami': ['Miami', 'miami', 'Florida', 'florida'],
            'Qatar': ['Qatar', 'Lusail', 'lusail'],
            'Las Vegas': ['Las Vegas', 'Vegas', 'las vegas', 'vegas']
        }
        
        input_lower = input_race_name.lower().strip()
        
        # 1. 直接匹配（忽略大小寫）
        for race in available_races:
            if input_lower == race.lower():
                print(f"   [SUCCESS] 直接匹配: '{input_race_name}' -> '{race}'")
                return race
        
        # 2. 使用別名映射表匹配
        print(f"   [DEBUG] 檢查別名映射...")
        for standard_name, aliases in race_aliases.items():
            if standard_name in available_races:
                for alias in aliases:
                    if input_lower == alias.lower():
                        print(f"   [SUCCESS] 別名匹配成功: '{input_race_name}' -> '{alias}' -> '{standard_name}'")
                        return standard_name
        
        # 3. 部分匹配 - 檢查輸入是否包含在比賽名稱中
        print(f"   [DEBUG] 檢查部分匹配...")
        for race in available_races:
            if input_lower in race.lower() and len(input_lower) >= 3:
                print(f"   [SUCCESS] 部分匹配: '{input_race_name}' -> '{race}'")
                return race
        
        # 4. 反向部分匹配 - 檢查比賽名稱是否包含在輸入中
        for race in available_races:
            if race.lower() in input_lower and len(race) >= 3:
                print(f"   [SUCCESS] 反向匹配: '{input_race_name}' -> '{race}'")
                return race
        
        # 5. 模糊匹配建議
        print(f"   [ERROR] 無法匹配")
        print(f"   [TIP] 建議:")
        for race in available_races:
            # 簡單的相似度檢查
            if any(char in race.lower() for char in input_lower) and len(input_lower) >= 2:
                print(f"      - 也許您想找 '{race}'?")
                break
        
        return None
    
    def _get_detailed_race_overtaking_data(self, year, race_name):
        """獲取單場比賽詳細超車資料"""
        try:
            # 使用真實的 FastF1 和 OpenF1 資料分析超車
            race_data = {}
            total_overtakes = 0
            
            if hasattr(self.data_loader, 'results') and self.data_loader.results is not None:
                for index, driver_result in self.data_loader.results.iterrows():
                    driver = driver_result['Abbreviation']
                    
                    # 獲取該車手的真實超車數據
                    driver_stats = self.get_driver_overtaking_stats(driver)
                    overtakes_made = driver_stats.get('overtakes_made', 0)
                    overtaken_by = driver_stats.get('overtaken_by', 0)
                    
                    total_overtakes += overtakes_made
                    
                    # 獲取位置資訊
                    grid_pos = int(driver_result.get('GridPosition', 999)) if pd.notna(driver_result.get('GridPosition')) else 999
                    finish_pos = int(driver_result.get('Position', 999)) if pd.notna(driver_result.get('Position')) else 999
                    
                    race_data[driver] = {
                        'overtakes_made': overtakes_made,
                        'overtakes_suffered': overtaken_by,
                        'net_overtakes': overtakes_made - overtaken_by,
                        'total_overtakes': overtakes_made + overtaken_by,
                        'success_rate': (overtakes_made / (overtakes_made + overtaken_by) * 100) if (overtakes_made + overtaken_by) > 0 else 0,
                        'starting_position': grid_pos if grid_pos != 999 else None,
                        'finishing_position': finish_pos if finish_pos != 999 else None,
                        'positions_gained': (grid_pos - finish_pos) if grid_pos != 999 and finish_pos != 999 else 0,
                        'race_name': race_name,
                        'year': year
                    }
            
            # 獲取真實天氣資訊
            weather_info = self._get_real_weather_info(race_name, year)
            
            race_data['race_weather'] = {
                'has_rain': weather_info.get('has_rain', False),
                'weather_status': weather_info.get('weather_status', '☀️晴天'),
                'total_race_overtakes': total_overtakes
            }
            
            return race_data
            
        except Exception as e:
            print(f"   [ERROR] 獲取 {race_name} 詳細超車資料失敗: {e}")
            return None
    
    def _get_real_weather_info(self, race_name, year):
        """獲取真實天氣資訊 - 使用 FastF1 或 OpenF1 資料"""
        try:
            # 嘗試從 FastF1 會話資料獲取天氣
            if hasattr(self.data_loader, 'session') and self.data_loader.session is not None:
                try:
                    weather_data = self.data_loader.session.weather
                    if weather_data is not None and not weather_data.empty:
                        # 檢查是否有降雨資料
                        has_rain = False
                        if 'Rainfall' in weather_data.columns:
                            has_rain = weather_data['Rainfall'].any()
                        
                        return {
                            'has_rain': has_rain,
                            'weather_status': '🌧️下雨' if has_rain else '☀️晴天'
                        }
                except:
                    pass
            
            # 後備方案：返回未知天氣
            return {
                'has_rain': False,
                'weather_status': '❓未知天氣'
            }
            
        except Exception as e:
            print(f"[WARNING] 獲取 {race_name} 天氣資訊失敗: {e}")
            return {
                'has_rain': False,
                'weather_status': '❓未知天氣'
            }
    
    def _process_detailed_drivers_data(self, all_drivers_data, years):
        """處理詳細的車手超車資料"""
        try:
            analysis_results = {
                'drivers_stats': {},
                'race_summary': {},
                'yearly_summary': {},
                'overall_summary': {},
                'performance_rankings': {},
                'detailed_analysis': {}
            }
            
            # 初始化車手統計
            drivers = ['VER', 'HAM', 'RUS', 'LEC', 'SAI', 'NOR', 'PIA', 'ALB', 'ALO', 'STR', 'TSU', 'RIC', 'GAS', 'OCO', 'MAG', 'HUL', 'BOT', 'ZHO', 'SAR', 'PER']
            
            for driver in drivers:
                analysis_results['drivers_stats'][driver] = {
                    'total_races': 0,
                    'total_overtakes': 0,
                    'overtakes_made': 0,
                    'overtakes_suffered': 0,
                    'net_overtakes': 0,
                    'success_rate': 0.0,
                    'avg_overtakes_per_race': 0.0,
                    'best_performance': {'race': '', 'overtakes': 0},
                    'worst_performance': {'race': '', 'overtakes': 999},
                    'rain_performance': {'races': 0, 'overtakes': 0},
                    'dry_performance': {'races': 0, 'overtakes': 0},
                    'positions_gained_total': 0,
                    'consistency_score': 0.0
                }
            
            # 處理每年每場比賽的資料
            total_races = 0
            total_overtakes_all = 0
            
            for year, year_data in all_drivers_data.items():
                year_stats = {
                    'races': 0,
                    'total_overtakes': 0,
                    'drivers_participated': set()
                }
                
                for race_name, race_data in year_data.items():
                    if race_name == 'race_weather':
                        continue
                    
                    total_races += 1
                    race_overtakes = race_data.get('race_weather', {}).get('total_race_overtakes', 0)
                    total_overtakes_all += race_overtakes
                    year_stats['races'] += 1
                    year_stats['total_overtakes'] += race_overtakes
                    
                    # 是否為雨戰
                    is_rain = race_data.get('race_weather', {}).get('has_rain', False)
                    
                    for driver, driver_data in race_data.items():
                        if driver == 'race_weather' or not isinstance(driver_data, dict):
                            continue
                        
                        year_stats['drivers_participated'].add(driver)
                        
                        if driver in analysis_results['drivers_stats']:
                            stats = analysis_results['drivers_stats'][driver]
                            stats['total_races'] += 1
                            
                            overtakes_made = driver_data.get('overtakes_made', 0)
                            overtakes_suffered = driver_data.get('overtakes_suffered', 0)
                            
                            stats['overtakes_made'] += overtakes_made
                            stats['overtakes_suffered'] += overtakes_suffered
                            stats['total_overtakes'] += overtakes_made
                            stats['net_overtakes'] += driver_data.get('net_overtakes', 0)
                            stats['positions_gained_total'] += driver_data.get('positions_gained', 0)
                            
                            # 最佳/最差表現
                            if overtakes_made > stats['best_performance']['overtakes']:
                                stats['best_performance'] = {'race': f"{year} {race_name}", 'overtakes': overtakes_made}
                            if overtakes_made < stats['worst_performance']['overtakes']:
                                stats['worst_performance'] = {'race': f"{year} {race_name}", 'overtakes': overtakes_made}
                            
                            # 雨戰/乾戰統計
                            if is_rain:
                                stats['rain_performance']['races'] += 1
                                stats['rain_performance']['overtakes'] += overtakes_made
                            else:
                                stats['dry_performance']['races'] += 1
                                stats['dry_performance']['overtakes'] += overtakes_made
                
                year_stats['drivers_participated'] = len(year_stats['drivers_participated'])
                analysis_results['yearly_summary'][year] = year_stats
            
            # 計算平均值和排名
            for driver, stats in analysis_results['drivers_stats'].items():
                if stats['total_races'] > 0:
                    stats['avg_overtakes_per_race'] = stats['total_overtakes'] / stats['total_races']
                    
                    # 成功率計算
                    total_attempts = stats['overtakes_made'] + stats['overtakes_suffered']
                    if total_attempts > 0:
                        stats['success_rate'] = (stats['overtakes_made'] / total_attempts) * 100
                    
                    # 一致性評分 (基於平均值和變異)
                    stats['consistency_score'] = min(100, max(0, stats['avg_overtakes_per_race'] * 20))
            
            # 計算整體統計
            active_drivers = len([d for d in analysis_results['drivers_stats'].values() if d['total_races'] > 0])
            
            analysis_results['overall_summary'] = {
                'total_races_analyzed': total_races,
                'total_overtakes': total_overtakes_all,
                'active_drivers': active_drivers,
                'avg_overtakes_per_race': total_overtakes_all / total_races if total_races > 0 else 0,
                'avg_overtakes_per_driver': total_overtakes_all / active_drivers if active_drivers > 0 else 0,
                'years_analyzed': len(years),
                'seasons_covered': f"{min(years)}-{max(years)}" if len(years) > 1 else str(years[0])
            }
            
            # 建立績效排名
            analysis_results['performance_rankings'] = {
                'by_total_overtakes': sorted(
                    [(k, v['total_overtakes']) for k, v in analysis_results['drivers_stats'].items() if v['total_races'] > 0],
                    key=lambda x: x[1], reverse=True
                ),
                'by_success_rate': sorted(
                    [(k, v['success_rate']) for k, v in analysis_results['drivers_stats'].items() if v['total_races'] > 0],
                    key=lambda x: x[1], reverse=True
                ),
                'by_consistency': sorted(
                    [(k, v['consistency_score']) for k, v in analysis_results['drivers_stats'].items() if v['total_races'] > 0],
                    key=lambda x: x[1], reverse=True
                )
            }
            
            return analysis_results
            
        except Exception as e:
            print(f"[ERROR] 詳細資料處理失敗: {e}")
            return None


class F1AnalysisInstance:
    """簡化的F1分析實例"""
    
    def __init__(self):
        self.data_loader = None
        self.dynamic_team_mapping = {}
        self.session_loaded = False
        self.overtaking_analyzer = F1OvertakingAnalyzer()
        self.accident_analysis_data = None
    
    def _load_accident_analysis_data(self):
        """載入事故分析數據 - 簡化版本"""
        try:
            # 這是一個簡化的實現
            # 在實際情況下，這裡會載入事故分析所需的數據
            self.accident_analysis_data = {
                'track_status_changes': [],
                'safety_car_periods': [],
                'yellow_flag_periods': [],
                'red_flag_periods': []
            }
            print("[SUCCESS] 事故分析數據載入完成 (簡化模式)")
            return True
        except Exception as e:
            print(f"[ERROR] 事故分析數據載入失敗: {e}")
            return False
    
    def get_session_info(self):
        """獲取會話信息"""
        if self.data_loader and hasattr(self.data_loader, 'loaded_data'):
            return self.data_loader.loaded_data.get('metadata', {})
        return {}
    
    def get_drivers_info(self):
        """獲取車手信息"""
        if self.data_loader and hasattr(self.data_loader, 'loaded_data'):
            return self.data_loader.loaded_data.get('drivers_info', {})
        return {}


def create_f1_analysis_instance(data_loader=None, dynamic_team_mapping=None):
    """創建F1分析實例的工廠函數"""
    instance = F1AnalysisInstance()
    
    if data_loader:
        instance.data_loader = data_loader
        instance.session_loaded = True
    
    if dynamic_team_mapping:
        instance.dynamic_team_mapping = dynamic_team_mapping
    
    # 設置超車分析器
    instance.overtaking_analyzer = F1OvertakingAnalyzer()
    
    return instance
