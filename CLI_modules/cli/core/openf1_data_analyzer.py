#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F1 OpenF1 API 數據分析器
F1 OpenF1 API Data Analyzer

完全獨立的 OpenF1 API 數據分析模組
基於 f1_analysis_cli_new.py 的 F1OpenDataAnalyzer 類別

版本: 1.0
作者: F1 Analysis Team
"""

import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

import requests
import json
import os
from datetime import datetime
from typing import Dict, List, Optional


class F1OpenDataAnalyzer:
    """F1 OpenF1 API 數據分析器 - 完全復刻版"""
    
    def __init__(self):
        """初始化 F1 數據分析器"""
        self.base_url = "https://api.openf1.org/v1"
        
    def _make_request(self, endpoint: str, params: dict = None) -> list:
        """發送 API 請求 - 增強重試機制"""
        import time
        
        max_retries = 3
        retry_delay = 3  # 增加延遲到3秒
        
        for attempt in range(max_retries):
            try:
                url = f"{self.base_url}/{endpoint}"
                # 增加基本請求間隔以避免服務器過載
                time.sleep(1.0)  # 每個請求間隔1秒
                # 增加超時時間到90秒
                response = requests.get(url, params=params, timeout=90)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.Timeout:
                print(f"⏰ API 請求超時 (嘗試 {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    print(f"💤 等待 {retry_delay} 秒後重試...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指數退避 (3→6→12秒)
                else:
                    print(f"[ERROR] API 請求超時，已達最大重試次數")
                    return []
            except requests.exceptions.RequestException as e:
                print(f"[ERROR] API 請求失敗: {e}")
                if attempt < max_retries - 1:
                    print(f"💤 等待 {retry_delay} 秒後重試...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    return []
    
    def get_sessions(self, year: int = 2024) -> list:
        """獲取指定年份的會話"""
        return self._make_request("sessions", {"year": year})
    
    def get_race_sessions(self, year: int = 2024) -> list:
        """獲取正賽會話"""
        sessions = self.get_sessions(year)
        return [s for s in sessions if s.get('session_type') == 'Race']
    
    def get_pit_stops(self, session_key: int) -> list:
        """獲取進站數據"""
        return self._make_request("pit", {"session_key": session_key})
    
    def get_drivers(self, session_key: int) -> dict:
        """獲取車手信息"""
        drivers_list = self._make_request("drivers", {"session_key": session_key})
        return {d.get('driver_number'): d for d in drivers_list}
    
    def get_enhanced_pit_stops(self, session_key: int) -> list:
        """獲取增強的進站數據（包含車手信息）"""
        try:
            print(f"📡 從 OpenF1 API 獲取進站數據...")
            
            # 獲取進站數據
            pit_stops = self.get_pit_stops(session_key)
            if not pit_stops:
                print("[ERROR] 沒有找到進站數據")
                return []
            
            # 獲取車手信息
            drivers_info = self.get_drivers(session_key)
            if not drivers_info:
                print("[WARNING] 沒有找到車手信息")
            
            # 合併數據
            enhanced_stops = []
            for stop in pit_stops:
                driver_number = stop.get('driver_number')
                driver_info = drivers_info.get(driver_number, {})
                
                enhanced_stop = {
                    **stop,  # 包含所有原始進站數據
                    'driver_info': driver_info  # 添加車手信息
                }
                enhanced_stops.append(enhanced_stop)
            
            print(f"[SUCCESS] 成功獲取 {len(enhanced_stops)} 個進站記錄")
            return enhanced_stops
            
        except Exception as e:
            print(f"[ERROR] 獲取增強進站數據失敗: {e}")
            return []
    
    def get_driver_team_mapping(self, session_key: int) -> dict:
        """獲取車手代碼與車隊的映射關係"""
        drivers_list = self._make_request("drivers", {"session_key": session_key})
        mapping = {}
        
        print(f"\n[DEBUG] 從 OpenF1 API 獲取車手-車隊映射 (session_key: {session_key})")
        print("=" * 60)
        
        for driver in drivers_list:
            name_acronym = driver.get('name_acronym', '')
            team_name = driver.get('team_name', '')
            full_name = driver.get('full_name', '')
            driver_number = driver.get('driver_number', '')
            
            if name_acronym and team_name:
                mapping[name_acronym] = team_name
                # 安全處理 driver_number 可能為 None 的情況
                number_display = f"#{driver_number:2}" if driver_number is not None else "#--"
                print(f"  {name_acronym:4} | {team_name:25} | {number_display} {full_name}")
        
        print("=" * 60)
        print(f"[SUCCESS] 共載入 {len(mapping)} 位車手的車隊映射")
        
        return mapping
    
    def find_race_session_by_name(self, year: int, race_name: str) -> dict:
        """根據比賽名稱找到對應的會話"""
        sessions = self.get_sessions(year)
        race_sessions = [s for s in sessions if s.get('session_type') == 'Race' and s.get('session_name') == 'Race']
        
        # 建立比賽名稱對應表
        race_name_mapping = {
            'british': ['silverstone', 'britain', 'uk', 'united kingdom', 'great britain'],
            'japan': ['suzuka', 'japanese'],
            'australia': ['melbourne', 'australian'],
            'china': ['shanghai', 'chinese'],  # 添加中國大獎賽映射
            'monaco': ['monte carlo', 'montecarlo'],
            'spain': ['barcelona', 'spanish', 'catalunya'],
            'canada': ['montreal', 'canadian', 'montréal'],
            'austria': ['spielberg', 'austrian'],
            'france': ['paul ricard', 'french'],
            'hungary': ['budapest', 'hungarian'],
            'belgium': ['spa', 'belgian'],
            'italy': ['monza', 'italian', 'imola', 'san marino'],
            'singapore': ['marina bay', 'singaporean'],
            'russia': ['sochi', 'russian'],
            'turkey': ['istanbul', 'turkish'],
            'usa': ['austin', 'cota', 'united states', 'american', 'miami', 'florida'],
            'mexico': ['mexico city', 'mexican'],
            'brazil': ['interlagos', 'sao paulo', 'brazilian'],
            'abu dhabi': ['yas island', 'yas marina', 'uae', 'united arab emirates'],
            'bahrain': ['sakhir', 'bahraini'],
            'saudi arabia': ['jeddah', 'saudi'],
        }
        
        race_name_lower = race_name.lower()
        
        # 直接匹配
        for session in race_sessions:
            location = session.get('location', '').lower()
            country = session.get('country_name', '').lower()
            
            if race_name_lower in location or race_name_lower in country:
                return session
        
        # 使用映射表匹配
        for key, aliases in race_name_mapping.items():
            # 檢查搜尋名稱是否匹配 key 或任何 alias
            if race_name_lower == key or race_name_lower in aliases or any(alias in race_name_lower for alias in aliases):
                # 在所有會話中搜尋匹配的 location 或 country
                for session in race_sessions:
                    location = session.get('location', '').lower()
                    country = session.get('country_name', '').lower()
                    
                    # 檢查 key 或任何 alias 是否出現在 location 或 country 中
                    if (key in location or key in country or 
                        any(alias in location or alias in country for alias in aliases)):
                        return session
        
        print(f"[WARNING] 找不到匹配的比賽會話: {race_name}")
        return {}
    
    def save_pitstop_data_to_cache(self, pitstop_data: list, year: int, race_name: str) -> Optional[str]:
        """保存進站數據到快取文件"""
        try:
            # 確保快取目錄存在
            cache_dir = "cache"
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)
            
            # 生成快取文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"f1_{year}_{race_name}_pitstops_{timestamp}.json"
            filepath = os.path.join(cache_dir, filename)
            
            # 保存數據
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(pitstop_data, f, indent=2, ensure_ascii=False)
            
            return filepath
            
        except Exception as e:
            print(f"[ERROR] 保存進站數據到快取失敗: {e}")
            return None
    
    def get_weather_data(self, session_key: int) -> list:
        """獲取天氣數據"""
        return self._make_request("weather", {"session_key": session_key})
    
    def get_car_data(self, session_key: int, driver_number: int = None) -> list:
        """獲取車輛數據"""
        params = {"session_key": session_key}
        if driver_number:
            params["driver_number"] = driver_number
        return self._make_request("car_data", params)
    
    def get_position_data(self, session_key: int, driver_number: int = None) -> list:
        """獲取位置數據"""
        params = {"session_key": session_key}
        if driver_number:
            params["driver_number"] = driver_number
        return self._make_request("position", params)


# 測試用主函數
def main():
    """測試用主函數"""
    print("F1 OpenF1 API 數據分析器 - 獨立測試")
    
    analyzer = F1OpenDataAnalyzer()
    
    # 測試獲取 2025 年的會話
    print("\n[DEBUG] 測試獲取 2025 年會話...")
    sessions = analyzer.get_sessions(2025)
    print(f"找到 {len(sessions)} 個會話")
    
    # 測試獲取正賽會話
    race_sessions = analyzer.get_race_sessions(2025)
    print(f"找到 {len(race_sessions)} 個正賽會話")
    
    # 測試查找特定比賽
    if race_sessions:
        print("\n📍 測試查找 Japan 比賽...")
        japan_session = analyzer.find_race_session_by_name(2025, "Japan")
        if japan_session:
            print(f"[SUCCESS] 找到日本站: {japan_session.get('location')} (session_key: {japan_session.get('session_key')})")
        else:
            print("[ERROR] 未找到日本站")


if __name__ == "__main__":
    main()
