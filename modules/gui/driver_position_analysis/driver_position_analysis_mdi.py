#!/usr/bin/env python3
"""
車手比賽排名分析 MDI 視窗
Driver Position Analysis MDI

負責管理車手比賽排名分析的 MDI 視窗，整合 API Worker 和表格元件

作者: F1T Team
日期: 2025-10-28
版本: 1.0.0
"""

import time
import requests
from typing import Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSlot, QThread, pyqtSignal

from core.gui_i18n import tr

# 導入基類
from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig


class DriverPositionApiWorker(QThread):
    """
    車手比賽排名 API 請求工作執行緒
    
    負責異步調用 API 獲取車手排名數據
    API 端點: POST /api/v2/analysis/execute?function_id=25
    """
    
    # 信號
    progress = pyqtSignal(int)  # 進度 (0-100)
    success = pyqtSignal(dict)  # 成功 (返回數據)
    failure = pyqtSignal(str)   # 失敗 (錯誤訊息)
    
    def __init__(self, params: Dict[str, Any], base_url: str = None, timeout: float = 60.0):
        """
        初始化 API Worker
        
        Args:
            params: API 參數 (year, race, session)
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
            self.progress.emit(20)
            
            # 構建 API 端點
            endpoint = f"{self.base_url}/api/v2/analysis/execute"
            
            # 構建查詢參數（CLI Function 25 - Driver Race Position）
            query_params: Dict[str, Any] = {
                "function_id": 25,
                "year": int(self.params.get("year")),
                "race": self.params.get("race"),
                "session": self.params.get("session"),
            }
            
            # 強制刷新（可選）
            if self.params.get("force_refresh"):
                query_params["force_refresh"] = True
            
            print(f"[POSITION_API_WORKER] 🌐 調用 API: {endpoint}")
            print(f"[POSITION_API_WORKER] 📋 參數: {query_params}")
            
            # 發送 POST 請求
            start_ts = time.perf_counter()
            response = requests.post(
                endpoint,
                params=query_params,
                timeout=self.timeout,
                headers={"Accept": "application/json"}
            )
            self.progress.emit(70)
            
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
            
            print(f"[POSITION_API_WORKER] ✅ API 調用成功")
            print(f"[POSITION_API_WORKER] ⏱️  延遲: {meta['latency_ms']}ms")
            print(f"[POSITION_API_WORKER] 📊 數據源: {meta['source']}")
            
            self.progress.emit(90)
            self.success.emit({"data": data, "meta": meta})
            
        except Exception as exc:
            error_msg = f"API 請求失敗: {str(exc)}"
            print(f"[POSITION_API_WORKER] ❌ {error_msg}")
            import traceback
            traceback.print_exc()
            self.failure.emit(error_msg)
        finally:
            self.progress.emit(100)


# 導入 Widget
try:
    from .driver_position_analysis_widget import DriverPositionAnalysisWidget
except ImportError:
    from modules.gui.driver_position_analysis.driver_position_analysis_widget import DriverPositionAnalysisWidget


class DriverPositionAnalysisMDI(UniversalAnalysisMDI):
    """
    車手比賽排名分析 MDI 視窗
    
    繼承自 UniversalAnalysisMDI，提供統一的視窗管理和數據流控制
    整合 DriverPositionApiWorker 和 DriverPositionAnalysisWidget
    """
    
    # 在類別層級註冊模組類型
    _REGISTERED = False
    
    @classmethod
    def ensure_registered(cls):
        """確保模組類型已註冊"""
        if not cls._REGISTERED:
            config = AnalysisMDIConfig(
                analysis_type="driver_position",
                display_name=tr("driver_position_analysis", "Driver Race Position Analysis"),
                default_size=(1200, 700),
                requires_driver_params=False,
                requires_lap_params=False,
                supports_single_driver=False,
                supports_dual_driver=False
            )
            UniversalAnalysisMDI.register_mdi_module_type("driver_position", config)
            cls._REGISTERED = True
            print("[POSITION_MDI] ✅ 模組類型已註冊")
    
    def __init__(self, parent=None):
        """
        初始化 MDI 視窗
        
        Args:
            parent: 父元件
        """
        print(f"[POSITION_MDI] DriverPositionAnalysisMDI 開始初始化...")
        
        # 確保類型已註冊
        self.ensure_registered()
        
        # 調用基類初始化
        super().__init__(analysis_type="driver_position", parent=parent)
        
        # 初始化參數
        self.year = None
        self.race = None
        self.session = None
        
        # 狀態變數
        self._current_data = None
        self._is_data_loaded = False
        
        print(f"[POSITION_MDI] 基類初始化完成, 等待參數設置...")
    
    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        """
        初始化模組（設置參數並載入初始數據）
        
        ⚠️ 覆寫基類方法：此模組使用 API Worker，不需要 DataManager
        
        Args:
            parent_widget: 父級 widget（可選）
            **kwargs: 額外參數
            
        Returns:
            bool: 初始化是否成功
        """
        try:
            print(f"[POSITION_MDI] 開始初始化模組...")
            
            # 驗證必要屬性
            if not hasattr(self, 'current_year') or not self.current_year:
                print(f"[POSITION_MDI] ❌ 缺少 current_year 屬性")
                return False
                
            if not hasattr(self, 'current_race') or not self.current_race:
                print(f"[POSITION_MDI] ❌ 缺少 current_race 屬性")
                return False
                
            if not hasattr(self, 'current_session') or not self.current_session:
                print(f"[POSITION_MDI] ❌ 缺少 current_session 屬性")
                return False
            
            # 設置參數
            self.year = str(self.current_year)
            self.race = self.current_race
            self.session = self.current_session
            
            print(f"[POSITION_MDI] ✅ 參數已設置: {self.year} {self.race} {self.session}")
            
            # ⚠️ 跳過基類的 initialize_module（它會檢查 data_manager）
            # 直接創建必要組件
            
            # 1. 創建圖表組件
            self.chart_widget = self.create_chart_widget()
            if not self.chart_widget:
                print(f"[POSITION_MDI] ❌ chart_widget 未創建")
                return False
            
            print(f"[POSITION_MDI] ✅ 組件創建成功 (chart_widget={type(self.chart_widget).__name__})")
            
            # 2. 設置主界面
            self._setup_ui()
            
            # 3. 註冊到分析模組管理器
            self._register_to_analysis_manager()
            
            # 4. 標記為已初始化
            self._initialized = True
            
            # 5. 載入初始數據
            self.load_initial_data()
            
            print(f"[POSITION_MDI] ✅ 模組初始化完成")
            return True
            
        except Exception as e:
            print(f"[POSITION_MDI] ❌ 初始化失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # ========== 基類抽象方法實作 ==========
    
    def create_data_manager(self):
        """
        創建資料載入器（由基類調用）
        
        注意: 此模組直接使用 API Worker，不需要傳統 DataLoader
        """
        print("[POSITION_MDI] ⚠️  此模組使用 API Worker，不需要 DataManager")
        return None
    
    def create_chart_widget(self) -> DriverPositionAnalysisWidget:
        """
        創建圖表元件（由基類調用）
        
        Returns:
            DriverPositionAnalysisWidget: 表格元件實例
        """
        print("[POSITION_MDI] 創建表格元件...")
        widget = DriverPositionAnalysisWidget(parent=None)
        print("[POSITION_MDI] ✅ 表格元件已創建")
        return widget
    
    def _setup_control_panel(self):
        """
        設置控制面板（由基類調用）
        """
        print("[POSITION_MDI] 設置控制面板...")
        
        # 創建控制面板容器
        control_panel = QGroupBox(tr("control_panel", "控制面板"))
        control_layout = QHBoxLayout()
        control_panel.setLayout(control_layout)
        
        # 重新載入按鈕
        self.btn_reload = QPushButton(tr("reload_button", "🔄 重新載入"))
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
        
        print("[POSITION_MDI] ✅ 控制面板已設置")
    
    # ========== 數據流處理 ==========
    
    def load_initial_data(self):
        """
        載入初始資料 - 強制使用 API
        """
        print("[POSITION_MDI] 🚀 開始載入初始資料...")
        print(f"[POSITION_MDI] 📋 參數: {self.year} {self.race} {self.session}")
        
        # 更新狀態
        if hasattr(self, 'lbl_control_status'):
            self.lbl_control_status.setText(tr("loading_from_api", "正在從 API 載入資料..."))
        
        # 創建 API Worker
        api_params = {
            "year": self.year,
            "race": self.race,
            "session": self.session,
            "force_refresh": False
        }
        
        print("[POSITION_MDI] 🌐 創建 API Worker...")
        self.api_worker = DriverPositionApiWorker(
            params=api_params,
            base_url="https://api.f1telemetrystationpro.org",
            timeout=60.0
        )
        
        # 連接信號
        self.api_worker.progress.connect(self._on_api_progress)
        self.api_worker.success.connect(self._on_api_success)
        self.api_worker.failure.connect(self._on_api_failure)
        
        # 啟動 API 請求
        print("[POSITION_MDI] ▶️  啟動 API 請求...")
        self.api_worker.start()
    
    @pyqtSlot(int)
    def _on_api_progress(self, progress: int):
        """API 請求進度更新"""
        print(f"[POSITION_MDI] 📊 API 進度: {progress}%")
        if hasattr(self, 'lbl_control_status'):
            self.lbl_control_status.setText(f"{tr('api_loading', 'API 載入中')}... {progress}%")
    
    @pyqtSlot(dict)
    def _on_api_success(self, result: Dict[str, Any]):
        """API 請求成功"""
        try:
            print("[POSITION_MDI] ✅ API 調用成功")
            
            # 提取數據和元數據
            data = result.get("data", {})
            meta = result.get("meta", {})
            
            print(f"[POSITION_MDI] 📦 數據源: {meta.get('source')}")
            print(f"[POSITION_MDI] ⏱️  延遲: {meta.get('latency_ms')}ms")
            
            # 處理數據
            self._process_position_data(data)
            
            # 更新狀態
            if hasattr(self, 'lbl_control_status'):
                source_label = "API" if meta.get('source') == 'api' else meta.get('source', 'Unknown')
                self.lbl_control_status.setText(f"✅ {tr('loaded_from', '已從')} {source_label} {tr('load_data', '載入資料')}")
            
        except Exception as e:
            print(f"❌ [POSITION_MDI] API 數據處理失敗: {e}")
            import traceback
            traceback.print_exc()
            self._on_api_failure(str(e))
    
    @pyqtSlot(str)
    def _on_api_failure(self, error_msg: str):
        """API 請求失敗"""
        print(f"❌ [POSITION_MDI] API 調用失敗: {error_msg}")
        
        if hasattr(self, 'lbl_control_status'):
            self.lbl_control_status.setText(tr("api_request_failed", "API 請求失敗，請稍後再試"))
        
        self._show_error(
            tr("load_failed_title", "載入失敗"),
            tr(
                "position_api_failure_message",
                "車手排名資料僅支援透過 API 載入。請確認 API 服務可用或稍後再試。\n\n詳細錯誤:\n{error}",
            ).format(error=error_msg)
        )
    
    def _process_position_data(self, data: Dict[str, Any]):
        """
        處理排名數據並填充表格
        
        Args:
            data: API 返回的數據
        """
        try:
            print("[POSITION_MDI] 開始處理排名數據...")
            
            # 驗證數據結構
            if "all_drivers_position_analysis" not in data:
                raise ValueError("數據缺少 'all_drivers_position_analysis' 鍵")
            
            all_drivers_data = data["all_drivers_position_analysis"]
            
            # 轉換為表格格式
            position_list = []
            for driver_code, driver_info in all_drivers_data.items():
                position_list.append({
                    "driver": driver_code,
                    "team": driver_info.get("team", "Unknown"),
                    "starting_position": driver_info.get("starting_position"),
                    "finishing_position": driver_info.get("finishing_position"),
                    "best_position": driver_info.get("best_position"),
                    "worst_position": driver_info.get("worst_position"),
                })
            
            # 按完賽排名排序（處理 None 值和 DNF）
            def get_sort_key(driver_data):
                pos = driver_data.get("finishing_position")
                if pos is None:
                    return 999  # N/A 排最後
                elif pos == "DNF":
                    return 998  # DNF 排倒數第二
                else:
                    return int(pos)  # 正常位置
            
            position_list.sort(key=get_sort_key)
            
            print(f"[POSITION_MDI] 填充表格（{len(position_list)} 位車手）...")
            self.chart_widget.populate_table(position_list)
            
            # 儲存資料
            self._current_data = data
            self._is_data_loaded = True
            
            print("[POSITION_MDI] ✅ 資料處理完成")
            
        except Exception as e:
            print(f"❌ [POSITION_MDI] 資料處理失敗: {e}")
            import traceback
            traceback.print_exc()
            self._show_error(tr("data_processing_failed", "資料處理失敗"), str(e))
    
    # ========== 事件處理 ==========
    
    def _on_reload_clicked(self):
        """處理重新載入按鈕點擊"""
        print("[POSITION_MDI] 重新載入資料...")
        if hasattr(self, 'lbl_control_status'):
            self.lbl_control_status.setText(tr("reloading", "重新載入中..."))
        
        # 清空表格
        self.chart_widget.clear_table()
        
        # 重新載入
        self.load_initial_data()
    
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
            print(f"[POSITION_MDI] 🔄 更新參數: {year} {race} {session}")
            
            # 更新內部參數
            self.current_year = str(year)
            self.current_race = race
            self.current_session = session
            self.year = str(year)
            self.race = race
            self.session = session
            
            # 同時更新 DataLoader 的參數（如果存在）
            if hasattr(self, 'data_manager') and self.data_manager:
                self.data_manager.year = str(year)
                self.data_manager.race = race
                self.data_manager.session = session
                print(f"[POSITION_MDI] ✅ DataManager 參數已同步")
            elif hasattr(self, 'data_loader') and self.data_loader:
                self.data_loader.year = str(year)
                self.data_loader.race = race
                self.data_loader.session = session
                print(f"[POSITION_MDI] ✅ DataLoader 參數已同步")
            
            # 🔑 重點：調用 load_initial_data() 觸發 API 請求
            # 這個方法會啟動 API Worker 並更新 UI
            print(f"[POSITION_MDI] 🌐 觸發資料重新載入...")
            self.load_initial_data()
            
            # 異步載入，返回 True 表示啟動成功
            return True
            
        except Exception as e:
            print(f"❌ [POSITION_MDI] 參數更新失敗: {e}")
            import traceback
            traceback.print_exc()
            return False

    def update_parameters(self, year: int = None, race: str = None, session: str = None, **kwargs) -> bool:
        """
        覆寫通用參數更新邏輯，確保觸發 API 載入
        
        Args:
            year: 年份
            race: 賽事
            session: 賽段
            **kwargs: 其他參數（忽略）
            
        Returns:
            bool: 更新是否成功
        """
        try:
            target_year = year if year is not None else (self.year or getattr(self, 'current_year', None))
            target_race = race if race is not None else (self.race or getattr(self, 'current_race', None))
            target_session = session if session is not None else (self.session or getattr(self, 'current_session', None))

            if not all([target_year, target_race, target_session]):
                print("❌ [POSITION_MDI] 參數更新失敗：缺少必要參數")
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
            print(f"❌ [POSITION_MDI] update_parameters 失敗: {exc}")
            import traceback
            traceback.print_exc()
            return False
    
    def _show_error(self, title: str, message: str):
        """
        顯示錯誤對話框（已禁用彈窗功能）
        
        Args:
            title: 對話框標題
            message: 錯誤訊息
        """
        # ❌ 已禁用彈窗：僅保留方法以維持相容性
        # parent = self.chart_widget if hasattr(self, 'chart_widget') else None
        # QMessageBox.critical(parent, title, message)
        print(f"[POSITION_MDI] ⚠️ 錯誤: {title} - {message}")
