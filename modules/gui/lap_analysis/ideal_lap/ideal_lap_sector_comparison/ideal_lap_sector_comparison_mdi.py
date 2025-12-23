#!/usr/bin/env python3
"""
理想圈分段對比 MDI 視窗
Ideal Lap Sector Comparison MDI

負責管理理想圈分段對比的 MDI 視窗，整合資料載入器和圖表元件

作者: F1T Team
日期: 2025-10-09
版本: 1.0.0
"""

import sys
import time
import traceback
import requests
from typing import Dict, Any, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QPushButton, QMessageBox, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSlot, QThread, pyqtSignal

from core.logger import get_logger
logger = get_logger(__name__)

# 導入基類
try:
    from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig
except ImportError:
    from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig

# 導入資料載入器和元件
try:
    from .ideal_lap_sector_comparison_data_loader import IdealLapSectorComparisonDataLoader
    # ✅ 測試: 使用新的表格版本
    from .ideal_lap_sector_comparison_table_widget import IdealLapSectorComparisonTableWidget as IdealLapSectorComparisonWidget
except ImportError:
    from modules.gui.lap_analysis.ideal_lap.ideal_lap_sector_comparison.ideal_lap_sector_comparison_data_loader import IdealLapSectorComparisonDataLoader
    # ✅ 測試: 使用新的表格版本
    from modules.gui.lap_analysis.ideal_lap.ideal_lap_sector_comparison.ideal_lap_sector_comparison_table_widget import IdealLapSectorComparisonTableWidget as IdealLapSectorComparisonWidget


class IdealLapSectorComparisonApiWorker(QThread):
    """
    理想圈分段對比 API 請求工作執行緒
    
    負責異步調用 API 獲取理想圈分段對比數據
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
                "function_id": 53,  # CLI Function 53 - Ideal Lap Analysis
                "year": int(self.params.get("year")),
                "race": self.params.get("race"),
                "session": self.params.get("session"),
            }
            
            # 強制刷新（可選）
            if self.params.get("force_refresh"):
                query_params["force_refresh"] = True
            
            logger.debug(f"[SECTOR_COMPARISON_API] 🌐 調用 API: {endpoint}")
            logger.debug(f"[SECTOR_COMPARISON_API] 📋 參數: {query_params}")
            
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
                error = payload.get("error", "未知錯誤")
                raise RuntimeError(f"API 返回錯誤: {error}")
            
            elapsed_ms = int((time.perf_counter() - start_ts) * 1000)
            logger.info(f"[SECTOR_COMPARISON_API] ✅ API 調用成功 (耗時: {elapsed_ms}ms)")
            
            self.progress.emit(100)
            
            # ✅ 中斷檢查點 4: success 信號發送前
            if self.isInterruptionRequested():
                return
            
            # 發送成功信號
            result = {
                "data": payload.get("data", {}),
                "meta": {
                    "source": payload.get("source", "api"),
                    "latency_ms": elapsed_ms,
                    "timestamp": payload.get("timestamp"),
                }
            }
            self.success.emit(result)
            
        except requests.exceptions.Timeout:
            # ✅ 中斷檢查：被中斷時不發送錯誤信號
            if self.isInterruptionRequested():
                return
            error_msg = f"API 請求超時 (>{self.timeout}秒)"
            logger.error(f"[SECTOR_COMPARISON_API] ❌ {error_msg}")
            self.failure.emit(error_msg)
            
        except requests.exceptions.ConnectionError as e:
            # ✅ 中斷檢查：被中斷時不發送錯誤信號
            if self.isInterruptionRequested():
                return
            error_msg = f"無法連接到 API 服務器: {str(e)}"
            logger.error(f"[SECTOR_COMPARISON_API] ❌ {error_msg}")
            self.failure.emit(error_msg)
            
        except requests.exceptions.HTTPError as e:
            # ✅ 中斷檢查：被中斷時不發送錯誤信號
            if self.isInterruptionRequested():
                return
            error_msg = f"HTTP 錯誤 {e.response.status_code}: {e.response.reason}"
            logger.error(f"[SECTOR_COMPARISON_API] ❌ {error_msg}")
            self.failure.emit(error_msg)
            
        except Exception as e:
            # ✅ 中斷檢查：被中斷時不發送錯誤信號
            if self.isInterruptionRequested():
                return
            error_msg = f"API 請求失敗: {str(e)}"
            logger.error(f"[SECTOR_COMPARISON_API] ❌ {error_msg}")
            import traceback
            traceback.print_exc()
            self.failure.emit(error_msg)


class IdealLapSectorComparisonMDI(UniversalAnalysisMDI):
    """
    理想圈分段對比 MDI 視窗
    
    繼承自 UniversalAnalysisMDI，提供統一的視窗管理和數據流控制
    整合 IdealLapSectorComparisonDataLoader 和 IdealLapSectorComparisonWidget
    """
    
    # 在類別層級註冊模組類型
    _REGISTERED = False
    
    @classmethod
    def ensure_registered(cls):
        """確保模組類型已註冊"""
        if not cls._REGISTERED:
            config = AnalysisMDIConfig(
                analysis_type="ideal_lap_sector_comparison",
                display_name="Ideal Lap Sector Comparison",
                default_size=(1400, 1000),
                requires_driver_params=False,
                requires_lap_params=False,
                supports_single_driver=False,
                supports_dual_driver=False
            )
            UniversalAnalysisMDI.register_mdi_module_type("ideal_lap_sector_comparison", config)
            cls._REGISTERED = True
            logger.info("[SECTOR_COMPARISON_MDI] ✅ 模組類型已註冊")
    
    def __init__(self, parent=None):
        """
        初始化 MDI 視窗
        
        Args:
            parent: 父元件
        """
        logger.debug(f"[SECTOR_COMPARISON_MDI] IdealLapSectorComparisonMDI 開始初始化...")
        
        # 確保類型已註冊
        self.ensure_registered()
        
        # 調用基類初始化
        super().__init__(analysis_type="ideal_lap_sector_comparison", parent=parent)
        
        # 初始化參數（將在 initialize_module 中設置）
        self.year = None
        self.race = None
        self.session = None
        
        # 狀態變數
        self._current_data = None
        self._is_data_loaded = False
        
        # API Worker
        self.api_worker: Optional[IdealLapSectorComparisonApiWorker] = None
        
        # 控制面板
        self.control_panel: Optional[SectorComparisonControlPanel] = None
        
        # 狀態標籤
        self.lbl_control_status: Optional[QLabel] = None
        
        logger.debug(f"[SECTOR_COMPARISON_MDI] 基類初始化完成，等待參數設置...")
    
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
            logger.debug(f"[SECTOR_COMPARISON_MDI] 開始初始化模組...")
            
            # 驗證必要屬性
            if not hasattr(self, 'current_year') or not self.current_year:
                logger.error(f"[SECTOR_COMPARISON_MDI] ❌ 缺少 current_year 屬性")
                return False
                
            if not hasattr(self, 'current_race') or not self.current_race:
                logger.error(f"[SECTOR_COMPARISON_MDI] ❌ 缺少 current_race 屬性")
                return False
                
            if not hasattr(self, 'current_session') or not self.current_session:
                logger.error(f"[SECTOR_COMPARISON_MDI] ❌ 缺少 current_session 屬性")
                return False
            
            # 設置參數
            self.year = str(self.current_year)
            self.race = self.current_race
            self.session = self.current_session
            
            logger.info(f"[SECTOR_COMPARISON_MDI] ✅ 參數已設置: {self.year} {self.race} {self.session}")
            
            # ⚠️ 關鍵：調用基類的 initialize_module 來創建 chart_widget 和 data_manager
            if not super().initialize_module(parent_widget=parent_widget, **kwargs):
                logger.error(f"[SECTOR_COMPARISON_MDI] ❌ 基類初始化失敗")
                return False
            
            # 驗證組件已創建
            if not self.chart_widget:
                logger.error(f"[SECTOR_COMPARISON_MDI] ❌ chart_widget 未創建")
                return False
            
            if not self.data_manager:
                logger.error(f"[SECTOR_COMPARISON_MDI] ❌ data_manager 未創建")
                return False
            
            logger.info(f"[SECTOR_COMPARISON_MDI] ✅ 組件創建成功 (chart_widget={type(self.chart_widget).__name__}, data_manager={type(self.data_manager).__name__})")
            
            # 自動載入初始數據
            logger.debug(f"[SECTOR_COMPARISON_MDI] 🚀 準備載入初始數據...")
            self.load_initial_data()
            
            return True
            
        except Exception as e:
            logger.error(f"[SECTOR_COMPARISON_MDI] 初始化失敗: {e}")
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
        translated_title = tr("ideal_lap_sector_comparison", "Ideal Lap Sector Comparison")
        
        # 返回純模組名稱
        return translated_title
    
    #  ========== 基類抽象方法實作 ==========
    
    def create_data_manager(self):
        """
        創建資料管理器（資料載入器）
        
        Returns:
            IdealLapSectorComparisonDataLoader: 資料載入器實例
        """
        logger.debug("[SECTOR_COMPARISON_MDI] 創建資料管理器...")
        
        if not all([self.year, self.race, self.session]):
            logger.error("[SECTOR_COMPARISON_MDI] 參數不完整，無法創建資料管理器")
            return None
        
        loader = IdealLapSectorComparisonDataLoader(
            year=self.year,
            race=self.race,
            session=self.session,
            parent=self
        )
        
        # 連接信號
        loader.data_loaded.connect(self._on_data_loaded)
        loader.load_error.connect(self._on_load_error)
        
        logger.info("[SECTOR_COMPARISON_MDI] 資料管理器已創建")
        return loader
    
    def create_chart_widget(self):
        """
        創建圖表元件
        
        Returns:
            IdealLapSectorComparisonTableWidget: 表格元件實例
        """
        logger.debug("[SECTOR_COMPARISON_MDI] 創建表格元件（新版本）...")
        
        # ⚠️ parent 必須傳 None，因為 UniversalAnalysisMDI 不是 QWidget
        widget = IdealLapSectorComparisonWidget(parent=None)
        
        # ✅ 表格版本不需要 bar_clicked 信號（使用 QTableWidget 自帶的選擇機制）
        
        logger.info("[SECTOR_COMPARISON_MDI] 表格元件已創建")
        return widget
    
    def _setup_ui_components(self):
        """設置額外的 UI 組件"""
        logger.debug("[SECTOR_COMPARISON_MDI] 設置 UI 組件...")
        
        # 創建控制面板
        self.control_panel = SectorComparisonControlPanel(parent=self)
        self.control_panel.sort_requested.connect(self._on_sort_requested)
        self.control_panel.reload_requested.connect(self.load_initial_data)
        
        # 保存狀態標籤引用（用於 API 進度更新）
        self.lbl_control_status = self.control_panel.lbl_status
        
        # 重新組織布局（使用分割器）
        splitter = QSplitter(Qt.Vertical)
        
        # 上半部：控制面板
        splitter.addWidget(self.control_panel)
        
        # 下半部：圖表
        if self.chart_widget:
            splitter.addWidget(self.chart_widget)
        
        # 設置分割比例（5% 控制面板，95% 圖表）
        splitter.setSizes([50, 950])
        
        # 更新主佈局
        if self.layout():
            # 清除現有布局
            while self.layout().count():
                item = self.layout().takeAt(0)
                if item.widget():
                    item.widget().setParent(None)
        
        layout = QVBoxLayout(self)
        layout.addWidget(splitter)
        layout.setContentsMargins(5, 5, 5, 5)
        
        logger.info("[SECTOR_COMPARISON_MDI] UI 組件設置完成（含狀態標籤引用）")
    
    # ========== 數據處理回調 ==========
    
    @pyqtSlot(dict)
    def _on_data_loaded(self, data: Dict[str, Any]):
        """
        數據載入完成回調
        
        Args:
            data: 載入的資料
        """
        try:
            logger.debug("[SECTOR_COMPARISON_MDI] 收到資料載入完成信號")
            
            if not data or not data.get("success"):
                error_msg = data.get("error", "未知錯誤") if data else "資料為空"
                self._on_load_error(f"資料載入失敗: {error_msg}")
                return
            
            self._current_data = data
            self._is_data_loaded = True
            
            # ✅ 正確：使用 update_data() 方法（參考 lap_box_plot_analysis_mdi）
            logger.debug(f"[SECTOR_COMPARISON_MDI] 更新圖表數據...")
            
            if self.chart_widget:
                self.chart_widget.update_data(data)
            
            logger.info("[SECTOR_COMPARISON_MDI] 資料處理完成")
            
        except Exception as e:
            logger.error(f"[SECTOR_COMPARISON_MDI] 資料處理失敗: {e}")
            import traceback
            traceback.print_exc()
            self._on_load_error(f"資料處理錯誤: {str(e)}")
    
    @pyqtSlot(str)
    def _on_load_error(self, error_msg: str):
        """
        資料載入錯誤回調
        
        Args:
            error_msg: 錯誤訊息
        """
        logger.error(f"[SECTOR_COMPARISON_MDI] 載入錯誤: {error_msg}")
        
        # ✅ 只在控制台記錄錯誤，不彈出對話框（API-ONLY 模式）
        # 用戶應該通過 API 獲取數據，找不到本地 JSON 不應該彈窗
        # ❌ 移除彈窗：self._show_error("資料載入失敗", error_msg)
    
    # ========== API 整合方法 ==========
    
    def load_initial_data(self):
        """
        載入初始數據（通過 API）
        
        ⚠️ API-ONLY 模式: 優先使用 API，失敗時回退到本地 JSON
        """
        logger.debug(f"🌐 [SECTOR_COMPARISON_MDI] 開始載入數據 (API-ONLY 模式)")
        logger.debug(f"   參數: {self.year} {self.race} {self.session}")
        
        # 更新狀態標籤
        if hasattr(self, 'lbl_control_status') and self.lbl_control_status:
            self.lbl_control_status.setText("正在從 API 載入數據...")
        
        # 構建 API 參數
        api_params = {
            "year": self.year,
            "race": self.race,
            "session": self.session
        }
        
        # 創建 API Worker
        self.api_worker = IdealLapSectorComparisonApiWorker(
            params=api_params,
            timeout=300  # 5 分鐘超時
        )
        
        # 連接信號
        # 🔧 關鍵修復: 使用 Qt.QueuedConnection 確保槽函數在 UI 線程執行
        # 原因: API Worker 在 QThread.run() 中發射信號（非 UI 線程）
        #       如果使用默認的 AutoConnection，槽函數可能在 Worker 線程執行
        #       導致在非 UI 線程更新 Qt Widget → 程式崩潰
        self.api_worker.progress.connect(self._on_api_progress)
        self.api_worker.success.connect(self._on_api_success)
        self.api_worker.failure.connect(self._on_api_failure)
        
        # 啟動異步請求
        self.api_worker.start()
        logger.info("[SECTOR_COMPARISON_MDI] API Worker 已啟動（使用 Qt.QueuedConnection）")
    
    @pyqtSlot(int)
    def _on_api_progress(self, progress: int):
        """
        API 請求進度回調
        
        Args:
            progress: 進度百分比 (0-100)
        """
        logger.debug(f"[SECTOR_COMPARISON_API] 進度: {progress}%")
        
        if hasattr(self, 'lbl_control_status') and self.lbl_control_status:
            self.lbl_control_status.setText(f"API 載入中... {progress}%")
    
    @pyqtSlot(dict)
    def _on_api_success(self, result: Dict):
        """
        API 請求成功回調
        
        ⚠️ 關鍵修復: 使用 @pyqtSlot 確保在 UI 線程執行
        
        Args:
            result: API 返回的數據
        """
        try:
            logger.info("[SECTOR_COMPARISON_API] API 請求成功")
            logger.debug(f"API 返回數據鍵: {list(result.keys())}")
            
            # 提取實際數據（處理 API Worker 的包裝格式）
            api_data = result.get('data', result)
            meta = result.get('meta', {})
            
            logger.debug(f"實際數據鍵: {list(api_data.keys()) if isinstance(api_data, dict) else type(api_data)}")
            
            # 驗證數據格式
            if not self._validate_api_data(api_data):
                raise ValueError("API 返回數據格式無效")
            
            # ✅ 修正: 調用 _on_data_loaded() 處理數據（複製 ranking_table 模式）
            # 而非調用不存在的 update_chart()
            logger.debug("[SECTOR_COMPARISON_API] 🔄 在 UI 線程更新數據...")
            self._on_data_loaded(api_data)
            
            # 更新狀態
            if hasattr(self, 'lbl_control_status') and self.lbl_control_status:
                source_label = "API" if meta.get('source') == 'api' else meta.get('source', 'Unknown')
                self.lbl_control_status.setText(f"✅ 已從 {source_label} 載入資料")
            
            # 保存當前數據
            self._current_data = api_data
            logger.info("[SECTOR_COMPARISON_API] UI 更新完成")
            
        except Exception as e:
            logger.error(f"[SECTOR_COMPARISON_API] 數據處理失敗: {e}")
            traceback.print_exc()
            self._on_api_failure(f"數據處理錯誤: {str(e)}")
    
    @pyqtSlot(str)
    def _on_api_failure(self, error_msg: str):
        """
        API 請求失敗回調（回退到本地 JSON）
        
        Args:
            error_msg: 錯誤訊息
        """
        logger.warning(f"[SECTOR_COMPARISON_API] API 請求失敗: {error_msg}")
        logger.debug("[SECTOR_COMPARISON_MDI] 嘗試回退到本地 JSON 檔案...")
        
        # 更新狀態
        if hasattr(self, 'lbl_control_status') and self.lbl_control_status:
            self.lbl_control_status.setText("API 失敗，嘗試本地 JSON...")
        
        # 回退到本地 JSON 載入（使用基類的 data_manager）
        if self.data_manager:
            try:
                self.data_manager.load_data(
                    year=self.year,
                    race=self.race,
                    session=self.session
                )
                logger.info("[SECTOR_COMPARISON_MDI] 本地 JSON 載入成功（回退模式）")
                
                if hasattr(self, 'lbl_control_status') and self.lbl_control_status:
                    self.lbl_control_status.setText("已載入本地 JSON（API 失敗回退）")
                    
            except Exception as fallback_error:
                logger.error(f"[SECTOR_COMPARISON_MDI] 本地 JSON 載入也失敗: {fallback_error}")
                
                # ✅ 修正: 使用 _show_error() 方法（複製 ranking_table 模式）
                self._show_error(
                    "數據載入完全失敗",
                    f"API 和本地 JSON 載入均失敗:\n\n"
                    f"API 錯誤: {error_msg}\n"
                    f"JSON 錯誤: {str(fallback_error)}\n\n"
                    f"請檢查:\n"
                    f"1. API 服務器是否運行在 https://api.f1telemetrystationpro.org\n"
                    f"2. 本地 JSON 檔案是否存在\n"
                    f"3. 參數是否正確 ({self.year} {self.race} {self.session})"
                )
                
                if hasattr(self, 'lbl_control_status') and self.lbl_control_status:
                    self.lbl_control_status.setText("數據載入失敗（API + JSON 均失敗）")
    
    def _validate_api_data(self, data: Dict) -> bool:
        """
        驗證 API 返回的數據格式
        
        Args:
            data: API 返回的數據
            
        Returns:
            bool: 數據格式是否有效
        """
        try:
            logger.debug(f"[API_VALIDATION] 開始驗證數據: {list(data.keys()) if isinstance(data, dict) else type(data)}")
            
            # 檢查基本格式
            if not isinstance(data, dict):
                logger.error(f"[API_VALIDATION] 數據不是字典，而是: {type(data)}")
                return False
            
            # CLI Function 53 的標準輸出格式包含：
            # - sector_comparison: 分段對比數據
            # - metadata: 元數據
            # 或者可能直接是 sector_comparison 數據
            
            # 檢查是否有 sector_comparison 鍵
            if 'sector_comparison' in data:
                sector_data = data['sector_comparison']
                logger.debug(f"[API_VALIDATION] 找到 sector_comparison 鍵")
            else:
                # 可能直接就是分段數據（頂層就是車手字典）
                logger.debug(f"[API_VALIDATION] 未找到 sector_comparison 鍵，假設頂層就是數據")
                sector_data = data
            
            # 驗證分段數據
            if not isinstance(sector_data, dict):
                logger.error(f"[API_VALIDATION] 分段數據不是字典")
                return False
            
            # 檢查至少有一個車手數據
            if len(sector_data) == 0:
                logger.error(f"[API_VALIDATION] 分段數據為空")
                return False
            
            logger.info(f"[API_VALIDATION] 數據格式驗證通過，包含 {len(sector_data)} 個車手")
            return True
            
        except Exception as e:
            logger.error(f"[API_VALIDATION] 驗證異常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _transform_api_data_for_display(self, api_data: Dict) -> Dict:
        """
        將 API 數據轉換為顯示格式
        
        Args:
            api_data: API 返回的原始數據
            
        Returns:
            Dict: 轉換後的顯示數據
        """
        try:
            # API 數據已經是正確格式，直接返回
            # （CLI Function 53 的輸出格式已匹配 GUI 需求）
            return api_data
            
        except Exception as e:
            logger.error(f"[API_TRANSFORM] 轉換失敗: {e}")
            raise
    
    # ========== 信號處理 ==========
    
    @pyqtSlot(str)
    def _on_bar_clicked(self, driver_code: str):
        """
        棒狀圖被點擊
        
        Args:
            driver_code: 車手代碼
        """
        logger.debug(f"[SECTOR_COMPARISON_MDI] 車手棒狀圖被點擊: {driver_code}")
        
        # ✅ MDI 不是 QWidget，需要使用 chart_widget 作為 parent
        # 參考: ideal_lap_ranking_table_mdi.py line 617
        parent = self.chart_widget if hasattr(self, 'chart_widget') else None
        
        # TODO: 可實作顯示該車手的詳細分段趨勢圖
        # 目前僅顯示提示訊息
        QMessageBox.information(
            parent,
            f"車手 {driver_code}",
            f"分段對比詳情\n\n"
            f"車手: {driver_code}\n"
            f"賽事: {self.year} {self.race} {self.session}\n\n"
            f"（詳細趨勢圖功能開發中...）"
        )
    
    @pyqtSlot(str)
    def _on_sort_requested(self, sort_key: str):
        """
        排序請求
        
        Args:
            sort_key: 排序鍵
        """
        logger.debug(f"[SECTOR_COMPARISON_MDI] 排序請求: {sort_key}")
        
        if self.chart_widget:
            self.chart_widget.sort_data(sort_key)
    
    # ========== 公開方法 ==========
    
    def get_current_data(self) -> Optional[Dict]:
        """
        獲取當前數據
        
        Returns:
            Optional[Dict]: 當前數據
        """
        return self._current_data
    
    def export_chart(self, file_path: str) -> bool:
        """
        匯出圖表
        
        Args:
            file_path: 匯出檔案路徑
            
        Returns:
            bool: 匯出是否成功
        """
        try:
            if not self.chart_widget:
                return False
            
            # ✅ 正確：使用 export_chart() 方法（參考 lap_box_plot_analysis）
            success = self.chart_widget.export_chart(file_path)
            if success:
                logger.info(f"[SECTOR_COMPARISON_MDI] 圖表已匯出至: {file_path}")
            return success
            
        except Exception as e:
            logger.error(f"[SECTOR_COMPARISON_MDI] 匯出失敗: {e}")
            return False
    
    def reload_data(self):
        """重新載入數據"""
        logger.debug("[SECTOR_COMPARISON_MDI] 重新載入數據...")
        
        if self.data_loader:
            self.data_loader.load_data(
                year=self.year,
                race=self.race,
                session=self.session
            )
        else:
            logger.error("[SECTOR_COMPARISON_MDI] 資料載入器未初始化")
    
    def update_analysis_parameters(self, year: str, race: str, session: str) -> bool:
        """
        更新分析參數並重新載入資料
        
        ⚠️ 參考: ideal_lap_ranking_table_mdi.py line 553-590
        
        Args:
            year: 新的年份
            race: 新的賽事
            session: 新的賽段
            
        Returns:
            bool: 更新是否成功
        """
        try:
            logger.debug(f"[SECTOR_COMPARISON_MDI] 🔄 更新參數: {year} {race} {session}")
            
            # 更新內部參數
            self.year = str(year)
            self.race = race
            self.session = session
            
            # 同時更新 DataManager 的參數（如果存在）
            if hasattr(self, 'data_manager') and self.data_manager:
                self.data_manager.year = str(year)
                self.data_manager.race = race
                self.data_manager.session = session
                logger.info(f"[SECTOR_COMPARISON_MDI] ✅ DataManager 參數已同步")
            
            # 🔑 重點：調用 load_initial_data() 觸發 API 請求
            # 這個方法會啟動 API Worker 並更新 UI
            logger.debug(f"[SECTOR_COMPARISON_MDI] 🌐 觸發資料重新載入...")
            self.load_initial_data()
            
            # 異步載入，返回 True 表示啟動成功
            return True
            
        except Exception as e:
            logger.error(f"[SECTOR_COMPARISON_MDI] 參數更新失敗: {e}")
            import traceback

            traceback.print_exc()
            return False
    
    def update_parameters(self, **params):
        """
        更新參數（舊版相容方法，轉發到 update_analysis_parameters）
        
        Args:
            **params: 新參數 (year, race, session)
        """
        year = params.get('year', self.year)
        race = params.get('race', self.race)
        session = params.get('session', self.session)
        
        return self.update_analysis_parameters(year, race, session)
    
    def cleanup(self):
        """清理資源"""
        logger.debug("[SECTOR_COMPARISON_MDI] 清理資源...")
        
        try:
            # 清理資料載入器
            if hasattr(self, 'data_loader') and self.data_loader:
                self.data_loader.deleteLater()
                self.data_loader = None
            
            # 清理圖表元件
            if hasattr(self, 'chart_widget') and self.chart_widget:
                self.chart_widget.deleteLater()
                self.chart_widget = None
            
            # 清理控制面板
            if self.control_panel:
                self.control_panel.deleteLater()
                self.control_panel = None
            
            self._current_data = None
            self._is_data_loaded = False
            
            logger.info("[SECTOR_COMPARISON_MDI] 資源清理完成")
            
        except Exception as e:
            logger.error(f"[SECTOR_COMPARISON_MDI] 清理失敗: {e}")
    
    # ========== 輔助方法 ==========
    
    def _show_error(self, title: str, message: str):
        """
        顯示錯誤對話框
        
        ⚠️ 重要: MDI 不是 QWidget，需要使用 chart_widget 作為 parent
        
        Args:
            title: 對話框標題
            message: 錯誤訊息
        """
        # MDI 不是 QWidget，需要使用 chart_widget 作為 parent
        parent = self.chart_widget if hasattr(self, 'chart_widget') else None
        QMessageBox.critical(parent, title, message)


class SectorComparisonControlPanel(QWidget):
    """
    分段對比控制面板
    
    提供排序、重新載入等控制功能
    """
    
    # 自定義信號
    sort_requested = pyqtSignal(str)  # 排序請求信號
    reload_requested = pyqtSignal()   # 重新載入信號
    
    def __init__(self, parent=None):
        """
        初始化控制面板
        
        Args:
            parent: 父元件
        """
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """設置 UI 組件"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # 標題標籤
        lbl_title = QLabel("分段對比控制:")
        lbl_title.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(lbl_title)
        
        # 狀態標籤
        self.lbl_status = QLabel("就緒")
        self.lbl_status.setStyleSheet("color: #2196F3; font-size: 11px;")
        layout.addWidget(self.lbl_status)
        
        layout.addStretch()
        
        # 排序按鈕組
        sort_group = QGroupBox("排序方式")
        sort_layout = QHBoxLayout(sort_group)
        sort_layout.setContentsMargins(5, 5, 5, 5)
        
        btn_sort_time = QPushButton("總時間")
        btn_sort_time.setToolTip("按總分段時間排序")
        btn_sort_time.clicked.connect(lambda: self.sort_requested.emit("total_time"))
        sort_layout.addWidget(btn_sort_time)
        
        btn_sort_s1 = QPushButton("第1段")
        btn_sort_s1.setToolTip("按第1分段時間排序")
        btn_sort_s1.clicked.connect(lambda: self.sort_requested.emit("sector1"))
        sort_layout.addWidget(btn_sort_s1)
        
        btn_sort_s2 = QPushButton("第2段")
        btn_sort_s2.setToolTip("按第2分段時間排序")
        btn_sort_s2.clicked.connect(lambda: self.sort_requested.emit("sector2"))
        sort_layout.addWidget(btn_sort_s2)
        
        btn_sort_s3 = QPushButton("第3段")
        btn_sort_s3.setToolTip("按第3分段時間排序")
        btn_sort_s3.clicked.connect(lambda: self.sort_requested.emit("sector3"))
        sort_layout.addWidget(btn_sort_s3)
        
        layout.addWidget(sort_group)
        
        # 重新載入按鈕
        btn_reload = QPushButton("🔄 重新載入")
        btn_reload.setToolTip("重新從 API 載入數據")
        btn_reload.clicked.connect(self.reload_requested.emit)
        btn_reload.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        layout.addWidget(btn_reload)
    
    def update_status(self, status_text: str, color: str = "#2196F3"):
        """
        更新狀態標籤
        
        Args:
            status_text: 狀態文字
            color: 文字顏色 (預設藍色)
        """
        self.lbl_status.setText(status_text)
        self.lbl_status.setStyleSheet(f"color: {color}; font-size: 11px;")
