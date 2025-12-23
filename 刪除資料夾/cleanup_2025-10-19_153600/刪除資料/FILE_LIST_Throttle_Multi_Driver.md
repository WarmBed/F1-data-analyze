# 📄 檔案清單：Throttle Line Chart 多車手重構

**版本**: v2.0.0  
**日期**: 2025-10-08  
**狀態**: ✅ 核心實施已完成

---

## 🆕 新增檔案

### 1. throttle_multi_driver_chart_widget.py
**路徑**: `modules/gui/Throttle_analysis/throttle_line_chart_analysis/throttle_multi_driver_chart_widget.py`  
**行數**: 680 lines  
**用途**: 多車手油門折線圖組件（完全參考 Detailed Lap Analysis）

**內容結構**:
```python
# 1. ThrottleChartTheme - 顏色主題定義 (25 lines)
DRIVER1_COLOR = QColor(220, 53, 69)    # 紅色
DRIVER2_COLOR = QColor(0, 123, 255)    # 藍色
DRIVER3_COLOR = QColor(40, 167, 69)    # 綠色
DRIVER4_COLOR = QColor(255, 193, 7)    # 黃色
DRIVER5_COLOR = QColor(108, 117, 125)  # 灰色

# 2. ThrottleDataPoint - 單圈數據點 (15 lines)
lap_number: int
throttle_duration: float
throttle_percentage: float

# 3. ThrottleDataSeries - 車手數據系列 (20 lines)
driver_code: str
data_points: List[ThrottleDataPoint]
color: QColor

# 4. ThrottleChartWidget - 主圖表組件 (400 lines)
def paintEvent(self, event):
    # 繪製坐標軸、網格、折線、固定點、圖例

def mouseMoveEvent(self, event):
    # Hover 提示

def mousePressEvent(self, event):
    # 左鍵固定點，右鍵清除

def wheelEvent(self, event):
    # 滾輪縮放

# 5. DriverSelectionWidget - 車手選擇器 (100 lines)
drivers_selected = pyqtSignal(list)
# 5 個 QComboBox 水平排列

# 6. ThrottleMultiDriverChartWidget - 整合組件 (120 lines)
def update_chart_data(self, drivers_data):
    # 更新圖表顯示
```

**關鍵方法**:
- `paintEvent()` - 圖表繪製（坐標軸、網格、折線、圖例）
- `_draw_axes_and_grid()` - 坐標軸和網格繪製
- `_draw_throttle_lines()` - 多條折線繪製
- `_draw_legend()` - 可拖移圖例繪製
- `_find_closest_lap()` - 查找最近圈數（Hover 用）
- `set_available_drivers()` - 設定可用車手列表
- `update_chart_data()` - 更新圖表數據

**依賴項**:
```python
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel
from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont
from core.gui_i18n import get_text
```

**語法狀態**: ✅ 無錯誤

---

## 🔧 修改檔案

### 2. throttle_line_chart_data_loader.py
**路徑**: `modules/gui/Throttle_analysis/throttle_line_chart_analysis/throttle_line_chart_data_loader.py`  
**修改範圍**: Header + 新增 150 lines  
**版本**: v1.0.0 → v2.0.0

**修改內容**:

#### Header 更新
```python
版本: 2.0.0 (多車手模式)
修改日期: 2025-10-08
主要變更: 添加多車手數據處理支援
```

#### 新增屬性 (Line ~50)
```python
self.available_drivers = []   # 可用車手列表
self.selected_drivers = []    # 已選中的車手列表
self.multi_driver_data = {}   # 多車手數據：{driver_code: {...}}
```

#### 新增方法 (~150 lines)
```python
def _process_data(self, raw_data: Dict) -> Dict:
    """
    處理 Function 54 原始數據，轉換為多車手格式
    
    輸入: {'analysis': {'drivers': [...]}}
    輸出: {'VER': {'laps': {'1': {...}}, 'driver_info': {...}}}
    """
    # 80 lines

def load_multi_driver_data(self, **kwargs) -> bool:
    """載入多車手數據"""
    # 20 lines

def get_driver_data(self, driver_code: str) -> Dict:
    """獲取指定車手的數據"""
    # 10 lines

def get_available_drivers(self) -> list:
    """獲取可用車手列表"""
    # 5 lines

def set_selected_drivers(self, driver_codes: list):
    """設定已選中的車手"""
    # 5 lines
```

**數據格式轉換**:
```python
# 輸入 (Function 54)
{
    'metadata': {...},
    'analysis': {
        'drivers': [
            {
                'driver_code': 'VER',
                'team': 'Red Bull Racing',
                'laps': [
                    {
                        'lap_number': 1,
                        'full_throttle_duration_seconds': 45.2,
                        'full_throttle_percentage': 67.5,
                        'lap_time': 95.123,
                        'compound': 'SOFT',
                        'tire_life': 1,
                        'stint': 1
                    }
                ]
            }
        ]
    }
}

# 輸出 (多車手字典)
{
    'VER': {
        'laps': {
            '1': {
                'lap_number': 1,
                'full_throttle_duration_seconds': 45.2,
                'full_throttle_percentage': 67.5,
                'lap_time': 95.123,
                'compound': 'SOFT',
                'tire_life': 1,
                'stint': 1,
                'is_personal_best': False
            }
        },
        'driver_info': {
            'code': 'VER',
            'team': 'Red Bull Racing',
            'color': '#FFFFFF'
        }
    }
}
```

**語法狀態**: ✅ 無錯誤

---

### 3. throttle_line_chart_mdi.py
**路徑**: `modules/gui/Throttle_analysis/throttle_line_chart_analysis/throttle_line_chart_mdi.py`  
**修改範圍**: 完全重構，簡化至 ~150 lines（原 ~500 lines）  
**版本**: v1.0.0 → v2.0.0

**刪除內容** (約 350 lines):
- ❌ `_create_control_widget()` 方法
- ❌ `_create_control_panel()` 方法
- ❌ `_populate_driver_list()` 方法
- ❌ `_on_driver_changed()` 方法
- ❌ `_load_and_show_charts()` 方法
- ❌ `_create_chart_windows()` 方法
- ❌ `_add_chart_to_mdi()` 方法
- ❌ `_arrange_windows()` 方法
- ❌ `_connect_sync_signals()` 方法
- ❌ `_get_team_color()` 方法
- ❌ `_export_charts()` 方法
- ❌ 雙圖表視窗管理屬性

**修改導入**:
```python
# 舊版本
from .throttle_duration_chart_widget import ThrottleDurationChartWidget
from .lap_time_chart_widget import LapTimeChartWidget

# 新版本
from .throttle_multi_driver_chart_widget import ThrottleMultiDriverChartWidget
```

**新實現 (~150 lines)**:
```python
class ThrottleLineChartMDI(UniversalAnalysisMDI):
    def __init__(self, year, race, session, parent=None):
        super().__init__(analysis_type="throttle_line", parent=parent)
        self.chart_widget = None
    
    def create_data_manager(self):
        loader = ThrottleLineChartDataLoader(parent=self)
        loader.data_loaded.connect(self._on_data_loaded)
        loader.load_error.connect(self._on_data_error)
        return loader
    
    def create_chart_widget(self):
        """直接返回多車手圖表組件（無額外控制面板）"""
        self.chart_widget = ThrottleMultiDriverChartWidget(parent=self)
        self.chart_widget.drivers_selected.connect(self._on_drivers_selected)
        return self.chart_widget
    
    def load_data(self, force_reload: bool = False):
        """使用 load_multi_driver_data 載入"""
        success = self.data_manager.load_multi_driver_data(...)
        if success:
            available_drivers = self.data_manager.get_available_drivers()
            self.chart_widget.set_available_drivers(available_drivers)
    
    def _on_drivers_selected(self, driver_codes: list):
        """處理車手選擇，更新圖表"""
        drivers_data = {
            code: self.data_manager.get_driver_data(code)
            for code in driver_codes
        }
        self.chart_widget.update_chart_data(drivers_data)
```

**模組註冊更新**:
```python
UniversalAnalysisMDI.register_mdi_module_type(
    'throttle_line',
    AnalysisMDIConfig(
        display_name='油門折線圖（多車手）',
        supports_single_driver=False,  # v2.0.0 只支援多車手
        supports_dual_driver=False
    )
)
```

**語法狀態**: ✅ 無錯誤

---

### 4. throttle_line_chart_module.py
**路徑**: `modules/gui/Throttle_analysis/throttle_line_chart_analysis/throttle_line_chart_module.py`  
**修改範圍**: Header only (~20 lines)  
**版本**: v1.0.0 → v2.0.0

**修改內容**:
```python
# 舊版本
self._display_name = "Throttle Line Chart Analysis"
self._version = "1.0.0"
self._description = "F1 Throttle Line Chart Analysis - Single Driver Mode"

# 新版本
self._display_name = "Throttle Line Chart Analysis (Multi-Driver)"
self._version = "2.0.0"
self._description = "F1 Throttle Line Chart Analysis - Multi-Driver Mode (5 Drivers)"
```

**其他部分**: 保持不變（與 `ThrottleLineChartMDI` 整合）

**語法狀態**: ✅ 無錯誤

---

## 📊 統計總結

### 代碼變更量
| 類型 | 檔案數 | 行數 | 說明 |
|------|--------|------|------|
| 新增 | 1 | +680 | throttle_multi_driver_chart_widget.py |
| 修改 | 3 | +150, -350, +20 | 數據載入器、MDI、模組主檔案 |
| 刪除 | 0 | 0 | 無刪除檔案（直接覆蓋） |
| **總計** | **4** | **+850, -350** | **淨增 500 lines** |

### 功能對比
| 功能 | v1.0.0 (單車手) | v2.0.0 (多車手) |
|------|----------------|----------------|
| 支援車手數 | 1 | 5 |
| 圖表數量 | 2（全油門+圈速） | 1（多車手油門） |
| 車手選擇 | 單下拉選單 | 5 個下拉選單 |
| UI 參考 | 自訂 | Detailed Lap Analysis |
| 控制面板 | 獨立控制面板 | 無（整合在圖表組件） |
| 視窗管理 | 雙 MDI 子視窗 | 單一圖表組件 |
| 顏色系統 | 車隊顏色 | 5 色固定（紅藍綠黃灰） |

---

## 🔗 檔案依賴關係

```
f1t_gui_main.py
    ↓ (載入模組)
throttle_line_chart_module.py (IAnalysisModule)
    ↓ (創建)
throttle_line_chart_mdi.py (UniversalAnalysisMDI)
    ↓ (create_data_manager)
    ├── throttle_line_chart_data_loader.py (UniversalDataLoader)
    │       ↓ (處理數據)
    │       Function 54 JSON → {driver: {laps: {...}}}
    │
    └── (create_chart_widget)
        throttle_multi_driver_chart_widget.py
            ├── ThrottleChartWidget (圖表繪製)
            ├── DriverSelectionWidget (車手選擇)
            └── ThrottleMultiDriverChartWidget (整合)
```

---

## ✅ 驗證清單

### 語法檢查
- [x] throttle_multi_driver_chart_widget.py - ✅ No errors
- [x] throttle_line_chart_data_loader.py - ✅ No errors
- [x] throttle_line_chart_mdi.py - ✅ No errors
- [x] throttle_line_chart_module.py - ✅ No errors

### 架構驗證
- [x] 與 Detailed Lap Analysis 一致性 - ✅ 通過
- [x] 無多餘 UI 元素 - ✅ 通過
- [x] 數據流正確性 - ✅ 通過
- [x] 信號槽連接正確性 - ✅ 通過

### 文檔完整性
- [x] 代碼註解清晰 - ✅ 中文註解
- [x] 類型提示完整 - ✅ Dict, List, Optional
- [x] Docstring 規範 - ✅ 三引號註解

---

## 📋 待執行項目

### Phase 5: 測試與優化 ⏳
- [ ] 啟動 F1T GUI 主程式
- [ ] 打開 Throttle Line Chart 模組
- [ ] 測試車手選擇功能
- [ ] 測試圖表繪製正確性
- [ ] 測試交互功能（Hover, 固定點, 縮放）
- [ ] 測試圖例拖移
- [ ] 性能測試（5 車手 × 60 圈）

### 數據準備
- [ ] 確保有 Function 54 JSON 檔案
- [ ] 或手動執行 CLI 生成：
  ```powershell
  python f1_analysis_modular_main.py -f 54 -y 2024 -r Japan -s R
  ```

---

## 🎯 下一步行動

1. **立即測試**: 啟動 GUI 驗證功能
   ```powershell
   python f1t_gui_main.py
   ```

2. **數據檢查**: 確認 Function 54 JSON 可用
   ```powershell
   # 檢查 json 目錄
   ls json/throttle_ratio_*.json
   ```

3. **問題追蹤**: 記錄測試中發現的問題
   - 在 `tasks/` 創建 `throttle_multi_test_issues.md`

---

**狀態**: ✅ **核心實施已完成，所有檔案語法無錯誤**  
**下一步**: GUI 測試驗證  
**最後更新**: 2025-10-08
