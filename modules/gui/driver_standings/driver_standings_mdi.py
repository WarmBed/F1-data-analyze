#!/usr/bin/env python3
"""
車手積分榜 MDI 視窗
Driver Standings MDI

負責管理車手積分榜的 MDI 視窗，整合資料載入器和表格元件

作者: F1T Team
日期: 2025-10-12
版本: 1.0.0
"""

import sys
import time
import requests
from typing import Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QProgressBar, QLabel,
    QApplication
)
from PyQt5.QtCore import Qt, pyqtSlot, QThread, pyqtSignal

from core.gui_i18n import tr

from core.logger import get_logger
logger = get_logger(__name__)




class ChampionshipStandingsApiWorker(QThread):
    """
    積分榜 API 請求工作執行緒
    
    負責異步調用 API 獲取積分榜數據
    API 端點: POST /api/v2/analysis/execute?function_id=97
    """
    
    # 信號
    progress = pyqtSignal(int)  # 進度 (0-100)
    success = pyqtSignal(dict)  # 成功 (返回數據)
    failure = pyqtSignal(str)   # 失敗 (錯誤訊息)
    
    def __init__(self, params: Dict[str, Any], base_url: str = None, timeout: float = 60.0):
        """
        初始化 API Worker
        
        Args:
            params: API 參數 (year, etc.)
            base_url: API 基礎 URL (預設: https://api.f1telemetrystationpro.org)
            timeout: 請求超時時間（秒）
        """
        super().__init__()
        self.base_url = (base_url or "https://api.f1telemetrystationpro.org").rstrip('/')
        self.params = dict(params)
        self.timeout = timeout
    
    def run(self):
        """執行 API 請求"""
        try:
            # ✅ 中斷檢查點 1: 開始時
            if self.isInterruptionRequested():
                return
            self.progress.emit(20)
            
            # 構建 API 端點
            endpoint = f"{self.base_url}/api/v2/analysis/execute"
            
            # 構建查詢參數
            query_params: Dict[str, Any] = {
                "function_id": 97,  # CLI Function 97 - Championship Standings
                "year": int(self.params.get("year")),
            }
            
            # 強制刷新（可選）
            if self.params.get("force_refresh"):
                query_params["force_refresh"] = True
            
            logger.info("[API_WORKER] 調用 API: %s", endpoint)
            logger.debug("[API_WORKER] 參數: %s", query_params)
            
            # ✅ 中斷檢查點 2: HTTP 請求前
            if self.isInterruptionRequested():
                return
            
            # 發送 POST 請求
            start_ts = time.perf_counter()
            response = requests.post(
                endpoint,
                params=query_params,
                timeout=self.timeout,
                headers={"Accept": "application/json"}
            )
            self.progress.emit(70)
            
            # ✅ 中斷檢查點 3: HTTP 請求後
            if self.isInterruptionRequested():
                return
            
            # 檢查 HTTP 狀態
            response.raise_for_status()
            
            # 解析 JSON 回應
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("API 回應必須是 JSON 物件")
            
            if not payload.get("success", False):
                raise RuntimeError(payload.get("message", "API 返回 success=False"))
            
            # 提取數據
            data = payload.get("data")
            if not isinstance(data, dict):
                raise ValueError("API 回應缺少 'data' 物件")
            
            # 計算延遲
            latency_ms = (time.perf_counter() - start_ts) * 1000.0
            
            # 構建元數據
            meta = {
                "source": payload.get("source", "api"),
                "execution_time": payload.get("execution_time"),
                "request_id": payload.get("request_id"),
                "timestamp": payload.get("timestamp"),
                "latency_ms": round(latency_ms, 2),
                "base_url": self.base_url,
            }
            
            logger.info("[API_WORKER] API 調用成功 (延遲: %sms, 數據源: %s)", meta["latency_ms"], meta["source"])
            
            self.progress.emit(90)
            # ✅ 中斷檢查點 4: success 信號發送前
            if self.isInterruptionRequested():
                return
            self.success.emit({"data": data, "meta": meta})
            
        except Exception as exc:
            # ✅ 中斷檢查：被中斷時不發送錯誤信號
            if self.isInterruptionRequested():
                return
            error_msg = f"API 請求失敗: {str(exc)}"
            logger.error("[API_WORKER] %s", error_msg, exc_info=True)
            self.failure.emit(error_msg)
        finally:
            # ✅ 中斷檢查：被中斷時不發送 progress 信號
            if not self.isInterruptionRequested():
                self.progress.emit(100)


try:
    from .driver_standings_data_loader import DriverStandingsDataLoader
    from .driver_standings_widget import DriverStandingsWidget
except ImportError:
    from driver_standings_data_loader import DriverStandingsDataLoader
    from driver_standings_widget import DriverStandingsWidget


class DriverStandingsMDI(QWidget):
    """
    車手積分榜 MDI 視窗
    
    簡單的 QWidget 容器，整合資料載入器和表格元件
    """
    
    def __init__(self, year: str = "2024", parent=None):
        """
        初始化 MDI 視窗
        
        Args:
            year: 賽季年份 (例如: "2025")
            parent: 父元件
        """
        super().__init__(parent)
        self.year = str(year)
        
        # 初始化 UI
        self._setup_ui()
        
        # 初始化資料載入器
        self.data_loader = DriverStandingsDataLoader(year=self.year, parent=self)
        
        # 連接信號
        self._connect_signals()
        
        # 自動載入數據
        self._trigger_initial_load()
    
    def _setup_ui(self):
        """設置 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 狀態列（隱藏）
        self.status_label = QLabel(tr("loading_status", "正在載入..."), self)
        self.status_label.setStyleSheet("padding: 5px; background: #f0f0f0;")
        self.status_label.hide()  # 隱藏狀態列
        layout.addWidget(self.status_label)
        
        # 進度條（隱藏）
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.hide()  # 隱藏進度條
        layout.addWidget(self.progress_bar)
        
        # 積分榜 Widget
        self.standings_widget = DriverStandingsWidget(parent=self)
        layout.addWidget(self.standings_widget)
    
    def _connect_signals(self):
        """連接信號"""
        self.data_loader.data_loaded.connect(self._on_data_loaded)
        self.data_loader.load_error.connect(self._on_load_error)
        self.data_loader.status_changed.connect(self._on_status_changed)
        self.data_loader.load_progress.connect(self._on_progress_changed)
    
    def _trigger_initial_load(self):
        """
        觸發初始數據載入 - 強制使用 API
        
        優先級：
        1. API 調用 (https://api.f1telemetrystationpro.org)
        2. 備援: 本地 JSON 檔案（API 失敗時）
        """
        logger.info("[DRIVER_MDI] 觸發初始載入: year=%s", self.year)
        self.status_label.setText(tr("loading_status", "正在從 API 載入車手積分資料..."))
        self.progress_bar.setValue(10)
        self.progress_bar.show()
        
        # 創建 API Worker
        api_params = {
            "year": self.year,
            "force_refresh": False  # 可選：強制刷新
        }
        
        logger.debug("[DRIVER_MDI] 創建 API Worker")
        self.api_worker = ChampionshipStandingsApiWorker(
            params=api_params,
            base_url="https://api.f1telemetrystationpro.org",
            timeout=60.0
        )
        
        # 連接信號
        self.api_worker.progress.connect(self._on_api_progress)
        self.api_worker.success.connect(self._on_api_success)
        self.api_worker.failure.connect(self._on_api_failure)
        
        # 啟動 API 請求
        logger.debug("[DRIVER_MDI] 啟動 API 請求")
        self.api_worker.start()
    
    @pyqtSlot(int)
    def _on_api_progress(self, progress: int):
        """API 請求進度更新"""
        logger.debug("[DRIVER_MDI] API 進度: %s%%", progress)
        self.progress_bar.setValue(progress)
        self.status_label.setText(f"API 載入中... {progress}%")
    
    @pyqtSlot(dict)
    def _on_api_success(self, result: Dict[str, Any]):
        """API 請求成功"""
        try:
            logger.info("[DRIVER_MDI] API 調用成功")
            
            # API 返回的 data 是完整的 JSON 內容（可能有雙層嵌套）
            api_response = result.get("data", {})
            meta = result.get("meta", {})
            
            logger.debug(
                "[DRIVER_MDI] 數據源: %s | 延遲: %sms",
                meta.get("source"),
                meta.get("latency_ms"),
            )
            
            # 處理雙層嵌套：API 返回的 data 可能包含完整的 CLI JSON 輸出
            if "data" in api_response and isinstance(api_response.get("data"), dict):
                # 雙層嵌套：data.data.drivers
                metadata = api_response.get("metadata", {})
                inner_data = api_response.get("data", {})
                drivers = inner_data.get("drivers", [])
                logger.debug("[DRIVER_MDI] 檢測到雙層嵌套結構 (CLI JSON)")
            else:
                # 單層：data.drivers
                metadata = api_response.get("metadata", {})
                drivers = api_response.get("drivers", [])
                logger.debug("[DRIVER_MDI] 檢測到單層結構")
            
            # 驗證數據
            if not isinstance(drivers, list):
                raise ValueError(f"API 數據缺少 'drivers' 列表，實際類型: {type(drivers)}")
            
            logger.debug(
                "[DRIVER_MDI] 載入 %s 位車手 | Metadata: season_year=%s, round=%s",
                len(drivers),
                metadata.get("season_year"),
                metadata.get("resolved_round"),
            )
            
            # 轉換為顯示格式 (Widget 期望的格式)
            display_data = {
                "standings": [],
                "season_year": metadata.get("season_year"),
                "round": metadata.get("resolved_round"),
                "metadata": metadata
            }
            
            for entry in drivers:
                display_data["standings"].append({
                    "position": entry.get("position"),
                    "driver_code": entry.get("driver", {}).get("code"),
                    "driver_name": entry.get("driver", {}).get("full_name"),
                    "team": entry.get("constructors", [{}])[0].get("name") if entry.get("constructors") else "N/A",
                    "points": entry.get("points"),
                    "wins": entry.get("wins"),
                    "points_delta": entry.get("points_delta")
                })
            
            logger.info(
                "[DRIVER_MDI] 轉換後數據: %s 位車手, 年份=%s, 輪次=%s",
                len(display_data["standings"]),
                display_data.get("season_year"),
                display_data.get("round"),
            )
            
            # 觸發載入完成處理
            self._on_data_loaded(display_data)
            
            # 更新狀態
            source_label = "API" if meta.get('source') == 'api' else meta.get('source', 'Unknown')
            self.status_label.setText(f"✅ 已從 {source_label} 載入資料")
            
        except Exception as e:
            logger.error("[DRIVER_MDI] API 數據處理失敗: %s", e, exc_info=True)
            self._on_api_failure(str(e))
    
    @pyqtSlot(str)
    def _on_api_failure(self, error_msg: str):
        """API 請求失敗 - 嘗試本地 JSON 備援"""
        logger.error("[DRIVER_MDI] API 調用失敗: %s", error_msg)
        self.status_label.setText(tr("api_failure_status", "API 失敗，嘗試本地檔案..."))
        
        # 備援：嘗試本地 JSON
        logger.warning("[DRIVER_MDI] 嘗試本地 JSON 備援")
        self.data_loader.load_data(force_refresh=False)
    
    @pyqtSlot(str)
    def _on_status_changed(self, message: str):
        """狀態變更處理"""
        self.status_label.setText(message)
    
    @pyqtSlot(int)
    def _on_progress_changed(self, value: int):
        """進度變更處理"""
        self.progress_bar.setValue(value)
    
    @pyqtSlot()
    def _on_load_started(self):
        """載入開始處理（已棄用，保留向後兼容）"""
        pass
    
    @pyqtSlot(dict)
    def _on_data_loaded(self, data: Dict[str, Any]):
        """
        載入完成處理
        
        Args:
            data: 轉換後的積分資料
        """
        logger.info("[DRIVER_MDI] 數據載入完成")
        
        # 填充表格
        self.standings_widget.populate_table(data)
        
        # 更新狀態
        num_drivers = len(data.get("standings", []))
        self.status_label.setText(tr("load_success_status", "載入成功 ({count} 位車手)").format(count=num_drivers))
        self.progress_bar.setValue(100)
        self.progress_bar.hide()
    
    @pyqtSlot(str)
    def _on_load_error(self, error_msg: str):
        """
        載入錯誤處理
        
        Args:
            error_msg: 錯誤訊息
        """
        logger.error("[DRIVER_MDI] 載入錯誤: %s", error_msg)
        self.status_label.setText(tr("load_error_status", "載入失敗: {error}").format(error=error_msg))
        self.progress_bar.setValue(0)
        self.progress_bar.hide()


# 測試代碼
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 測試 MDI 視窗
    mdi = DriverStandingsMDI(year="2024")
    mdi.setWindowTitle("車手積分榜測試")
    mdi.resize(1000, 700)
    mdi.show()
    
    sys.exit(app.exec_())
