#!/usr/bin/env python3
"""
Ideal Lap Sector Heatmap MDI
============================

UI orchestration for the sector heatmap module.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import time
import requests
import certifi

import pandas as pd

from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QThread
from PyQt5.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from modules.gui.base.universal_analysis_mdi_base import (
    AnalysisMDIConfig,
    UniversalAnalysisMDI,
)
from core.gui_i18n import tr

from .ideal_lap_sector_heatmap_data_loader import IdealLapSectorHeatmapDataLoader
from .ideal_lap_sector_heatmap_widget import IdealLapSectorHeatmapWidget

from core.logger import get_logger
logger = get_logger(__name__)


# ========================================================================
# API Worker 類別（與 ranking_table 一致）
# ========================================================================

class IdealLapSectorHeatmapApiWorker(QThread):
    """
    理想圈分段熱力圖 API 請求工作執行緒
    
    負責異步調用 API 獲取理想圈排名數據（Function 53）
    API 端點: POST /api/v2/analysis/execute?function_id=53
    """
    
    # 信號
    progress = pyqtSignal(int)  # 進度 (0-100)
    success = pyqtSignal(dict)  # 成功 (返回數據)
    failure = pyqtSignal(str)   # 失敗 (錯誤訊息)
    
    def __init__(self, params: Dict[str, Any], base_url: str = None, timeout: float = 60.0):
        """
        初始化 API Worker
        
        Args:
            params: API 參數 (year, race, session, etc.)
            base_url: API 基礎 URL (預設: http://localhost:8000)
            timeout: 請求超時時間（秒）
        """
        super().__init__()
        self.base_url = (base_url or "http://localhost:8000").rstrip('/')
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
                "function_id": 53,  # CLI Function 53 - Ideal Lap Ranking
                "year": int(self.params.get("year")),
                "race": self.params.get("race"),
                "session": self.params.get("session"),
            }
            
            # 強制刷新（可選）
            if self.params.get("force_refresh"):
                query_params["force_refresh"] = True
            
            logger.debug(f"[HEATMAP_API_WORKER] 🌐 調用 API: {endpoint}")
            logger.debug(f"[HEATMAP_API_WORKER] 📋 參數: {query_params}")
            
            # ✅ 中斷檢查點 2: HTTP 請求前
            if self.isInterruptionRequested():
                return
            
            # 發送 POST 請求
            start_ts = time.perf_counter()
            response = requests.post(
                endpoint,
                params=query_params,
                timeout=self.timeout,
                headers={"Accept": "application/json"},
                verify=certifi.where()  # ✅ SSL證書（EXE必須）
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
                "function_spec": payload.get("function_spec"),
                "latency_ms": round(latency_ms, 2),
                "base_url": self.base_url,
            }
            
            logger.info(f"[HEATMAP_API_WORKER] ✅ API 調用成功")
            logger.debug(f"[HEATMAP_API_WORKER] ⏱️  延遲: {meta['latency_ms']}ms")
            logger.debug(f"[HEATMAP_API_WORKER] 📊 數據源: {meta['source']}")
            
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
            logger.error(f"[HEATMAP_API_WORKER] ❌ {error_msg}")
            import traceback
            traceback.print_exc()
            self.failure.emit(error_msg)
        finally:
            # ✅ 中斷檢查：被中斷時不發送 progress 信號
            if not self.isInterruptionRequested():
                self.progress.emit(100)


# ========================================================================
# 控制面板（已隱藏，保留以備將來使用）
# ========================================================================


class SectorHeatmapControlPanel(QWidget):
    """
    Top-level control bar for sorting and highlight toggles.
    """

    sort_requested = pyqtSignal(str)
    reload_requested = pyqtSignal()
    highlight_option_changed = pyqtSignal(bool, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(10)

        title = QLabel(tr("sector_heatmap_controls", "Sector Heatmap Controls:"))
        title.setStyleSheet("font-weight: bold;")
        layout.addWidget(title)

        self.status_label = QLabel(tr("ready", "Ready"))
        self.status_label.setStyleSheet("color: #2196F3;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        sort_group = QGroupBox(tr("sort_by", "Sort by"))
        sort_layout = QHBoxLayout(sort_group)
        sort_layout.setContentsMargins(6, 4, 6, 4)

        btn_default = QPushButton(tr("ranking_order", "Ranking Order"))
        btn_default.clicked.connect(lambda: self.sort_requested.emit("ranking"))
        sort_layout.addWidget(btn_default)

        btn_total = QPushButton(tr("total_time", "Total Time"))
        btn_total.clicked.connect(lambda: self.sort_requested.emit("total"))
        sort_layout.addWidget(btn_total)

        btn_s1 = QPushButton("S1")
        btn_s1.clicked.connect(lambda: self.sort_requested.emit("S1"))
        sort_layout.addWidget(btn_s1)

        btn_s2 = QPushButton("S2")
        btn_s2.clicked.connect(lambda: self.sort_requested.emit("S2"))
        sort_layout.addWidget(btn_s2)

        btn_s3 = QPushButton("S3")
        btn_s3.clicked.connect(lambda: self.sort_requested.emit("S3"))
        sort_layout.addWidget(btn_s3)

        layout.addWidget(sort_group)

        highlight_group = QGroupBox(tr("highlights", "Highlights"))
        highlight_layout = QHBoxLayout(highlight_group)
        highlight_layout.setContentsMargins(6, 4, 6, 4)

        self.chk_fastest = QCheckBox(tr("show_global_fastest", "Show Global Fastest"))
        self.chk_fastest.setChecked(True)
        self.chk_fastest.toggled.connect(self._emit_highlight_change)
        highlight_layout.addWidget(self.chk_fastest)

        self.chk_personal = QCheckBox(tr("show_driver_personal_best", "Show Driver Personal Best"))
        self.chk_personal.setChecked(False)
        self.chk_personal.toggled.connect(self._emit_highlight_change)
        highlight_layout.addWidget(self.chk_personal)

        layout.addWidget(highlight_group)

        reload_btn = QPushButton(tr("reload", "Reload"))
        reload_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; padding: 6px 14px; }"
            "QPushButton:hover { background-color: #43A047; }"
        )
        reload_btn.clicked.connect(self.reload_requested.emit)
        layout.addWidget(reload_btn)

    def _emit_highlight_change(self) -> None:
        self.highlight_option_changed.emit(
            self.chk_fastest.isChecked(), self.chk_personal.isChecked()
        )

    def update_status(self, text: str, color: str = "#2196F3") -> None:
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color};")


class SectorHeatmapStatsPanel(QGroupBox):
    """
    Display summary metrics derived from the sector comparison block.
    """

    def __init__(self, parent=None):
        super().__init__(tr("sector_statistics", "Sector Statistics"), parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        self.table = QTableWidget(3, 5, self)
        self.table.setHorizontalHeaderLabels([
            tr("sector", "Sector"),
            tr("fastest", "Fastest"),
            tr("slowest", "Slowest"),
            tr("average", "Average"),
            tr("range", "Range")
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        layout.addWidget(self.table)

    def update_stats(self, summary: Dict[str, Dict[str, Any]]) -> None:
        sectors = ["S1", "S2", "S3"]
        for row_idx, sector in enumerate(sectors):
            info = summary.get(sector, {}) or {}

            fastest_driver = info.get("fastest_driver") or "-"
            fastest_time = info.get("fastest_time")
            fastest_text = (
                f"{fastest_driver} ({fastest_time:.3f}s)"
                if fastest_time is not None
                else "-"
            )

            slowest_driver = info.get("slowest_driver") or "-"
            slowest_time = info.get("slowest_time")
            slowest_text = (
                f"{slowest_driver} ({slowest_time:.3f}s)"
                if slowest_time is not None
                else "-"
            )

            average_time = info.get("average_time")
            average_text = (
                f"{average_time:.3f}s" if average_time is not None else "-"
            )

            range_time = info.get("range")
            range_percentage = info.get("range_percentage")
            if range_time is not None:
                if range_percentage is not None:
                    range_text = f"{range_time:.3f}s ({range_percentage:.2f}%)"
                else:
                    range_text = f"{range_time:.3f}s"
            else:
                range_text = "-"

            values = [
                sector,
                fastest_text,
                slowest_text,
                average_text,
                range_text,
            ]

            for col_idx, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_idx, col_idx, item)


class IdealLapSectorHeatmapMDI(UniversalAnalysisMDI):
    """
    MDI orchestrator capturing data loader, widget, control panel, and stats.
    """

    _REGISTERED = False

    @classmethod
    def ensure_registered(cls) -> None:
        if cls._REGISTERED:
            return

        config = AnalysisMDIConfig(
            analysis_type="ideal_lap_sector_heatmap",
            display_name=tr("ideal_lap_sector_heatmap", "Ideal Lap Sector Heatmap"),
            default_size=(1280, 860),
            requires_driver_params=False,
            requires_lap_params=False,
            supports_single_driver=False,
            supports_dual_driver=False,
        )
        UniversalAnalysisMDI.register_mdi_module_type(
            "ideal_lap_sector_heatmap", config
        )
        cls._REGISTERED = True

    def __init__(self, parent=None):
        self.ensure_registered()
        super().__init__(analysis_type="ideal_lap_sector_heatmap", parent=parent)

        self.control_panel: Optional[SectorHeatmapControlPanel] = None
        self.stats_panel: Optional[SectorHeatmapStatsPanel] = None
        self._last_payload: Optional[Dict[str, Any]] = None
        self._current_sort_mode: str = "ranking"
        self.api_worker: Optional[IdealLapSectorHeatmapApiWorker] = None

    # ------------------------------------------------------------------ #
    # UniversalAnalysisMDI overrides
    # ------------------------------------------------------------------ #
    def create_data_manager(self):
        # ⚠️ parent 必須傳 None，因為 UniversalAnalysisMDI 不是 QWidget
        return IdealLapSectorHeatmapDataLoader(
            year=self.current_year,
            race=self.current_race,
            session=self.current_session,
            parent=None,
        )

    def create_chart_widget(self):
        # ⚠️ parent 必須傳 None，因為 UniversalAnalysisMDI 不是 QWidget
        widget = IdealLapSectorHeatmapWidget(parent=None)
        widget.cell_clicked.connect(self._handle_cell_click)
        return widget

    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        """
        初始化模組 - 覆寫基類方法以添加 API 數據載入
        
        ⚠️ 關鍵：必須覆寫此方法才能觸發 load_initial_data()
        參考實現：ideal_lap_ranking_table, ideal_lap_sector_comparison
        
        流程:
        1. 調用基類 initialize_module() 創建 chart_widget 和 data_manager
        2. 驗證組件創建成功
        3. 調用 load_initial_data() 觸發 API 請求
        """
        try:
            self._debug("========== 開始初始化模組 ==========")
            
            # ⚠️ 關鍵：調用基類的 initialize_module 來創建 chart_widget 和 data_manager
            if not super().initialize_module(parent_widget=parent_widget, **kwargs):
                self._debug("❌ 基類初始化失敗")
                return False
            
            # 驗證組件已創建
            if not self.chart_widget:
                self._debug("❌ chart_widget 未創建")
                return False
            
            if not self.data_manager:
                self._debug("❌ data_manager 未創建")
                return False
            
            self._debug(f"✅ 組件創建成功 (chart_widget={type(self.chart_widget).__name__}, data_manager={type(self.data_manager).__name__})")
            
            # 🔑 關鍵：調用 load_initial_data() 觸發 API 請求
            self._debug("🚀 準備載入初始數據...")
            self.load_initial_data()
            
            self._debug("✅ 模組初始化完成")
            return True
            
        except Exception as e:
            self._debug(f"❌ 初始化失敗: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_window_title(self, year: str = None, race: str = None, session: str = None) -> str:
        """
        生成視窗標題 - 只顯示模組名稱，不包含年份/賽事/賽段
        
        Args:
            year: 年份（忽略）
            race: 賽事（忽略）
            session: 賽段（忽略）
            
        Returns:
            str: 模組名稱標題
        """
        # 導入翻譯函數
        from core.gui_i18n import tr
        
        # 使用 tr() 支持多國語言
        translated_title = tr("ideal_lap_sector_heatmap", "Ideal Lap Sector Heatmap")
        
        # 返回純模組名稱
        return translated_title

    def load_initial_data(self):
        """
        載入初始資料 - 強制使用 API (API-ONLY 模式)
        
        ⚠️ 覆寫基類方法：直接調用 API Worker，不使用 UniversalDataLoader.load_data()
        此模式與 ideal_lap_ranking_table 保持一致
        """
        self._debug("🌐 [API-ONLY] 開始 API 請求...")

        self._stop_api_worker()
        self._sync_loader_parameters()
        
        # 構建 API 參數
        api_params = {
            "year": self.current_year,
            "race": self.current_race,
            "session": self.current_session
        }
        
        # 創建 API Worker
        base_url = "http://localhost:8000"
        timeout = 60
        
        self.api_worker = IdealLapSectorHeatmapApiWorker(
            params=api_params,
            base_url=base_url,
            timeout=timeout
        )
        
        # 連接信號
        self.api_worker.progress.connect(self._on_api_progress)
        self.api_worker.success.connect(self._on_api_success)
        self.api_worker.failure.connect(self._on_api_failure)
        self.api_worker.finished.connect(self._on_api_finished)
        
        # 啟動 API 請求
        self.api_worker.start()
        
        self._debug("✅ [API-ONLY] API Worker 已啟動")

    def _sync_loader_parameters(self) -> None:
        if not self.data_manager:
            return

        if hasattr(self.data_manager, "year"):
            self.data_manager.year = str(self.current_year)
        if hasattr(self.data_manager, "race"):
            self.data_manager.race = self.current_race
        if hasattr(self.data_manager, "session"):
            self.data_manager.session = self.current_session

    def _stop_api_worker(self) -> None:
        """
        異步停止 API Worker（方案 2: 信號驅動清理）
        ✅ 不阻塞主線程
        ✅ 使用信號自動清理
        """
        worker = getattr(self, "api_worker", None)
        if not worker:
            return

        # 1. 斷開所有信號（防止意外觸發）
        try:
            worker.progress.disconnect(self._on_api_progress)
        except (TypeError, RuntimeError):
            pass
        try:
            worker.success.disconnect(self._on_api_success)
        except (TypeError, RuntimeError):
            pass
        try:
            worker.failure.disconnect(self._on_api_failure)
        except (TypeError, RuntimeError):
            pass
        try:
            worker.finished.disconnect(self._on_api_finished)
        except (TypeError, RuntimeError):
            pass

        if worker.isRunning():
            # 2. 請求中斷（非阻塞）
            worker.requestInterruption()
            worker.quit()
            
            # 3. 使用信號自動清理（當 Worker 停止時）
            def on_worker_stopped():
                """Worker 停止後自動清理"""
                if worker:
                    worker.deleteLater()
                self.api_worker = None
            
            worker.finished.connect(on_worker_stopped)
            
            # 4. 延遲強制終止（15 秒後，但不阻塞主線程）
            from PyQt5.QtCore import QTimer
            def force_terminate():
                # ✅ 安全檢查：確保 worker 仍然有效且未被刪除
                try:
                    if worker and worker.isRunning():
                        logger.warning("ideal_lap_heatmap API Worker 未在 15 秒內停止，強制終止")
                        worker.terminate()
                except (RuntimeError, AttributeError):
                    # Worker 已被刪除，無需處理
                    pass
            
            QTimer.singleShot(15000, force_terminate)
        else:
            # Worker 已停止，立即清理
            worker.deleteLater()
            self.api_worker = None

    def _on_api_finished(self) -> None:
        """API Worker 完成後的回調（保留用於其他用途）"""
        # 注意：清理邏輯已移至 _stop_api_worker 的信號處理
        pass

    def _setup_ui(self):
        """
        Simplified layout: only display the heatmap widget.
        Control panel and statistics panel are hidden per user request.
        """
        self.main_widget = QWidget()
        root_layout = QVBoxLayout(self.main_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ❌ 隱藏控制面板（用戶要求）
        # self.control_panel = SectorHeatmapControlPanel()
        self.control_panel = None

        # ✅ 只顯示圖表
        root_layout.addWidget(self.chart_widget)

        # ❌ 隱藏統計面板（用戶要求）
        # self.stats_panel = SectorHeatmapStatsPanel()
        self.stats_panel = None

    def _update_chart(self, data: dict):
        """
        Extend base behaviour to keep local payload.
        Control panel and stats panel updates removed (panels hidden).
        """
        super()._update_chart(data)

        if not isinstance(data, dict):
            return

        self._last_payload = data
        
        # ❌ 移除面板更新（面板已隱藏）
        # summary = data.get("sector_summary", {}) or {}
        # if self.control_panel:
        #     self.control_panel.update_status("Data loaded", "#4CAF50")
        # if self.stats_panel:
        #     self.stats_panel.update_stats(summary)

        # Reapply ranking order (no sorting options since control panel is hidden)
        self._apply_sort(self._current_sort_mode, emit_status=False, redraw_only=True)

    # ------------------------------------------------------------------ #
    # API 回調處理器 (API-ONLY 模式)
    # ------------------------------------------------------------------ #
    @pyqtSlot(int)
    def _on_api_progress(self, progress: int):
        """API 請求進度更新"""
        self._debug(f"📊 [API] 進度: {progress}%")
    
    @pyqtSlot(dict)
    def _on_api_success(self, result: dict):
        """
        API 請求成功回調
        
        處理流程:
        1. 提取 API 響應中的數據（完整 data 對象）
        2. 使用 DataLoader 轉換為 DataFrame 格式
        3. 調用 widget.set_data() 顯示熱力圖
        
        ⚠️ 注意：必須傳遞完整的 data 對象（包含 analysis_result 鍵）
        參考實現：ideal_lap_ranking_table._on_api_success
        """
        self._debug("✅ [API] 請求成功，開始處理數據...")
        
        try:
            # 提取完整 data 對象（包含 analysis_result）
            if "data" not in result:
                raise ValueError("API 響應格式錯誤：缺少 'data' 鍵")
            
            data = result["data"]  # ✅ 完整 data 對象
            
            # 驗證數據結構
            if "analysis_result" not in data:
                raise ValueError("API 數據缺少 'analysis_result'")
            
            # 使用 DataLoader 轉換數據格式
            # ⚠️ 必須傳遞完整 data 對象，因為 _transform_data_for_display 需要 data["analysis_result"]
            payload = self.data_manager._transform_data_for_display(data)
            
            if not payload:
                raise ValueError("數據轉換失敗：payload 為空")
            
            # 更新圖表
            self._last_payload = payload
            self.chart_widget.set_data(payload)
            
            # 應用預設排序（ranking 模式）
            self._apply_sort("ranking", emit_status=False, redraw_only=True)
            
            self._debug("🎉 [API] 數據載入完成！")
            
        except Exception as e:
            error_msg = f"API 數據處理失敗: {str(e)}"
            self._debug(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            self._on_api_failure(error_msg)
    
    @pyqtSlot(str)
    def _on_api_failure(self, error: str):
        """
        API 請求失敗回調
        
        錯誤處理:
        1. 顯示錯誤訊息
        2. 嘗試讀取本地 JSON 備援（如果存在）
        """
        self._debug(f"❌ [API] 請求失敗: {error}")
        
        # 嘗試本地 JSON 備援
        try:
            self._debug("🔍 [FALLBACK] 嘗試讀取本地 JSON...")
            
            json_files = self.data_manager._search_json_files(
                year=self.current_year,
                race=self.current_race,
                session=self.current_session
            )
            
            if json_files:
                self._debug(f"📁 [FALLBACK] 找到本地檔案: {json_files[0]}")
                raw_data = self.data_manager._load_json_data(json_files[0])
                
                if raw_data:
                    payload = self.data_manager._transform_data_for_display(raw_data)
                    self._last_payload = payload
                    self.chart_widget.set_data(payload)
                    self._apply_sort("ranking", emit_status=False, redraw_only=True)
                    self._debug("✅ [FALLBACK] 本地數據載入成功")
                    return
            
            # 無備援數據
            self._show_error(
                tr("api_error", "API 錯誤"),
                tr("api_failure_no_fallback", f"API 請求失敗且無本地備援數據\n\n錯誤: {error}")
            )
            
        except Exception as fallback_error:
            self._debug(f"❌ [FALLBACK] 本地數據載入也失敗: {str(fallback_error)}")
            self._show_error(
                tr("data_error", "數據錯誤"),
                tr("all_sources_failed", f"所有數據源均失敗\n\nAPI: {error}\n本地: {str(fallback_error)}")
            )
    
    def _show_error(self, title: str, message: str):
        """顯示錯誤對話框"""
        from PyQt5.QtWidgets import QMessageBox

        parent = self.chart_widget if hasattr(self, 'chart_widget') else None
        QMessageBox.critical(parent, title, message)
    
    def _debug(self, message: str):
        """調試輸出"""
        logger.debug(f"[HEATMAP_MDI] {message}")

    # ------------------------------------------------------------------ #
    # Event handlers / helpers
    # ------------------------------------------------------------------ #
    def _apply_sort(
        self,
        mode: str,
        *,
        emit_status: bool = True,
        redraw_only: bool = False,
    ) -> None:
        if not self.chart_widget or not self._last_payload:
            return

        matrix = self._last_payload.get("sector_matrix")
        if not isinstance(matrix, (pd.DataFrame,)):
            return

        df: pd.DataFrame = matrix.copy()
        order: List[str]

        if mode == "total":
            totals = df.sum(axis=0, skipna=True)
            order = totals.sort_values(ascending=True).index.tolist()
        elif mode in {"S1", "S2", "S3"}:
            if mode in df.index:
                order = (
                    df.loc[mode]
                    .dropna()
                    .sort_values(ascending=True)
                    .index.tolist()
                )
            else:
                order = list(df.columns)
        else:
            order = self._last_payload.get("driver_order", list(df.columns))
            mode = "ranking"

        if not order:
            order = list(df.columns)

        self._current_sort_mode = mode
        self.chart_widget.render_heatmap(order)

        # ❌ 移除狀態更新（控制面板已隱藏）
        # if emit_status and self.control_panel:
        #     label = {...}.get(mode, "Custom order")
        #     self.control_panel.update_status(f"Order: {label}")

    def _apply_highlight_options(self, fastest: bool, personal: bool) -> None:
        if not self.chart_widget:
            return
        self.chart_widget.set_highlight_options(
            show_global_fastest=fastest, show_personal_best=personal
        )

    def _handle_cell_click(self, driver: str, sector: str) -> None:
        # ❌ 移除點擊處理（控制面板已隱藏）
        # if not self.control_panel:
        #     return
        # self.control_panel.update_status(...)
        pass

    def _load_data_with_current_parameters(self):
        if getattr(self, "_cleanup_performed", False):
            self._debug("🛑 模組已釋放，略過數據載入")
            return

        self._debug(
            f"🌐 [API-ONLY] 重新載入參數: {self.current_year} {self.current_race} {self.current_session}"
        )

        self._sync_loader_parameters()
        self.load_initial_data()

    def cleanup(self):
        self._stop_api_worker()
        super().cleanup()
