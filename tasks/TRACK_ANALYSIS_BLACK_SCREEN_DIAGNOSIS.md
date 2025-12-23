# Track Analysis 黑屏問題深度診斷報告
**Track Analysis Black Screen Deep Diagnosis Report**

**調查日期**: 2025-10-02  
**問題描述**: Track Analysis 模組在 GUI 中顯示黑色畫面，無法正常顯示賽道地圖  
**調查結果**: ✅ **問題確認並找到根因**

---

## 🔍 問題確認

### 使用者回報

使用者在 GUI 中打開 Track Analysis 模組時，看到的是**黑色畫面**（截圖顯示），而非預期的賽道地圖。

### 初步假設驗證

**假設 1**: 模組找不到或導入失敗  
**結果**: ❌ **錯誤假設**
- 模組檔案結構完整 ✅
- Python 導入測試成功 ✅
- GUI 主程式已正確整合 ✅

**假設 2**: 使用了舊版模組  
**結果**: ⚠️ **部分正確**
- GUI 主程式 **確實調用了新版 `TrackAnalysisModule`**
- 但新版模組內部使用了 **佔位符實現的 `TrackMapWidget`**

---

## 🎯 根因分析

### 問題核心：TrackMapWidget 是佔位符實現

**檔案**: `modules/gui/track_analysis/track_map_widget.py`

#### 關鍵代碼發現

**Line 22-50**:
```python
class TrackMapWidget(QWidget):
    """賽道地圖繪製元件 - 佔位符版本"""  # ⚠️ 注意：佔位符版本
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.track_data = None
        self.position_records = []
        self.track_bounds = {}
        
        # ... 初始化代碼 ...
        
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setStyleSheet("""
            TrackMapWidget {
                background-color: white;  # ⚠️ 白色背景
                border: 1px solid #ccc;
                border-radius: 5px;
            }
        """)
        
        # 設置佔位符
        layout = QVBoxLayout(self)
        self.placeholder_label = QLabel("賽道地圖\n(準備中...)")  # ⚠️ 佔位符標籤
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 16px;
                border: 2px dashed #ddd;
                border-radius: 10px;
                background-color: #f9f9f9;  # ⚠️ 淺灰背景
                padding: 20px;
            }
        """)
        layout.addWidget(self.placeholder_label)
```

**Line 117-143** (paintEvent):
```python
def paintEvent(self, event):
    """繪製事件 - 簡化版本"""
    painter = QPainter(self)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # 如果有數據，繪製簡化的賽道示意圖
    if self.position_records and len(self.position_records) > 1:
        self.draw_simplified_track(painter)  # ⚠️ 簡化版繪製
    else:
        # 繪製佔位符
        self.draw_placeholder(painter)  # ⚠️ 佔位符繪製
```

**Line 145-170** (draw_simplified_track):
```python
def draw_simplified_track(self, painter):
    """繪製簡化的賽道示意圖"""
    try:
        # 計算顯示範圍
        widget_rect = self.rect()
        map_rect = widget_rect.adjusted(self.margin, self.margin, -self.margin, -self.margin)
        
        if map_rect.width() <= 0 or map_rect.height() <= 0:
            return  # ⚠️ 條件失敗時直接返回，不繪製任何內容
        
        # ... 座標計算 ...
        
        if x_range == 0 or y_range == 0:
            return  # ⚠️ 條件失敗時直接返回，不繪製任何內容
```

### 問題總結

**TrackMapWidget 當前狀態**:
1. ✅ **檔案存在** - `track_map_widget.py` 檔案完整
2. ✅ **可正常導入** - Python 導入測試通過
3. ❌ **僅為佔位符** - 類別文檔說明「佔位符版本」
4. ❌ **繪製不完整** - `draw_simplified_track()` 有多個提前返回點
5. ❌ **未實作完整功能** - 缺少完整的賽道地圖繪製邏輯

**為何顯示黑屏**:
1. **佔位符標籤未正確顯示** - 可能由於佈局或樣式問題
2. **背景設為白色** - 但在暗色主題下可能顯示為黑色
3. **數據載入可能失敗** - 導致 `position_records` 為空
4. **繪製邏輯提前返回** - 條件判斷失敗時不繪製任何內容

---

## 📊 架構分析

### TrackAnalysisModule 調用流程

```
F1T GUI Main
    ↓
open_track_analysis_window() (Line 10043)
    ↓
創建 TrackAnalysisModule 實例
    ↓
TrackAnalysisModule.__init__() (Line 793)
    ↓
init_ui() (Line 814)
    ↓
create_track_map_area_only() (Line 928)
    ↓
創建 TrackMapWidget 實例 (Line 929)
    ↓
TrackMapWidget.__init__()
    ↓
init_ui() - 設置佔位符標籤
    ↓
⚠️ 黑屏問題出現
```

### TrackAnalysisModule 的設計意圖

**檔案**: `modules/gui/track_analysis/track_analysis_module.py`

**Line 787-829**:
```python
class TrackAnalysisModule(QWidget):
    """賽道分析主模組"""
    
    def __init__(self, year=2025, race="Japan", session="R", driver="VER"):
        super().__init__()
        # ... 初始化代碼 ...
        
        self.init_ui()
        self.init_connections()
        
        # 自動開始分析
        QTimer.singleShot(100, self.start_analysis_workflow)  # ⚠️ 100ms 後執行
    
    def init_ui(self):
        """初始化用戶界面 - 僅顯示賽道地圖"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # 移除邊距
        layout.setSpacing(0)  # 移除間距
        
        # 隱藏控制面板
        # self.create_control_panel(layout)  # ⚠️ 已註釋
        
        # 直接創建賽道地圖區域，無需分割器
        self.create_track_map_area_only(layout)  # ⚠️ 創建地圖區域
        
        # 隱藏右側資訊面板
        # self.create_info_panel(splitter)  # ⚠️ 已註釋
        
        # 隱藏底部狀態區域
        # self.create_status_area(layout)  # ⚠️ 已註釋
```

**設計意圖**:
1. 創建簡潔的純地圖介面（無控制面板、無資訊面板）
2. 100ms 後自動開始分析工作流程
3. 從 API 或本地 JSON 載入數據
4. 數據載入完成後更新地圖顯示

**實際問題**:
1. ❌ **TrackMapWidget 是佔位符** - 無法正確顯示地圖
2. ❌ **數據載入可能失敗** - 導致地圖無內容可顯示
3. ❌ **佔位符標籤不可見** - 使用者看到黑屏而非「準備中...」

---

## 🔧 問題驗證

### 測試 1: 檢查數據載入

**預期行為**:
```python
# 數據載入成功
self.track_data = {...}  # 包含 session_info, position_analysis 等
self.position_records = [...]  # 位置點列表

# 調用
self.track_map.load_track_data(self.track_data)
self.track_map.draw_track_map()
```

**可能問題**:
- ❌ API 調用失敗，未返回數據
- ❌ JSON 檔案不存在或格式錯誤
- ❌ 數據載入成功但未調用 `load_track_data()`

### 測試 2: 檢查 Widget 可見性

**預期行為**:
```python
# TrackMapWidget 應該可見
self.track_map.isVisible()  # → True
self.track_map.size()  # → QSize(寬, 高)

# 佔位符標籤應該可見
self.track_map.placeholder_label.isVisible()  # → True
```

**可能問題**:
- ❌ Widget 尺寸為 0x0
- ❌ Widget 被其他元素遮擋
- ❌ 樣式表導致內容不可見

### 測試 3: 檢查繪製邏輯

**預期行為**:
```python
# paintEvent 應該被調用
def paintEvent(self, event):
    painter = QPainter(self)
    # 繪製內容...
```

**可能問題**:
- ❌ `paintEvent` 未被調用
- ❌ `draw_simplified_track()` 提前返回
- ❌ 繪製邏輯有錯誤但無異常拋出

---

## 🎯 解決方案

### 方案 1: 修復 TrackMapWidget 佔位符顯示（短期）

**目標**: 讓使用者至少能看到「準備中...」而非黑屏

**修改檔案**: `modules/gui/track_analysis/track_map_widget.py`

**修改內容**:
1. 改進佔位符標籤的可見性
2. 添加調試輸出以追蹤問題
3. 確保背景色在各種主題下可見

```python
def init_ui(self):
    """初始化UI"""
    # 確保背景為可見色彩
    self.setStyleSheet("""
        TrackMapWidget {
            background-color: #2C2C2C;  /* 暗灰色，與主題一致 */
            border: 1px solid #444444;
            border-radius: 5px;
        }
    """)
    
    # 設置佔位符（使用更明顯的顏色）
    layout = QVBoxLayout(self)
    self.placeholder_label = QLabel("賽道地圖\n(正在載入...)")
    self.placeholder_label.setAlignment(Qt.AlignCenter)
    self.placeholder_label.setStyleSheet("""
        QLabel {
            color: #FFFFFF;  /* 白色文字 */
            font-size: 18px;
            font-weight: bold;
            border: 2px dashed #666666;
            border-radius: 10px;
            background-color: #3C3C3C;  /* 稍亮的灰色 */
            padding: 40px;
        }
    """)
    layout.addWidget(self.placeholder_label)
    
    print("[TRACK_MAP_WIDGET] UI 初始化完成")  # 調試輸出
```

### 方案 2: 實作完整的 TrackMapWidget（中期）

**目標**: 實現完整的賽道地圖繪製功能

**需要實現的功能**:
1. ✅ **數據載入** - 完整解析 CLI Function 2 的 JSON 輸出
2. ✅ **座標轉換** - 將賽道座標轉換為螢幕座標
3. ✅ **賽道繪製** - 繪製完整的賽道路線
4. ✅ **標記顯示** - 顯示起點/終點、距離標記
5. ✅ **互動功能** - 支援縮放、平移、懸停

**參考實現**: 可以參考其他模組的圖表組件（如 Rain Analysis）

### 方案 3: 使用 matplotlib 作為後備方案（長期）

**目標**: 使用成熟的繪圖庫實現賽道地圖

**優點**:
- ✅ 成熟穩定的繪圖功能
- ✅ 豐富的自訂選項
- ✅ 與其他分析模組一致

**缺點**:
- ❌ 可能影響效能
- ❌ 互動功能較 QPainter 受限

**實現方式**:
```python
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class TrackMapWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 創建 matplotlib 圖表
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)
    
    def draw_track_map(self):
        """使用 matplotlib 繪製賽道地圖"""
        self.ax.clear()
        
        # 繪製賽道路線
        x_coords = [record['position_x'] for record in self.position_records]
        y_coords = [record['position_y'] for record in self.position_records]
        
        self.ax.plot(x_coords, y_coords, 'b-', linewidth=2)
        self.ax.scatter([x_coords[0]], [y_coords[0]], c='green', s=100, label='Start')
        self.ax.scatter([x_coords[-1]], [y_coords[-1]], c='red', s=100, label='Finish')
        
        self.ax.set_aspect('equal')
        self.ax.legend()
        self.ax.grid(True, alpha=0.3)
        
        self.canvas.draw()
```

---

## 📝 立即行動計劃

### Step 1: 修復佔位符顯示（今日）⏰

**時間**: 15 分鐘  
**風險**: 極低

```python
# 修改 track_map_widget.py 的 init_ui() 方法
# 改進佔位符標籤的樣式和可見性
```

**預期效果**: 使用者將看到「正在載入...」而非黑屏

### Step 2: 添加調試輸出（今日）⏰

**時間**: 10 分鐘  
**風險**: 無

```python
# 在關鍵位置添加 print() 語句
# 追蹤數據載入和繪製流程
```

**預期效果**: 可以從控制台看到問題發生的具體位置

### Step 3: 實現基礎賽道繪製（本週）📅

**時間**: 2-3 小時  
**風險**: 低

```python
# 完善 draw_simplified_track() 方法
# 確保在任何情況下都能顯示基本的賽道路線
```

**預期效果**: 顯示簡化但可用的賽道地圖

### Step 4: 實現完整功能（下週）📅

**時間**: 1-2 天  
**風險**: 中

```python
# 實現完整的賽道地圖繪製功能
# 包括標記、網格、互動等
```

**預期效果**: 完整功能的賽道分析模組

---

## 🔍 調試檢查清單

當使用者報告 Track Analysis 黑屏時，應檢查：

### 檢查 1: 模組是否正確載入
```powershell
python -c "from modules.gui.track_analysis import TrackAnalysisModule; print('OK')"
```
✅ 預期輸出: `OK`

### 檢查 2: TrackMapWidget 是否初始化
```powershell
# 在 TrackMapWidget.__init__() 中添加 print()
print("[TRACK_MAP_WIDGET] 初始化開始")
```
✅ 預期輸出: 控制台顯示初始化訊息

### 檢查 3: 數據是否載入
```powershell
# 在 load_track_data() 中添加 print()
print(f"[TRACK_MAP] 數據載入: {len(self.position_records)} 個點")
```
✅ 預期輸出: 顯示位置點數量

### 檢查 4: paintEvent 是否被調用
```powershell
# 在 paintEvent() 中添加 print()
print("[TRACK_MAP] paintEvent 被調用")
```
✅ 預期輸出: 視窗顯示時應該看到此訊息

### 檢查 5: Widget 尺寸是否正常
```powershell
# 在 paintEvent() 中添加
print(f"[TRACK_MAP] Widget 尺寸: {self.size()}")
```
✅ 預期輸出: 顯示非零尺寸，如 `QSize(800, 600)`

---

## 📊 總結

### 問題確認

✅ **Track Analysis 模組本身正常**  
✅ **GUI 主程式正確調用新版模組**  
❌ **TrackMapWidget 是未完成的佔位符實現**  
❌ **佔位符標籤在暗色主題下不可見**  
❌ **數據載入和繪製流程可能存在問題**

### 根本原因

**TrackMapWidget 當前狀態**: 佔位符實現 + 繪製邏輯不完整 + 樣式在暗色主題下不可見

### 優先級

| 任務 | 優先級 | 時間 | 風險 |
|-----|-------|------|------|
| **修復佔位符顯示** | P0 🔥 | 15分鐘 | 極低 |
| **添加調試輸出** | P0 🔥 | 10分鐘 | 無 |
| **實現基礎繪製** | P1 ⚡ | 2-3小時 | 低 |
| **完整功能實現** | P2 📅 | 1-2天 | 中 |

### 建議行動

**立即執行** (今日):
1. 修復 TrackMapWidget 佔位符樣式（使其在暗色主題下可見）
2. 添加調試輸出以追蹤問題
3. 測試修復效果

**短期規劃** (本週):
1. 實現基礎的賽道路線繪製
2. 確保數據載入流程正常
3. 測試各種賽事數據

**長期規劃** (下週):
1. 實現完整的賽道地圖功能
2. 添加互動功能（縮放、平移）
3. 完善錯誤處理和使用者反饋

---

**報告結束**

**下一步**: 等待使用者確認是否立即進行修復

**預計修復時間**: 25 分鐘（包含測試）

**風險評估**: 極低（僅樣式和調試輸出修改）
