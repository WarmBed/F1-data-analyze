# F1T 連動模組化遷移指南

## 概述

為了解決代碼重複問題，我們創建了統一的連動模組系統。這個系統將所有連動相關的功能模組化，消除了在三個分析模組中重複的 20+ 個連動函數。

## 新連動系統架構

```
modules/gui/lap_analysis/linkage/
├── __init__.py           # 模組介面
├── linkage_mixin.py      # 連動混合類
├── linkage_manager.py    # 連動管理器
├── linkage_ui.py         # 標準化UI組件
└── linkage_example.py    # 使用示例
```

## 核心組件

### 1. LapAnalysisLinkageMixin
統一的連動邏輯混合類，提供：
- 連動狀態管理 (`master_linkage_enabled`, `individual_linkage_enabled`)
- 信號處理 (`on_x_linkage_received`, `on_click_linkage_received`)
- 狀態查詢 (`_is_linkage_fully_enabled`)
- 清除功能 (`clear_linkage_marks`)

### 2. LapAnalysisLinkageDrawingMixin
統一的連動繪製功能，提供：
- X軸連動線繪製 (`draw_x_linkage_line`)
- 點擊連動線繪製 (`draw_click_linkage_line`)
- 標準化的視覺樣式和顏色

### 3. LinkageManager
集中式連動管理器，提供：
- 模組註冊和管理
- 信號統一分發
- 主開關狀態控制
- 模組統計和監控

### 4. 標準化UI組件
- `LinkageButton`: 統一樣式的連動按鈕
- `LinkageStatusIndicator`: 狀態指示器
- `LinkageControlPanel`: 完整的控制面板
- `LinkageToolBar`: 可嵌入的工具欄

## 遷移步驟

### 第一步：修改圖表類繼承
```python
# 原來的類
class SpeedAnalysisChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

# 遷移後的類
from modules.gui.lap_analysis.linkage import LapAnalysisLinkageMixin, LapAnalysisLinkageDrawingMixin, linkage_manager

class SpeedAnalysisChartWidget(QWidget, LapAnalysisLinkageMixin, LapAnalysisLinkageDrawingMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化連動功能
        self.init_linkage(module_type="speed_analysis")
        
        # 註冊到連動管理器
        linkage_manager.register_module(self, "speed_analysis")
```

### 第二步：實現必要的抽象方法
```python
def draw_linkage_lines(self, painter):
    """實現抽象方法：繪製連動線條"""
    self.draw_x_linkage_line(painter, self.current_x_linkage_position)
    self.draw_click_linkage_line(painter, self.current_click_linkage_position)

def get_chart_rect(self):
    """實現抽象方法：獲取圖表區域"""
    return self.rect().adjusted(10, 50, -10, -10)
```

### 第三步：移除重複的連動代碼
刪除以下重複的方法：
- `_is_linkage_fully_enabled()`
- `set_master_linkage_enabled()`
- `on_master_linkage_changed()`
- `set_linkage_enabled()`
- `on_x_linkage_received()`
- `on_x_linkage_clear()`
- `on_click_linkage_received()`
- `on_click_linkage_clear()`
- `clear_linkage_marks()`

### 第四步：更新UI組件
```python
# 使用標準化的連動工具欄
from modules.gui.lap_analysis.linkage import create_linkage_toolbar

self.linkage_toolbar = create_linkage_toolbar(
    title="速度分析",
    show_master=False,  # 主開關由主視窗控制
    show_individual=True,
    parent=self
)
layout.addWidget(self.linkage_toolbar)

# 連接信號
self.linkage_toolbar.individual_linkage_toggled.connect(self.set_linkage_enabled)
self.linkage_toolbar.clear_linkage_requested.connect(self.clear_linkage_marks)
```

### 第五步：更新主視窗整合
```python
# 在主視窗中設置主連動開關
from modules.gui.lap_analysis.linkage import linkage_manager

def toggle_master_linkage(self, enabled: bool):
    """切換主連動開關"""
    linkage_manager.set_master_linkage_enabled(enabled)
    # 更新按鈕狀態
    self.set_linkage_button_state(enabled)
```

## 遷移好處

### 1. 代碼簡化
- **消除重複**：移除了 20+ 個重複的連動函數
- **統一邏輯**：所有連動邏輯集中在混合類中
- **標準化**：統一的介面和實現方式

### 2. 維護性提升
- **集中管理**：連動邏輯修改只需更新混合類
- **易於測試**：獨立的連動模組便於單元測試
- **版本控制**：連動功能的變更更容易追蹤

### 3. 擴展性增強
- **新模組**：新的分析模組只需繼承混合類
- **功能擴展**：新的連動功能可以直接添加到混合類
- **UI一致性**：標準化的UI組件確保界面一致

### 4. 架構改善
- **解耦合**：連動邏輯與具體圖表實現分離
- **可重用**：連動功能可以在其他項目中重用
- **模組化**：清晰的模組邊界和職責分工

## 影響的檔案清單

### 需要遷移的檔案
1. `modules/gui/lap_analysis/speed_analysis/speed_analysis_chart_widget.py`
2. `modules/gui/lap_analysis/rpm_analysis/rpm_analysis_chart_widget.py`
3. `modules/gui/lap_analysis/throttle_analysis/Throttle_analysis_chart_widget.py`

### 需要更新的檔案
1. `f1t_gui_main.py` - 主視窗連動控制
2. 各個容器類的 `set_linkage_enabled` 方法

### 預估工作量
- **檔案修改**：3-4 個主要檔案
- **代碼移除**：約 200-300 行重複代碼
- **新增代碼**：約 50-100 行整合代碼
- **測試時間**：2-3 小時驗證所有連動功能

## 遷移時程建議

1. **第一階段**（1-2小時）：完成一個模組的遷移並測試
2. **第二階段**（1小時）：遷移其餘兩個模組
3. **第三階段**（1小時）：整合測試和除錯
4. **第四階段**（30分鐘）：清理舊代碼和文檔更新

這個模組化的連動系統將大大提高代碼的可維護性和擴展性，同時減少技術債務。
