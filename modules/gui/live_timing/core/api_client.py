"""
Live Timing API 客戶端
======================

提供統一的 API 調用接口，供 Live Timing 模組獲取配置和分析數據。

Author: F1T Team
Date: 2025-12-05
"""

import json
from core import local_requests as requests
from typing import Dict, Any, Optional, Callable
from pathlib import Path
from functools import lru_cache
from threading import Lock

from core.api_base_url import resolve_api_base_url, PUBLIC_API_BASE_URL
from core.logger import get_logger


class LiveTimingAPIClient:
    """
    Live Timing API 客戶端
    
    提供同步 API 調用，用於獲取：
    - 配置數據庫 (tire_degradation, fuel_coefficients, track_features)
    - 賽道分析數據 (Function 2)
    - 賽季日曆 (Function 99)
    
    特性：
    - 自動使用公開 API 網域
    - 內建請求超時
    - 本地緩存支持
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        """單例模式"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._api_base_url = resolve_api_base_url()
        self._session = requests.Session()
        self._timeout = 30  # 秒
        self._cache: Dict[str, Any] = {}
        self._initialized = True
        
        self._logger = get_logger("live_timing.api_client", component="gui")
        self._logger.info("[LiveTimingAPIClient] 初始化完成，API 網域: %s", self._api_base_url)
    
    @classmethod
    def instance(cls) -> 'LiveTimingAPIClient':
        """獲取單例實例"""
        return cls()
    
    # ===========================================
    # 配置數據 API
    # ===========================================
    def get_tire_degradation(self, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        獲取輪胎衰退數據庫
        
        Args:
            use_cache: 是否使用緩存
            
        Returns:
            數據字典，失敗返回 None
        """
        return self._fetch_config("tire-degradation", use_cache)
    
    def get_fuel_coefficients(self, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        獲取燃油係數數據庫
        """
        return self._fetch_config("fuel-coefficients", use_cache)
    
    def get_track_features(self, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        獲取賽道特性數據庫
        """
        return self._fetch_config("track-features", use_cache)
    
    def get_pit_loss(self, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        獲取進站時間損失數據庫
        """
        return self._fetch_config("pit-loss", use_cache)
    
    def get_all_configs(self, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        獲取所有配置數據庫
        """
        return self._fetch_config("all", use_cache)
    
    def _fetch_config(self, config_type: str, use_cache: bool) -> Optional[Dict[str, Any]]:
        """
        獲取配置數據
        """
        cache_key = f"config_{config_type}"
        
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]
        
        url = f"{self._api_base_url}/api/v2/config/{config_type}"
        
        try:
            response = self._session.get(url, timeout=self._timeout)
            response.raise_for_status()
            
            data = response.json()
            
            # 即使 success=false，只要有 data 就使用
            # (例如部分配置載入失敗時，仍可使用其他成功的配置)
            result = data.get("data", {})
            if result:
                if not data.get("success"):
                    errors = data.get("errors", [])
                    if errors:
                        self._logger.warning("[LiveTimingAPIClient] 部分配置載入失敗: %s", errors)
                self._cache[cache_key] = result
                return result
            else:
                self._logger.error("[LiveTimingAPIClient] 配置獲取失敗: %s", data.get('message'))
                return None
                
        except requests.exceptions.Timeout:
            self._logger.warning("[LiveTimingAPIClient] 請求超時: %s", url)
            return None
        except requests.exceptions.RequestException as e:
            self._logger.error("[LiveTimingAPIClient] 請求失敗: %s", e)
            return None
        except json.JSONDecodeError as e:
            self._logger.error("[LiveTimingAPIClient] JSON 解析失敗: %s", e)
            return None
    
    # ===========================================
    # 分析數據 API
    # ===========================================
    def get_track_analysis(
        self, 
        year: int, 
        race: str, 
        session: str = "R",
        force_refresh: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        獲取賽道分析數據 (Function 2)
        
        Args:
            year: 賽季年份
            race: 賽事名稱
            session: 會話類型 (R/Q/FP1/FP2/FP3)
            force_refresh: 是否強制刷新
            
        Returns:
            賽道分析數據，包含 position_records, track_bounds, official_corners
        """
        cache_key = f"track_{year}_{race}_{session}"
        
        if not force_refresh and cache_key in self._cache:
            return self._cache[cache_key]
        
        url = f"{self._api_base_url}/api/v2/analysis/execute"
        params = {
            "function_id": "2",
            "year": year,
            "race": race,
            "session": session,
            "force_refresh": force_refresh
        }
        
        try:
            response = self._session.post(url, params=params, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            if data.get("success"):
                # 注意：API 回應結構是嵌套的 data.data
                outer_data = data.get("data", {})
                result = outer_data.get("data", outer_data)  # 兼容兩種結構
                self._cache[cache_key] = result
                return result
            else:
                self._logger.error("[LiveTimingAPIClient] 賽道分析失敗: %s", data.get('message'))
                return None
                
        except requests.exceptions.Timeout:
            self._logger.warning("[LiveTimingAPIClient] 請求超時: %s", url)
            return None
        except requests.exceptions.RequestException as e:
            self._logger.error("[LiveTimingAPIClient] 請求失敗: %s", e)
            return None
        except json.JSONDecodeError as e:
            self._logger.error("[LiveTimingAPIClient] JSON 解析失敗: %s", e)
            return None
    
    def get_season_calendar(
        self, 
        year: Optional[int] = None,
        force_refresh: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        獲取賽季日曆 (Function 99)
        
        Args:
            year: 賽季年份 (可選，不指定則返回所有年份)
            force_refresh: 是否強制刷新
            
        Returns:
            賽季日曆數據
        """
        cache_key = f"calendar_{year or 'all'}"
        
        if not force_refresh and cache_key in self._cache:
            return self._cache[cache_key]
        
        url = f"{self._api_base_url}/api/v2/analysis/execute"
        params = {
            "function_id": "99",
            "force_refresh": force_refresh
        }
        if year:
            params["year"] = year
        
        try:
            response = self._session.post(url, params=params, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            if data.get("success"):
                # 注意：API 回應結構是嵌套的 data.data
                outer_data = data.get("data", {})
                result = outer_data.get("data", outer_data)  # 兼容兩種結構
                self._cache[cache_key] = result
                return result
            else:
                self._logger.error("[LiveTimingAPIClient] 賽季日曆獲取失敗: %s", data.get('message'))
                return None
                
        except requests.exceptions.Timeout:
            self._logger.warning("[LiveTimingAPIClient] 請求超時: %s", url)
            return None
        except requests.exceptions.RequestException as e:
            self._logger.error("[LiveTimingAPIClient] 請求失敗: %s", e)
            return None
        except json.JSONDecodeError as e:
            self._logger.error("[LiveTimingAPIClient] JSON 解析失敗: %s", e)
            return None
    
    # ===========================================
    # 工具方法
    # ===========================================
    def clear_cache(self):
        """清除所有緩存"""
        self._cache.clear()
        self._logger.info("[LiveTimingAPIClient] 緩存已清除")
    
    def get_api_base_url(self) -> str:
        """獲取當前 API 基礎網址"""
        return self._api_base_url
    
    def health_check(self) -> bool:
        """
        檢查 API 服務健康狀態
        
        Returns:
            True 如果 API 可用，否則 False
        """
        url = f"{self._api_base_url}/api/v2/system/health"
        
        try:
            response = self._session.get(url, timeout=10)
            return response.status_code == 200
        except Exception:
            return False


# 便捷函數
def get_api_client() -> LiveTimingAPIClient:
    """獲取 API 客戶端單例"""
    return LiveTimingAPIClient.instance()


__all__ = ['LiveTimingAPIClient', 'get_api_client']
