"""
詳細圈速分析 MDI 模組
功能: 提供詳細的圈速分析，包括圈速趨勢、智能標記和輪胎策略時間軸
"""

from typing import Dict, Any, List, Optional
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QComboBox, QLabel, QCheckBox, QGridLayout
from PyQt5.QtCore import pyqtSignal, QObject

# 導入基類
from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI
from modules.gui.driverLap_analysis.driverlap_data_loader import driverLapDataLoader


class driverLapAnalysisDataManager(QObject):
    """詳細圈速分析數據管理器 - 支援 CLI Function 28"""
    
    # 定義信號（UniversalAnalysisMDI 需要的）
    data_loaded = pyqtSignal(dict)  # 數據載入完成信號
    error_occurred = pyqtSignal(str)  # 錯誤發生信號
    
    def __init__(self, parent=None):
        """
        初始化詳細圈速分析數據管理器
        支援 CLI Function 28 格式的詳細圈速分析數據
        """
        super().__init__(parent)
        
        # 詳細圈速分析特定屬性
        self.detailed_laptime_data = {}  # 存儲所有車手的詳細圈速數據
        self.available_drivers = []  # 可用車手列表
        self.selected_drivers = []  # 已選中的車手列表
        self.tire_strategy_data = {}  # 輪胎策略數據
        self.incident_markers = {}  # 事故標記數據
        
        # 載入狀態控制
        self._loading = False
        self._last_load_params = None
        
        # 數據載入器 - 使用有信號的專門載入器
        self.data_loader = driverLapDataLoader(parent=self)
        
        print(f"[LAPTIME_DATA_MANAGER] 詳細圈速分析數據管理器初始化完成")
        
    def load_data(self, **kwargs) -> bool:
        """載入詳細圈速分析數據 - 委託給專門的數據載入器"""
        try:
            # 檢查是否與上次載入參數相同
            current_params = (kwargs.get('year'), kwargs.get('race'), kwargs.get('session'))
            print(f"[LAPTIME_DATA_MANAGER] 🔍 載入檢查: 當前參數={current_params}, 上次參數={self._last_load_params}, 載入中={self._loading}")
            
            if self._last_load_params == current_params and not self._loading:
                print(f"[LAPTIME_DATA_MANAGER] ⚠️ 參數未變化，跳過重複載入: {current_params}")
                return True
            
            # 如果參數有變化，強制重置載入狀態
            if self._last_load_params != current_params:
                print(f"[LAPTIME_DATA_MANAGER] 🔄 參數變化檢測: {self._last_load_params} -> {current_params}")
                self._loading = False  # 強制重置載入狀態
                print(f"[LAPTIME_DATA_MANAGER] ✅ 載入狀態已重置為: {self._loading}")
                
            # 檢查是否正在載入中
            if self._loading:
                print(f"[LAPTIME_DATA_MANAGER] ⚠️ 數據正在載入中，跳過重複請求")
                return True
                
            self._loading = True
            self._last_load_params = current_params
            
            print(f"[LAPTIME_DATA_MANAGER] 🔄 開始載入數據: {kwargs}")
            
            # 提取參數
            year = kwargs.get('year', 2025)
            race = kwargs.get('race', 'Japan')
            session = kwargs.get('session', 'R')
            driver = kwargs.get('driver', 'all_drivers')
            
            print(f"[LAPTIME_DATA_MANAGER] 載入參數: {year} {race} {session} {driver}")
            
            # 使用專門的數據載入器
            if self.data_loader:
                print(f"[LAPTIME_DATA_MANAGER] 使用專門數據載入器載入數據")
                
                # 連接載入器信號（如果還沒連接）
                if hasattr(self.data_loader, 'data_loaded'):
                    try:
                        self.data_loader.data_loaded.disconnect()  # 先斷開避免重複連接
                    except:
                        pass
                    self.data_loader.data_loaded.connect(self._on_data_loaded)
                    print(f"[LAPTIME_DATA_MANAGER] ✅ 已連接數據載入器信號")
                
                # 連接錯誤信號
                if hasattr(self.data_loader, 'load_error'):
                    try:
                        self.data_loader.load_error.disconnect()  # 先斷開避免重複連接
                    except:
                        pass
                    self.data_loader.load_error.connect(self._on_load_error)
                    print(f"[LAPTIME_DATA_MANAGER] ✅ 已連接錯誤處理信號")
                
                # 委託給專門載入器
                self.data_loader.load_from_parameters(
                    year=year, 
                    race=race, 
                    session=session, 
                    driver=driver
                )
                print(f"[LAPTIME_DATA_MANAGER] ✅ 已委託給專門載入器")
                return True
            else:
                print(f"[LAPTIME_DATA_MANAGER] ❌ 數據載入器未初始化")
                self._loading = False
                return False
                
        except Exception as e:
            print(f"[LAPTIME_DATA_MANAGER] ❌ 載入數據失敗: {e}")
            import traceback
            traceback.print_exc()
            self.error_occurred.emit(str(e))
            self._loading = False
            return False
        
    def _on_data_loaded(self, data):
        """處理專門載入器的數據載入完成信號"""
        try:
            print(f"[LAPTIME_DATA_MANAGER] 📥 接收到載入器數據")
            print(f"   - 數據類型: {type(data)}")
            if isinstance(data, dict):
                print(f"   - 數據鍵: {list(data.keys())}")
            
            # 處理數據並發出信號給 MDI
            processed_data = self.process_loaded_data(data)
            self.data_loaded.emit(processed_data)
            print(f"[LAPTIME_DATA_MANAGER] ✅ 已發出 data_loaded 信號")
            
            # 重置載入狀態
            self._loading = False
            
        except Exception as e:
            print(f"[LAPTIME_DATA_MANAGER] ❌ 數據處理失敗: {e}")
            import traceback
            traceback.print_exc()
            self.error_occurred.emit(str(e))
            self._loading = False
    
    def _on_load_error(self, error_message):
        """處理專門載入器的載入錯誤信號"""
        try:
            print(f"[LAPTIME_DATA_MANAGER] ❌ 載入器報告錯誤: {error_message}")
            
            # 重置載入狀態
            self._loading = False
            
            # 轉發錯誤信號給 MDI
            self.error_occurred.emit(error_message)
            
        except Exception as e:
            print(f"[LAPTIME_DATA_MANAGER] ❌ 錯誤處理失敗: {e}")
            self._loading = False
        
    def set_parameters(self, year: str, race: str, session: str):
        """設置分析參數"""
        print(f"🔧 [PARAMS] 設置分析參數: {year} {race} {session}")
        
        # 設置本地參數
        self.current_year = year
        self.current_race = race
        self.current_session = session
        print(f"🔧 [PARAMS] 本地參數設置完成: {year} {race} {session}")
        return True
        
    def update_analysis_parameters(self, year: str, race: str, session: str) -> bool:
        """更新分析參數（與 set_parameters 相同功能，提供不同的介面名稱）"""
        try:
            print(f"🔄 [UPDATE_PARAMS] 更新分析參數: {year} {race} {session}")
            result = self.set_parameters(year, race, session)
            if result:
                print(f"✅ [UPDATE_PARAMS] 更新分析參數成功: {year} {race} {session}")
            else:
                print(f"❌ [UPDATE_PARAMS] 更新分析參數失敗: {year} {race} {session}")
            return result
        except Exception as e:
            print(f"❌ [UPDATE_PARAMS] 更新分析參數失敗: {e}")
            return False
        
    def get_expected_file_patterns(self, year: int, race: str, session: str) -> List[str]:
        """取得預期的檔案模式"""
        patterns = [
            f"detailed_laptime_analysis_{year}_{race}_{session}*.json",
            f"{race}_{year}_detailed_laptime_*.json"
        ]
        return patterns
        
    def _validate_data_format(self, data: Any) -> bool:
        """驗證數據格式 - 支援 Function 28 JSON 格式"""
        if not isinstance(data, dict):
            print("數據格式錯誤：必須是字典格式")
            return False
        
        # 支援 Function 28 JSON 格式
        valid_formats = [
            "all_drivers_detailed_laptime",  # CLI -f28 主要格式
            "detailed_laptime_analysis"      # 另一種可能的格式
        ]
        
        has_valid_format = any(key in data for key in valid_formats)
        if not has_valid_format:
            print(f"數據格式錯誤：缺少必要欄位，支援格式: {valid_formats}")
            print(f"實際數據鍵值: {list(data.keys())}")
            return False
            
        return True
        
    def _process_data(self, data: Any) -> Dict[str, Any]:
        """處理數據的具體實現"""
        return self.process_loaded_data(data)
        
    def process_loaded_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """處理載入的詳細圈速分析數據 - 支援 Function 28 JSON 格式"""
        try:
            if not isinstance(data, dict):
                raise ValueError("數據格式不正確：必須是字典格式")
                
            # 儲存完整的原始數據
            self.data = data
            
            # 支援 Function 28 JSON 格式的數據解析
            if "all_drivers_detailed_laptime" in data:
                # CLI -f28 標準格式
                self.detailed_laptime_data = data["all_drivers_detailed_laptime"]
                print("使用 all_drivers_detailed_laptime 格式 (CLI -f28)")
            elif "detailed_laptime_analysis" in data:
                # 另一種可能的格式
                self.detailed_laptime_data = data["detailed_laptime_analysis"]
                print("使用 detailed_laptime_analysis 格式")
            else:
                raise ValueError("找不到支援的詳細圈速分析數據格式")
                
            # 獲取摘要數據
            if "analysis_info" in data:
                self.analysis_stats = data["analysis_info"]
            elif "metadata" in data:
                self.analysis_stats = data["metadata"]
                print("使用 metadata 作為摘要數據")
            else:
                self.analysis_stats = {}
                
            # 轉換為分析用數據格式
            processed_data = {
                "detailed_laptime_data": self._process_detailed_laptime_analysis_data(),
                "summary": self.analysis_stats,
                "metadata": data.get("metadata", {}),
                "analysis_mode": data.get("analysis_mode", "all"),
                "drivers_analyzed": data.get("drivers_analyzed", list(self.detailed_laptime_data.keys())),
                "charts_data": self._prepare_detailed_laptime_chart_data()
            }
            
            print(f"成功處理 {len(self.detailed_laptime_data)} 車手詳細圈速數據")
            
            return processed_data
            
        except Exception as e:
            print(f"數據處理失敗: {e}")
            return {"error": str(e), "raw_data": data}
    
    def _process_detailed_laptime_analysis_data(self) -> Dict[str, List]:
        """處理詳細圈速分析數據"""
        drivers_data = []
        
        # 處理所有車手的詳細圈速數據
        for driver_code, driver_data in self.detailed_laptime_data.items():
            if isinstance(driver_data, dict):
                driver_info = {
                    "driver": driver_code,
                    "total_laps": driver_data.get("total_laps", 0),
                    "detailed_lap_data": driver_data.get("detailed_lap_data", []),
                    "smart_markers_summary": driver_data.get("smart_markers_summary", {}),
                    "fastest_lap": self._extract_fastest_lap(driver_data),
                    "analysis_success": driver_data.get("success", True)
                }
                drivers_data.append(driver_info)
        
        return {
            "drivers": drivers_data,
            "total_drivers": len(drivers_data)
        }
        
    def _extract_fastest_lap(self, driver_data: Dict) -> Dict:
        """提取車手最快圈數據"""
        detailed_laps = driver_data.get("detailed_lap_data", [])
        if not detailed_laps:
            return {}
        
        # 找出最快圈
        fastest_lap = min(detailed_laps, key=lambda lap: lap.get("lap_time_seconds", float('inf')))
        return {
            "lap_number": fastest_lap.get("lap_number", 0),
            "lap_time": fastest_lap.get("lap_time", "N/A"),
            "lap_time_seconds": fastest_lap.get("lap_time_seconds", 0),
            "tire_compound": fastest_lap.get("tire_compound", "UNKNOWN")
        }
        
    def _prepare_detailed_laptime_chart_data(self) -> Dict[str, Any]:
        """準備詳細圈速圖表數據 - 構建圖表組件期望的數據結構"""
        if not hasattr(self, 'data') or not self.data:
            return {}
        
        # 構建圖表組件期望的數據結構
        chart_data = {
            "drivers_analyzed": list(self.detailed_laptime_data.keys()),
            "all_drivers_detailed_laptime": self.detailed_laptime_data,
            "detailed_laptime_analysis": self.detailed_laptime_data,
            "analysis_info": self.data.get("analysis_info", {}),
            "metadata": self.data.get("metadata", {})
        }
        
        print(f"圖表數據已準備：{len(chart_data['drivers_analyzed'])} 個車手")
        
        return chart_data
        
    def get_detailed_laptime_summary(self) -> Dict[str, Any]:
        """獲取詳細圈速分析摘要統計"""
        return {
            "total_drivers": len(self.detailed_laptime_data),
            "total_laps": sum(driver_data.get("total_laps", 0) 
                            for driver_data in self.detailed_laptime_data.values() 
                            if isinstance(driver_data, dict)),
            "smart_markers_available": any(
                driver_data.get("smart_markers_summary", {})
                for driver_data in self.detailed_laptime_data.values()
                if isinstance(driver_data, dict)
            ),
            "has_detailed_laptime_data": len(self.detailed_laptime_data) > 0,
            "analysis_stats": self.analysis_stats.get("summary", {})
        }


class driverLapAnalysisMDI(UniversalAnalysisMDI):
    """詳細圈速分析 MDI 類 - 實現 UniversalAnalysisMDI 介面"""
    
    def __init__(self, parent=None):
        """初始化詳細圈速分析 MDI"""
        super().__init__(analysis_type='laptime', parent=parent)
        print(f"[LAPTIME_MDI] 詳細圈速分析 MDI 基類初始化完成")
        
        # 調用模組初始化來創建數據管理器和圖表組件
        if self.initialize_module(parent_widget=parent):
            print(f"[LAPTIME_MDI] 詳細圈速分析 MDI 完整初始化成功")
        else:
            print(f"[LAPTIME_MDI] 詳細圈速分析 MDI 初始化失敗")
        
    def create_data_manager(self):
        """創建數據管理器"""
        print(f"[LAPTIME_MDI] 創建詳細圈速分析數據管理器")
        return driverLapAnalysisDataManager(parent=self)
        
    def create_chart_widget(self):
        """創建圖表組件"""
        try:
            from .driverlap_analysis_chart_widget import driverLapAnalysisChartWidget
            # 修正：不要傳遞 self 作為 parent，讓圖表組件自己處理父子關係
            chart_widget = driverLapAnalysisChartWidget()
            print(f"[LAPTIME_MDI] 詳細圈速分析圖表組件創建成功")
            return chart_widget
        except ImportError as e:
            print(f"[LAPTIME_MDI] 圖表組件導入失敗: {e}")
            # 創建一個簡單的替代組件
            from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget
            from PyQt5.QtCore import Qt
            
            widget = QWidget()
            layout = QVBoxLayout(widget)
            
            label = QLabel("詳細圈速分析圖表")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("QLabel { color: blue; font-size: 16px; padding: 20px; }")
            
            status_label = QLabel("等待數據載入...")
            status_label.setAlignment(Qt.AlignCenter)
            status_label.setStyleSheet("QLabel { color: gray; font-size: 12px; }")
            
            layout.addWidget(label)
            layout.addWidget(status_label)
            
            # 添加一個簡單的更新方法
            def update_data(data):
                if isinstance(data, dict) and 'drivers_analyzed' in data:
                    drivers_count = len(data['drivers_analyzed'])
                    status_label.setText(f"已載入 {drivers_count} 位車手的詳細圈速數據")
                else:
                    status_label.setText("數據格式不正確")
            
            widget.update_data = update_data
            
            return widget
        except Exception as e:
            print(f"[LAPTIME_MDI] 創建詳細圈速分析圖表組件失敗: {e}")
            # 返回一個簡單的佔位符
            from PyQt5.QtWidgets import QLabel
            from PyQt5.QtCore import Qt
            placeholder = QLabel("詳細圈速分析圖表載入失敗")
            placeholder.setAlignment(Qt.AlignCenter)
            return placeholder


# 導入專用圖表組件
from .driverlap_analysis_chart_widget import driverLapAnalysisChartWidget


class driverLapAnalysisControlWidget(QWidget):
    """詳細圈速分析控制面板"""
    
    # 信號定義
    chart_type_changed = pyqtSignal(str)
    parameter_changed = pyqtSignal(str, object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """設置UI"""
        layout = QVBoxLayout(self)
        
        # 圖表選擇群組
        chart_group = QGroupBox("圖表類型")
        chart_layout = QGridLayout(chart_group)
        
        self.chart_combo = QComboBox()
        self.chart_combo.addItems([
            "詳細圈速分析",
            "圈速趨勢比較",
            "智能標記顯示"
        ])
        self.chart_combo.currentTextChanged.connect(self._on_chart_type_changed)
        
        chart_layout.addWidget(QLabel("選擇圖表:"), 0, 0)
        chart_layout.addWidget(self.chart_combo, 0, 1)
        
        layout.addWidget(chart_group)
        
        # 顯示選項群組
        display_group = QGroupBox("顯示選項")
        display_layout = QGridLayout(display_group)
        
        self.show_grid_cb = QCheckBox("顯示網格")
        self.show_grid_cb.setChecked(True)
        self.show_grid_cb.toggled.connect(lambda x: self.parameter_changed.emit("show_grid", x))
        
        self.show_legend_cb = QCheckBox("顯示圖例")
        self.show_legend_cb.setChecked(True)
        self.show_legend_cb.toggled.connect(lambda x: self.parameter_changed.emit("show_legend", x))
        
        display_layout.addWidget(self.show_grid_cb, 0, 0)
        display_layout.addWidget(self.show_legend_cb, 0, 1)
        
        layout.addWidget(display_group)
        
        layout.addStretch()
        
    def _on_chart_type_changed(self, text: str):
        """圖表類型改變處理"""
        chart_type_map = {
            "詳細圈速分析": "laptime_analysis",
            "圈速趨勢比較": "laptime_trends",
            "智能標記顯示": "smart_markers"
        }
        
        chart_type = chart_type_map.get(text, "laptime_analysis")
        self.chart_type_changed.emit(chart_type)


# 模組註冊 - 確保在導入時自動註冊
def register_detailed_laptime_analysis_module():
    """註冊詳細圈速分析模組"""
    try:
        # 這裡可以添加到全局模組註冊表
        pass
    except Exception as e:
        print(f"[WARNING] 詳細圈速分析模組註冊失敗: {str(e)}")

# 執行註冊
register_detailed_laptime_analysis_module()
