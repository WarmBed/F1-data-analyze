# -*- coding: utf-8 -*-
"""
F1T GUI - API Workers
======================

API 健康檢查和運行時狀態查詢的背景工作執行緒。

從 f1t_gui_main.py 提取 (原始行號: 7919-8075, 157 行)
提取日期: 2025-06-14
"""

# LOCAL_ONLY_REFACTOR:
# Legacy API-mode workers. The desktop app is moving to a local-first runtime,
# so new GUI code should use a local task runner instead of these workers.
# Keep this file temporarily for hybrid/API compatibility during migration.

import time
import datetime
import logging

try:
    import requests
except ImportError:
    requests = None

from PyQt5.QtCore import QThread, pyqtSignal
from core.runtime_mode import is_api_enabled

# 設定日誌
logger = logging.getLogger(__name__)


class ApiHealthWorker(QThread):
    """Background worker to probe API health endpoints without blocking the UI thread.
    
    設計為可重複使用的 Worker，避免頻繁創建銷毀導致的洩漏。
    """

    result_ready = pyqtSignal(dict)

    def __init__(self, base_url: str, timeout: float = 5.0, manual: bool = False, parent=None):
        super().__init__(parent)
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.manual = manual
        self._should_stop = False  # 停止標誌
    
    def update_params(self, base_url: str = None, manual: bool = None):
        """更新 worker 參數（在下次 run 前調用）"""
        if base_url is not None:
            self.base_url = base_url.rstrip('/')
        if manual is not None:
            self.manual = manual

    def run(self):
        """執行一次健康檢查"""
        if not is_api_enabled():
            self.result_ready.emit({
                "state": "disabled",
                "details": ["API workers disabled in local runtime mode"],
                "errors": [],
                "latency_ms": None,
                "checked_at": datetime.datetime.now().isoformat(timespec='seconds'),
                "base_url": self.base_url,
                "manual": self.manual,
            })
            return

        if self._should_stop:
            return
            
        summary = {
            "state": "offline",
            "details": [],
            "errors": [],
            "latency_ms": None,
            "checked_at": datetime.datetime.now().isoformat(timespec='seconds'),
            "base_url": self.base_url,
            "manual": self.manual,
        }

        endpoints = [
            ("system", f"{self.base_url}/api/v2/system/health"),
            ("analysis", f"{self.base_url}/api/v2/analysis/status"),
        ]

        success_count = 0
        latencies = []
        degrade_flag = False

        for name, url in endpoints:
            if self._should_stop:
                return
                
            response = None
            try:
                start = time.perf_counter()
                response = requests.get(url, timeout=self.timeout)
                latency = (time.perf_counter() - start) * 1000.0
                latencies.append(latency)

                if response.status_code == 200:
                    success_count += 1
                    try:
                        payload = response.json()
                    except ValueError:
                        summary["errors"].append(f"{name}: invalid JSON payload from API")
                        degrade_flag = True
                        continue

                    message = payload.get('message') or payload.get('status') or 'OK'
                    summary["details"].append(f"{name}: {message}")
                    if not payload.get('success', True):
                        degrade_flag = True
                        summary["errors"].append(f"{name}: API reported success=False")
                else:
                    summary["errors"].append(f"{name}: HTTP {response.status_code}")
            except requests.exceptions.RequestException as exc:
                summary["errors"].append(f"{name}: {exc}")
            except Exception as exc:
                summary["errors"].append(f"{name}: {type(exc).__name__} - {exc}")
            finally:
                # 確保關閉 HTTP 連接，避免連接洩漏
                if response is not None:
                    response.close()

        if latencies:
            summary["latency_ms"] = round(sum(latencies) / len(latencies), 1)

        if success_count == len(endpoints) and not degrade_flag and not summary["errors"]:
            summary["state"] = "online"
        elif success_count > 0:
            summary["state"] = "degraded"
        else:
            summary["state"] = "offline"
            if not summary["errors"]:
                summary["errors"].append('API did not respond')

        if not summary["details"]:
            summary["details"].append('No API response received')

        if not self._should_stop:
            self.result_ready.emit(summary)
    
    def stop_worker(self):
        """請求停止 worker"""
        self._should_stop = True


class ApiRuntimeWorker(QThread):
    """Background worker that polls the analysis runtime endpoint.
    
    設計為可重複使用的 Worker，避免頻繁創建銷毀導致的洩漏。
    """

    result_ready = pyqtSignal(dict)

    def __init__(self, base_url: str, timeout: float = 5.0, parent=None):
        super().__init__(parent)
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._should_stop = False  # 停止標誌

    def run(self):
        """執行一次 API 請求"""
        if not is_api_enabled():
            self.result_ready.emit({
                "ok": False,
                "payload": None,
                "error": "API runtime worker disabled in local runtime mode",
                "endpoint": f"{self.base_url}/api/v2/analysis/status",
            })
            return

        if self._should_stop:
            return
            
        endpoint = f"{self.base_url}/api/v2/analysis/status"
        summary = {
            "ok": False,
            "payload": None,
            "error": None,
            "endpoint": endpoint,
        }

        response = None
        try:
            response = requests.get(endpoint, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
            summary["payload"] = payload
            summary["ok"] = True
        except requests.exceptions.RequestException as exc:
            summary["error"] = str(exc)
        except ValueError as exc:
            summary["error"] = f"JSON decode error: {exc}"
        except Exception as exc:  # pragma: no cover - defensive
            summary["error"] = f"{type(exc).__name__}: {exc}"
        finally:
            # 確保關閉 HTTP 連接，避免連接洩漏
            if response is not None:
                response.close()

        if not self._should_stop:
            self.result_ready.emit(summary)
    
    def stop_worker(self):
        """請求停止 worker"""
        self._should_stop = True
