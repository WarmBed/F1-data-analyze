#!/usr/bin/env python3
"""
TelemetryDataLoader - F1T 遙測數據載入器基類
======================================================

這個模組提供了所有遙測分析模組共用的數據載入邏輯，
整合了原本分散在各個 *_analysis_data_loader.py 中的重複代碼。

支援的遙測類型：
- speed (速度分析)
- rpm (轉速分析) 
- gear (檔位分析)
- throttle (油門分析)
- brake (煞車分析)
- acceleration (加速度分析)
- distancediff (距離差異分析)
- speeddiff (速度差異分析)

設計原則：
1. 統一的載入邏輯，消除代碼重複
2. 保持向後兼容性，不破壞現有API
3. 模組化設計，支援新增遙測類型
4. 統一的錯誤處理和監控機制

Author: F1T Team
Date: 2025-09-09
Version: 1.0.0
"""

import sys
import os
import json
import glob
import pickle
import time
from datetime import datetime
import threading
import requests
import fastf1
import pandas as pd
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QThread
from core.api_base_url import resolve_api_base_url
from core.gui_i18n import tr
from core.api_runtime_state import is_api_available


class TelemetryApiWorker(QThread):
    """Background worker responsible for fetching telemetry comparison data via REST API."""

    progress = pyqtSignal(int)
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)

    def __init__(self, base_url: str, params: Dict[str, Any], timeout: float = 75.0,
                 request_token: Optional[int] = None, parent=None):
        super().__init__(parent)
        self.base_url = (base_url or "https://api.f1telemetrystationpro.org").rstrip('/')
        self.params = dict(params)
        self.timeout = timeout
        self.request_token = request_token

    def run(self) -> None:
        try:
            self.progress.emit(15)
            endpoint = f"{self.base_url}/api/v2/analysis/execute"
            query_params: Dict[str, Any] = {
                "function_id": 13,
                "year": int(self.params.get("year")),
                "race": self.params.get("race"),
                "session": self.params.get("session"),
                "driver1": self.params.get("driver1"),
                "driver2": self.params.get("driver2"),
                "lap1": self.params.get("lap1"),
                "lap2": self.params.get("lap2"),
            }

            if self.params.get("force_refresh"):
                query_params["force_refresh"] = True

            start_ts = time.perf_counter()
            response = requests.post(
                endpoint,
                params=query_params,
                timeout=self.timeout,
                headers={"Accept": "application/json"}
            )
            self.progress.emit(70)
            response.raise_for_status()

            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("API response must be a JSON object")
            if not payload.get("success", False):
                raise RuntimeError(payload.get("message", "API returned success=False"))

            data = payload.get("data")
            if not isinstance(data, dict):
                raise ValueError("API response missing 'data' object")

            latency_ms = (time.perf_counter() - start_ts) * 1000.0
            meta = {
                "source": payload.get("source", "api"),
                "execution_time": payload.get("execution_time"),
                "request_id": payload.get("request_id"),
                "timestamp": payload.get("timestamp"),
                "latency_ms": round(latency_ms, 2),
                "base_url": self.base_url,
                "function_id": 13,
            }

            self.progress.emit(90)
            self.success.emit({
                "data": data,
                "payload": payload,
                "meta": meta,
                "request_token": self.request_token
            })
        except Exception as exc:
            self.failure.emit(str(exc))
        finally:
            self.progress.emit(100)


class TelemetryDataLoader(QObject):
    """
    遙測數據載入器基類
    
    所有遙測分析模組的共用載入器，提供統一的數據載入、
    檔案搜尋、CLI生成和監控機制。
    """
    
    # 標準信號定義 (所有遙測模組共用)
    data_loaded = pyqtSignal(dict)      # 數據載入完成
    load_progress = pyqtSignal(int)     # 載入進度 (0-100)
    load_error = pyqtSignal(str)        # 載入錯誤
    status_changed = pyqtSignal(str)    # 狀態變更
    
    # 支援的遙測類型映射
    TELEMETRY_TYPES = {
        'speed': {
            'display_name': tr('speed_analysis', '速度分析'),
            'data_field': 'Speed',
            'unit': 'km/h',
            'debug_prefix': 'SPEED'
        },
        'rpm': {
            'display_name': tr('rpm_analysis', 'RPM分析'), 
            'data_field': 'RPM',
            'unit': 'rpm',
            'debug_prefix': 'RPM'
        },
        'gear': {
            'display_name': tr('gear_analysis', '檔位分析'),
            'data_field': 'nGear', 
            'unit': 'gear',
            'debug_prefix': 'GEAR'
        },
        'throttle': {
            'display_name': tr('throttle_analysis', '油門分析'),
            'data_field': 'Throttle',
            'unit': '%',
            'debug_prefix': 'THROTTLE'
        },
        'brake': {
            'display_name': tr('brake_analysis', '煞車分析'),
            'data_field': 'Brake',
            'unit': '%', 
            'debug_prefix': 'BRAKE'
        },
        'acceleration': {
            'display_name': tr('acceleration_analysis', '加速度分析'),
            'data_field': 'Acceleration',
            'unit': 'm/s²',
            'debug_prefix': 'ACCEL'
        },
        'distancediff': {
            'display_name': tr('distancediff_analysis', '距離差異分析'),
            'data_field': 'distance_difference',
            'unit': 'm',
            'debug_prefix': 'DISTDIFF'
        },
        'speeddiff': {
            'display_name': tr('speeddiff_analysis', '速度差異分析'), 
            'data_field': 'speed_difference',
            'unit': 'km/h',
            'debug_prefix': 'SPEEDDIFF'
        },
        'rain': {
            'display_name': tr('rain_analysis', '降雨分析'),
            'data_field': 'rain_intensity',
            'unit': 'mm/h',
            'debug_prefix': 'RAIN'
        }
    }
    
    def __init__(self, telemetry_type: str, parent=None):
        """
        初始化遙測數據載入器
        
        Args:
            telemetry_type: 遙測類型 ('speed', 'rpm', 'gear', 等)
            parent: 父級 QObject
        """
        super().__init__(parent)
        
        # 驗證遙測類型
        if telemetry_type not in self.TELEMETRY_TYPES:
            raise ValueError(f"不支援的遙測類型: {telemetry_type}")
            
        self.telemetry_type = telemetry_type
        self.config = self.TELEMETRY_TYPES[telemetry_type]
        
        # 狀態變數
        self._base_path = "json"
        self._is_loading = False
        self._current_data = None
        self.current_session = None
        self._generation_params = None
        self._active_request_token = 0
        self._pending_params: Dict[str, Any] = {}
        self._api_worker: Optional[TelemetryApiWorker] = None
        self._last_data_source: str = "unknown"
        self._last_api_meta: Dict[str, Any] = {}
        
        # 監控定時器 - 設置 parent 防止被垃圾回收
        self._generation_timer = QTimer(self)
        self._generation_timer.timeout.connect(self._check_generation_progress)
        
        self._generation_timeout_timer = QTimer(self)
        self._generation_timeout_timer.timeout.connect(self._on_generation_timeout)
        
        self._debug(f"初始化 {self.config['display_name']} 載入器")
        self._api_base_url = self._determine_api_base_url()
        self._api_timeout = 75.0
        self._allow_local_fallback, self._fallback_policy_reason = self._resolve_local_fallback_policy()
        fallback_state = "啟用" if self._allow_local_fallback else "停用"
        self._debug(f"API 基底網址: {self._api_base_url}")
        self._debug(f"本地 JSON 後備已{fallback_state} (策略: {self._fallback_policy_reason})")
    
    def _debug(self, message: str):
        """統一的除錯輸出"""
        prefix = self.config['debug_prefix']
        print(f"[{prefix} DEBUG] {message}")
    
    def _error(self, message: str):
        """統一的錯誤輸出"""
        prefix = self.config['debug_prefix']
        print(f"[ERROR] [{prefix}] {message}")

    def _normalize_driver_code(self, raw_value: Optional[str], fallback: Optional[str] = None) -> Optional[str]:
        """正規化車手代碼輸入"""
        if raw_value is None:
            return fallback
        text = str(raw_value).strip()
        if not text:
            return fallback
        lowered = text.lower()
        if lowered in {"none", "null", "nan", "undefined", "select", "n/a", "na"}:
            return fallback
        return text.upper()

    def _build_request_signature(self, params: Dict[str, Any]) -> Tuple[Any, ...]:
        """建立請求簽章，用於比對參數是否一致"""
        return (
            params.get('year'),
            params.get('race'),
            params.get('session'),
            params.get('driver1'),
            params.get('driver2'),
            params.get('driver2_effective'),
            params.get('lap1'),
            params.get('lap2'),
            params.get('single_driver_mode'),
            params.get('is_fastest_lap')
        )

    def _sessions_match(self, active_session: Optional[Dict[str, Any]],
                        incoming_session: Dict[str, Any]) -> bool:
        """檢查即將載入的參數是否與目前正在處理的相同"""
        if not active_session:
            return False
        active_signature = active_session.get('signature')
        incoming_signature = incoming_session.get('signature')
        if active_signature and incoming_signature:
            return active_signature == incoming_signature

        keys_to_compare = [
            'year', 'race', 'session', 'driver1', 'driver2',
            'driver2_effective', 'lap1', 'lap2',
            'single_driver_mode', 'is_fastest_lap'
        ]
        return all(active_session.get(key) == incoming_session.get(key) for key in keys_to_compare)

    def _next_request_token(self) -> int:
        """取得下一個請求標識值"""
        self._active_request_token += 1
        return self._active_request_token
    
    # ========== 公開API方法 ==========
    
    def load_telemetry_data(self, year: int, race: str, session: str,
                           driver1: str, driver2: str = None,
                           lap1: int = 1, lap2: int = None,
                           is_fastest_lap: bool = False) -> bool:
        """
        載入遙測分析數據 - 通用載入方法
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 會話類型 (R/Q/S/FP1/FP2/FP3)
            driver1: 車手1代碼
            driver2: 車手2代碼 (可選，None表示單車手分析)
            lap1: 車手1圈數
            lap2: 車手2圈數 (可選)
            is_fastest_lap: 是否為最快圈分析
            
        Returns:
            bool: 載入是否成功啟動
        """
        try:
            if lap2 is None:
                lap2 = lap1

            driver1_normalized = self._normalize_driver_code(driver1)
            driver2_normalized = self._normalize_driver_code(driver2)

            if not driver1_normalized:
                self._error("缺少主要車手代碼，無法載入遙測數據")
                self.load_error.emit("缺少 driver1")
                return False

            single_driver_mode = (driver2_normalized is None) or (driver2_normalized == driver1_normalized)
            effective_driver2 = driver2_normalized if driver2_normalized else driver1_normalized

            driver1 = driver1_normalized
            driver2 = None if single_driver_mode else driver2_normalized

            incoming_session = {
                'year': year,
                'race': race,
                'session': session,
                'driver1': driver1,
                'driver2': driver2,
                'driver2_effective': effective_driver2,
                'lap1': lap1,
                'lap2': lap2,
                'is_fastest_lap': is_fastest_lap,
                'force_refresh': False,
                'single_driver_mode': single_driver_mode
            }
            incoming_session['signature'] = self._build_request_signature(incoming_session)

            if self._is_loading:
                if self._sessions_match(self.current_session, incoming_session):
                    self._debug("已在載入中且參數相同，忽略重複請求")
                    return False
                self._debug("偵測到新的請求參數，準備重置當前載入流程")
                self._stop_generation_monitoring()
                self._cleanup_api_worker()

            request_token = self._next_request_token()
            incoming_session['request_token'] = request_token
            incoming_session['request_started_at'] = time.time()

            self.current_session = incoming_session
            self._pending_params = {
                'year': year,
                'race': race,
                'session': session,
                'driver1': driver1,
                'driver2': driver2,
                'driver2_effective': effective_driver2,
                'lap1': lap1,
                'lap2': lap2,
                'single_driver_mode': single_driver_mode
            }

            self._is_loading = True
            self.load_progress.emit(5)
            self.status_changed.emit("正在透過 API 載入遙測比較資料...")

            self._debug("========== 遙測數據載入 ==========")
            self._debug(f"類型: {self.config['display_name']}")
            comparison_target = driver2 if driver2 else effective_driver2
            self._debug(f"參數: {year} {race} {session} {driver1} vs {comparison_target} L{lap1}/L{lap2}")
            self._debug(f"分析模式: {'單車手' if single_driver_mode else '雙車手對比'}")
            if single_driver_mode:
                self._debug(f"API 將使用 {effective_driver2} 作為第二車手參數")
            self._debug(f"請求標識 (token): {request_token}")

            self._start_api_request(request_token)
            return True

        except Exception as e:
            self._error(f"載入失敗: {str(e)}")
            self.load_error.emit(f"載入失敗: {str(e)}")
            self._is_loading = False
            return False
    
    def get_current_data(self) -> Optional[Dict[str, Any]]:
        """獲取當前載入的數據"""
        return self._current_data
    
    def is_loading(self) -> bool:
        """檢查是否正在載入"""
        return self._is_loading
    
    def get_telemetry_type(self) -> str:
        """獲取遙測類型"""
        return self.telemetry_type
    
    def get_display_name(self) -> str:
        """獲取顯示名稱"""
        return self.config['display_name']
    
    # ========== 檔案搜尋邏輯 ==========
    
    def _find_telemetry_data_file(self, year: int, race: str, session: str,
                                 driver1: str, driver2: str = None,
                                 lap1: int = 1, lap2: int = 1) -> Optional[str]:
        """搜尋遙測分析數據檔案 - 統一搜尋邏輯"""
        try:
            self._debug("========== 搜尋遙測分析檔案 ==========")
            self._debug(f"🔍 搜尋條件:")
            self._debug(f"   📅 年份: {year} (type: {type(year).__name__})")
            self._debug(f"   🏁 賽事: {race} (type: {type(race).__name__})")
            self._debug(f"   🏁 賽段: {session} (type: {type(session).__name__})")
            self._debug(f"   🏎️ 車手1: {driver1} (第{lap1}圈)")
            self._debug(f"   🏎️ 車手2: {driver2} (第{lap2}圈)")
            self._debug(f"   🔑 race 參數 repr: {repr(race)}")
            self._debug(f"   🔑 race 參數 bytes: {race.encode('utf-8') if isinstance(race, str) else 'N/A'}")
            
            # 搜尋目錄
            search_dirs = ["json", "json_exports", "cache"]
            self._debug(f"📂 搜尋目錄: {search_dirs}")
            
            # 構建檔案名稱搜尋模式
            filename_patterns = self._build_filename_patterns(year, race, session, driver1, driver2, lap1, lap2)
            
            # 精確搜尋
            self._debug("🔍 開始精確搜尋...")
            found_file = None
            
            for search_dir in search_dirs:
                self._debug(f"📂 搜尋目錄: {search_dir}")
                
                for i, filename_pattern in enumerate(filename_patterns, 1):
                    search_pattern = os.path.join(search_dir, filename_pattern)
                    self._debug(f"   🔍 模式 {i}: {search_pattern}")
                    matches = glob.glob(search_pattern)
                    
                    if matches:
                        # 精確匹配模式：直接選擇找到的檔案（應該只有一個）
                        found_file = matches[0] if len(matches) == 1 else max(matches, key=os.path.getmtime)
                        self._debug(f"✅ 找到檔案: {os.path.basename(found_file)}")
                        
                        if len(matches) > 1:
                            self._debug(f"⚠️  警告: 精確模式匹配到多個檔案 ({len(matches)} 個)，選擇最新的")
                            self._debug("📋 所有匹配檔案:")
                            for match in matches:
                                marker = "👉" if match == found_file else "  "
                                self._debug(f"     {marker} {os.path.basename(match)}")
                        break
                    else:
                        self._debug(f"   ❌ 模式 {i} 無匹配")
                
                # 如果找到檔案就跳出目錄循環
                if found_file:
                    break
                
                self._debug(f"❌ 目錄 {search_dir} 無匹配檔案")
            
            if found_file:
                self._debug(f"✅ 搜尋成功: {found_file}")
                return found_file
            
            # 精確搜尋失敗，直接生成新檔案
            self._debug("❌ 未找到符合的JSON檔案，需要生成新檔案")
            return None
            
        except Exception as e:
            self._error(f"搜尋檔案時發生錯誤: {str(e)}")
            self.load_error.emit(f"搜尋檔案時發生錯誤: {str(e)}")
            return None
    
    def _build_filename_patterns(self, year: int, race: str, session: str,
                                driver1: str, driver2: str, lap1: int, lap2: int) -> List[str]:
        """構建檔案名稱搜尋模式"""
        driver1_norm = self._normalize_driver_code(driver1)
        driver2_norm = self._normalize_driver_code(driver2)
        lap1_safe = lap1 if lap1 is not None else 1
        lap2_safe = lap2 if lap2 is not None else lap1_safe

        if driver2_norm and driver2_norm != driver1_norm:
            # 🆕 雙車手對比檔案 - 只使用精確搜尋（移除萬用字元回退）
            filename_patterns = [
                f"comparison_telemetry_{driver1_norm}_{driver2_norm}_{year}_{race}_{session}_Lap{lap1_safe}_Lap{lap2_safe}.json",
                # ❌ 移除萬用字元模式，檔案不存在時將通過 API 生成
            ]
            self._debug("🔄 雙車手檔案搜尋模式（精確匹配）:")
        else:
            # 🆕 同車手檔案 - 只使用精確搜尋（移除萬用字元回退）
            filename_patterns = [
                f"comparison_telemetry_{driver1_norm}_{driver1_norm}_{year}_{race}_{session}_Lap{lap1_safe}.json",
                f"comparison_telemetry_{driver1_norm}_{driver1_norm}_{year}_{race}_{session}_Lap{lap1_safe}_Lap{lap2_safe}.json",
                # ❌ 移除萬用字元模式，檔案不存在時將通過 API 生成
            ]
            self._debug("🏎️ 同車手檔案搜尋模式（精確匹配）:")

        for i, pattern in enumerate(filename_patterns, 1):
            self._debug(f"   {i}. {pattern}")

        return filename_patterns
    
    # ========== API 載入邏輯 ========== 

    def _determine_api_base_url(self) -> str:
        return resolve_api_base_url(event_logger=self._debug)

    def _resolve_local_fallback_policy(self) -> Tuple[bool, str]:
        env_value = os.getenv("F1T_ALLOW_TELEMETRY_JSON_FALLBACK")
        if env_value is not None:
            normalized = str(env_value).strip().lower()
            if normalized in {"1", "true", "yes", "on"}:
                return True, f"環境變數 F1T_ALLOW_TELEMETRY_JSON_FALLBACK={env_value}"
            return False, f"環境變數 F1T_ALLOW_TELEMETRY_JSON_FALLBACK={env_value}"
        return True, "預設策略 (允許本地 JSON 後備)"

    def _is_api_available(self) -> bool:
        available = is_api_available()
        if not available:
            self._debug("API marked offline by shared runtime cache")
        return available

    def set_local_fallback_allowed(self, allowed: bool, reason: Optional[str] = None) -> None:
        self._allow_local_fallback = bool(allowed)
        self._fallback_policy_reason = reason or "手動覆寫"
        state = "啟用" if self._allow_local_fallback else "停用"
        self._debug(f"本地 JSON 後備手動設為{state} (原因: {self._fallback_policy_reason})")

    def load_data_from_local(self, year: int, race: str, session: str,
                              driver1: str, driver2: Optional[str] = None,
                              lap1: int = 1, lap2: Optional[int] = None,
                              is_fastest_lap: bool = False) -> bool:
        """Force loading telemetry data through the legacy JSON/CLI path for diagnostics."""
        if lap2 is None:
            lap2 = lap1

        driver1_normalized = self._normalize_driver_code(driver1)
        driver2_normalized = self._normalize_driver_code(driver2)
        if not driver1_normalized:
            self._error("缺少主要車手代碼，無法載入本地遙測數據")
            self.load_error.emit("缺少 driver1")
            return False

        single_driver_mode = (driver2_normalized is None) or (driver2_normalized == driver1_normalized)
        effective_driver2 = driver2_normalized if driver2_normalized else driver1_normalized

        params = {
            'year': year,
            'race': race,
            'session': session,
            'driver1': driver1_normalized,
            'driver2': None if single_driver_mode else driver2_normalized,
            'driver2_effective': effective_driver2,
            'lap1': lap1,
            'lap2': lap2,
            'is_fastest_lap': is_fastest_lap,
            'single_driver_mode': single_driver_mode,
            'force_refresh': False
        }
        params['signature'] = self._build_request_signature(params)
        params['request_token'] = self._next_request_token()
        params['request_started_at'] = time.time()

        previous_state = self._allow_local_fallback
        previous_reason = self._fallback_policy_reason
        try:
            self._allow_local_fallback = True
            self._fallback_policy_reason = "手動診斷模式"
            self.current_session = params
            self._debug("🔁 手動觸發本地 JSON/CLI 後備流程")
            return self._fallback_to_local("manual local load", params['request_token'])
        finally:
            self._allow_local_fallback = previous_state
            self._fallback_policy_reason = previous_reason

    def _start_api_request(self, request_token: Optional[int] = None) -> None:
        if not self.current_session:
            self._error("缺少當前會話資訊，無法呼叫 API")
            self._fallback_to_local("缺少會話資訊", request_token)
            return

        params = self.current_session

        if request_token is None:
            request_token = params.get('request_token')

        if request_token is not None and request_token != self._active_request_token:
            self._debug(f"忽略過時的 API 請求 (token {request_token} != {self._active_request_token})")
            return

        driver1 = self._normalize_driver_code(params.get('driver1'))
        driver2 = self._normalize_driver_code(params.get('driver2_effective'), driver1)

        if not driver1:
            self._error("缺少主要車手代碼，無法發送遙測比較 API")
            self._on_api_error("缺少 driver1", request_token)
            return
        if not driver2:
            driver2 = driver1
        if params.get('single_driver_mode'):
            self._debug(f"單車手模式啟動，driver2 將使用 {driver2}")

        lap1 = params.get('lap1') or params.get('lap') or 1
        lap2 = params.get('lap2') or lap1

        worker_params = {
            "year": params.get('year'),
            "race": params.get('race'),
            "session": params.get('session'),
            "driver1": driver1,
            "driver2": driver2,
            "lap1": lap1,
            "lap2": lap2,
            "force_refresh": params.get('force_refresh', False)
        }

        if params.get('is_fastest_lap'):
            self._debug("檢測到最速圈模式，lap1/lap2 由 API 自行解析")

        self._api_base_url = self._determine_api_base_url()
        self._debug(f"🚀 呼叫 API: {self._api_base_url}/api/v2/analysis/execute")
        self._debug(f"參數: {worker_params}")

        if not self._is_api_available():
            self._debug("API 健康檢查失敗，啟動本地後備流程")
            self._fallback_to_local("API 服務未啟動", request_token)
            return

        self._cleanup_api_worker()

        timeout = getattr(self, "_api_timeout", 75.0)
        self._api_worker = TelemetryApiWorker(
            self._api_base_url,
            worker_params,
            timeout=timeout,
            request_token=request_token,
            parent=self
        )
        self._api_worker.progress.connect(self._on_api_progress)
        self._api_worker.success.connect(self._on_api_success)
        self._api_worker.failure.connect(self._on_api_error)
        self._api_worker.finished.connect(self._cleanup_api_worker)
        self._api_worker.start()

    def _on_api_progress(self, value: int) -> None:
        try:
            bounded = max(0, min(int(value), 100))
            self.load_progress.emit(bounded)
        except Exception:
            pass

    def _on_api_success(self, payload: Dict[str, Any]) -> None:
        if not isinstance(payload, dict):
            self._on_api_error("無效的 API 回傳格式", None)
            return
        request_token = payload.get("request_token")
        data = payload.get("data")
        raw_payload = payload.get("payload", {})
        meta = payload.get("meta", {})
        self._handle_api_success(data, raw_payload, meta, request_token)

    def _on_api_error(self, message: str, request_token: Optional[int] = None) -> None:
        if request_token is not None and request_token != self._active_request_token:
            self._debug(f"忽略過時的 API 失敗回應 (token {request_token} != {self._active_request_token})")
            return
        self._error(f"API 請求失敗: {message}")
        self._is_loading = False
        self.status_changed.emit("API 請求失敗，嘗試本地 JSON/CLI 後備流程")
        if not self._fallback_to_local(message, request_token):
            self.load_error.emit(f"API 載入失敗: {message}")

    def _cleanup_api_worker(self) -> None:
        if self._api_worker:
            try:
                if self._api_worker.isRunning():
                    self._api_worker.requestInterruption()
                    self._api_worker.wait(200)
                self._api_worker.progress.disconnect()
            except Exception:
                pass
            try:
                self._api_worker.success.disconnect()
            except Exception:
                pass
            try:
                self._api_worker.failure.disconnect()
            except Exception:
                pass
            try:
                self._api_worker.finished.disconnect()
            except Exception:
                pass
            self._api_worker.deleteLater()
            self._api_worker = None

    def _handle_api_success(self, data: Any, payload: Dict[str, Any], meta: Dict[str, Any],
                            request_token: Optional[int] = None) -> None:
        if request_token is not None and request_token != self._active_request_token:
            self._debug(f"忽略過時的 API 成功回應 (token {request_token} != {self._active_request_token})")
            return
        try:
            if not isinstance(data, dict):
                raise ValueError("API 回傳缺少 data 物件")

            self._debug("========== _handle_api_success 開始 ==========")
            self._debug(f"📦 data 類型: {type(data)}")
            self._debug(f"📦 data 鍵值: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")

            self._last_data_source = "api"
            self._last_api_meta = meta or {}

            self._debug("🧪 步驟1: 開始驗證 API 數據格式")
            if not self._validate_telemetry_data(data):
                raise ValueError("API 回傳數據格式驗證失敗")
            self._debug("✅ 步驟1: 數據格式驗證通過")

            self._debug("📝 步驟2: 設置 metadata")
            metadata = data.setdefault("metadata", {})
            metadata.setdefault("telemetry_type", self.telemetry_type)
            metadata.setdefault("data_source", "api")
            if meta:
                metadata.setdefault("api", meta)
            session_snapshot = self.current_session or {}
            metadata.setdefault("year", session_snapshot.get('year'))
            metadata.setdefault("race", session_snapshot.get('race'))
            metadata.setdefault("session", session_snapshot.get('session'))
            self._debug("✅ 步驟2: metadata 設置完成")

            self._debug("� 步驟3: 處理遙測數據")
            processed_data = self._process_telemetry_data(data)
            if isinstance(processed_data, dict):
                metadata_bucket = processed_data.setdefault("metadata", {})
                metadata_bucket.setdefault("telemetry_type", self.telemetry_type)
                metadata_bucket.setdefault("data_source", "api")
                if meta:
                    metadata_bucket.setdefault("api", meta)
            self._debug("✅ 步驟3: API 數據處理完成")

            self._debug("📊 步驟4: 發送進度和狀態信號")
            self.load_progress.emit(100)
            self.status_changed.emit("已透過 API 載入遙測比較資料")
            self._current_data = processed_data
            self._is_loading = False
            self._debug("✅ 步驟4: 狀態更新完成")

            self._debug("🚀 步驟5: 即將發送 data_loaded 信號")
            self._debug(f"📡 信號接收者數量: {self.receivers(self.data_loaded)}")
            self.data_loaded.emit(processed_data)
            self._debug("✅ 步驟5: data_loaded 信號已發送")
            self._debug("========== _handle_api_success 完成 ==========")
        except Exception as exc:
            self._error(f"❌ 處理 API 數據失敗: {exc}")
            import traceback
            self._error("完整錯誤追蹤:")
            self._error(traceback.format_exc())
            self._on_api_error(str(exc), request_token)

    def _fallback_to_local(self, reason: str, request_token: Optional[int] = None) -> bool:
        if request_token is not None and request_token != self._active_request_token:
            self._debug(f"忽略過時的本地後備請求 (token {request_token} != {self._active_request_token})")
            return False
        if not self._allow_local_fallback:
            self._last_data_source = "local-fallback-disabled"
            self._last_api_meta = {}
            self._debug(f"本地 JSON 後備被停用: {reason}")
            return False

        params = self._pending_params or self.current_session or {}
        self._debug(f"啟動本地後備流程 (原因: {reason})")
        json_file = self._find_telemetry_data_file(
            params.get('year'), params.get('race'), params.get('session'),
            params.get('driver1'), params.get('driver2'), params.get('lap1', 1), params.get('lap2', 1)
        )

        if json_file:
            self._last_data_source = "local-json"
            self._debug(f"使用本地 JSON 檔案: {json_file}")
            QTimer.singleShot(10, lambda: self._load_json_file(json_file, request_token))
            return True

        self._debug("本地 JSON 不存在，改用 CLI 生成")
        self._last_data_source = "cli-generation"
        self._start_cli_generation(
            params.get('year'), params.get('race'), params.get('session'),
            params.get('driver1'), params.get('driver2'), params.get('lap1', 1), params.get('lap2', 1),
            request_token=request_token
        )
        return True

    def _persist_api_payload(self, data: Dict[str, Any]):
        try:
            params = self.current_session or {}
            year = params.get('year')
            race = params.get('race')
            session = params.get('session')
            driver1 = self._normalize_driver_code(params.get('driver1'))
            raw_driver2 = self._normalize_driver_code(params.get('driver2'))
            driver2_effective = self._normalize_driver_code(params.get('driver2_effective'), driver1)
            single_driver_mode = (raw_driver2 is None) or (raw_driver2 == driver1)
            lap1 = params.get('lap1', 1)
            lap2 = params.get('lap2', lap1)
            lap2_safe = lap2 if lap2 is not None else lap1

            metadata = data.setdefault('metadata', {}) if isinstance(data, dict) else {}
            metadata.setdefault('year', year)
            metadata.setdefault('race', race)
            metadata.setdefault('session', session)
            metadata.setdefault('lap', metadata.get('lap') or params.get('lap'))
            metadata.setdefault('lap1', lap1)
            metadata.setdefault('lap2', lap2)
            metadata.setdefault('driver1', driver1)
            metadata.setdefault('driver2', driver2_effective)
            metadata.setdefault('lap_number1', metadata.get('lap_number1') or lap1)
            metadata.setdefault('lap_number2', metadata.get('lap_number2') or lap2_safe)
            metadata.setdefault('single_driver_mode', single_driver_mode)
            drivers_meta = metadata.setdefault('drivers', [])
            if isinstance(drivers_meta, list):
                if not any(isinstance(item, dict) for item in drivers_meta):
                    if driver1 and driver1 not in drivers_meta:
                        drivers_meta.append(driver1)
                    if not single_driver_mode and driver2_effective and driver2_effective not in drivers_meta:
                        drivers_meta.append(driver2_effective)

            analysis_info = data.setdefault('analysis_info', {}) if isinstance(data, dict) else {}
            if isinstance(analysis_info, dict):
                analysis_info.setdefault('function_id', '13')
                analysis_info.setdefault('year', year)
                analysis_info.setdefault('race', race)
                analysis_info.setdefault('session', session)
                analysis_info.setdefault('lap', analysis_info.get('lap') or metadata.get('lap'))
                lap_numbers = analysis_info.setdefault('lap_numbers', {})
                if isinstance(lap_numbers, dict):
                    if driver1 and driver1 not in lap_numbers:
                        lap_numbers[driver1] = lap1
                    if driver2_effective and driver2_effective not in lap_numbers:
                        lap_numbers[driver2_effective] = lap2_safe

            driver1_token = driver1 or "UNK"
            driver2_token = driver2_effective or driver1_token
            if single_driver_mode:
                filename = f"comparison_telemetry_{driver1_token}_{driver1_token}_{year}_{race}_{session}_Lap{lap1}.json"
            else:
                filename = f"comparison_telemetry_{driver1_token}_{driver2_token}_{year}_{race}_{session}_Lap{lap1}_Lap{lap2_safe}.json"
            output_dir = "json"
            os.makedirs(output_dir, exist_ok=True)
            file_path = os.path.join(output_dir, filename)

            self._debug(f"💾 將 API 回傳保存至 {file_path}")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            self._debug(f"儲存 API 結果失敗: {exc}")

    # ========== CLI 生成邏輯 ========== 
    
    def _start_cli_generation(self, year: int, race: str, session: str,
                             driver1: str, driver2: str = None,
                             lap1: int = 1, lap2: int = 1,
                             request_token: Optional[int] = None):
        """啟動 CLI 生成流程"""
        try:
            if request_token is not None and request_token != self._active_request_token:
                self._debug(f"忽略過時的 CLI 生成請求 (token {request_token} != {self._active_request_token})")
                return False
            self._debug("========== 啟動 CLI 生成流程 ==========")
            self._debug(f"生成參數:")
            self._debug(f"   年份: {year}")
            self._debug(f"   賽站: {race}")
            self._debug(f"   賽段: {session}")
            self._debug(f"   車手1: {driver1}, 圈數: {lap1}")
            self._debug(f"   車手2: {driver2}, 圈數: {lap2}")
            
            # 儲存參數供後續使用
            self._generation_params = {
                'year': year,
                'race': race,
                'session': session,
                'driver1': driver1,
                'driver2': driver2,
                'lap1': lap1,
                'lap2': lap2,
                'request_token': request_token
            }
            
            # 啟動 CLI 生成
            success = self._generate_telemetry_data_via_cli(
                year, race, session, driver1, driver2, lap1, lap2,
                request_token=request_token
            )
            
            if success:
                self._debug("✅ CLI 啟動成功，開始監控檔案生成")
                # 啟動定時器檢查檔案是否生成完成
                self._start_generation_monitoring()
            else:
                self._debug("❌ CLI 啟動失敗")
                self.load_error.emit(f"啟動 CLI 生成失敗: {year} {race} {session}")
                self._is_loading = False
                
        except Exception as e:
            self._error(f"啟動生成時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            self.load_error.emit(f"啟動生成時發生錯誤: {str(e)}")
            self._is_loading = False
    
    def _generate_telemetry_data_via_cli(self, year: int, race: str, session: str,
                                        driver1: str, driver2: str = None,
                                        lap1: int = 1, lap2: int = 1,
                                        request_token: Optional[int] = None) -> bool:
        """透過 CLI 工具生成遙測數據"""
        try:
            if request_token is not None and request_token != self._active_request_token:
                self._debug(f"忽略過時的 CLI 生成請求 (token {request_token} != {self._active_request_token})")
                return False
            self._debug("========== CLI 命令生成 ==========")
            self._debug(f"生成{self.config['display_name']}數據: {year} {race} {session}")
            
            # 構建命令 - 使用Function 13: 車手比較分析
            command = [
                "python", "f1_analysis_modular_main.py",
                "-f", "13",  # 功能13: 車手比較分析
                "-y", str(year),
                "-r", race,
                "-s", session,
                "-d", driver1
            ]
            
            # 添加第二位車手參數
            if driver2:
                command.extend(["-d2", driver2])
                self._debug(f"雙車手模式: {driver1} vs {driver2}")
            else:
                # 單車手模式：設置 driver2 與 driver1 相同
                command.extend(["-d2", driver1])
                self._debug(f"單車手模式: {driver1} vs {driver1}")
            
            # 添加圈數參數 - 始終使用雙參數模式
            command.extend(["--lap1", str(lap1), "--lap2", str(lap2)])
            
            if driver2:
                self._debug(f"雙車手模式圈數設定: {driver1} 第{lap1}圈 vs {driver2} 第{lap2}圈")
            else:
                self._debug(f"單車手模式圈數設定: {driver1} 第{lap1}圈 vs {driver1} 第{lap2}圈")
            
            self._debug(f"完整 CLI 命令: {' '.join(command)}")
            self.status_changed.emit(f"正在生成{self.config['display_name']}數據...")
            
            # 非阻塞執行
            def run_cli():
                try:
                    self._debug("🚀 開始執行 CLI 命令...")
                    process = subprocess.Popen(
                        command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        encoding='utf-8',
                        errors='replace',  # 遇到無法解碼的字符時用替代字符
                        cwd=os.getcwd()
                    )
                    
                    stdout, stderr = process.communicate()
                    
                    if process.returncode == 0:
                        self._debug("CLI 執行成功")
                    else:
                        self._error(f"CLI 執行失敗: {stderr}")
                        
                except Exception as e:
                    self._error(f"CLI 執行異常: {e}")
            
            # 在背景執行緒中執行CLI
            thread = threading.Thread(target=run_cli, daemon=True)
            thread.start()
            
            return True
            
        except Exception as e:
            self._error(f"啟動 CLI 失敗: {e}")
            return False
    
    # ========== 監控系統 ==========
    
    def _start_generation_monitoring(self):
        """啟動檔案生成監控"""
        self._debug("========== 啟動監控系統 ==========")
        self._debug("檢查計時器狀態...")
        self._debug(f"_generation_timer 存在: {hasattr(self, '_generation_timer')}")
        self._debug(f"_generation_timeout_timer 存在: {hasattr(self, '_generation_timeout_timer')}")
        
        # 啟動監控 (每5秒檢查一次，最多等待180秒)
        self._debug("啟動主監控計時器 (每5秒檢查)")
        self._generation_timer.start(5000)
        self._debug(f"計時器是否運行: {self._generation_timer.isActive()}")
        self._debug(f"計時器間隔: {self._generation_timer.interval()}")
        
        self._debug("啟動超時計時器 (180秒)")
        self._generation_timeout_timer.start(180000)
        self._debug(f"超時計時器是否運行: {self._generation_timeout_timer.isActive()}")
        
        self._debug("✅ 監控系統已啟動")
        self.status_changed.emit("正在生成數據，請稍候...")
        
        # 立即執行一次檢查以確認方法可以被調用
        self._debug("🧪 執行立即測試檢查...")
        QTimer.singleShot(1000, self._check_generation_progress)
    
    def _check_generation_progress(self):
        """檢查檔案生成進度"""
        try:
            self._debug("========== 監控檢查觸發 ==========")
            self._debug(f"時間: {datetime.now().strftime('%H:%M:%S')}")
            
            if hasattr(self, '_generation_params'):
                params = self._generation_params
                request_token = None

                if isinstance(params, dict):
                    year = params.get('year')
                    race = params.get('race')
                    session = params.get('session')
                    driver1 = params.get('driver1')
                    driver2 = params.get('driver2')
                    lap1 = params.get('lap1', 1)
                    lap2 = params.get('lap2', lap1)
                    request_token = params.get('request_token')
                else:
                    year, race, session, driver1, driver2, lap1, lap2 = params

                if request_token is not None and request_token != self._active_request_token:
                    self._debug(f"偵測到過時的 CLI 監控請求 (token {request_token} != {self._active_request_token})，停止監控")
                    self._stop_generation_monitoring()
                    return

                self._debug(f"檢查參數: {year} {race} {session} {driver1} vs {driver2} L{lap1}/L{lap2}")
                
                # 檢查是否有新檔案生成
                self._debug("開始搜尋檔案...")
                json_file = self._find_telemetry_data_file(year, race, session, driver1, driver2, lap1, lap2)
                
                if json_file:
                    self._debug(f"檔案生成完成: {json_file}")
                    self._debug("停止監控並載入檔案")
                    
                    # 停止監控
                    self._stop_generation_monitoring()
                    
                    # 載入新生成的檔案
                    QTimer.singleShot(10, lambda: self._load_json_file(json_file, request_token))
                else:
                    self._debug("繼續等待檔案生成...")
                    self._debug("下次檢查將在5秒後進行")
            else:
                self._debug("❌ 缺少 _generation_params 參數")
                self._debug("停止監控")
                self._stop_generation_monitoring()
                
        except Exception as e:
            self._error(f"監控檢查異常: {e}")
            import traceback
            traceback.print_exc()
            self._debug("嘗試繼續監控...")
    
    def _on_generation_timeout(self):
        """處理生成超時"""
        self._debug("========== 監控超時 ==========")
        self._debug("檔案生成超時 (180秒)")
        self._debug("停止監控系統")
        self._stop_generation_monitoring()
        self.load_error.emit("數據生成超時，請檢查網路連線或重試")
        self._is_loading = False
    
    def _stop_generation_monitoring(self):
        """停止檔案生成監控"""
        self._debug("========== 停止監控系統 ==========")
        if hasattr(self, '_generation_timer'):
            self._generation_timer.stop()
            self._debug("主監控計時器已停止")
        if hasattr(self, '_generation_timeout_timer'):
            self._generation_timeout_timer.stop()
            self._debug("超時計時器已停止")
        self._debug("✅ 監控系統已完全停止")
    
    # ========== JSON 載入和處理 ==========
    
    def _load_json_file(self, file_path: str, expected_token: Optional[int] = None):
        """載入 JSON 檔案"""
        try:
            if expected_token is not None and expected_token != self._active_request_token:
                self._debug(f"忽略過時的 JSON 載入請求 (token {expected_token} != {self._active_request_token})")
                return
            self._debug("========== JSON 檔案載入 ==========")
            self._debug(f"載入檔案: {file_path}")
            
            # 檢查檔案狀態
            if not os.path.exists(file_path):
                self._debug(f"❌ 檔案不存在: {file_path}")
                self.load_error.emit(f"檔案不存在: {file_path}")
                return
                
            file_size = os.path.getsize(file_path)
            self._debug(f"檔案大小: {file_size} bytes")
            
            self.load_progress.emit(90)
            self.status_changed.emit("正在處理數據...")
            
            # 載入JSON檔案
            self._debug("開始讀取 JSON 內容...")
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            self._debug("JSON 載入成功")
            self._debug(f"頂層鍵值: {list(raw_data.keys()) if isinstance(raw_data, dict) else 'Not a dict'}")
            
            # 驗證數據格式
            self._debug("開始驗證數據格式...")
            if self._validate_telemetry_data(raw_data):
                self._debug("✅ 數據格式驗證通過")
                # 處理為遙測分析格式
                processed_data = self._process_telemetry_data(raw_data)
                
                self._debug("========== 即將發送數據 ==========")
                self._debug(f"處理後數據類型: {type(processed_data)}")
                self._debug(f"處理後數據鍵值: {list(processed_data.keys()) if isinstance(processed_data, dict) else 'Not a dict'}")
                
                # 檢查特定數據結構
                data_key = f"{self.telemetry_type}_data"
                if data_key in processed_data:
                    telemetry_data = processed_data[data_key]
                    self._debug(f"{self.telemetry_type}數據鍵值: {list(telemetry_data.keys())}")
                    self._debug(f"距離數據點數: {len(telemetry_data.get('distance', []))}")
                    self._debug(f"車手1數據點數: {len(telemetry_data.get(f'driver1_{self.telemetry_type}', []))}")
                    self._debug(f"車手2數據點數: {len(telemetry_data.get(f'driver2_{self.telemetry_type}', []))}")
                
                self.load_progress.emit(100)
                self.status_changed.emit("數據載入完成")
                self._current_data = processed_data
                self._is_loading = False
                
                self._debug("🚀 即將發送 data_loaded 信號...")
                self._debug(f"📦 信號數據類型: {type(processed_data)}")
                self._debug(f"📦 信號數據鍵值: {list(processed_data.keys()) if isinstance(processed_data, dict) else 'Not a dict'}")
                if isinstance(processed_data, dict) and 'speed_data' in processed_data:
                    speed_data = processed_data['speed_data']
                    self._debug(f"📊 speed_data 鍵值: {list(speed_data.keys())}")
                    self._debug(f"📊 distance 點數: {len(speed_data.get('distance', []))}")
                    self._debug(f"📊 driver1_speed 點數: {len(speed_data.get('driver1_speed', []))}")
                    self._debug(f"📊 driver2_speed 點數: {len(speed_data.get('driver2_speed', []))}")
                self.data_loaded.emit(processed_data)
                self._debug("✅ data_loaded 信號已發送")
                self._debug(f"📡 信號接收者數量: {self.receivers(self.data_loaded)}")
                
            else:
                self._debug("❌ 數據格式驗證失敗")
                self.load_error.emit("數據格式驗證失敗")
                self._is_loading = False
                
        except Exception as e:
            self._error(f"JSON 檔案載入失敗: {str(e)}")
            self.load_error.emit(f"載入失敗: {str(e)}")
            self._is_loading = False
    
    def _validate_telemetry_data(self, raw_data: dict) -> bool:
        """驗證遙測數據格式"""
        try:
            self._debug("🔍 驗證數據格式...")
            
            # 檢查基本結構
            if not isinstance(raw_data, dict):
                self._debug("❌ 數據不是字典格式")
                return False
            
            # 檢查是否有遙測比較數據
            if 'results' not in raw_data:
                self._debug("❌ 缺少 results 字段")
                return False
                
            results = raw_data['results']
            data_field = self.config['data_field']
            
            # 根據遙測類型選擇不同的數據路徑
            if self.telemetry_type in ['speeddiff', 'distancediff']:
                # 速度差和距離差數據直接在 results 下
                if data_field not in results:
                    self._debug(f"❌ 缺少 {data_field} 字段")
                    return False
                
                telemetry_data = results[data_field]
                
                # 檢查差異分析的數據結構 - 根據類型使用不同的驗證邏輯
                if self.telemetry_type == 'speeddiff':
                    # 速度差：期望 'distance' 和 'speed_difference'
                    required_fields = ['distance', data_field]
                elif self.telemetry_type == 'distancediff':
                    # 距離差：期望 'reference_distance' 和 'cumulative_distance_difference'
                    required_fields = ['reference_distance', 'cumulative_distance_difference']
                else:
                    # 其他差異分析：使用默認邏輯
                    required_fields = ['distance', data_field]
                
                for field in required_fields:
                    if field not in telemetry_data:
                        self._debug(f"❌ 缺少必要欄位: {field}")
                        return False
                
            else:
                # 常規遙測數據在 telemetry_comparison 下
                if 'telemetry_comparison' not in results:
                    self._debug("❌ 缺少 telemetry_comparison 字段")
                    return False
                    
                telemetry_comp = results['telemetry_comparison']
                
                if data_field not in telemetry_comp:
                    self._debug(f"❌ 缺少 {data_field} 字段")
                    return False
                
                telemetry_data = telemetry_comp[data_field]
                
                # 檢查常規遙測數據欄位
                required_fields = ['distance', 'driver1_data', 'driver2_data']
                for field in required_fields:
                    if field not in telemetry_data:
                        self._debug(f"❌ 缺少必要欄位: {field}")
                        return False
            
            # 驗證數據長度一致性
            if self.telemetry_type == 'speeddiff':
                # 速度差：檢查 distance 和 speed_difference
                distance_data = telemetry_data.get('distance', [])
                diff_data = telemetry_data.get('speed_difference', [])
                
                if len(distance_data) == 0:
                    self._debug("❌ 距離數據為空")
                    return False
                    
                if len(diff_data) == 0:
                    self._debug("❌ 速度差數據為空")
                    return False
                    
                if len(distance_data) != len(diff_data):
                    self._debug(f"❌ 數據長度不一致: distance={len(distance_data)}, speed_difference={len(diff_data)}")
                    return False
                    
            elif self.telemetry_type == 'distancediff':
                # 距離差：檢查 reference_distance 和 cumulative_distance_difference
                distance_data = telemetry_data.get('reference_distance', [])
                diff_data = telemetry_data.get('cumulative_distance_difference', [])
                
                if len(distance_data) == 0:
                    self._debug("❌ 參考距離數據為空")
                    return False
                    
                if len(diff_data) == 0:
                    self._debug("❌ 累積距離差數據為空")
                    return False
                    
                if len(distance_data) != len(diff_data):
                    self._debug(f"❌ 數據長度不一致: reference_distance={len(distance_data)}, cumulative_distance_difference={len(diff_data)}")
                    return False
                    
            elif self.telemetry_type in ['speeddiff', 'distancediff']:
                # 其他差異分析：使用默認邏輯  
                distance_data = telemetry_data.get('distance', [])
                diff_data = telemetry_data.get(data_field, [])
                
                if len(distance_data) == 0:
                    self._debug("❌ 距離數據為空")
                    return False
                    
                if len(diff_data) == 0:
                    self._debug("❌ 差異數據為空")
                    return False
                    
                if len(distance_data) != len(diff_data):
                    self._debug(f"❌ 數據長度不一致: distance={len(distance_data)}, {data_field}={len(diff_data)}")
                    return False
            else:
                # 常規遙測數據驗證
                distance_data = telemetry_data.get('distance', [])
                driver1_data = telemetry_data.get('driver1_data', [])
                driver2_data = telemetry_data.get('driver2_data', [])
                
                if len(distance_data) == 0:
                    self._debug("❌ 距離數據為空")
                    return False
                
                if len(driver1_data) == 0:
                    self._debug("❌ 車手1數據為空")
                    return False
                    
                if len(driver2_data) == 0:
                    self._debug("❌ 車手2數據為空")
                    return False
                
                if len(distance_data) != len(driver1_data) or len(distance_data) != len(driver2_data):
                    self._debug(f"❌ 數據長度不一致: distance={len(distance_data)}, driver1={len(driver1_data)}, driver2={len(driver2_data)}")
                    return False
            
            self._debug("✅ 數據格式驗證通過")
            return True
            
        except Exception as e:
            self._debug(f"❌ 數據格式驗證失敗: {str(e)}")
            return False
    
    def _process_telemetry_data(self, raw_data: dict) -> dict:
        """處理遙測數據為標準格式"""
        try:
            self._debug("🔧 處理遙測數據...")
            
            results = raw_data['results']
            data_field = self.config['data_field']
            
            # 根據遙測類型選擇不同的數據路徑
            if self.telemetry_type in ['speeddiff', 'distancediff']:
                # 速度差和距離差數據直接在 results 下
                telemetry_raw = results[data_field]
                self._debug(f"差異分析原始數據鍵值: {list(telemetry_raw.keys())}")
                self._debug(f"距離數據點數: {len(telemetry_raw.get('distance', []))}")
                self._debug(f"{data_field}數據點數: {len(telemetry_raw.get(data_field, []))}")
            else:
                # 常規遙測數據在 telemetry_comparison 下
                telemetry_comp = results['telemetry_comparison']
                telemetry_raw = telemetry_comp[data_field]
                self._debug(f"常規遙測原始數據鍵值: {list(telemetry_raw.keys())}")
                self._debug(f"距離數據點數: {len(telemetry_raw.get('distance', []))}")
                self._debug(f"車手1數據點數: {len(telemetry_raw.get('driver1_data', []))}")
                self._debug(f"車手2數據點數: {len(telemetry_raw.get('driver2_data', []))}")
            
            # 提取基本資訊
            metadata = raw_data.get('metadata', {})
            
            # 從 comparison_info 提取更詳細的車手資訊
            comparison_info = results.get('comparison_info', {})
            
            # 構建標準化數據結構
            processed_data = {
                "metadata": {
                    "drivers": [
                        {
                            "code": metadata.get('driver1', comparison_info.get('driver1', 'UNK')), 
                            "lap_number": metadata.get('lap_number1', comparison_info.get('act_lap1_number', 1)),
                            "lap_time": comparison_info.get('lap_time1', 'N/A'),
                            "compound": comparison_info.get('compound1', 'N/A'),
                            "tyre_life": comparison_info.get('tyre_life1', 0)
                        },
                        {
                            "code": metadata.get('driver2', comparison_info.get('driver2', 'UNK')), 
                            "lap_number": metadata.get('lap_number2', comparison_info.get('act_lap2_number', 1)),
                            "lap_time": comparison_info.get('lap_time2', 'N/A'),
                            "compound": comparison_info.get('compound2', 'N/A'),
                            "tyre_life": comparison_info.get('tyre_life2', 0)
                        }
                    ],
                    "sectors": metadata.get('sectors', []),
                    "year": metadata.get('year', 2025),
                    "race": metadata.get('race', 'Unknown'),
                    "session": metadata.get('session', 'R'),
                    "telemetry_type": self.telemetry_type,
                    "display_name": self.config['display_name'],
                    "unit": self.config['unit'],
                    "analysis_timestamp": metadata.get('analysis_timestamp', '')
                }
            }
            
            # 構建遙測數據結構 - 根據類型處理
            data_key = f"{self.telemetry_type}_data"
            
            if self.telemetry_type in ['speeddiff', 'distancediff']:
                # 差異分析數據結構 - 需要匹配前端期望的鍵名
                if self.telemetry_type == 'speeddiff':
                    # 速度差分析：前端期望 'speed' 和 'cumulative_speed_difference'
                    processed_data[data_key] = {
                        "speed": telemetry_raw.get('distance', []),  # 前端期望 'speed' 作為距離數據
                        "cumulative_speed_difference": telemetry_raw.get(data_field, []),  # 前端期望這個鍵名
                        "distance": telemetry_raw.get('distance', []),  # 保留原始鍵名以備用
                        "speeddiff": telemetry_raw.get(data_field, []),  # 保留原始鍵名以備用
                        "driver1_name": comparison_info.get('driver1', 'UNK'),
                        "driver2_name": comparison_info.get('driver2', 'UNK'),
                        "reference": telemetry_raw.get('reference', '')  # 添加參考信息
                    }
                elif self.telemetry_type == 'distancediff':
                    # 距離差分析：JSON結構與速度差不同，需要特殊處理
                    processed_data[data_key] = {
                        "distance": telemetry_raw.get('reference_distance', []),  # 使用 reference_distance 作為距離數據
                        "cumulative_distance_difference": telemetry_raw.get('cumulative_distance_difference', []),  # 前端期望這個鍵名
                        "reference_distance": telemetry_raw.get('reference_distance', []),  # 保留原始鍵名以備用
                        "position_difference": telemetry_raw.get('position_difference', []),  # 保留原始數據
                        "driver1_name": comparison_info.get('driver1', 'UNK'),
                        "driver2_name": comparison_info.get('driver2', 'UNK'),
                        "reference": telemetry_raw.get('reference', '')  # 添加參考信息
                    }
                else:
                    # 其他差異分析：保持原有結構
                    processed_data[data_key] = {
                        "distance": telemetry_raw.get('distance', []),
                        f"{self.telemetry_type}": telemetry_raw.get(data_field, []),
                        "driver1_name": comparison_info.get('driver1', 'UNK'),
                        "driver2_name": comparison_info.get('driver2', 'UNK')
                    }
                
                self._debug(f"構建差異分析數據結構:")
                self._debug(f"  distance: {len(processed_data[data_key]['distance'])} 點")
                if self.telemetry_type == 'speeddiff':
                    self._debug(f"  speed: {len(processed_data[data_key]['speed'])} 點")
                    self._debug(f"  cumulative_speed_difference: {len(processed_data[data_key]['cumulative_speed_difference'])} 點")
                elif self.telemetry_type == 'distancediff':
                    self._debug(f"  cumulative_distance_difference: {len(processed_data[data_key]['cumulative_distance_difference'])} 點")
                else:
                    self._debug(f"  {self.telemetry_type}: {len(processed_data[data_key][self.telemetry_type])} 點")
            else:
                # 常規遙測數據結構
                processed_data[data_key] = {
                    "distance": telemetry_raw.get('distance', []),
                    f"driver1_{self.telemetry_type}": telemetry_raw.get('driver1_data', []),
                    f"driver2_{self.telemetry_type}": telemetry_raw.get('driver2_data', []),
                    "driver1_name": metadata.get('driver1', comparison_info.get('driver1', 'UNK')),
                    "driver2_name": metadata.get('driver2', comparison_info.get('driver2', 'UNK'))
                }
            
            # 計算統計數據 - 根據類型選擇不同的數據源
            distance_data = telemetry_raw.get('distance', [])
            
            if self.telemetry_type in ['speeddiff', 'distancediff']:
                # 差異分析統計
                diff_data = telemetry_raw.get(data_field, [])
                processed_data["statistics"] = {
                    "difference": self._calculate_statistics(diff_data),
                    "distance": {
                        "min": min(distance_data) if distance_data else 0,
                        "max": max(distance_data) if distance_data else 0,
                        "total_points": len(distance_data)
                    }
                }
                
                self._debug(f"✅ {self.config['display_name']}數據處理完成")
                self._debug(f"   距離點數: {len(distance_data)}")
                self._debug(f"   差異數據點數: {len(diff_data)}")
                
            else:
                # 常規遙測統計
                driver1_data = telemetry_raw.get('driver1_data', [])
                driver2_data = telemetry_raw.get('driver2_data', [])
                
                processed_data["statistics"] = {
                    "driver1": self._calculate_statistics(driver1_data),
                    "driver2": self._calculate_statistics(driver2_data),
                    "distance": {
                        "min": min(distance_data) if distance_data else 0,
                        "max": max(distance_data) if distance_data else 0,
                        "total_points": len(distance_data)
                    }
                }
                
                self._debug(f"✅ {self.config['display_name']}數據處理完成")
                self._debug(f"   距離點數: {len(distance_data)}")
                self._debug(f"   車手1數據點數: {len(driver1_data)}")
                self._debug(f"   車手2數據點數: {len(driver2_data)}")
            
            return processed_data
            
        except Exception as e:
            self._error(f"數據處理失敗: {e}")
            import traceback
            traceback.print_exc()
            # 返回空數據結構避免錯誤
            return self._get_empty_data_structure()
    
    def _calculate_statistics(self, data: List[float]) -> dict:
        """計算統計數據 - 自動過濾 None 值"""
        if not data:
            return {"max": 0, "min": 0, "avg": 0, "count": 0}
        
        # 過濾掉 None 值,避免加速度等數據中的 None 導致計算失敗
        valid_data = [x for x in data if x is not None]
        
        if not valid_data:
            return {"max": 0, "min": 0, "avg": 0, "count": 0}
        
        return {
            "max": max(valid_data),
            "min": min(valid_data),
            "avg": sum(valid_data) / len(valid_data),
            "count": len(valid_data)
        }
    
    def _get_empty_data_structure(self) -> dict:
        """獲取空的數據結構"""
        data_key = f"{self.telemetry_type}_data"
        return {
            "metadata": {
                "drivers": [],
                "sectors": [],
                "year": 2025,
                "race": "Unknown", 
                "session": "R",
                "telemetry_type": self.telemetry_type,
                "display_name": self.config['display_name'],
                "unit": self.config['unit']
            },
            data_key: {
                "distance": [],
                f"driver1_{self.telemetry_type}": [],
                f"driver2_{self.telemetry_type}": [],
                "driver1_name": "UNK",
                "driver2_name": "UNK"
            },
            "statistics": {
                "driver1": {"max": 0, "min": 0, "avg": 0, "count": 0},
                "driver2": {"max": 0, "min": 0, "avg": 0, "count": 0}
            }
        }


# ========== 向後兼容的輔助方法 ==========

def create_telemetry_loader(telemetry_type: str, parent=None) -> TelemetryDataLoader:
    """
    創建遙測數據載入器的工廠函數
    
    Args:
        telemetry_type: 遙測類型
        parent: 父級 QObject
        
    Returns:
        TelemetryDataLoader: 遙測數據載入器實例
    """
    return TelemetryDataLoader(telemetry_type, parent)
