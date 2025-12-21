# MDI 滾動條功能說明

## 📋 功能概述

**實現時間**: 2025-12-08  
**版本**: 1.0  
**實現方案**: 方案 C（嚴格保留原始位置 + 滾動條支援）

## 🎯 功能目標

解決 Workspace 載入時視窗超出可視範圍的問題：
- ✅ **保留原始佈局**：完全保持儲存時的視窗位置和尺寸
- ✅ **自動滾動條**：視窗超出範圍時自動顯示水平/垂直滾動條
- ✅ **動態調整**：滾動範圍根據所有視窗的實際位置自動計算

## 🔧 技術實現

### 1. CustomMdiArea 初始化
**檔案**: `f1t_gui_main.py` (第 252-280 行)

```python
def __init__(self, parent=None):
    super().__init__(parent)
    
    # ✅ 啟用自動滾動條策略
    self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
```

**說明**:
- `Qt.ScrollBarAsNeeded` (值=0): 內容超出時自動顯示滾動條
- `Qt.ScrollBarAlwaysOn` (值=2): 始終顯示滾動條
- `Qt.ScrollBarAlwaysOff` (值=1): 永不顯示滾動條

### 2. 滾動範圍更新方法
**檔案**: `f1t_gui_main.py` (第 543-584 行)

```python
def _update_scroll_area(self):
    """
    更新 MDI 區域的滾動範圍
    
    計算邏輯：
    1. 遍歷所有可見子視窗
    2. 計算最大的右邊界和底部邊界
    3. 如果超出當前可視範圍，觸發 updateGeometry()
    4. QMdiArea 自動調整滾動條範圍
    """
```

**計算範例**:
```
MDI 可視範圍: 1920x1080
視窗 A 位置: (0, 0, 800, 600)       → 右=800,  底=600
視窗 B 位置: (1500, 500, 800, 600)  → 右=2300, 底=1100

計算結果:
- max_right = 2300 (超出 1920)
- max_bottom = 1100 (超出 1080)
- 需要水平滾動條: 是
- 需要垂直滾動條: 是
- 滾動範圍: 2350x1150 (加上 50px 邊距)
```

### 3. 自動觸發時機

#### 時機 A: 添加新視窗後
**檔案**: `f1t_gui_main.py` (第 536-541 行)

```python
def addSubWindow(self, widget, flags=None):
    # ... 創建子視窗 ...
    
    # ✅ 延遲 100ms 後更新滾動範圍（確保視窗已完全佈局）
    QTimer.singleShot(100, self._update_scroll_area)
```

#### 時機 B: Workspace 載入後
**檔案**: `f1t_gui_main.py` (第 17653-17660 行)

```python
def _on_workspace_loaded(self, workspace_id: int, config: Dict):
    success = self.workspace_serializer.deserialize_workspace(config)
    
    if success:
        # ✅ 延遲 300ms 後更新所有分頁的滾動範圍
        QTimer.singleShot(300, self._update_all_mdi_scroll_areas)
```

**多分頁更新邏輯**:
```python
def _update_all_mdi_scroll_areas(self):
    """遍歷所有分頁（跳過 HOME），更新每個 MDI 區域的滾動範圍"""
    for tab_index in range(1, self.tab_widget.count()):
        tab_widget = self.tab_widget.widget(tab_index)
        if hasattr(tab_widget, '_update_scroll_area'):
            tab_widget._update_scroll_area()
```

## 📊 使用範例

### 場景 1: 正常載入（視窗在範圍內）
```
MDI 尺寸: 1920x1080
視窗 A: (0, 0, 960, 540)
視窗 B: (960, 0, 960, 540)
視窗 C: (0, 540, 960, 540)
視窗 D: (960, 540, 960, 540)

結果: ✅ 無需滾動條，所有視窗可見
```

### 場景 2: 超出範圍（需要滾動條）
```
MDI 尺寸: 1920x1080
視窗 A: (0, 0, 800, 600)
視窗 B: (1500, 500, 800, 600)  ← 右邊界 = 2300 (超出)
視窗 C: (800, 900, 800, 600)   ← 底部邊界 = 1500 (超出)

結果: 
✅ 顯示水平滾動條 (範圍 0-2350)
✅ 顯示垂直滾動條 (範圍 0-1550)
✅ 使用者可拖動滾動條查看視窗 B 和 C
```

### 場景 3: 多螢幕環境
```
儲存環境: 2560x1440 (2K 螢幕)
載入環境: 1920x1080 (FHD 螢幕)

視窗 A: (1800, 1000, 600, 400)  ← 在 2K 螢幕內，但超出 FHD

結果: 
✅ 視窗 A 保持原始位置 (1800, 1000)
✅ 顯示滾動條讓使用者訪問視窗 A
✅ 不會自動縮放或移動視窗
```

## 🐛 除錯日誌

系統會在以下情況輸出日誌：

```
[MDI_INIT] ✅ 已啟用滾動條策略：當視窗超出範圍時自動顯示

[MDI_SCROLL] 📏 檢測到視窗超出範圍
[MDI_SCROLL]   可視範圍: 1920x1080
[MDI_SCROLL]   實際範圍: 2300x1500
[MDI_SCROLL]   ✅ 滾動條已自動啟用

[WORKSPACE] 🔄 更新所有 MDI 區域的滾動範圍...
[WORKSPACE] 📏 更新分頁 'Analysis 1' 的滾動範圍
[WORKSPACE] 📏 更新分頁 'Analysis 2' 的滾動範圍
[WORKSPACE] ✅ 已更新 2 個分頁的滾動範圍
```

## ⚙️ 進階配置

### 修改滾動條行為

如果需要改變滾動條顯示策略，修改 `CustomMdiArea.__init__()`:

```python
# 選項 1: 始終顯示滾動條（即使內容未超出）
self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

# 選項 2: 永不顯示滾動條（不推薦）
self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

# 選項 3: 僅水平方向自動顯示
self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
```

### 調整邊距

修改 `_update_scroll_area()` 中的 `padding` 值：

```python
# 預設: 50px 邊距
padding = 50

# 增加邊距（更多空白空間）
padding = 100

# 減少邊距（更緊湊）
padding = 20
```

## 🔍 故障排除

### 問題 1: 滾動條未出現

**可能原因**:
- 視窗實際上沒有超出範圍
- `_update_scroll_area()` 未被調用

**解決方法**:
1. 檢查日誌是否有 `[MDI_SCROLL]` 輸出
2. 手動調用 `mdi_area._update_scroll_area()`
3. 確認 `updateGeometry()` 已被觸發

### 問題 2: 滾動條範圍不正確

**可能原因**:
- 視窗幾何尺寸計算錯誤
- 隱藏視窗被納入計算

**解決方法**:
1. 檢查 `subwindow.isVisible()` 過濾邏輯
2. 驗證 `geometry()` 返回值
3. 增加除錯日誌輸出每個視窗的位置

### 問題 3: Workspace 載入後滾動條未更新

**可能原因**:
- 延遲時間不足（視窗未完全佈局）
- `_update_all_mdi_scroll_areas()` 未被調用

**解決方法**:
1. 增加 `QTimer.singleShot()` 的延遲時間（300ms → 500ms）
2. 確認 `_on_workspace_loaded()` 有正確觸發
3. 檢查分頁是否有 `_update_scroll_area()` 方法

## 📝 與其他方案的比較

| 方案 | 優點 | 缺點 |
|------|------|------|
| **方案 A (智慧調整)** | 自動縮放適應螢幕 | 失去原始尺寸 |
| **方案 B (自動平鋪)** | 視窗均勻分布 | 完全失去原始佈局 |
| **方案 C (本實現)** | 100% 保留原始佈局 | 可能需要滾動查看 |

## 🚀 未來改進方向

1. **智慧初始位置**: 載入時將滾動條自動定位到最常用的視窗
2. **快捷鍵導航**: 添加 Ctrl+方向鍵快速移動滾動條
3. **小地圖功能**: 在角落顯示所有視窗的縮略圖
4. **邊界警告**: 視窗接近超出範圍時顯示提示
5. **混合模式**: 允許使用者在載入時選擇保留/調整模式

## 📚 相關檔案

- `f1t_gui_main.py`: 主要實現
- `core/workspace_serializer.py`: Workspace 序列化邏輯
- `windows/load_workspace_dialog.py`: 載入對話框

## 🔗 參考資料

- [Qt QMdiArea 文檔](https://doc.qt.io/qt-5/qmdiarea.html)
- [Qt QScrollBar 文檔](https://doc.qt.io/qt-5/qscrollbar.html)
- [PyQt5 滾動區域範例](https://www.riverbankcomputing.com/static/Docs/PyQt5/)
