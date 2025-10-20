#!/usr/bin/env python3
"""
F1 Compatible Data Loader - 完全復刻版數據載入器
Complete replica of F1DataLoader from f1_analysis_cli_new.py for modular system
完全兼容 f1_analysis_cli_new.py 中的 F1DataLoader 類別
"""

import os
import sys
import pickle
import requests
import traceback
from datetime import datetime
from pathlib import Path
import fastf1
import pandas as pd
import numpy as np

class F1OpenDataAnalyzer:
    """F1 OpenF1 API 數據分析器 - 完全復刻版"""
    def __init__(self):
        """初始化 F1 數據分析器"""
        self.base_url = "https://api.openf1.org/v1"
        
    def _make_request(self, endpoint: str, params: dict = None) -> list:
        """發送 API 請求"""
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] API 請求失敗: {e}")
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
        race_sessions = [s for s in sessions if s.get('session_type') == 'Race']
        
        # 建立比賽名稱對應表
        race_name_mapping = {
            'british': ['silverstone', 'britain', 'uk', 'united kingdom', 'great britain'],
            'japan': ['suzuka', 'japanese'],
            'australia': ['melbourne', 'australian'],
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
            'abu dhabi': ['yas marina', 'uae'],
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
            if race_name_lower in aliases or any(alias in race_name_lower for alias in aliases):
                for session in race_sessions:
                    location = session.get('location', '').lower()
                    country = session.get('country_name', '').lower()
                    
                    if key in location or key in country or any(alias in location or alias in country for alias in aliases):
                        return session
        
        return {}

class CompatibleF1DataLoader:
    """完全兼容 f1_analysis_cli_new.py 的 F1DataLoader 類別"""
    
    def __init__(self):
        self.session = None
        self.loaded_data = {}
        self.cache_dir = "f1_analysis_cache"
        self._ensure_cache_dir()
        
        # 便利屬性 - 與 IndependentF1DataLoader 兼容
        self.results = None
        self.laps = None
        self.session_loaded = False
        self.year = None
        self.race_name = None
        self.session_type = None
        self.weather_data = None
    
    def _ensure_cache_dir(self):
        """確保快取資料夾存在"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def _get_cache_filename(self, year, race_name, session_type):
        """生成快取檔案名稱"""
        safe_race_name = race_name.replace(" ", "_").replace("'", "")
        return f"{self.cache_dir}/f1_data_{year}_{safe_race_name}_{session_type}.pkl"
    
    def load_race_data(self, year, race_name, session_type='R', force_reload=False):
        """
        載入指定比賽的所有 FastF1 資料，並同步 OpenF1 車手車隊資料
        完全復刻 f1_analysis_cli_new.py 版本
        
        Args:
            year: 年份 (2024, 2025)
            race_name: 比賽名稱 (如 'Japan', 'Britain', 'Monaco')
            session_type: 賽段類型 ('R'=正賽, 'Q'=排位賽, 'P1/P2/P3'=練習賽)
            force_reload: 是否強制重新載入資料
        """
        cache_file = self._get_cache_filename(year, race_name, session_type)
        
        # 嘗試從快取載入
        if not force_reload and os.path.exists(cache_file):
            try:
                print(f"[CACHE] 從快取載入資料: {cache_file}")
                with open(cache_file, 'rb') as f:
                    self.loaded_data = pickle.load(f)
                print(f"[SUCCESS] 快取資料載入成功")
                
                # 設置便利屬性以便其他模組訪問
                self.year = year
                self.race_name = race_name
                self.session_type = session_type
                self.session = self.loaded_data['session']
                self.laps = self.loaded_data['laps']
                self.weather_data = self.loaded_data['weather_data']
                self.results = self.loaded_data['results']
                self.session_loaded = True
                
                return True
            except Exception as e:
                print(f"[WARNING]  快取載入失敗，將重新載入: {e}")
        
        # 從 FastF1 載入新資料
        try:
            print(f"[REFRESH] 載入 {year} 年 {race_name} 大獎賽 ({session_type}) 資料...")
            
            # FastF1 比賽名稱映射 - 將我們的標準名稱轉換為 FastF1 期望的名稱
            fastf1_race_mapping = {
                'Great Britain': 'British',  # 統一使用 'British' 保持與GUI一致
                'United States': 'United States',  # 🔧 修復: Austin COTA 使用 'United States'
                'Las Vegas': 'Las Vegas',
                'Emilia Romagna': 'Imola',
                'Saudi Arabia': 'Saudi Arabia',
                'Austria': 'Austria',
                'Australia': 'Australia',
                'Bahrain': 'Bahrain',
                'Canada': 'Canada',
                'Spain': 'Spain',
                'Monaco': 'Monaco',
                'Japan': 'Japan',
                'China': 'China',
                'Miami': 'Miami',  # Miami Grand Prix 保持原名
                'Netherlands': 'Netherlands',
                'Singapore': 'Singapore',
                'Hungary': 'Hungary',
                'Belgium': 'Belgium',
                'Italy': 'Italy',
                'Abu Dhabi': 'Abu Dhabi'
            }
            
            # 轉換比賽名稱給 FastF1
            fastf1_race_name = fastf1_race_mapping.get(race_name, race_name)
            if fastf1_race_name != race_name:
                print(f"   [REFRESH] 轉換比賽名稱: {race_name} -> {fastf1_race_name} (for FastF1)")
            
            # 啟用 FastF1 快取 - 使用正確的緩存目錄
            fastf1.Cache.enable_cache('f1_analysis_cache')
            
            # 載入 FastF1 session - 關鍵：要載入天氣數據
            self.session = fastf1.get_session(year, fastf1_race_name, session_type)
            self.session.load(weather=True)  # 確保載入天氣數據
            
            # 初始化 OpenF1 分析器
            openf1_analyzer = F1OpenDataAnalyzer()
            
            # 尋找對應的 OpenF1 session
            openf1_session = openf1_analyzer.find_race_session_by_name(year, race_name)
            openf1_drivers = {}
            openf1_team_mapping = {}
            
            if openf1_session:
                session_key = openf1_session.get('session_key')
                print(f"[LINK] 找到 OpenF1 session_key: {session_key}")
                
                # 獲取 OpenF1 車手資料
                openf1_drivers = openf1_analyzer.get_drivers(session_key)
                openf1_team_mapping = openf1_analyzer.get_driver_team_mapping(session_key)
            else:
                print(f"[WARNING]  未找到對應的 OpenF1 session，將只使用 FastF1 資料")
            
            # 收集所有相關資料
            self.loaded_data = {
                'metadata': {
                    'year': year,
                    'race_name': race_name,
                    'session_type': session_type,
                    'event_name': self.session.event['EventName'],
                    'location': self.session.event['Location'],
                    'date': self.session.date.strftime('%Y-%m-%d'),
                    'loaded_at': datetime.now().isoformat(),
                    'openf1_session_key': openf1_session.get('session_key') if openf1_session else None
                },
                'session': self.session,
                'results': self.session.results,
                'laps': self.session.laps,
                'weather_data': self.session.weather_data,
                'car_data': self.session.car_data,
                'track_status': self.session.track_status if hasattr(self.session, 'track_status') else None,
                'race_control_messages': self.session.race_control_messages if hasattr(self.session, 'race_control_messages') else None,
                'drivers_info': self._extract_drivers_info(),
                'openf1_drivers': openf1_drivers,
                'openf1_team_mapping': openf1_team_mapping,
                'synchronized_driver_data': self._synchronize_driver_data(openf1_drivers, openf1_team_mapping)
            }
            
            # 儲存到快取
            try:
                with open(cache_file, 'wb') as f:
                    pickle.dump(self.loaded_data, f)
                print(f"[SAVE] 資料已儲存到快取: {cache_file}")
            except Exception as e:
                print(f"[WARNING]  快取儲存失敗: {e}")
            
            print(f"[SUCCESS] 資料載入完成")
            
            # 設置便利屬性以便其他模組訪問
            self.year = year
            self.race_name = race_name
            self.session_type = session_type
            self.session = self.loaded_data['session']
            self.laps = self.loaded_data['laps']
            self.weather_data = self.loaded_data['weather_data']
            self.results = self.loaded_data['results']
            self.session_loaded = True
            
            self._display_data_summary()
            return True
            
        except Exception as e:
            print(f"[ERROR] 資料載入失敗: {e}")
            self.session_loaded = False
            return False
    
    def _extract_drivers_info(self):
        """提取車手資訊"""
        drivers_info = {}
        for _, driver in self.session.results.iterrows():
            drivers_info[driver['Abbreviation']] = {
                'name': driver['FullName'],
                'number': driver['DriverNumber'],
                'team': driver['TeamName'],
                'abbreviation': driver['Abbreviation']
            }
        return drivers_info
    
    def _synchronize_driver_data(self, openf1_drivers, openf1_team_mapping):
        """同步 FastF1 和 OpenF1 的車手車隊資料"""
        synchronized_data = {}
        
        print(f"\n[REFRESH] 同步 FastF1 與 OpenF1 車手資料...")
        print("=" * 80)
        
        # FastF1 車手資料
        fastf1_drivers = self.loaded_data.get('drivers_info', {})
        
        for abbreviation, fastf1_data in fastf1_drivers.items():
            synchronized_entry = {
                'abbreviation': abbreviation,
                'fastf1_data': fastf1_data,
                'openf1_data': {},
                'reconciled_data': {}
            }
            
            # 尋找對應的 OpenF1 資料
            openf1_match = None
            for driver_number, openf1_driver in openf1_drivers.items():
                if openf1_driver.get('name_acronym') == abbreviation:
                    openf1_match = openf1_driver
                    break
            
            if openf1_match:
                synchronized_entry['openf1_data'] = openf1_match
                
                # 協調資料 - 優先使用 FastF1，補充 OpenF1
                reconciled = {
                    'name': fastf1_data.get('name', openf1_match.get('full_name', '')),
                    'abbreviation': abbreviation,
                    'number': fastf1_data.get('number', openf1_match.get('driver_number', '')),
                    'team_fastf1': fastf1_data.get('team', ''),
                    'team_openf1': openf1_match.get('team_name', ''),
                    'team_reconciled': fastf1_data.get('team', openf1_match.get('team_name', '')),
                    'country_code': openf1_match.get('country_code', ''),
                    'headshot_url': openf1_match.get('headshot_url', ''),
                    'team_colour': openf1_match.get('team_colour', ''),
                    'data_source': 'FastF1+OpenF1'
                }
                
                # 檢查車隊名稱是否一致
                if fastf1_data.get('team') and openf1_match.get('team_name'):
                    if fastf1_data['team'] != openf1_match['team_name']:
                        reconciled['team_discrepancy'] = True
                        print(f"[WARNING]  車隊名稱不一致 - {abbreviation}: FastF1='{fastf1_data['team']}' vs OpenF1='{openf1_match['team_name']}'")
                    else:
                        reconciled['team_discrepancy'] = False
                
                print(f"[SUCCESS] 同步成功 - {abbreviation:4} | {reconciled['name'][:25]:25} | #{reconciled['number']:2} | {reconciled['team_reconciled']}")
                
            else:
                # 只有 FastF1 資料
                reconciled = {
                    'name': fastf1_data.get('name', ''),
                    'abbreviation': abbreviation,
                    'number': fastf1_data.get('number', ''),
                    'team_fastf1': fastf1_data.get('team', ''),
                    'team_openf1': '',
                    'team_reconciled': fastf1_data.get('team', ''),
                    'country_code': '',
                    'headshot_url': '',
                    'team_colour': '',
                    'data_source': 'FastF1 only',
                    'team_discrepancy': False
                }
                
                print(f"[WARNING]  僅 FastF1 - {abbreviation:4} | {reconciled['name'][:25]:25} | #{reconciled['number']:2} | {reconciled['team_reconciled']}")
            
            synchronized_entry['reconciled_data'] = reconciled
            synchronized_data[abbreviation] = synchronized_entry
        
        # 檢查是否有 OpenF1 獨有的車手資料
        for driver_number, openf1_driver in openf1_drivers.items():
            abbreviation = openf1_driver.get('name_acronym', '')
            if abbreviation and abbreviation not in synchronized_data:
                reconciled = {
                    'name': openf1_driver.get('full_name', ''),
                    'abbreviation': abbreviation,
                    'number': openf1_driver.get('driver_number', ''),
                    'team_fastf1': '',
                    'team_openf1': openf1_driver.get('team_name', ''),
                    'team_reconciled': openf1_driver.get('team_name', ''),
                    'country_code': openf1_driver.get('country_code', ''),
                    'headshot_url': openf1_driver.get('headshot_url', ''),
                    'team_colour': openf1_driver.get('team_colour', ''),
                    'data_source': 'OpenF1 only',
                    'team_discrepancy': False
                }
                
                synchronized_data[abbreviation] = {
                    'abbreviation': abbreviation,
                    'fastf1_data': {},
                    'openf1_data': openf1_driver,
                    'reconciled_data': reconciled
                }
                
                print(f"[WARNING]  僅 OpenF1 - {abbreviation:4} | {reconciled['name'][:25]:25} | #{reconciled['number']:2} | {reconciled['team_reconciled']}")
        
        print("=" * 80)
        print(f"[SUCCESS] 車手資料同步完成，共處理 {len(synchronized_data)} 位車手")
        
        # 顯示車隊對應摘要
        teams = set()
        for driver_data in synchronized_data.values():
            team = driver_data['reconciled_data'].get('team_reconciled', '')
            if team:
                teams.add(team)
        
        print(f"[INFO] 參賽車隊: {', '.join(sorted(teams))}")
        
        return synchronized_data
    
    def get_synchronized_driver_info(self, abbreviation=None):
        """獲取同步後的車手資訊
        
        Args:
            abbreviation: 車手縮寫，如果為 None 則返回所有車手
            
        Returns:
            dict: 同步後的車手資訊
        """
        synchronized_data = self.loaded_data.get('synchronized_driver_data', {})
        
        if abbreviation:
            return synchronized_data.get(abbreviation, {}).get('reconciled_data', {})
        else:
            return {abbr: data.get('reconciled_data', {}) for abbr, data in synchronized_data.items()}
    
    def get_enhanced_team_mapping(self):
        """獲取增強的車隊映射（包含額外資訊）
        
        Returns:
            dict: 增強的車隊映射
        """
        synchronized_data = self.loaded_data.get('synchronized_driver_data', {})
        enhanced_mapping = {}
        
        for abbr, data in synchronized_data.items():
            reconciled = data.get('reconciled_data', {})
            enhanced_mapping[abbr] = {
                'team': reconciled.get('team_reconciled', ''),
                'team_colour': reconciled.get('team_colour', ''),
                'country_code': reconciled.get('country_code', ''),
                'data_source': reconciled.get('data_source', ''),
                'has_discrepancy': reconciled.get('team_discrepancy', False)
            }
        
        return enhanced_mapping
    
    def _display_data_summary(self):
        """顯示載入資料的摘要"""
        metadata = self.loaded_data['metadata']
        drivers_count = len(self.loaded_data['drivers_info'])
        laps_count = len(self.loaded_data['laps']) if self.loaded_data['laps'] is not None else 0
        weather_records = len(self.loaded_data['weather_data']) if self.loaded_data['weather_data'] is not None else 0
        
        print(f"\n[INFO] 載入資料摘要:")
        print(f"   [FINISH] 賽事: {metadata['event_name']}")
        print(f"   [DATE] 日期: {metadata['date']}")
        print(f"   [CARS] 車手數量: {drivers_count}")
        print(f"   [LAPS] 圈次記錄: {laps_count}")
        print(f"   [WEATHER] 天氣記錄: {weather_records}")
        print(f"   [TRACK] 賽道: {metadata['location']}")
        
        # 顯示同步資料摘要
        synchronized_data = self.loaded_data.get('synchronized_driver_data', {})
        if synchronized_data:
            fastf1_only = sum(1 for data in synchronized_data.values() if data['reconciled_data']['data_source'] == 'FastF1 only')
            openf1_only = sum(1 for data in synchronized_data.values() if data['reconciled_data']['data_source'] == 'OpenF1 only')
            both_sources = sum(1 for data in synchronized_data.values() if data['reconciled_data']['data_source'] == 'FastF1+OpenF1')
            discrepancies = sum(1 for data in synchronized_data.values() if data['reconciled_data'].get('team_discrepancy', False))
            
            print(f"\n[SYNC] 車手資料同步狀態:")
            print(f"   [SUCCESS] FastF1+OpenF1: {both_sources}")
            print(f"   [WARNING]  僅 FastF1: {fastf1_only}")
            print(f"   [WARNING]  僅 OpenF1: {openf1_only}")
            if discrepancies > 0:
                print(f"   [ERROR] 車隊名稱不一致: {discrepancies}")
            
            openf1_session_key = metadata.get('openf1_session_key')
            if openf1_session_key:
                print(f"   [LINK] OpenF1 Session Key: {openf1_session_key}")
            else:
                print(f"   [ERROR] 未找到對應的 OpenF1 session")
    
    def get_loaded_data(self):
        """取得已載入的資料並進行驗證 - 關鍵方法！"""
        # 添加資料驗證
        self._validate_loaded_data()
        return self.loaded_data
    
    def _validate_loaded_data(self):
        """驗證載入的資料完整性"""
        try:
            print(f"\n[DEBUG] 資料驗證檢查:")
            print("-" * 50)
            
            if not self.loaded_data:
                print(f"[ERROR] 沒有載入的資料")
                return
            
            # 檢查基本資料
            session = self.loaded_data.get('session')
            if session:
                print(f"[SUCCESS] 比賽資料: {session.event['EventName']} - {session.name}")
                print(f"   比賽時間: {session.date}")
            else:
                print(f"[ERROR] 比賽基本資料: 無資料")
            
            # 檢查圈速資料
            lap_data = self.loaded_data.get('laps')
            if lap_data is not None and not lap_data.empty:
                print(f"[SUCCESS] 圈速資料: {len(lap_data)} 筆記錄")
                drivers_count = lap_data['Driver'].nunique() if 'Driver' in lap_data.columns else 0
                print(f"   涉及車手數: {drivers_count}")
                
                # 檢查關鍵欄位
                key_columns = ['LapTime', 'LapNumber', 'Compound', 'TyreLife']
                missing_columns = [col for col in key_columns if col not in lap_data.columns]
                if missing_columns:
                    print(f"   [WARNING]  缺少欄位: {', '.join(missing_columns)}")
                else:
                    print(f"   [SUCCESS] 關鍵欄位完整")
                    
                # 檢查資料品質
                valid_laptimes = lap_data['LapTime'].dropna() if 'LapTime' in lap_data.columns else pd.Series()
                if not valid_laptimes.empty:
                    print(f"   [SUCCESS] 有效圈速: {len(valid_laptimes)} 筆")
                
            else:
                print(f"[ERROR] 圈速資料: 無資料")
            
            # 檢查車手資訊
            drivers_info = self.loaded_data.get('drivers_info', {})
            if drivers_info:
                print(f"[SUCCESS] 車手資訊: {len(drivers_info)} 位車手")
            else:
                print(f"[ERROR] 車手資訊: 無資料")
            
            # 檢查遙測資料
            car_data = self.loaded_data.get('car_data', {})
            if car_data:
                print(f"[SUCCESS] 遙測資料: {len(car_data)} 位車手有資料")
            else:
                print(f"[ERROR] 遙測資料: 無資料")
            
            # 檢查天氣資料
            weather_data = self.loaded_data.get('weather_data')
            if weather_data is not None and not weather_data.empty:
                print(f"[SUCCESS] 天氣資料: {len(weather_data)} 筆記錄")
            else:
                print(f"[WARNING]  天氣資料: 無資料")
            
            # 檢查賽事控制訊息
            race_control = self.loaded_data.get('race_control_messages')
            if race_control is not None and not race_control.empty:
                print(f"[SUCCESS] 賽事控制訊息: {len(race_control)} 筆記錄")
            else:
                print(f"[WARNING]  賽事控制訊息: 無資料")
            
            print("-" * 50)
            
        except Exception as e:
            print(f"[ERROR] 資料驗證失敗: {e}")
    
    def list_cache_files(self):
        """列出快取檔案"""
        if not os.path.exists(self.cache_dir):
            return []
        
        cache_files = []
        for filename in os.listdir(self.cache_dir):
            if filename.startswith('f1_data_') and filename.endswith('.pkl'):
                file_path = os.path.join(self.cache_dir, filename)
                file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                cache_files.append({
                    'filename': filename,
                    'size_mb': f"{file_size:.1f}",
                    'path': file_path
                })
        return cache_files

# 為了向後兼容，提供別名
F1DataLoader = CompatibleF1DataLoader

def run_compatible_data_loader_test():
    """測試兼容數據載入器"""
    print("🧪 測試兼容數據載入器...")
    
    loader = CompatibleF1DataLoader()
    
    # 測試載入數據
    success = loader.load_race_data(2025, "Japan", "R")
    
    if success:
        print("[SUCCESS] 數據載入成功")
        
        # 測試 get_loaded_data 方法
        try:
            data = loader.get_loaded_data()
            print(f"[SUCCESS] get_loaded_data() 方法正常，返回 {len(data)} 個數據項")
            
            # 檢查關鍵數據
            if 'laps' in data:
                print(f"[SUCCESS] 圈速數據: {len(data['laps'])} 筆記錄")
            if 'results' in data:
                print(f"[SUCCESS] 結果數據: {len(data['results'])} 位車手")
                
        except Exception as e:
            print(f"[ERROR] get_loaded_data() 測試失敗: {e}")
    else:
        print("[ERROR] 數據載入失敗")

if __name__ == "__main__":
    run_compatible_data_loader_test()
