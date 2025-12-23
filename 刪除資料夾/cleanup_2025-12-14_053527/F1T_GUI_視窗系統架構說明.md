# F1T GUI 視窗系統架構詳細說明

## 📋 文件目的

本文件專注於說明 F1T GUI 的**視窗管理系統**，包括 MDI 架構、工作區（Workspace）概念、視窗尺寸控制、磁吸對齊、彈出功能等視窗層級的機制。

**不涵蓋**：具體分析模組功能（如 Lap Analysis、Rain Analysis 等）

---

## 🏗️ 整體架構概覽

### 三層視窗架構

```
┌─────────────────────────────────────────────────────────────┐
│ F1TelemetryStationMainWindow (主視窗)                       │
│  - 標題欄、選單欄、工具欄                                    │
│  - 全局參數控制（年份/賽事/賽段選擇器）                      │
│  - 狀態欄（API 狀態、版本資訊）                              │
├─────────────────────────────────────────────────────────────┤
│ QTabWidget (分頁系統)                                        │
│  ├─ Tab 0: 主頁 (Home) - 固定不可關閉                       │
│  ├─ Tab 1: Workspace 1 (可重命名/可彈出)                    │
│  ├─ Tab 2: Workspace 2 (可重命名/可彈出)                    │
│  └─ Tab N: Workspace N (可重命名/可彈出)                    │
│     │                                                         │
│     └─ CustomMdiArea (MDI 工作區)                           │
│         ├─ PopoutSubWindow (子視窗 1)                        │
│         │   └─ 分析模組 Widget (實際內容)                   │
│         ├─ PopoutSubWindow (子視窗 2)                        │
│         │   └─ 分析模組 Widget                              │
│         └─ PopoutSubWindow (子視窗 N)                        │
│             └─ 分析模組 Widget                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 核心組件詳解

### 1. CustomMdiArea (自訂 MDI 工作區)

**繼承自**：`QMdiArea` (PyQt5)

**核心職責**：
- 管理多個子視窗（MDI Sub-Windows）的容器
- 提供視窗 Snap（對齊）功能
- 支援滾動條（當視窗超出可視範圍時）
- 磁吸對齊（Magnetic Snap）

#### 1.1 MDI 模式設定

```python
self.setViewMode(QMdiArea.SubWindowView)  # 子視窗模式（非分頁模式）
self.setActivationOrder(QMdiArea.CreationOrder)  # 視窗激活順序：按創建順序
self.setOption(QMdiArea.DontMaximizeSubWindowOnActivation, True)  # 激活時不自動最大化
```

**解釋**：
- **SubWindowView**：每個內容都是獨立的子視窗，可自由拖曳、縮放
- **CreationOrder**：使用 Ctrl+Tab 切換視窗時，按照創建順序循環
- **DontMaximizeSubWindowOnActivation**：點擊視窗不會自動最大化（保持自由排列）

#### 1.2 滾動條策略（超出範圍支援）

```python
self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # 水平滾動條：需要時顯示
self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)    # 垂直滾動條：需要時顯示
```

**行為**：
- 當子視窗被拖曳到 MDI 區域邊界外時，自動顯示滾動條
- 用戶可以滾動查看超出範圍的視窗
- `_update_scroll_area()` 方法動態計算所需的虛擬空間

**範例場景**：
```
MDI 區域可視範圍：1920x1080
子視窗 A 位置：(1800, 900) 尺寸：400x300
→ 右下角超出可視範圍
→ 自動顯示水平和垂直滾動條
→ 虛擬空間擴展為 2200x1200
```

#### 1.3 視窗對齊（Snap）功能

**Snap 區域定義**（9 個區域）：

```
┌──────────┬──────────┬──────────┐
│ TOP_LEFT │   TOP    │TOP_RIGHT │  ← 上方三個區域
├──────────┼──────────┼──────────┤
│   LEFT   │  CENTER  │  RIGHT   │  ← 中間三個區域
├──────────┼──────────┼──────────┤
│BOTTOM_LT │  BOTTOM  │BOTTOM_RT │  ← 下方三個區域
└──────────┴──────────┴──────────┘
```

**觸發條件**：
- 拖曳視窗到 MDI 邊緣 **30 像素**內：顯示邊緣 Snap 預覽
- 拖曳視窗到 MDI 角落 **80 像素**內：顯示角落 Snap 預覽（更大的觸發區域）

**視覺反饋**：
- `SnapPreviewOverlay`：半透明藍色預覽框（仿 Windows Aero Snap）
- 顏色：`rgba(0, 120, 215, 80)` - 藍色半透明
- 邊框：`rgba(0, 120, 215, 200)` - 藍色實線

**Snap 尺寸計算**：
- **單視窗模式**（第一個視窗）：
  - 左/右：50% 寬度，100% 高度
  - 上/下：100% 寬度，50% 高度
  - 角落：50% 寬度，50% 高度
  
- **多視窗模式**（已有視窗）：
  - 動態計算剩餘空間，避免重疊
  - 智慧填充未使用的區域

**範例**：
```python
# 拖曳視窗到左邊緣 → Snap 到 LEFT 區域
detect_snap_zone(QPoint(10, 500))  # x=10 < 30 (邊緣閾值)
→ 返回 SnapZone.LEFT
→ 視窗設置為 QRect(0, 0, 960, 1080)  # 左半邊
```

#### 1.4 磁吸對齊（Magnetic Snap）

**功能**：拖曳視窗接近另一個視窗時，自動對齊邊緣（減少手動調整）

**參數**：
```python
self._magnetic_snap_distance = 15  # 磁吸距離：15 像素
```

**觸發邏輯**：
```python
# 計算當前視窗邊緣與其他視窗邊緣的距離
if abs(current_left - other_right) < 15:
    # 吸附到右邊視窗的左側
    new_x = other_right
```

**對齊方向**：
- 左邊緣 ↔ 右邊緣
- 右邊緣 ↔ 左邊緣
- 上邊緣 ↔ 下邊緣
- 下邊緣 ↔ 上邊緣

---

### 2. PopoutSubWindow (可彈出子視窗)

**繼承自**：`QMdiSubWindow` (PyQt5)

**核心職責**：
- 作為分析模組的容器（包裝層）
- 提供自訂標題欄（可拖曳、可調整大小）
- 支援彈出為獨立視窗
- 管理參數同步

#### 2.1 標題欄設計

**隱藏系統標題欄**：
```python
QMdiSubWindow::title {
    height: 0px;          # 標題欄高度為 0
    margin: 0px;
    padding: 0px;
    background: transparent;
    border: none;
}
```

**自訂標題欄**：`DraggableTitleBar` (在 PopoutSubWindow 內部實現)

**標題欄結構**：
```
┌────────────────────────────────────────────┐
│ [📊 圖標] 模組名稱_2025_Japan_R   [─][□][✕]│  ← 28px 高度
├────────────────────────────────────────────┤
│                                            │
│         分析模組內容                        │
│                                            │
└────────────────────────────────────────────┘
```

**標題欄功能按鈕**：
- **[─]** 最小化：縮小為標題欄（高度 28px）
- **[□]** 最大化/還原：在 MDI 區域內最大化
- **[✕]** 關閉：關閉視窗並釋放資源

**拖曳行為**：
- 按住標題欄拖曳：移動整個視窗
- 拖曳到 MDI 邊緣：觸發 Snap 預覽
- 拖曳到其他視窗附近：觸發磁吸對齊

#### 2.2 視窗邊框與調整大小

**視覺邊框**：
```python
QMdiSubWindow {
    border: 2px solid #666666;  # 2px 灰色邊框
    border-radius: 2px;
    background-color: #FFFFFF;
}
```

**調整大小機制**：
```python
self.resize_margin = 3                    # 視覺邊框寬度（與 QSS 一致）
self.resize_detection_margin = 10         # 實際可操作區域（更容易抓取）
```

**調整大小行為**：
- 滑鼠移到邊緣 **10 像素**內：游標變為調整大小游標（↔ ↕ ⤡ ⤢）
- 拖曳邊緣：實時調整視窗大小
- **無最小尺寸限制**（允許完全自由縮放）

**8 個調整方向**：
```
⤢───↕───⤡     ← 四個角：對角線調整
│       │
↔       ↔     ← 四條邊：單向調整
│       │
⤡───↕───⤢
```

#### 2.3 彈出（Pop-out）功能

**彈出前狀態**：
```
Tab Widget
├─ Workspace 1 (QTabWidget 內)
│   └─ CustomMdiArea
│       └─ PopoutSubWindow A (在 MDI 內)
│           └─ 分析模組 Widget
```

**彈出後狀態**：
```
Tab Widget                          獨立視窗 (StandaloneAnalysisWindow)
├─ Workspace 1                      ┌────────────────────────────┐
│   └─ 🔗 佔位符 Widget              │ 模組名稱 - F1T Pro         │
│       (灰色文字提示)               ├────────────────────────────┤
│                                   │ CustomMdiArea              │
                                    │  └─ PopoutSubWindow A      │
                                    │      └─ 分析模組 Widget    │
                                    └────────────────────────────┘
```

**彈出過程**（關鍵步驟）：
1. 從原 Tab 取出 MDI 區域（`tab_widget.widget(index)`）
2. 創建獨立視窗 `StandaloneAnalysisWindow`
3. 將 MDI 區域設置為獨立視窗的中央元件（`setCentralWidget(mdi_area)`）
4. 在原 Tab 插入佔位符 Widget（顯示 "🔗 此工作區已彈出為獨立視窗"）
5. 更新 Tab 標籤：添加 🔗 圖標，設置灰色文字

**返回過程**：
1. 從獨立視窗取出 MDI 區域（`takeCentralWidget()`）
2. 移除佔位符 Tab
3. 將 MDI 區域重新插入 Tab Widget（`insertTab(index, mdi_area, name)`）
4. 恢復 Tab 標籤：移除 🔗 圖標，恢復黑色文字
5. 關閉獨立視窗

**防護機制**：
```python
# 避免重複返回（closeEvent 可能多次觸發）
if tab_index not in self.popped_out_tabs:
    return  # 已經返回，跳過
```

#### 2.4 最小化功能

**最小化狀態**：
```
正常狀態：                  最小化狀態：
┌─────────────────┐        ┌─────────────────┐
│ 標題欄 (28px)   │        │ 標題欄 (28px)   │
├─────────────────┤        └─────────────────┘
│                 │         ← 內容區域隱藏
│   內容區域      │
│   (400px)       │
│                 │
└─────────────────┘
```

**實現方式**：
```python
if not self.is_minimized:
    # 最小化
    self.original_geometry = self.geometry()  # 保存原始尺寸
    self.setFixedHeight(28)  # 固定高度為標題欄高度
    self.is_minimized = True
else:
    # 還原
    self.setMinimumHeight(0)
    self.setMaximumHeight(16777215)  # Qt 的最大值
    self.setGeometry(self.original_geometry)
    self.is_minimized = False
```

**最小化行為**：
- 內容 Widget 不被銷毀（僅隱藏）
- 可拖曳移動最小化視窗
- 點擊標題欄的 [─] 按鈕還原

---

### 3. Workspace（工作區）概念

#### 3.1 工作區定義

**工作區 = QTabWidget 中的一個 Tab，內含一個 CustomMdiArea**

```python
# 創建新工作區
def create_new_workspace(self, name="Workspace"):
    mdi_area = CustomMdiArea()
    tab_index = self.tab_widget.addTab(mdi_area, name)
    return tab_index
```

#### 3.2 工作區特性

| 特性               | 主頁 (Tab 0)       | 其他工作區 (Tab 1+)   |
|-------------------|--------------------|-----------------------|
| **可關閉**         | ❌ 禁止             | ✅ 允許               |
| **可重命名**       | ❌ 禁止             | ✅ 允許               |
| **可彈出**         | ❌ 禁止             | ✅ 允許               |
| **標籤樣式**       | 固定黑色文字        | 彈出時灰色 + 🔗 圖標   |
| **右鍵選單**       | 新增工作區         | 新增/重命名/關閉/彈出  |

#### 3.3 工作區右鍵選單

**主頁 Tab (index=0)**：
```
┌────────────────┐
│ 新增工作區     │  ← 唯一選項
└────────────────┘
```

**其他 Tab (index>0)**：
```
┌────────────────┐
│ 新增工作區     │
├────────────────┤
│ 重新命名       │
├────────────────┤
│ 關閉工作區     │
├────────────────┤
│ 彈出為獨立視窗 │
└────────────────┘
```

#### 3.4 工作區重命名機制

**重複名稱處理**：
```python
def _get_unique_tab_name(self, base_name):
    # 範例：
    # 已有：["Workspace", "Workspace (1)"]
    # 輸入："Workspace"
    # 輸出："Workspace (2)"
    
    counter = 1
    while f"{base_name} ({counter})" in existing_names:
        counter += 1
    return f"{base_name} ({counter})"
```

**命名範例**：
```
Tab 1: "Workspace"
Tab 2: "Verstappen vs Leclerc"
Tab 3: "Japan GP Analysis"
Tab 4: "Workspace (1)"  ← 自動添加後綴
```

---

## 🎨 視窗樣式系統

### 4.1 MDI 區域背景

**白色背景強制設定**（三重保險）：
```python
# 方法 1: 調色盤
palette = mdi_area.palette()
palette.setColor(QPalette.Window, QColor(255, 255, 255))
mdi_area.setPalette(palette)

# 方法 2: 樣式表
mdi_area.setStyleSheet("QMdiArea { background-color: white; }")

# 方法 3: Viewport 背景（內部 QScrollArea）
viewport = mdi_area.viewport()
if viewport:
    viewport.setStyleSheet("background-color: white;")
```

### 4.2 子視窗樣式

**正常狀態**：
```css
QMdiSubWindow {
    border: 2px solid #666666;          /* 灰色邊框 */
    border-radius: 2px;
    background-color: #FFFFFF;          /* 白色背景 */
}
```

**標題欄樣式**（隱藏系統標題欄）：
```css
QMdiSubWindow::title {
    height: 0px;                        /* 高度為 0 */
    margin: 0px;
    padding: 0px;
    background: transparent;
    border: none;
}
```

### 4.3 Tab 標籤樣式

**正常狀態**：
```python
tab_bar.setTabTextColor(index, QColor(0, 0, 0))  # 黑色文字
tab_text = "Workspace 1"
```

**彈出狀態**：
```python
tab_bar.setTabTextColor(index, QColor(102, 102, 102))  # 灰色文字 #666666
tab_text = "🔗 Workspace 1"  # 添加連結圖標
```

---

## 📐 視窗尺寸與位置管理

### 5.1 Smart Width（智慧寬度）系統

**目的**：根據模組類型自動計算最佳寬度

**尺寸提示表**：
```python
MODULE_SIZE_HINTS = {
    'circle_map': {
        'preferred_ratio': 0.30,  # 佔 MDI 寬度的 30%
        'min_width': 280,         # 最小寬度 280px
        'aspect': 'square'        # 寬高比接近 1:1
    },
    'ranking_tower': {
        'preferred_ratio': 0.18,  # 18% - 細長的排名塔
        'min_width': 160,
        'aspect': 'tall'          # 高度 > 寬度
    },
    'lap_time_distribution': {
        'preferred_ratio': 0.25,  # 25% - 中等寬度
        'min_width': 200,
        'aspect': 'wide'          # 寬度 > 高度
    },
    'driver_strategy': {
        'preferred_ratio': 0.45,  # 45% - 較寬的策略圖
        'min_width': 380,
        'aspect': 'wide'
    },
    'default': {
        'preferred_ratio': 0.30,  # 預設 30%
        'min_width': 250,
        'aspect': 'wide'
    }
}
```

**計算範例**：
```python
# MDI 區域寬度：1920px
# 模組類型：driver_strategy
# preferred_ratio: 0.45

計算：
target_width = 1920 * 0.45 = 864px
實際寬度 = max(864, 380) = 864px  # 大於最小寬度，使用計算值

# 如果 MDI 寬度很小（例如 400px）
target_width = 400 * 0.45 = 180px
實際寬度 = max(180, 380) = 380px  # 使用最小寬度
```

### 5.2 固定視窗（歡迎頁面）

**主頁 (Tab 0) 佈局**：
```
┌──────────┬──────────┬──────────┐
│  左上    │          │          │  ← 45% 高度
│ (33%寬)  │   中欄   │   右欄   │
├──────────┤ (33%寬)  │ (34%寬)  │
│  左下    │          │          │  ← 55% 高度
│ (33%寬)  │ (100%高) │ (100%高) │
└──────────┴──────────┴──────────┘
```

**固定視窗屬性**：
```python
sub_window.setProperty("is_welcome_fixed", True)  # 標記為固定視窗
sub_window.setProperty("welcome_position", "left_top")  # 位置標記

# 禁用調整大小和移動
sub_window.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnBottomHint)
```

**自動重排**（視窗縮放時）：
```python
def resizeEvent(self, event):
    super().resizeEvent(event)
    self._rearrange_fixed_windows()  # 重新計算並設置所有固定視窗的尺寸
```

### 5.3 動態空間計算

**剩餘空間檢測**：
```python
def _find_available_space_for_zone(self, zone: SnapZone, exclude_window=None):
    # 收集所有已佔用的區域
    occupied = self._get_occupied_regions(exclude_window)
    
    # 計算邊界
    left_boundary = max(region.right() for region in left_regions)
    right_boundary = min(region.x() for region in right_regions)
    
    # 返回剩餘空間
    return QRect(left_boundary, 0, right_boundary - left_boundary, h)
```

**碰撞檢測**：
```python
def _would_overlap_other_windows(self, target_rect, exclude_window):
    for other_window in self.subWindowList():
        if other_window == exclude_window:
            continue
        if target_rect.intersects(other_window.geometry()):
            return True  # 會重疊
    return False
```

---

## 🔄 視窗狀態管理

### 6.1 視窗生命週期

```
創建 → 顯示 → 使用中 → 最小化 → 還原 → 關閉
 │      │       │        │        │       │
 │      │       │        │        │       └─ deleteLater()
 │      │       │        │        └─ setGeometry(original)
 │      │       │        └─ setFixedHeight(28)
 │      │       └─ 可拖曳、可調整大小
 │      └─ show(), addSubWindow()
 └─ PopoutSubWindow.__init__()
```

**資源釋放**：
```python
# 關閉時自動刪除
self.setAttribute(Qt.WA_DeleteOnClose, True)

# 關閉事件處理
def closeEvent(self, event):
    # 斷開信號連接
    if self.analysis_module:
        self.analysis_module.disconnect()
    
    # 移除追蹤記錄
    if self in parent_mdi.subWindowList():
        parent_mdi.removeSubWindow(self)
    
    event.accept()
```

### 6.2 視窗追蹤

**MDI 層級**：
```python
# 獲取所有子視窗
all_windows = mdi_area.subWindowList()

# 過濾固定視窗
movable_windows = [w for w in all_windows if not w.property("is_welcome_fixed")]

# 過濾可見視窗
visible_windows = [w for w in all_windows if w.isVisible()]
```

**主視窗層級**：
```python
# 追蹤彈出的工作區
self.popped_out_tabs = {
    1: {
        'standalone_window': StandaloneAnalysisWindow(...),
        'original_widget': CustomMdiArea(...),
        'placeholder': PlaceholderWidget(...),
        'tab_name': "Workspace 1"
    }
}
```

---

## 🖱️ 用戶互動流程

### 7.1 拖曳視窗進行 Snap

```
1. 用戶按住標題欄
   ↓
2. 開始拖曳 (mouseMoveEvent)
   ↓
3. 檢測滑鼠位置 (detect_snap_zone)
   ↓
4. 接近邊緣？
   ├─ 是 → 顯示 Snap 預覽 (SnapPreviewOverlay)
   └─ 否 → 隱藏預覽
   ↓
5. 釋放滑鼠 (mouseReleaseEvent)
   ↓
6. 有預覽？
   ├─ 是 → 執行 Snap (snap_window_to_zone)
   └─ 否 → 保持當前位置
```

### 7.2 調整視窗大小

```
1. 滑鼠移到視窗邊緣 (距離 < 10px)
   ↓
2. 游標變為調整大小游標 (setCursor)
   ├─ 上/下邊緣 → Qt.SizeVerCursor (↕)
   ├─ 左/右邊緣 → Qt.SizeHorCursor (↔)
   ├─ 左上/右下角 → Qt.SizeFDiagCursor (⤡)
   └─ 右上/左下角 → Qt.SizeBDiagCursor (⤢)
   ↓
3. 按下滑鼠左鍵 (mousePressEvent)
   ↓
4. 拖曳滑鼠 (mouseMoveEvent)
   ↓
5. 實時更新視窗尺寸 (setGeometry)
   ↓
6. 釋放滑鼠 (mouseReleaseEvent)
   ↓
7. 完成調整
```

### 7.3 彈出工作區

```
1. 右鍵點擊 Tab 標籤
   ↓
2. 選擇「彈出為獨立視窗」
   ↓
3. 系統執行 popout_tab(tab_index)
   ↓
4. 取出 MDI 區域 (tab_widget.widget(index))
   ↓
5. 創建獨立視窗 (StandaloneAnalysisWindow)
   ↓
6. 設置中央元件 (setCentralWidget(mdi_area))
   ↓
7. 插入佔位符到原 Tab
   ↓
8. 顯示獨立視窗 (show())
   ↓
9. 更新 Tab 標籤（灰色 + 🔗）
```

### 7.4 返回工作區

```
方式 1: 點擊佔位符的「返回」按鈕
方式 2: 關閉獨立視窗（點擊 X）
   ↓
1. 觸發 return_tab(tab_index)
   ↓
2. 從獨立視窗取出 MDI (takeCentralWidget)
   ↓
3. 移除佔位符 Tab (removeTab)
   ↓
4. 重新插入 MDI (insertTab)
   ↓
5. 關閉獨立視窗 (close)
   ↓
6. 恢復 Tab 標籤（黑色，無 🔗）
   ↓
7. 完成返回
```

---

## 🛠️ 技術細節與限制

### 8.1 Qt 版本與限制

| 組件            | Qt 類別           | 版本限制        | 備註                   |
|----------------|------------------|----------------|------------------------|
| MDI 區域        | QMdiArea         | PyQt5 5.12+    | 支援滾動條策略         |
| 子視窗          | QMdiSubWindow    | PyQt5 5.12+    | 支援自訂標題欄         |
| 標籤系統        | QTabWidget       | PyQt5 5.12+    | 支援可關閉標籤         |
| 拖曳系統        | QDrag            | PyQt5 5.12+    | 支援拖曳預覽           |

### 8.2 性能考量

**視窗數量限制**：
- 建議單個 MDI 區域內不超過 **20 個子視窗**
- 超過 20 個會影響拖曳流暢度

**滾動條性能**：
- 虛擬空間過大（>10000x10000px）可能導致滾動延遲
- 建議使用 Snap 功能合理排列視窗

**記憶體管理**：
- 關閉視窗時自動釋放資源（`WA_DeleteOnClose`）
- 彈出視窗時不複製 MDI 區域，而是移動引用（避免重複佔用記憶體）

### 8.3 已知問題與解決方案

#### 問題 1：視窗拖曳時閃爍
**原因**：頻繁的 `setGeometry()` 調用
**解決**：使用 `setUpdatesEnabled(False)` 暫停更新

```python
window.setUpdatesEnabled(False)
window.setGeometry(new_rect)
window.setUpdatesEnabled(True)
```

#### 問題 2：彈出後 MDI 背景變黑
**原因**：獨立視窗的調色盤覆蓋了 MDI 設定
**解決**：在彈出後重新設置背景色（已實現）

```python
def popout_tab(self, tab_index):
    # ...
    standalone_window.show()
    self._fix_mdi_background(mdi_area)  # 修復背景
```

#### 問題 3：Snap 預覽位置不準確
**原因**：全局座標與本地座標轉換錯誤
**解決**：使用 `mapFromGlobal()` 正確轉換

```python
local_pos = self.mapFromGlobal(global_pos)
```

---

## 📊 視窗系統統計資料

### 系統規模

- **總代碼行數**（視窗系統相關）：約 3500 行
- **CustomMdiArea 類別**：約 800 行
- **PopoutSubWindow 類別**：約 600 行
- **Snap 系統**：約 400 行
- **Tab 管理**：約 500 行

### 視窗屬性表

| 屬性                    | CustomMdiArea | PopoutSubWindow | StandaloneWindow |
|------------------------|---------------|-----------------|------------------|
| **可拖曳**              | N/A           | ✅ 是            | ✅ 是             |
| **可調整大小**          | ✅ 是          | ✅ 是            | ✅ 是             |
| **可最小化**            | N/A           | ✅ 是            | ✅ 是             |
| **可最大化**            | N/A           | ✅ 是（MDI 內）   | ✅ 是（全螢幕）    |
| **可關閉**              | N/A           | ✅ 是            | ✅ 是             |
| **支援 Snap**           | ✅ 是          | ✅ 是            | ❌ 否             |
| **支援磁吸對齊**        | ✅ 是          | ✅ 是            | ❌ 否             |
| **可彈出**              | N/A           | ✅ 是            | N/A              |

---

## 🎯 最佳實踐建議

### 視窗排列建議

1. **優先使用 Snap**：拖曳到邊緣比手動調整更快
2. **合理分組**：相關分析放在同一個 Workspace
3. **避免過度重疊**：利用 Snap 的剩餘空間計算功能
4. **善用彈出**：複雜分析彈出為獨立視窗，利用多顯示器

### 開發者建議

1. **視窗尺寸**：新增模組時在 `MODULE_SIZE_HINTS` 中定義尺寸提示
2. **資源釋放**：確保視窗關閉時斷開所有信號連接
3. **座標轉換**：使用 `mapFromGlobal()` / `mapToGlobal()` 正確轉換座標
4. **樣式繼承**：子視窗樣式應繼承主題設定

---

## 🔍 快速參考

### 常用方法速查

```python
# MDI 區域
mdi.addSubWindow(widget)              # 添加子視窗
mdi.subWindowList()                   # 獲取所有子視窗
mdi.tileSubWindows()                  # 平鋪排列
mdi.cascadeSubWindows()               # 層疊排列

# 子視窗
sub_window.setGeometry(x, y, w, h)    # 設置位置和尺寸
sub_window.geometry()                 # 獲取幾何資訊
sub_window.windowTitle()              # 獲取標題
sub_window.close()                    # 關閉視窗

# Snap 功能
mdi.detect_snap_zone(global_pos)      # 檢測 Snap 區域
mdi.snap_window_to_zone(window, zone) # 執行 Snap
mdi.show_snap_preview(zone)           # 顯示預覽
mdi.hide_snap_preview()               # 隱藏預覽

# 工作區管理
main.create_new_workspace(name)       # 創建工作區
main.popout_tab(index)                # 彈出工作區
main.return_tab(index)                # 返回工作區
main.rename_tab(index)                # 重命名工作區
```

### 視窗屬性速查

```python
# 固定視窗標記
sub_window.setProperty("is_welcome_fixed", True)
sub_window.property("is_welcome_fixed")  # 檢查

# 位置標記
sub_window.setProperty("welcome_position", "left_top")

# 模組類型（用於 Smart Width）
sub_window.analysis_module.analysis_type = "circle_map"
```

---

## 📝 版本更新記錄

| 版本   | 日期       | 更新內容                              |
|--------|-----------|---------------------------------------|
| 1.0.0  | 2025-10-01 | 初始版本，基礎 MDI 功能              |
| 1.1.0  | 2025-10-05 | 新增 Snap 對齊功能                   |
| 1.2.0  | 2025-10-08 | 新增磁吸對齊功能                     |
| 1.3.0  | 2025-10-10 | 新增彈出工作區功能                   |
| 1.4.0  | 2025-10-15 | 新增 Smart Width 系統                |
| 1.5.0  | 2025-10-20 | 新增工作區重命名功能                 |
| 2.0.0  | 2025-11-01 | 重構視窗系統，優化性能               |

---

## 📚 相關文件

- **模組開發指南**：`F1T_模組開發指南.md`（說明如何開發分析模組）
- **API 文件**：`F1T_API文件.md`（說明後端 API 架構）
- **用戶手冊**：`F1T_用戶手冊.md`（面向終端用戶的使用說明）

---

**文件維護者**：F1T 開發團隊  
**最後更新**：2025-12-11  
**適用版本**：F1T v2.5.0+
