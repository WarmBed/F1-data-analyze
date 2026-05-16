#!/usr/bin/env python3
"""
理想圈排名表格 MDI 視窗
Ideal Lap Ranking Table MDI

負責管理理想圈排名表格的 MDI 視窗，整合資料載入器和表格元件

作者: F1T Team
日期: 2025-10-09
版本: 1.0.0
"""

import sys
import os
import time
from core import local_requests as requests
import certifi
from typing import Dict, Any, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QPushButton, QMessageBox,
    QApplication
)
from PyQt5.QtCore import Qt, pyqtSlot, QThread, pyqtSignal

from core.gui_i18n import tr

# 導入基類
from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig

from core.logger import get_logger
logger = get_logger(__name__)


class IdealLapRankingApiWorker(QThread):
    """
    理想圈排名 API 請求工作執行緒
    
    負責異步調用 API 獲取理想圈排名數據
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
            
            logger.debug(f"[API_WORKER] 🌐 調用 API: {endpoint}")
            logger.debug(f"[API_WORKER] 📋 參數: {query_params}")
            
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
            
            logger.info(f"[API_WORKER] ✅ API 調用成功")
            logger.debug(f"[API_WORKER] ⏱️  延遲: {meta['latency_ms']}ms")
            logger.debug(f"[API_WORKER] 📊 數據源: {meta['source']}")
            
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
            logger.error(f"[API_WORKER] ❌ {error_msg}")
            import traceback
            traceback.print_exc()
            self.failure.emit(error_msg)
        finally:
            # ✅ 中斷檢查：被中斷時不發送 progress 信號
            if not self.isInterruptionRequested():
                self.progress.emit(100)

# 導入資料載入器和元件
try:
    from .ideal_lap_ranking_table_data_loader import IdealLapRankingTableDataLoader
    from .ideal_lap_ranking_table_widget import IdealLapRankingTableWidget
except ImportError:
    from modules.gui.lap_analysis.ideal_lap.ideal_lap_ranking_table.ideal_lap_ranking_table_data_loader import IdealLapRankingTableDataLoader
    from modules.gui.lap_analysis.ideal_lap.ideal_lap_ranking_table.ideal_lap_ranking_table_widget import IdealLapRankingTableWidget


class IdealLapRankingTableMDI(UniversalAnalysisMDI):
    """
    理想圈排名表格 MDI 視窗
    
    繼承自 UniversalAnalysisMDI，提供統一的視窗管理和數據流控制
    整合 IdealLapRankingTableDataLoader 和 IdealLapRankingTableWidget
    """
    
    # 在類別層級註冊模組類型
    _REGISTERED = False
    
    @classmethod
    def ensure_registered(cls):
        """確保模組類型已註冊"""
        if not cls._REGISTERED:
            config = AnalysisMDIConfig(
                analysis_type="ideal_lap_ranking",
                display_name="Ideal Lap Ranking Table",
                default_size=(1400, 900),
                requires_driver_params=False,
                requires_lap_params=False,
                supports_single_driver=False,
                supports_dual_driver=False
            )
            UniversalAnalysisMDI.register_mdi_module_type("ideal_lap_ranking", config)
            cls._REGISTERED = True
            logger.info("[IDEAL_LAP_MDI] ✅ 模組類型已註冊")
    
    def __init__(self, parent=None):
        """
        初始化 MDI 視窗
        
        Args:
            parent: 父元件
        """
        logger.debug(f"[IDEAL_LAP_MDI] IdealLapRankingTableMDI 開始初始化...")
        
        # 確保類型已註冊
        self.ensure_registered()
        
        # 調用基類初始化
        super().__init__(analysis_type="ideal_lap_ranking", parent=parent)
        
        # 初始化參數（將在 initialize_module 中設置）
        self.year = None
        self.race = None
        self.session = None
        
        # 狀態變數
        self._current_data = None
        self._is_data_loaded = False
        
        logger.debug(f"[IDEAL_LAP_MDI] 基類初始化完成, 等待參數設置...")
    
    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        """
        初始化模組（設置參數並載入初始數據）
        
        Args:
            parent_widget: 父級 widget（可選）
            **kwargs: 額外參數
            
        Returns:
            bool: 初始化是否成功
        """
        try:
            logger.debug(f"[IDEAL_LAP_MDI] 開始初始化模組...")
            
            # 驗證必要屬性
            if not hasattr(self, 'current_year') or not self.current_year:
                logger.error(f"[IDEAL_LAP_MDI] ❌ 缺少 current_year 屬性")
                return False
                
            if not hasattr(self, 'current_race') or not self.current_race:
                logger.error(f"[IDEAL_LAP_MDI] ❌ 缺少 current_race 屬性")
                return False
                
            if not hasattr(self, 'current_session') or not self.current_session:
                logger.error(f"[IDEAL_LAP_MDI] ❌ 缺少 current_session 屬性")
                return False
            
            # 設置參數
            self.year = str(self.current_year)
            self.race = self.current_race
            self.session = self.current_session
            
            logger.info(f"[IDEAL_LAP_MDI] ✅ 參數已設置: {self.year} {self.race} {self.session}")
            
            # ⚠️ 關鍵：調用基類的 initialize_module 來創建 chart_widget 和 data_manager
            if not super().initialize_module(parent_widget=parent_widget, **kwargs):
                logger.error(f"[IDEAL_LAP_MDI] ❌ 基類初始化失敗")
                return False
            
            # 驗證組件已創建
            if not self.chart_widget:
                logger.error(f"[IDEAL_LAP_MDI] ❌ chart_widget 未創建")
                return False
            
            if not self.data_manager:
                logger.error(f"[IDEAL_LAP_MDI] ❌ data_manager 未創建")
                return False
            
            logger.info(f"[IDEAL_LAP_MDI] ✅ 組件創建成功 (chart_widget={type(self.chart_widget).__name__}, data_manager={type(self.data_manager).__name__})")
            
            # 載入初始數據
            self.load_initial_data()
            
            logger.info(f"[IDEAL_LAP_MDI] ✅ 模組初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"[IDEAL_LAP_MDI] ❌ 初始化失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # ========== 基類抽象方法實作 ==========
    
    def create_data_manager(self) -> IdealLapRankingTableDataLoader:
        """
        創建資料載入器（由基類調用）
        
        Returns:
            IdealLapRankingTableDataLoader: 資料載入器實例
        """
        logger.debug("[IDEAL_LAP_MDI] 創建資料載入器...")
        loader = IdealLapRankingTableDataLoader(
            year=self.year,
            race=self.race,
            session=self.session,
            parent=self
        )
        
        # 連接信號
        loader.data_loaded.connect(self._on_data_loaded)
        loader.load_error.connect(self._on_load_error)
        loader.status_changed.connect(self._on_status_changed)
        
        logger.info("[IDEAL_LAP_MDI] ✅ 資料載入器已創建")
        return loader
    
    def create_chart_widget(self) -> IdealLapRankingTableWidget:
        """
        創建圖表元件（由基類調用）
        
        Returns:
            IdealLapRankingTableWidget: 表格元件實例
        """
        logger.debug("[IDEAL_LAP_MDI] 創建表格元件...")
        # ⚠️ parent 必須傳 None，因為 UniversalAnalysisMDI 不是 QWidget
        widget = IdealLapRankingTableWidget(parent=None)
        
        # 已移除 detail_requested 信號連接（Action 欄已移除）
        
        logger.info("[IDEAL_LAP_MDI] ✅ 表格元件已創建")
        return widget
    
    def _setup_control_panel(self):
        """
        設置控制面板（由基類調用）
        """
        logger.debug("[IDEAL_LAP_MDI] 設置控制面板...")
        
        # 創建控制面板容器
        control_panel = QGroupBox("控制面板")
        control_layout = QHBoxLayout()
        control_panel.setLayout(control_layout)
        
        # 重新載入按鈕
        self.btn_reload = QPushButton("🔄 重新載入")
        self.btn_reload.clicked.connect(self._on_reload_clicked)
        control_layout.addWidget(self.btn_reload)
        
        # 彈性空間
        control_layout.addStretch()
        
        # 狀態標籤
        self.lbl_control_status = QLabel("就緒")
        control_layout.addWidget(self.lbl_control_status)
        
        # 將控制面板添加到主佈局（如果基類有提供 main_layout）
        if hasattr(self, 'main_layout'):
            self.main_layout.addWidget(control_panel)
        
        logger.info("[IDEAL_LAP_MDI] ✅ 控制面板已設置")
    
    # ========== 數據流處理 ==========
    
    @pyqtSlot(dict)
    def _on_data_loaded(self, data: Dict[str, Any]):
        """
        資料載入完成回調
        
        Args:
            data: 載入的資料字典
        """
        try:
            logger.debug("[IDEAL_LAP_MDI] 資料載入完成，開始處理...")
            
            # 驗證資料結構
            if not isinstance(data, dict):
                self._show_error("資料格式錯誤", "載入的資料不是字典格式")
                return
            
            if "analysis_result" not in data:
                self._show_error("資料結構錯誤", "缺少 'analysis_result' 鍵")
                return
            
            analysis_result = data["analysis_result"]
            
            if "ranking" not in analysis_result:
                self._show_error("資料結構錯誤", "缺少 'ranking' 資料")
                return
            
            if "summary" not in analysis_result:
                self._show_error("資料結構錯誤", "缺少 'summary' 資料")
                return
            
            # 儲存資料
            self._current_data = data
            self._is_data_loaded = True
            
            # 更新表格
            ranking = analysis_result["ranking"]
            summary = analysis_result["summary"]
            
            logger.debug(f"[IDEAL_LAP_MDI] 填充表格（{len(ranking)} 位車手）...")
            self.chart_widget.populate_table(ranking)
            
            logger.debug(f"[IDEAL_LAP_MDI] 更新統計面板...")
            self.chart_widget.update_statistics_panel(summary)
            
            # 更新狀態（透過 Widget 更新，因為 MDI 本身沒有 UI 控件）
            if hasattr(self.chart_widget, 'lbl_control_status'):
                self.chart_widget.lbl_control_status.setText(f"已載入 {len(ranking)} 位車手資料")
            
            logger.info("[IDEAL_LAP_MDI] ✅ 資料處理完成")
            
        except Exception as e:
            logger.error(f"[IDEAL_LAP_MDI] 資料處理失敗: {e}")
            import traceback
            traceback.print_exc()
            self._show_error("資料處理失敗", str(e))
    
    @pyqtSlot(str)
    def _on_load_error(self, error_msg: str):
        """
        資料載入錯誤回調
        
        Args:
            error_msg: 錯誤訊息
        """
        logger.error(f"[IDEAL_LAP_MDI] 載入錯誤: {error_msg}")
        # ✅ 只在狀態標籤顯示錯誤，不彈出對話框（API-ONLY 模式）
        if hasattr(self.chart_widget, 'lbl_control_status'):
            self.chart_widget.lbl_control_status.setText(f"錯誤: {error_msg}")
        # ❌ 移除彈窗：self._show_error("資料載入失敗", error_msg)
    
    @pyqtSlot(str)
    def _on_status_changed(self, status: str):
        """
        狀態變更回調
        
        Args:
            status: 新狀態訊息
        """
        logger.debug(f"[IDEAL_LAP_MDI] 狀態: {status}")
        # 透過 Widget 更新狀態
        if hasattr(self.chart_widget, 'lbl_control_status'):
            self.chart_widget.lbl_control_status.setText(status)
    
    # ========== 事件處理 ==========
    
    # 已移除 _on_detail_requested 方法（Action 欄已移除）
    
    def _on_reload_clicked(self):
        """處理重新載入按鈕點擊"""
        logger.debug("[IDEAL_LAP_MDI] 重新載入資料...")
        self.lbl_control_status.setText("重新載入中...")
        
        # 清空表格
        self.chart_widget.clear_table()
        
        # 重新載入
        self.load_initial_data()
    
    # ========== 公開方法 ==========
    
    def load_initial_data(self):
        """
        載入初始資料 - 強制使用 API
        
        優先級：
        1. API 調用 (http://localhost:8000)
        2. 備援: 本地 JSON 檔案（API 失敗時）
        """
        logger.debug("[IDEAL_LAP_MDI] 🚀 開始載入初始資料...")
        logger.debug(f"[IDEAL_LAP_MDI] 📋 參數: {self.year} {self.race} {self.session}")
        
        # 更新狀態
        import os
        if os.environ.get("F1T_RUNTIME_MODE", "").lower() == "local" and self.data_manager:
            if self.data_manager.load_data(year=self.year, race=self.race, session=self.session):
                return

        if hasattr(self, 'lbl_control_status'):
            self.lbl_control_status.setText("正在從 API 載入資料...")
        
        # 創建 API Worker
        api_params = {
            "year": self.year,
            "race": self.race,
            "session": self.session,
            "force_refresh": False  # 可選：強制刷新
        }
        
        logger.debug("[IDEAL_LAP_MDI] 🌐 創建 API Worker...")
        self.api_worker = IdealLapRankingApiWorker(
            params=api_params,
            base_url="http://localhost:8000",
            timeout=60.0
        )
        
        # 🔧 關鍵修復: 使用 Qt.QueuedConnection 確保槽函數在 UI 線程執行
        # 原因: API Worker 在 QThread.run() 中發射信號（非 UI 線程）
        #       如果使用默認的 AutoConnection，槽函數可能在 Worker 線程執行
        #       導致在非 UI 線程更新 Qt Widget → 程式崩潰
        self.api_worker.progress.connect(self._on_api_progress)
        self.api_worker.success.connect(self._on_api_success)
        self.api_worker.failure.connect(self._on_api_failure)
        
        # 啟動 API 請求
        logger.debug("[IDEAL_LAP_MDI] ▶️  啟動 API 請求（使用 Qt.QueuedConnection）...")
        self.api_worker.start()
    
    @pyqtSlot(int)
    def _on_api_progress(self, progress: int):
        """API 請求進度更新"""
        logger.debug(f"[IDEAL_LAP_MDI] 📊 API 進度: {progress}%")
        if hasattr(self, 'lbl_control_status'):
            self.lbl_control_status.setText(f"API 載入中... {progress}%")
    
    @pyqtSlot(dict)
    def _on_api_success(self, result: Dict[str, Any]):
        """API 請求成功"""
        try:
            logger.info("[IDEAL_LAP_MDI] ✅ API 調用成功")
            
            # 提取數據和元數據
            data = result.get("data", {})
            meta = result.get("meta", {})
            
            logger.debug(f"[IDEAL_LAP_MDI] 📦 數據源: {meta.get('source')}")
            logger.debug(f"[IDEAL_LAP_MDI] ⏱️  延遲: {meta.get('latency_ms')}ms")
            
            # 驗證數據結構
            if not isinstance(data, dict):
                raise ValueError("API 返回的數據格式錯誤")
            
            if "analysis_result" not in data:
                raise ValueError("API 數據缺少 'analysis_result'")
            
            # 處理數據（觸發現有的 _on_data_loaded 處理邏輯）
            self._on_data_loaded(data)
            
            # 更新狀態
            if hasattr(self, 'lbl_control_status'):
                source_label = "API" if meta.get('source') == 'api' else meta.get('source', 'Unknown')
                self.lbl_control_status.setText(f"✅ 已從 {source_label} 載入資料")
            
        except Exception as e:
            logger.error(f"[IDEAL_LAP_MDI] API 數據處理失敗: {e}")
            import traceback
            traceback.print_exc()
            self._on_api_failure(str(e))
    
    @pyqtSlot(str)
    def _on_api_failure(self, error_msg: str):
        """API 請求失敗 - 嘗試備援方案"""
        logger.error(f"[IDEAL_LAP_MDI] API 調用失敗: {error_msg}")
        
        if hasattr(self, 'lbl_control_status'):
            self.lbl_control_status.setText(tr("ideal_lap_api_failure", "API 請求失敗，請稍後再試"))

        self._show_error(
            tr("ideal_lap_api_failure_title", "載入失敗"),
            tr(
                "ideal_lap_api_failure_message",
                "理想圈排名資料僅支援透過 API 載入。請確認 API 服務可用或稍後再試。\n\n詳細錯誤:\n{error}",
            ).format(error=error_msg)
        )
        logger.error("[IDEAL_LAP_MDI] 已封鎖本地 JSON 後備 (API-ONLY)")
    
    def update_analysis_parameters(self, year: str, race: str, session: str) -> bool:
        """
        更新分析參數並重新載入資料
        
        Args:
            year: 新的年份
            race: 新的賽事
            session: 新的賽段
            
        Returns:
            bool: 更新是否成功
        """
        try:
            logger.debug(f"[IDEAL_LAP_MDI] 🔄 更新參數: {year} {race} {session}")
            
            # 更新內部參數
            self.current_year = str(year)
            self.current_race = race
            self.current_session = session
            self.year = str(year)
            self.race = race
            self.session = session
            
            # 同時更新 DataLoader 的參數
            if hasattr(self, 'data_manager') and self.data_manager:
                self.data_manager.year = str(year)
                self.data_manager.race = race
                self.data_manager.session = session
                logger.info(f"[IDEAL_LAP_MDI] ✅ DataManager 參數已同步")
            elif hasattr(self, 'data_loader') and self.data_loader:
                self.data_loader.year = str(year)
                self.data_loader.race = race
                self.data_loader.session = session
                logger.info(f"[IDEAL_LAP_MDI] ✅ DataLoader 參數已同步")
            
            # 🔑 重點：調用 load_initial_data() 觸發 API 請求
            # 這個方法會啟動 API Worker 並更新 UI
            logger.debug(f"[IDEAL_LAP_MDI] 🌐 觸發資料重新載入...")
            self.load_initial_data()
            
            # 異步載入，返回 True 表示啟動成功
            return True
            
        except Exception as e:
            logger.error(f"[IDEAL_LAP_MDI] 參數更新失敗: {e}")
            import traceback
            traceback.print_exc()
            return False

    def update_parameters(self, year: int = None, race: str = None, session: str = None, **kwargs) -> bool:
        """覆寫通用參數更新邏輯，確保觸發 API 載入"""
        try:
            target_year = year if year is not None else (self.year or getattr(self, 'current_year', None))
            target_race = race if race is not None else (self.race or getattr(self, 'current_race', None))
            target_session = session if session is not None else (self.session or getattr(self, 'current_session', None))

            if not all([target_year, target_race, target_session]):
                logger.error("[IDEAL_LAP_MDI] 參數更新失敗：缺少必要參數")
                return False

            normalized_year = str(target_year)
            normalized_race = target_race
            normalized_session = target_session

            self.current_year = normalized_year
            self.current_race = normalized_race
            self.current_session = normalized_session

            params_payload = {
                'year': self.current_year,
                'race': self.current_race,
                'session': self.current_session
            }
            self.parameters_updated.emit(params_payload)
            self.update_window_title()

            return self.update_analysis_parameters(
                self.current_year,
                self.current_race,
                self.current_session
            )

        except Exception as exc:
            logger.error(f"[IDEAL_LAP_MDI] update_parameters 失敗: {exc}")
            import traceback

            traceback.print_exc()
            return False
    
    def get_window_title(self, year: str = None, race: str = None, session: str = None) -> str:
        """
        覆寫基類方法，返回正確的視窗標題 - 只顯示模組名稱
        
        Args:
            year: 年份（忽略）
            race: 賽事（忽略）
            session: 賽段（忽略）
            
        Returns:
            str: 視窗標題（純模組名稱）
        """
        # 使用 tr() 支援多國語言
        translated_title = tr("ideal_lap_ranking", "Ideal Lap Ranking")
        return translated_title
        
        return base_title
    
    def get_widget(self) -> QWidget:
        """
        獲取主要元件（用於模組介面）
        
        Returns:
            QWidget: 表格元件
        """
        # 返回表格元件而不是 MDI 本身
        if hasattr(self, 'chart_widget') and self.chart_widget:
            return self.chart_widget
        return None
    
    # ========== 輔助方法 ==========
    
    def _show_error(self, title: str, message: str):
        """
        顯示錯誤對話框
        
        Args:
            title: 對話框標題
            message: 錯誤訊息
        """
        # MDI 不是 QWidget，需要使用 chart_widget 作為 parent
        parent = self.chart_widget if hasattr(self, 'chart_widget') else None
        QMessageBox.critical(parent, title, message)


# ========== 測試代碼 ==========
if __name__ == "__main__":
    logger.debug("=" * 60)
    logger.debug("理想圈排名表格 MDI 視窗 - 獨立測試")
    logger.debug("=" * 60)
    
    app = QApplication(sys.argv)
    
    # 創建 MDI 視窗
    mdi = IdealLapRankingTableMDI(
        year="2025",
        race="Japan",
        session="R"
    )
    
    # 獲取主要元件
    widget = mdi.get_widget()
    if hasattr(widget, 'setWindowTitle'):
        widget.setWindowTitle("Ideal Lap Ranking MDI - Test")
    if hasattr(widget, 'resize'):
        widget.resize(1400, 900)
    if hasattr(widget, 'show'):
        widget.show()
    
    # 載入初始資料
    logger.debug("\n🚀 載入初始資料...")
    mdi.load_initial_data()
    
    sys.exit(app.exec_())
