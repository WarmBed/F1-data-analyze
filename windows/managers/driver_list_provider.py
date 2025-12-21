# -*- coding: utf-8 -*-
"""
DriverListProvider - 從 f1t_gui_main.py 提取
"""

import sys
from core.logger import get_logger
import json

IS_EXE_MODE = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

logger = get_logger(__name__)


class DriverListProvider:
    """從 f1t_gui_main.py 提取的 get_drivers_for_year 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def get_drivers_for_year(self, year: int) -> list:
        """
        取得指定年份的車手列表（帶快取機制）
        
        此方法提供全域車手列表快取，在系統啟動時預載入當前年份，
        後續所有模組（工具欄、對話框等）統一調用此方法獲取車手列表。
        
        載入策略：
        1. 檢查快取 → 如果有則直接返回
        2. 從 team_colors JSON 讀取（F98 功能生成）
        3. 如果 JSON 不存在，通過 API 調用 F98 生成
        4. 快取結果供後續使用
        
        Args:
            year: 賽季年份（例如 2025）
            
        Returns:
            車手代碼列表（已排序）例如 ['ALB', 'ALO', 'VER', ...]
            如果載入失敗返回空列表
        """
        # 僅使用 API 作為車手列表來源（移除 JSON 與硬編碼後備）
        if not IS_EXE_MODE:
            logger.debug(f"[DRIVER_CACHE] DEBUG: get_drivers_for_year called, year={year}")
            logger.debug(f"[DRIVER_CACHE] DEBUG: Cache keys: {list(self.main_window._cached_drivers_by_year.keys())}")

        # 檢查快取
        if year in self.main_window._cached_drivers_by_year:
            cached_list = self.main_window._cached_drivers_by_year[year]
            if not IS_EXE_MODE:
                logger.debug(f"[DRIVER_CACHE] SUCCESS: Returning cached drivers for {year} ({len(cached_list)} drivers)")
            return cached_list

        if not IS_EXE_MODE:
            logger.debug(f"[DRIVER_CACHE] DEBUG: Cache miss, loading {year} drivers from API...")

        drivers = []
        try:
            import requests
            from core.api_base_url import resolve_api_base_url

            api_base = resolve_api_base_url()
            api_url = f"{api_base}/api/v2/analysis/execute"  # 使用 v2 API 端點
            # 使用 Function 97 (Championship Standings) 而不是 Function 98 (Team Colour Export)
            # 因為 Function 97 會返回車手積分榜，包含所有車手列表
            query_params = {"function_id": 97, "year": int(year)}

            if not IS_EXE_MODE:
                logger.debug(f"[DRIVER_CACHE] DEBUG: Sending API request to {api_url} with params={query_params}")
            # 使用 params (URL 查詢參數) 而不是 json (請求 body)，與 Home 畫面的方式一致
            response = requests.post(api_url, params=query_params, timeout=60, headers={"Accept": "application/json"})
            if not IS_EXE_MODE:
                logger.debug(f"[DRIVER_CACHE] DEBUG: API status code: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                if not IS_EXE_MODE:
                    logger.debug(f"[DRIVER_CACHE] DEBUG: API response keys: {list(result.keys())}")
                
                if result.get('success') and 'data' in result:
                    data = result['data']
                    if not IS_EXE_MODE:
                        logger.debug(f"[DRIVER_CACHE] DEBUG: data keys: {list(data.keys())}")
                    
                    # Function 97 返回的結構: {"data": {"drivers": [{"driver": {"code": "PIA"}}, ...]}}
                    if 'data' in data and isinstance(data['data'], dict):
                        inner_data = data['data']
                        if 'drivers' in inner_data and isinstance(inner_data['drivers'], list):
                            # 從積分榜提取車手代碼
                            drivers = []
                            for entry in inner_data['drivers']:
                                # 結構: {"driver": {"code": "PIA", ...}, ...}
                                driver_info = entry.get('driver', {})
                                driver_code = driver_info.get('code', '')
                                if driver_code:
                                    drivers.append(driver_code)
                            
                            if not IS_EXE_MODE:
                                logger.debug(f"[DRIVER_CACHE] DEBUG: Extracted {len(drivers)} drivers from API")
                            
                            if drivers:
                                if not IS_EXE_MODE:
                                    logger.debug(f"[DRIVER_CACHE] SUCCESS: Loaded {len(drivers)} drivers from API")
                                    logger.debug(f"[DRIVER_CACHE] DEBUG: Drivers list: {drivers}")
                                
                                # 緩存車手列表
                                self.main_window._cached_drivers_by_year[year] = drivers
                                if not IS_EXE_MODE:
                                    logger.debug(f"[DRIVER_CACHE] DEBUG: Cached content length: {len(self.main_window._cached_drivers_by_year.get(year, []))}")
                                return drivers
                            else:
                                if not IS_EXE_MODE:
                                    logger.debug(f"[DRIVER_CACHE] WARNING: Extracted empty drivers list")
                        else:
                            if not IS_EXE_MODE:
                                logger.debug(f"[DRIVER_CACHE] WARNING: Missing 'drivers' key in inner data")
                                if isinstance(inner_data, dict):
                                    logger.debug(f"[DRIVER_CACHE] DEBUG: inner_data keys: {list(inner_data.keys())}")
                    else:
                        if not IS_EXE_MODE:
                            logger.debug(f"[DRIVER_CACHE] WARNING: Missing nested 'data' key or wrong format")
                            logger.debug(f"[DRIVER_CACHE] DEBUG: data structure keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")
                else:
                    if not IS_EXE_MODE:
                        logger.debug(f"[DRIVER_CACHE] WARNING: API response success=False or invalid format")
                        logger.debug(f"[DRIVER_CACHE] DEBUG: result structure: {result}")
            else:
                if not IS_EXE_MODE:
                    logger.debug(f"[DRIVER_CACHE] ERROR: API request failed with HTTP {response.status_code}")
                    try:
                        error_detail = response.text[:200]  # 只顯示前 200 字元
                        logger.debug(f"[DRIVER_CACHE] ERROR: Response detail: {error_detail}")
                    except:
                        pass

        except Exception as e:
            if not IS_EXE_MODE:
                logger.debug(f"[DRIVER_CACHE] ERROR: API call exception: {e}")

        # 無論 API 成功與否，快取結果（若沒有資料則快取空列表以避免重複請求）
        self.main_window._cached_drivers_by_year[year] = drivers
        if not IS_EXE_MODE:
            logger.debug(f"[DRIVER_CACHE] DEBUG: Cached keys after update: {list(self.main_window._cached_drivers_by_year.keys())}")
            logger.debug(f"[DRIVER_CACHE] DEBUG: Cached content length: {len(drivers)}")

        return drivers
