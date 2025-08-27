#!/usr/bin/env python3
"""
F1 Analysis Base Module
基礎模組 - 共享的類和工具函數
"""

import os
import sys
import re
import fastf1
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.patches as patches
import matplotlib.font_manager
from datetime import datetime
import json
import pickle
import requests


def setup_matplotlib_chinese(dark_theme=False):
    """設定matplotlib的中文字體支援和主題 - 全域函數"""
    import matplotlib.pyplot as plt
    
    if dark_theme:
        # 設定深色主題
        plt.style.use('dark_background')
        plt.rcParams['figure.facecolor'] = '#1f1f1f'
        plt.rcParams['axes.facecolor'] = '#2d2d2d'
        plt.rcParams['axes.edgecolor'] = '#8a8a8a'
        plt.rcParams['axes.labelcolor'] = 'white'
        plt.rcParams['text.color'] = 'white'
        plt.rcParams['xtick.color'] = 'white'
        plt.rcParams['ytick.color'] = 'white'
        plt.rcParams['grid.color'] = '#4a4a4a'
    else:
        # 重置為預設的白色主題
        plt.style.use('default')
        plt.rcParams['figure.facecolor'] = 'white'
        plt.rcParams['axes.facecolor'] = 'white'
        plt.rcParams['axes.edgecolor'] = 'black'
        plt.rcParams['axes.labelcolor'] = 'black'
        plt.rcParams['text.color'] = 'black'
        plt.rcParams['xtick.color'] = 'black'
        plt.rcParams['ytick.color'] = 'black'
        plt.rcParams['grid.color'] = '#b0b0b0'
    
    # 設定中文字體 (兩種主題都需要)
    plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'DejaVu Sans', 'SimHei', 'Arial']
    plt.rcParams['axes.unicode_minus'] = False


def initialize_data_loader(existing_data_loader=None):
    """通用數據載入器初始化函數"""
    if existing_data_loader is not None:
        print("[SUCCESS] 使用現有的數據載入器")
        return existing_data_loader
        
    print("🔄 初始化數據載入器...")
    try:
        # 優先嘗試導入現有的兼容數據載入器
        try:
            from modules.compatible_data_loader import CompatibleDataLoader
            data_loader = CompatibleDataLoader()
            print("[SUCCESS] 使用兼容數據載入器初始化成功")
            return data_loader
        except ImportError:
            pass
        
        # 嘗試從主程式模組載入器
        try:
            current_dir = os.path.dirname(os.path.dirname(__file__))
            if current_dir not in sys.path:
                sys.path.append(current_dir)
            from f1_analysis_cli_new import F1DataLoader
            data_loader = F1DataLoader()
            print("[SUCCESS] 主程式數據載入器初始化成功")
            return data_loader
        except ImportError:
            pass
            
        # 創建基本的 FastF1 數據載入器
        class SimpleDataLoader:
            """簡單的 FastF1 數據載入器"""
            def __init__(self):
                self.session = None
                
            def load_session_data(self, year, race, session_type='R'):
                """載入會話數據"""
                import fastf1
                try:
                    self.session = fastf1.get_session(year, race, session_type)
                    self.session.load()
                    return self.session
                except Exception as e:
                    print(f"⚠️ 載入會話數據失敗: {e}")
                    return None
                    
            def get_laps_data(self, session=None):
                """獲取圈數數據"""
                if session is None:
                    session = self.session
                if session is not None:
                    return session.laps
                return None
                
            def get_telemetry_data(self, lap):
                """獲取遙測數據"""
                try:
                    return lap.get_telemetry()
                except Exception as e:
                    print(f"⚠️ 獲取遙測數據失敗: {e}")
                    return None
        
        data_loader = SimpleDataLoader()
        print("[SUCCESS] 基本數據載入器初始化成功")
        return data_loader
        
    except Exception as e:
        print(f"[ERROR] 初始化數據載入器時發生錯誤: {e}")
        return None
import traceback
import time
from pathlib import Path
from prettytable import PrettyTable

# 啟用 fastf1 快取
fastf1.Cache.enable_cache('cache')

# 設置請求超時時間（避免卡住）
# 注意：fastf1.api 在未來版本可能會被移除或更改
try:
    import fastf1.api
    if hasattr(fastf1.api, 'Cache') and hasattr(fastf1.api.Cache, 'requests_timeout'):
        fastf1.api.Cache.requests_timeout = 60  # 60秒超時
except (ImportError, AttributeError):
    # 如果API結構改變，使用替代方法
    pass

class F1OpenDataAnalyzer:
    """F1 OpenF1 API 數據分析器"""
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
    
    def get_enhanced_pit_stops(self, session_key: int) -> list:
        """獲取增強進站數據（包含車手信息）"""
        pit_stops = self.get_pit_stops(session_key)
        drivers = self.get_drivers(session_key)
        sessions = self.get_sessions()
        
        session_info = next((s for s in sessions if s.get('session_key') == session_key), {})
        
        enhanced_stops = []
        for stop in pit_stops:
            driver_number = stop.get('driver_number')
            driver_info = drivers.get(driver_number, {})
            
            enhanced_stop = {
                **stop,
                'session_info': {
                    'location': session_info.get('location', 'Unknown'),
                    'country_name': session_info.get('country_name', 'Unknown'),
                    'session_name': session_info.get('session_name', 'Unknown')
                },
                'driver_info': {
                    'full_name': driver_info.get('full_name', f'Driver #{driver_number}'),
                    'name_acronym': driver_info.get('name_acronym', 'UNK'),
                    'team_name': driver_info.get('team_name', 'Unknown Team')
                }
            }
            enhanced_stops.append(enhanced_stop)
        
        return enhanced_stops


class F1AnalysisBase:
    """F1分析基礎類 - 提供共通的功能和配置"""
    
    def __init__(self):
        self.current_dir = Path(__file__).parent.parent
        self.cache_dir = self.current_dir / "cache"
        self.cache_dir.mkdir(exist_ok=True)
    
    def _setup_chinese_font(self, dark_theme=False):
        """設定matplotlib的中文字體支援和主題"""
        import matplotlib.pyplot as plt
        
        if dark_theme:
            # 設定深色主題
            plt.style.use('dark_background')
            plt.rcParams['figure.facecolor'] = '#1f1f1f'
            plt.rcParams['axes.facecolor'] = '#2d2d2d'
            plt.rcParams['axes.edgecolor'] = '#8a8a8a'
            plt.rcParams['axes.labelcolor'] = 'white'
            plt.rcParams['text.color'] = 'white'
            plt.rcParams['xtick.color'] = 'white'
            plt.rcParams['ytick.color'] = 'white'
            plt.rcParams['grid.color'] = '#4a4a4a'
        else:
            # 重置為預設的白色主題
            plt.style.use('default')
            plt.rcParams['figure.facecolor'] = 'white'
            plt.rcParams['axes.facecolor'] = 'white'
            plt.rcParams['axes.edgecolor'] = 'black'
            plt.rcParams['axes.labelcolor'] = 'black'
            plt.rcParams['text.color'] = 'black'
            plt.rcParams['xtick.color'] = 'black'
            plt.rcParams['ytick.color'] = 'black'
            plt.rcParams['grid.color'] = '#b0b0b0'
        
        # 設定中文字體 (兩種主題都需要)
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'DejaVu Sans', 'SimHei', 'Arial']
        plt.rcParams['axes.unicode_minus'] = False
    
    def create_output_filename(self, base_name, extension="png"):
        """創建帶時間戳的輸出文件名"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{base_name}_{timestamp}.{extension}"
    
    def safe_makedirs(self, path):
        """安全創建目錄"""
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception as e:
            print(f"[ERROR] 創建目錄失敗 {path}: {e}")
            return False
