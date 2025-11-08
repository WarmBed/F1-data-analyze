# 分頁彈出功能開發任務

**創建日期**：2025-10-21  
**狀態**：🔄 進行中  
**優先級**：⭐⭐⭐ 高優先級

---

## 📋 功能需求總結

### 核心功能
1. **彈出觸發**：右鍵點擊分頁標籤顯示選單，包含「彈出為獨立視窗」選項
2. **彈出內容**：整個分頁（包括 MDI 工作區和所有子視窗）
3. **HOME 主頁**：不提供彈出選項（右鍵選單不顯示）
4. **標籤狀態**：保留灰色標籤 + 🔗 圖標標記已彈出狀態
5. **視窗標題**：「分頁一 - F1 TelemetryStation Pro」格式

### 工具列功能（順序固定）
```
[⌂ 返回主畫面] [🔗 同步: ON] [Show All Data] [Close All Windows] [Tile Windows] [Cascade Windows]
```
- **⌂ 返回主畫面**：必須功能，返回分頁到主視窗
- **🔗 同步**：可選同步，控制是否跟隨主視窗參數（年份/賽事/賽段）
- **Show All Data**：重置所有 MDI 子視窗的 XY 軸視圖
- **Close All Windows**：關閉所有 MDI 子視窗
- **Tile Windows**：平鋪所有子視窗
- **Cascade Windows**：層疊所有子視窗

⚠️ **重要**：這些功能只影響該彈出分頁，不影響其他分頁或主視窗

### 進階功能
- **多分頁彈出**：允許多個分頁同時彈出（多個獨立視窗）
- **視窗調整**：完全複用 `ResizableStandaloneWindow` 類別
- **自動返回**：關閉獨立視窗時自動返回主視窗（不關閉分頁）
- **參數同步**：可選同步（工具列開關控制）
- **智能大小**：初始大小為主視窗的 80%

---

## 🎯 實現計劃

### 階段 1：基礎架構（預計 30 分鐘）
- [x] 創建任務追蹤檔案 `tab_popout_feature.md`
- [ ] 搜尋現有實現並驗證方法
  - 確認 `CustomMdiArea.tileSubWindows()`
  - 確認 `CustomMdiArea.cascadeSubWindows()`
  - 確認 `QTabWidget.contextMenuEvent()` 實現方式
- [ ] 設計分頁狀態管理結構
  ```python
  self.popped_out_tabs = {}  # {tab_index: standalone_window}
  ```

### 階段 2：右鍵選單實現（預計 20 分鐘）
- [ ] 為 `QTabWidget` 添加 `contextMenuEvent` 處理
- [ ] 判斷右鍵點擊的分頁索引
- [ ] 過濾 HOME 主頁（index=0），不顯示彈出選項
- [ ] 添加「彈出為獨立視窗 ⧉」選單項

### 階段 3：彈出邏輯實現（預計 40 分鐘）
- [ ] 實現 `pop_out_tab(tab_index)` 方法
  - 保存分頁狀態（widget、標題、MDI 區域）
  - 創建 `ResizableStandaloneWindow`
  - 設定視窗標題：「分頁名稱 - F1 TelemetryStation Pro」
  - 計算視窗大小：主視窗 80%
  - 移植 MDI 工作區到獨立視窗
  - 更新分頁標籤為灰色 + 🔗 圖標
  - 記錄到 `self.popped_out_tabs`

### 階段 4：工具列實現（預計 50 分鐘）
- [ ] 創建工具列並添加到獨立視窗
- [ ] **按鈕 1**：⌂ 返回主畫面
  - 連接到 `pop_back_in_tab(tab_index)`
- [ ] **按鈕 2**：🔗 同步: ON/OFF
  - 初始狀態：ON
  - 切換邏輯：控制是否接收主視窗參數變更通知
  - 文字動態更新：「🔗 同步: ON」↔「🔗 同步: OFF」
- [ ] **按鈕 3**：Show All Data
  - 調用獨立視窗內 MDI 區域的 `reset_all_chart_views()`
  - 遍歷所有子視窗並重置 XY 軸
- [ ] **按鈕 4**：Close All Windows
  - 調用 `mdi_area.closeAllSubWindows()`
- [ ] **按鈕 5**：Tile Windows
  - 調用 `mdi_area.tileSubWindows()`
- [ ] **按鈕 6**：Cascade Windows
  - 調用 `mdi_area.cascadeSubWindows()`

### 階段 5：返回邏輯實現（預計 30 分鐘）
- [ ] 實現 `pop_back_in_tab(tab_index)` 方法
  - 從 `self.popped_out_tabs` 獲取獨立視窗引用
  - 移植 MDI 工作區回主視窗分頁
  - 恢復分頁標籤正常樣式（移除灰色和 🔗）
  - 關閉獨立視窗
  - 從 `self.popped_out_tabs` 移除記錄

### 階段 6：視覺效果實現（預計 20 分鐘）
- [ ] 實現灰色標籤樣式
  ```python
  self.tab_widget.setTabText(index, f"🔗 {tab_name}")
  # QSS 設定灰色背景
  ```
- [ ] 添加 QSS 樣式規則
  ```css
  QTabBar::tab[popout="true"] {
      background: #D0D0D0;  /* 灰色背景 */
      color: #666666;       /* 灰色文字 */
  }
  ```

### 階段 7：參數同步實現（預計 30 分鐘）
- [ ] 在獨立視窗添加同步狀態屬性
  ```python
  self.sync_enabled = True  # 預設啟用
  ```
- [ ] 連接主視窗參數變更信號
  - `year_combo.currentIndexChanged`
  - `race_combo.currentIndexChanged`
  - `session_combo.currentIndexChanged`
- [ ] 實現 `_on_main_window_parameter_changed()` 方法
  - 檢查 `self.sync_enabled`
  - 如果啟用，更新獨立視窗內所有 MDI 子視窗的參數
  - 如果禁用，忽略信號
- [ ] 同步按鈕切換邏輯
  ```python
  def toggle_sync(self):
      self.sync_enabled = not self.sync_enabled
      self.sync_btn.setText(f"🔗 同步: {'ON' if self.sync_enabled else 'OFF'}")
  ```

### 階段 8：關閉事件處理（預計 15 分鐘）
- [ ] 覆寫獨立視窗的 `closeEvent`
  ```python
  def closeEvent(self, event):
      # 觸發自動返回主視窗
      self.pop_back_in_tab(self.tab_index)
      event.accept()
  ```
- [ ] 清理資源
  - 斷開信號連接
  - 釋放 MDI 區域引用
  - 從 `popped_out_tabs` 字典移除

---

## 🧪 測試計劃

### 測試 1：單一分頁彈出與返回
- [ ] 右鍵點擊「分頁一」
- [ ] 選擇「彈出為獨立視窗」
- [ ] 確認：
  - ✅ 獨立視窗正常顯示
  - ✅ 標題格式正確：「分頁一 - F1 TelemetryStation Pro」
  - ✅ 視窗大小為主視窗的 80%
  - ✅ 工具列 6 個按鈕都顯示
  - ✅ 主視窗分頁標籤變為灰色 + 🔗 圖標
- [ ] 點擊「⌂ 返回主畫面」
- [ ] 確認：
  - ✅ 獨立視窗關閉
  - ✅ 分頁恢復到主視窗
  - ✅ 標籤恢復正常樣式

### 測試 2：多分頁同時彈出
- [ ] 彈出「分頁一」
- [ ] 彈出「分頁二」
- [ ] 彈出「分頁三」
- [ ] 確認：
  - ✅ 三個獨立視窗同時存在
  - ✅ 三個分頁標籤都是灰色 + 🔗
  - ✅ 每個視窗的工具列功能互不干擾
  - ✅ 關閉任一視窗不影響其他視窗

### 測試 3：工具列功能測試
- [ ] 彈出「分頁一」（包含多個 MDI 子視窗）
- [ ] 測試「Show All Data」
  - ✅ 所有子視窗的圖表 XY 軸重置
- [ ] 測試「Close All Windows」
  - ✅ 所有 MDI 子視窗關閉
  - ✅ MDI 區域變為空白
- [ ] 重新打開幾個分析視窗
- [ ] 測試「Tile Windows」
  - ✅ 子視窗平鋪排列
- [ ] 測試「Cascade Windows」
  - ✅ 子視窗層疊排列

### 測試 4：參數同步測試
- [ ] 彈出「分頁一」，同步狀態為 ON
- [ ] 在主視窗更改年份：2025 → 2024
- [ ] 確認：
  - ✅ 獨立視窗內的 MDI 子視窗參數同步更新
- [ ] 點擊「🔗 同步: ON」切換為 OFF
- [ ] 在主視窗更改賽事：Japan → Italy
- [ ] 確認：
  - ✅ 獨立視窗內的子視窗不更新（保持 Japan）
- [ ] 再次點擊「🔗 同步: OFF」切換為 ON
- [ ] 在主視窗更改賽段：R → Q
- [ ] 確認：
  - ✅ 獨立視窗內的子視窗同步更新

### 測試 5：HOME 主頁測試
- [ ] 右鍵點擊「主頁」標籤
- [ ] 確認：
  - ✅ 選單**不顯示**「彈出為獨立視窗」選項
  - ✅ 或選單完全不顯示

### 測試 6：關閉行為測試
- [ ] 彈出「分頁一」
- [ ] 直接關閉獨立視窗（點擊 X）
- [ ] 確認：
  - ✅ 自動返回主視窗
  - ✅ 分頁標籤恢復正常
  - ✅ MDI 子視窗內容完整保留
  - ✅ 無記憶體洩漏

### 測試 7：邊緣案例測試
- [ ] 彈出「分頁一」
- [ ] 在主視窗關閉「分頁一」標籤
- [ ] 確認：
  - ✅ 獨立視窗自動關閉 或
  - ✅ 提示錯誤並保持獨立視窗
- [ ] 彈出所有分頁（只剩 HOME）
- [ ] 確認：
  - ✅ 主視窗仍可正常運作
  - ✅ HOME 主頁正常顯示

---

## 🔧 技術實現細節

### 關鍵方法列表
```python
# 主視窗類別 (StyleHMainWindow)
def _setup_tab_context_menu(self):
    """為 QTabWidget 設定右鍵選單"""
    
def _show_tab_context_menu(self, pos):
    """顯示分頁右鍵選單"""
    
def pop_out_tab(self, tab_index):
    """彈出指定分頁為獨立視窗"""
    
def pop_back_in_tab(self, tab_index):
    """將彈出的分頁返回主視窗"""
    
def _update_tab_appearance(self, tab_index, is_popped_out):
    """更新分頁標籤外觀（灰色 + 圖標）"""
    
def _on_main_window_parameter_changed(self, param_type, value):
    """主視窗參數變更時通知所有彈出分頁"""
```

### 獨立視窗類別 (TabStandaloneWindow)
```python
class TabStandaloneWindow(ResizableStandaloneWindow):
    """分頁彈出的獨立視窗，繼承自 ResizableStandaloneWindow"""
    
    def __init__(self, tab_name, mdi_area, tab_index, main_window):
        """初始化獨立視窗"""
        
    def setup_toolbar(self):
        """設定工具列（6 個按鈕）"""
        
    def toggle_sync(self):
        """切換參數同步狀態"""
        
    def show_all_data(self):
        """重置所有子視窗視圖"""
        
    def close_all_windows(self):
        """關閉所有子視窗"""
        
    def tile_windows(self):
        """平鋪子視窗"""
        
    def cascade_windows(self):
        """層疊子視窗"""
        
    def closeEvent(self, event):
        """關閉事件：自動返回主視窗"""
```

### 數據結構
```python
# 主視窗類別中追蹤彈出的分頁
self.popped_out_tabs = {
    tab_index: {
        'standalone_window': TabStandaloneWindow 實例,
        'original_widget': 原始分頁 widget,
        'tab_name': 分頁名稱
    }
}
```

---

## ⚠️ 注意事項

1. **資源管理**：
   - 彈出時不刪除分頁，只是隱藏/移動內容
   - 返回時正確恢復 widget 的 parent
   - 關閉時釋放所有信號連接

2. **信號連接**：
   - 主視窗參數變更信號需要動態連接/斷開
   - 避免重複連接導致多次觸發

3. **樣式管理**：
   - 灰色標籤使用 QSS 動態屬性或 setStyleSheet
   - 圖標使用 Unicode 字符（🔗 U+1F517）

4. **MDI 區域處理**：
   - 確保 MDI 區域的 parent 正確切換
   - Tile/Cascade 只影響當前獨立視窗

5. **同步邏輯**：
   - 同步開關只控制參數更新，不影響手動操作
   - 每個彈出分頁獨立管理同步狀態

---

## 📝 開發日誌

### 2025-10-21

#### 第一階段：核心功能實現（已完成）
- ✅ 創建任務追蹤檔案
- ✅ 確認所有功能需求和技術細節
- ✅ 在 `__init__` 方法添加 `self.popped_out_tabs` 追蹤字典
- ✅ 實現 `_setup_tab_context_menu()` 方法（設置右鍵選單）
- ✅ 實現 `_show_tab_context_menu()` 方法（顯示彈出/返回選項）
- ✅ 實現 `pop_out_tab()` 方法（彈出邏輯）
- ✅ 實現 `pop_back_in_tab()` 方法（返回邏輯）
- ✅ 實現 `_update_tab_appearance()` 方法（灰色標籤 + � 圖標）
- ✅ 創建 `TabStandaloneWindow` 類別（繼承 ResizableStandaloneWindow）
- ✅ 實現工具列 6 個按鈕（返回、同步、Show All、Close All、Tile、Cascade）
- ✅ 實現參數同步功能（可選開關）
- ✅ 實現 closeEvent 自動返回主視窗
- ✅ 語法檢查通過（無語法錯誤）

#### 程式碼統計
- **新增類別**：1 個（`TabStandaloneWindow`）
- **新增方法**：10+ 個
- **新增程式碼行數**：約 300+ 行
- **修改檔案**：1 個（`f1t_gui_main.py`）

#### 第二階段：Bug 修復（已完成）
- ✅ **修復 Widget Parent 問題**：彈出時 MDI 子視窗消失
  - **問題**：直接使用 `setCentralWidget()` 導致 MDI 區域從 QTabWidget 移除，子視窗被清空
  - **修復**：使用佔位符 widget 保持分頁索引，正確管理 parent 關係
  - **方法**：`removeTab()` → `insertTab(placeholder)` → `setCentralWidget(mdi_area)`
- ✅ **修復 KeyError 問題**：返回時出現索引錯誤
  - **問題**：彈出時未正確保存佔位符引用
  - **修復**：在 `popped_out_tabs` 字典中添加 `placeholder` 欄位
  - **方法**：`takeCentralWidget()` → `removeTab()` → `insertTab(mdi_area)`

#### 下一步：功能測試
- [ ] 測試單一分頁彈出/返回（修復後重新測試）
- [ ] 測試多分頁同時彈出
- [ ] 測試工具列功能
- [ ] 測試參數同步
- [ ] 測試 HOME 主頁限制

---

## 🎉 完成標準

- [ ] 所有測試計劃通過
- [ ] 無記憶體洩漏
- [ ] 無 AttributeError 或 TypeError
- [x] 代碼符合 F1T 專案規範
- [x] 添加完整的調試輸出
- [ ] 更新相關文檔
- [x] 無語法錯誤

**預計完成時間**：2-3 小時  
**實際完成時間**：約 1.5 小時（核心實現完成）
