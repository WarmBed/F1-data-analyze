#!/usr/bin/env python3
"""
FP2→Q 排位賽預測 MDI 視窗
FP2 to Qualifying Prediction MDI

負責管理 FP2→Q 排位賽預測的 MDI 視窗，整合資料載入器和表格元件
基於 FP2 練習賽數據和機器學習模型提供排位賽成績預測

作者: F1T Team
日期: 2025-01-27
版本: 1.0.0
"""

import time
import requests
from typing import Dict, Any
from PyQt5.QtWidgets import QGroupBox, QPushButton, QLabel, QHBoxLayout, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot

from core.gui_i18n import tr
from core.logger import get_logger
from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig


logger = get_logger(component="fp2_qualifying_prediction_mdi")


class FP2QualifyingPredictionApiWorker(QThread):
    """
    FP2→Q 排位賽預測 API 請求工作執行緒
    
    負責異步調用 API 獲取排位賽預測數據
    API 端點: POST /api/v2/analysis/execute?function_id=76
    """
    
    # 信號
    progress = pyqtSignal(int)  # 進度 (0-100)
    success = pyqtSignal(dict)  # 成功 (返回數據)
    failure = pyqtSignal(str)   # 失敗 (錯誤訊息)
    
    def __init__(self, params: Dict[str, Any], base_url: str = None, timeout: float = 60.0):
        """
        初始化 API Worker
        
        Args:
            params: API 參數 (year, race, etc.)
            base_url: API 基礎 URL (預設: https://localhost:8000)
            timeout: 請求超時時間（秒）
        """
        super().__init__()
        self.base_url = (base_url or "https://localhost:8000").rstrip('/')
        self.params = dict(params)
        self.timeout = timeout
        self._logger = get_logger(component="fp2_qual_pred_api_worker")
    
    def run(self):
        """執行 API 請求"""
        try:
            # 中斷檢查點 1: 開始時
            if self.isInterruptionRequested():
                self._logger.debug("[API_WORKER] 開始前已被中斷")
                return
            self.progress.emit(20)
            
            # 構建 API 端點
            endpoint = f"{self.base_url}/api/v2/analysis/execute"
            
            # 構建查詢參數
            query_params: Dict[str, Any] = {
                "function_id": 76,  # CLI Function 76 - FP2→Q 排位賽預測生成器
                "year": int(self.params.get("year")),
                "race": self.params.get("race"),
            }
            
            # 強制刷新（可選）
            if self.params.get("force_refresh"):
                query_params["force_refresh"] = True
            
            self._logger.info("[API_WORKER] 調用 API: %s", endpoint)
            self._logger.debug("[API_WORKER] 參數: %s", query_params)
            
            # 中斷檢查點 2: HTTP 請求前
            if self.isInterruptionRequested():
                self._logger.debug("[API_WORKER] HTTP 請求前被中斷")
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
            
            # 中斷檢查點 3: HTTP 請求後
            if self.isInterruptionRequested():
                self._logger.debug("[API_WORKER] HTTP 請求後被中斷")
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
            
            self._logger.info("[API_WORKER] API 調用成功")
            self._logger.info("[API_WORKER] 延遲: %sms", meta['latency_ms'])
            self._logger.debug("[API_WORKER] 數據源: %s", meta['source'])
            
            self.progress.emit(90)
            # 中斷檢查點 4: success 信號發送前
            if self.isInterruptionRequested():
                self._logger.debug("[API_WORKER] success 信號前被中斷")
                return
            self.success.emit({"data": data, "meta": meta})
            
        except Exception as exc:
            # 中斷檢查：被中斷時不發送錯誤信號
            if self.isInterruptionRequested():
                return
            error_msg = f"API 請求失敗: {str(exc)}"
            self._logger.exception("[API_WORKER] %s", error_msg)
            self.failure.emit(error_msg)
        finally:
            # 中斷檢查：被中斷時不發送 progress 信號
            if not self.isInterruptionRequested():
                self.progress.emit(100)


# 導入資料載入器和元件
try:
    from .fp2_qualifying_prediction_data_loader import FP2QualifyingPredictionDataLoader
    from .fp2_qualifying_prediction_widget import FP2QualifyingPredictionWidget
except ImportError:
    from modules.gui.fp2_qualifying_prediction.fp2_qualifying_prediction_data_loader import FP2QualifyingPredictionDataLoader
    from modules.gui.fp2_qualifying_prediction.fp2_qualifying_prediction_widget import FP2QualifyingPredictionWidget


class FP2QualifyingPredictionMDI(UniversalAnalysisMDI):
    """
    FP2→Q 排位賽預測 MDI 視窗
    
    繼承自 UniversalAnalysisMDI，提供統一的視窗管理和數據流控制
    整合 FP2QualifyingPredictionDataLoader 和 FP2QualifyingPredictionWidget
    """
    
    # 在類別層級註冊模組類型
    _REGISTERED = False
    
    @classmethod
    def ensure_registered(cls):
        """確保模組類型已註冊"""
        if not cls._REGISTERED:
            config = AnalysisMDIConfig(
                analysis_type="fp2_qualifying_prediction",
                display_name="FP2 to Qualifying Prediction",
                default_size=(1300, 800),
                requires_driver_params=False,
                requires_lap_params=False,
                supports_single_driver=False,
                supports_dual_driver=False
            )
            UniversalAnalysisMDI.register_mdi_module_type("fp2_qualifying_prediction", config)
            cls._REGISTERED = True
            logger.info("[FP2_QUAL_PRED_MDI] 模組類型已註冊")
    
    def __init__(self, parent=None):
        """
        初始化 MDI 視窗
        
        Args:
            parent: 父元件
        """
        self._logger = get_logger(component="fp2_qualifying_prediction_mdi")
        self._logger.info("[FP2_QUAL_PRED_MDI] FP2QualifyingPredictionMDI 開始初始化...")
        
        # 確保類型已註冊
        self.ensure_registered()
        
        # 調用基類初始化
        super().__init__(analysis_type="fp2_qualifying_prediction", parent=parent)
        
        # 初始化參數（將在 initialize_module 中設置）
        self.year = None
        self.race = None
        
        # 狀態變數
        self._current_data = None
        self._is_data_loaded = False
        
        self._logger.info("[FP2_QUAL_PRED_MDI] 基類初始化完成, 等待參數設置...")
    
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
            self._logger.info("[FP2_QUAL_PRED_MDI] 開始初始化模組...")
            
            # 驗證必要屬性
            if not hasattr(self, 'current_year') or not self.current_year:
                self._logger.error("[FP2_QUAL_PRED_MDI] 缺少 current_year 屬性")
                return False
                
            if not hasattr(self, 'current_race') or not self.current_race:
                self._logger.error("[FP2_QUAL_PRED_MDI] 缺少 current_race 屬性")
                return False
            
            # 設置參數（FP2→Q 預測不需要 session）
            self.year = str(self.current_year)
            self.race = self.current_race
            
            self._logger.info("[FP2_QUAL_PRED_MDI] 參數已設置: %s %s", self.year, self.race)
            
            # 關鍵：調用基類的 initialize_module 來創建 chart_widget 和 data_manager
            if not super().initialize_module(parent_widget=parent_widget, **kwargs):
                self._logger.error("[FP2_QUAL_PRED_MDI] 基類初始化失敗")
                return False
            
            # 驗證組件已創建
            if not self.chart_widget:
                self._logger.error("[FP2_QUAL_PRED_MDI] chart_widget 未創建")
                return False
            
            if not self.data_manager:
                self._logger.error("[FP2_QUAL_PRED_MDI] data_manager 未創建")
                return False
            
            self._logger.info("[FP2_QUAL_PRED_MDI] 組件創建成功")
            
            # 載入初始數據
            self.load_initial_data()
            
            self._logger.info("[FP2_QUAL_PRED_MDI] 模組初始化完成")
            return True
            
        except Exception as e:
            self._logger.exception("[FP2_QUAL_PRED_MDI] 初始化失敗: %s", e)
            return False
    
    # ========== 基類抽象方法實作 ==========
    
    def create_data_manager(self) -> FP2QualifyingPredictionDataLoader:
        """
        創建資料載入器（由基類調用）
        
        Returns:
            FP2QualifyingPredictionDataLoader: 資料載入器實例
        """
        self._logger.info("[FP2_QUAL_PRED_MDI] 創建資料載入器...")
        loader = FP2QualifyingPredictionDataLoader(
            year=self.year,
            race=self.race,
            parent=self
        )
        
        # 連接信號
        loader.data_loaded.connect(self._on_data_loaded)
        loader.load_error.connect(self._on_load_error)
        loader.status_changed.connect(self._on_status_changed)
        
        self._logger.info("[FP2_QUAL_PRED_MDI] 資料載入器已創建")
        return loader
    
    def create_chart_widget(self) -> FP2QualifyingPredictionWidget:
        """
        創建圖表元件（由基類調用）
        
        Returns:
            FP2QualifyingPredictionWidget: 表格元件實例
        """
        self._logger.info("[FP2_QUAL_PRED_MDI] 創建表格元件...")
        # parent 必須傳 None，因為 UniversalAnalysisMDI 不是 QWidget
        widget = FP2QualifyingPredictionWidget(parent=None)
        
        self._logger.info("[FP2_QUAL_PRED_MDI] 表格元件已創建")
        return widget
    
    def _setup_control_panel(self):
        """
        設置控制面板（由基類調用）
        """
        self._logger.info("[FP2_QUAL_PRED_MDI] 設置控制面板...")
        
        # 創建控制面板容器
        control_panel = QGroupBox(tr("control_panel", "控制面板"))
        control_layout = QHBoxLayout()
        control_panel.setLayout(control_layout)
        
        # 重新載入按鈕
        self.btn_reload = QPushButton(tr("reload_button", "重新載入"))
        self.btn_reload.clicked.connect(self._on_reload_clicked)
        control_layout.addWidget(self.btn_reload)
        
        # 彈性空間
        control_layout.addStretch()
        
        # 狀態標籤
        self.lbl_control_status = QLabel(tr("status_ready", "就緒"))
        control_layout.addWidget(self.lbl_control_status)
        
        # 將控制面板添加到主佈局
        if hasattr(self, 'main_layout'):
            self.main_layout.addWidget(control_panel)
        
        self._logger.info("[FP2_QUAL_PRED_MDI] 控制面板已設置")
    
    # ========== 數據流處理 ==========
    
    @pyqtSlot(dict)
    def _on_data_loaded(self, data: Dict[str, Any]):
        """
        資料載入完成回調
        
        Args:
            data: 載入的資料字典
        """
        try:
            self._logger.info("[FP2_QUAL_PRED_MDI] 資料載入完成，開始處理...")
            
            # 驗證資料結構
            if not isinstance(data, dict):
                self._show_error(tr("data_format_error", "資料格式錯誤"), tr("not_dict", "載入的資料不是字典格式"))
                return
            
            if "metadata" not in data:
                self._show_error(tr("data_structure_error", "資料結構錯誤"), tr("missing_metadata", "缺少 'metadata' 鍵"))
                return
            
            if "predictions" not in data:
                self._show_error(tr("data_structure_error", "資料結構錯誤"), tr("missing_predictions", "缺少 'predictions' 資料"))
                return
            
            # 儲存資料
            self._current_data = data
            self._is_data_loaded = True
            
            # 更新 Widget
            predictions = data["predictions"]
            self._logger.info("[FP2_QUAL_PRED_MDI] 更新表格（%s 位車手）...", len(predictions))
            self.chart_widget.update_display(data)
            
            # 更新狀態
            if hasattr(self, 'lbl_control_status'):
                self.lbl_control_status.setText(
                    tr("data_loaded_status", "已載入 {count} 位車手預測").format(count=len(predictions))
                )
            
            self._logger.info("[FP2_QUAL_PRED_MDI] 資料處理完成")
            
        except Exception as e:
            self._logger.exception("[FP2_QUAL_PRED_MDI] 資料處理失敗: %s", e)
            self._show_error(tr("data_processing_error", "資料處理失敗"), str(e))
    
    @pyqtSlot(str)
    def _on_load_error(self, error_msg: str):
        """
        資料載入錯誤回調
        
        Args:
            error_msg: 錯誤訊息
        """
        self._logger.error("[FP2_QUAL_PRED_MDI] 載入錯誤: %s", error_msg)
        # 只在狀態標籤顯示錯誤
        if hasattr(self, 'lbl_control_status'):
            self.lbl_control_status.setText(f"{tr('error', '錯誤')}: {error_msg}")
    
    @pyqtSlot(str)
    def _on_status_changed(self, status: str):
        """
        狀態變更回調
        
        Args:
            status: 新狀態訊息
        """
        self._logger.info("[FP2_QUAL_PRED_MDI] 狀態: %s", status)
        if hasattr(self, 'lbl_control_status'):
            self.lbl_control_status.setText(status)
    
    # ========== 事件處理 ==========
    
    def _on_reload_clicked(self):
        """處理重新載入按鈕點擊"""
        self._logger.info("[FP2_QUAL_PRED_MDI] 重新載入資料...")
        if hasattr(self, 'lbl_control_status'):
            self.lbl_control_status.setText(tr("reloading", "重新載入中..."))
        
        # 清空表格
        self.chart_widget.clear_display()
        
        # 重新載入
        self.load_initial_data()
    
    # ========== 公開方法 ==========
    
    def load_initial_data(self):
        """
        載入初始資料 - 強制使用 API
        
        優先級：
        1. API 調用 (https://localhost:8000)
        2. 備援: 本地 JSON 檔案（API 失敗時）
        """
        self._logger.info("[FP2_QUAL_PRED_MDI] 開始載入初始資料...")
        self._logger.info("[FP2_QUAL_PRED_MDI] 參數: %s %s", self.year, self.race)
        
        # 更新狀態
        if hasattr(self, 'lbl_control_status'):
            self.lbl_control_status.setText(tr("loading_from_api", "正在從 API 載入資料..."))
        
        # 創建 API Worker
        api_params = {
            "year": self.year,
            "race": self.race,
            "force_refresh": False  # 可選：強制刷新
        }
        
        self._logger.info("[FP2_QUAL_PRED_MDI] 創建 API Worker...")
        self.api_worker = FP2QualifyingPredictionApiWorker(
            params=api_params,
            base_url="https://localhost:8000",
            timeout=60.0
        )
        
        # 使用 Qt.QueuedConnection 確保槽函數在 UI 線程執行
        self.api_worker.progress.connect(self._on_api_progress)
        self.api_worker.success.connect(self._on_api_success)
        self.api_worker.failure.connect(self._on_api_failure)
        
        # 啟動 API 請求
        self._logger.info("[FP2_QUAL_PRED_MDI] 啟動 API 請求...")
        self.api_worker.start()
    
    @pyqtSlot(int)
    def _on_api_progress(self, progress: int):
        """API 請求進度更新"""
        self._logger.info("[FP2_QUAL_PRED_MDI] API 進度: %s%%", progress)
        if hasattr(self, 'lbl_control_status'):
            self.lbl_control_status.setText(f"{tr('api_loading', 'API 載入中')}... {progress}%")
    
    @pyqtSlot(dict)
    def _on_api_success(self, result: Dict[str, Any]):
        """API 請求成功"""
        try:
            self._logger.info("[FP2_QUAL_PRED_MDI] API 調用成功")
            
            # 提取數據和元數據
            data = result.get("data", {})
            meta = result.get("meta", {})
            
            self._logger.info("[FP2_QUAL_PRED_MDI] 數據源: %s", meta.get('source'))
            self._logger.info("[FP2_QUAL_PRED_MDI] 延遲: %sms", meta.get('latency_ms'))
            
            # 驗證數據結構
            if not isinstance(data, dict):
                raise ValueError(tr("api_data_format_error", "API 返回的數據格式錯誤"))
            
            if "metadata" not in data:
                raise ValueError(tr("api_data_missing_metadata", "API 數據缺少 'metadata'"))
            
            if "predictions" not in data:
                raise ValueError(tr("api_data_missing_predictions", "API 數據缺少 'predictions'"))
            
            # 處理數據（觸發現有的 _on_data_loaded 處理邏輯）
            self._on_data_loaded(data)
            
            # 更新狀態
            if hasattr(self, 'lbl_control_status'):
                source_label = "API" if meta.get('source') == 'api' else meta.get('source', 'Unknown')
                self.lbl_control_status.setText(
                    tr("data_loaded_from_source", "已從 {source} 載入資料").format(source=source_label)
                )
            
        except Exception as e:
            self._logger.exception("[FP2_QUAL_PRED_MDI] API 數據處理失敗: %s", e)
            self._on_api_failure(str(e))
    
    @pyqtSlot(str)
    def _on_api_failure(self, error_msg: str):
        """API 請求失敗 - 嘗試備援方案"""
        self._logger.error("[FP2_QUAL_PRED_MDI] API 調用失敗: %s", error_msg)
        
        if hasattr(self, 'lbl_control_status'):
            self.lbl_control_status.setText(
                tr("fp2_qual_pred_api_failure", "API 請求失敗，請稍後再試")
            )

        self._show_error(
            tr("fp2_qual_pred_api_failure_title", "載入失敗"),
            tr(
                "fp2_qual_pred_api_failure_message",
                "FP2→Q 排位賽預測資料僅支援透過 API 載入。請確認 API 服務可用或稍後再試。\n\n詳細錯誤:\n{error}",
            ).format(error=error_msg)
        )
        self._logger.warning("[FP2_QUAL_PRED_MDI] 已封鎖本地 JSON 後備 (API-ONLY)")
    
    def update_analysis_parameters(self, year: str, race: str) -> bool:
        """
        更新分析參數並重新載入資料
        
        Args:
            year: 新的年份
            race: 新的賽事
            
        Returns:
            bool: 更新是否成功
        """
        try:
            self._logger.info("[FP2_QUAL_PRED_MDI] 更新參數: %s %s", year, race)
            
            # 更新內部參數
            self.current_year = str(year)
            self.current_race = race
            self.year = str(year)
            self.race = race
            
            # 同時更新 DataLoader 的參數
            if hasattr(self, 'data_manager') and self.data_manager:
                self.data_manager.year = str(year)
                self.data_manager.race = race
                self._logger.info("[FP2_QUAL_PRED_MDI] DataManager 參數已同步")
            elif hasattr(self, 'data_loader') and self.data_loader:
                self.data_loader.year = str(year)
                self.data_loader.race = race
                self._logger.info("[FP2_QUAL_PRED_MDI] DataLoader 參數已同步")
            
            # 調用 load_initial_data() 觸發 API 請求
            self._logger.info("[FP2_QUAL_PRED_MDI] 觸發資料重新載入...")
            self.load_initial_data()
            
            # 異步載入，返回 True 表示啟動成功
            return True
            
        except Exception as e:
            self._logger.exception("[FP2_QUAL_PRED_MDI] 參數更新失敗: %s", e)
            return False

    def update_parameters(self, year: int = None, race: str = None, session: str = None, **kwargs) -> bool:
        """覆寫通用參數更新邏輯，確保觸發 API 載入"""
        try:
            # 增強調試輸出：入口日誌
            self._logger.info("[FP2_QUAL_PRED_MDI] update_parameters 被調用")
            self._logger.info("   接收參數: year=%s, race=%s, session=%s", year, race, session)
            self._logger.info(
                "   當前參數: year=%s, race=%s",
                getattr(self, 'year', 'N/A'), getattr(self, 'race', 'N/A')
            )
            
            target_year = year if year is not None else (self.year or getattr(self, 'current_year', None))
            target_race = race if race is not None else (self.race or getattr(self, 'current_race', None))
            # session 參數被忽略（FP2→Q 預測固定使用 FP2）

            if not all([target_year, target_race]):
                self._logger.error(
                    "[FP2_QUAL_PRED_MDI] 參數更新失敗：缺少必要參數 (year=%s, race=%s)",
                    target_year, target_race
                )
                return False

            normalized_year = str(target_year)
            normalized_race = target_race
            
            self._logger.info("[FP2_QUAL_PRED_MDI] 參數正規化: year=%s, race=%s", normalized_year, normalized_race)

            self.current_year = normalized_year
            self.current_race = normalized_race

            params_payload = {
                'year': self.current_year,
                'race': self.current_race
            }
            self.parameters_updated.emit(params_payload)
            self.update_window_title()
            
            self._logger.info("[FP2_QUAL_PRED_MDI] 開始調用 update_analysis_parameters...")

            return self.update_analysis_parameters(
                self.current_year,
                self.current_race
            )

        except Exception as exc:
            self._logger.exception("[FP2_QUAL_PRED_MDI] update_parameters 失敗: %s", exc)
            return False
    
    def get_window_title(self, year: str = None, race: str = None, session: str = None) -> str:
        """
        覆寫基類方法，返回正確的視窗標題 - 只顯示模組名稱
        
        Args:
            year: 年份（忽略）
            race: 賽事（忽略）
            session: 會話（忽略）
            
        Returns:
            str: 視窗標題（純模組名稱）
        """
        # 使用 tr() 支援多國語言
        translated_title = tr("fp2_qualifying_prediction", "FP2 to Qualifying Prediction")
        return translated_title
    
    def get_widget(self):
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
    import sys
    from PyQt5.QtWidgets import QApplication

    logger.info("=" * 60)
    logger.info("FP2→Q 排位賽預測 MDI 視窗 - 獨立測試")
    logger.info("=" * 60)

    app = QApplication(sys.argv)

    # 創建 MDI 視窗
    mdi = FP2QualifyingPredictionMDI(parent=None)

    # 設置參數（模擬 GUI 主程式的調用）
    mdi.current_year = "2025"
    mdi.current_race = "Austria"

    # 初始化模組
    if mdi.initialize_module():
        logger.info("模組初始化成功")

        # 獲取主要元件
        widget = mdi.get_widget()
        if widget and hasattr(widget, 'setWindowTitle'):
            widget.setWindowTitle("FP2 to Qualifying Prediction MDI - Test")
        if widget and hasattr(widget, 'resize'):
            widget.resize(1300, 800)
        if widget and hasattr(widget, 'show'):
            widget.show()

        logger.info("測試視窗已顯示")
    else:
        logger.error("模組初始化失敗")
        sys.exit(1)

    sys.exit(app.exec_())
