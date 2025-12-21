# MDI 視窗右鍵選單分析報告

## ✅ **回答您的問題**

**問題**：所有 MDI 視窗（包含 Lap Analysis）與通用 MDI 視窗的右鍵列表是我們自己定義的嗎？

**答案**：**是的！** 所有 MDI 視窗的右鍵選單都是我們在 `CustomMdiArea` 類別中自己定義的。

---

## 📊 **右鍵選單架構分析**

### **1. CustomMdiArea 類別** (Line 77-150)

這是所有 MDI 視窗的容器，負責統一管理右鍵選單：

```python
class CustomMdiArea(QMdiArea):
    """自定義MDI區域，強制執行子視窗最小尺寸限制並啟用內建功能"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # ✅ 啟用右鍵選單
        self.setContextMenuPolicy(Qt.DefaultContextMenu)  # 啟用預設右鍵選單
    
    def contextMenuEvent(self, event):
        """處理右鍵選單事件 - 我們自己定義的邏輯"""
        # 判斷右鍵點擊位置
        if subwindow:
            # 在子視窗上右鍵 → 顯示視窗管理選單
            menu = self._create_window_menu(subwindow)
        else:
            # 在空白區域右鍵 → 顯示區域管理選單
            menu = self._create_area_menu()
        
        menu.exec_(event.globalPos())
```

---

## 🎯 **右鍵選單內容**

### **情境 1: 在子視窗上右鍵** (MDI 子視窗標題列或內容區域)

```python
menu = QMenu(self)

# 視窗排列選項
cascade_action = menu.addAction("層疊視窗 (&C)")
tile_action = menu.addAction("平舖視窗 (&T)")

menu.addSeparator()

# 關閉選項
close_action = menu.addAction("關閉視窗 (&X)")
close_all_action = menu.addAction("關閉所有視窗 (&A)")

menu.addSeparator()

# 視窗狀態選項（動態生成）
if subwindow.isMaximized():
    restore_action = menu.addAction("還原視窗 (&R)")
else:
    maximize_action = menu.addAction("最大化視窗 (&M)")

minimize_action = menu.addAction("最小化視窗 (&N)")
```

**顯示的選單項目**：
1. 層疊視窗 (C)
2. 平舖視窗 (T)
3. --- 分隔線 ---
4. 關閉視窗 (X)
5. 關閉所有視窗 (A)
6. --- 分隔線 ---
7. 最大化視窗 (M) **或** 還原視窗 (R) ← 動態切換
8. 最小化視窗 (N)

### **情境 2: 在空白區域右鍵** (MDI 區域的背景)

```python
menu = QMenu(self)

# 區域管理選項
cascade_action = menu.addAction("層疊所有視窗")
tile_action = menu.addAction("平舖所有視窗")

menu.addSeparator()

close_all_action = menu.addAction("關閉所有視窗")
```

**顯示的選單項目**：
1. 層疊所有視窗
2. 平舖所有視窗
3. --- 分隔線 ---
4. 關閉所有視窗

---

## 🔍 **PopoutSubWindow 的右鍵選單**

### **發現**：

`PopoutSubWindow` 類別**沒有自定義 `contextMenuEvent()` 方法**！

**檢查結果**：
```python
# PopoutSubWindow 的所有方法（前30個）
def __init__(...)
def _extract_module_name_from_title(...)
def _handle_module_error(...)
def update_current_window(...)
def mousePressEvent(...)
def mouseMoveEvent(...)
def paintEvent(...)
# ... 其他方法

# ❌ 沒有 contextMenuEvent() 方法！
```

**結論**：
- `PopoutSubWindow` 繼承自 `QMdiSubWindow`
- 它**沒有覆寫** `contextMenuEvent()`
- 所以它的右鍵選單是由**父容器** `CustomMdiArea` 統一處理的

---

## 📋 **完整的右鍵選單流程**

### **當用戶在 MDI 視窗上按右鍵時**：

```
用戶右鍵點擊
    ↓
事件傳遞到 CustomMdiArea.contextMenuEvent(event)
    ↓
判斷點擊位置:
    ├─ 在子視窗上？
    │     ↓
    │  創建視窗管理選單
    │  ├─ 層疊視窗
    │  ├─ 平舖視窗
    │  ├─ 關閉視窗
    │  ├─ 關閉所有視窗
    │  ├─ 最大化/還原視窗
    │  └─ 最小化視窗
    │
    └─ 在空白區域？
          ↓
       創建區域管理選單
       ├─ 層疊所有視窗
       ├─ 平舖所有視窗
       └─ 關閉所有視窗
```

---

## 🎯 **適用範圍**

### **所有使用 CustomMdiArea 的分頁都有此右鍵選單**：

1. **Lap Analysis 分頁** ✅
   - Speed Analysis
   - Brake Analysis
   - Throttle Analysis
   - Gear Analysis
   - RPM Analysis
   - Acceleration Analysis
   - Speed Diff Analysis
   - Distance Diff Analysis
   - Time Diff Analysis

2. **其他分析分頁** ✅
   - Rain Analysis
   - Race Overview
   - Telemetry Comparison
   - 任何使用 `CustomMdiArea` 的分頁

---

## 🔧 **自定義右鍵選單的方法**

如果您想為特定的 MDI 視窗添加**專屬的右鍵選單項目**，有兩種方法：

### **方法 1: 在 PopoutSubWindow 中覆寫 contextMenuEvent()**

```python
class PopoutSubWindow(QMdiSubWindow):
    def contextMenuEvent(self, event):
        """自定義右鍵選單"""
        menu = QMenu(self)
        
        # 添加自定義選項
        refresh_action = menu.addAction("🔄 刷新數據")
        refresh_action.triggered.connect(self.update_current_window)
        
        export_action = menu.addAction("💾 導出圖表")
        export_action.triggered.connect(self._export_chart)
        
        menu.addSeparator()
        
        # 保留原有的視窗管理選項（手動添加）
        close_action = menu.addAction("❌ 關閉視窗")
        close_action.triggered.connect(self.close)
        
        # 顯示選單
        menu.exec_(event.globalPos())
```

### **方法 2: 在 CustomMdiArea 中擴展選單**

```python
class CustomMdiArea(QMdiArea):
    def contextMenuEvent(self, event):
        if subwindow:
            menu = QMenu(self)
            
            # ✅ 檢查子視窗類型，添加專屬選項
            if hasattr(subwindow, 'analysis_module'):
                # Lap Analysis 專屬選項
                refresh_action = menu.addAction("🔄 刷新此視窗")
                refresh_action.triggered.connect(subwindow.update_current_window)
                
                export_action = menu.addAction("💾 導出圖表")
                export_action.triggered.connect(lambda: self._export_window(subwindow))
                
                menu.addSeparator()
            
            # 原有的通用選項
            cascade_action = menu.addAction("層疊視窗 (&C)")
            tile_action = menu.addAction("平舖視窗 (&T)")
            # ... 其他選項
            
            menu.exec_(event.globalPos())
```

---

## ✅ **總結**

1. **是的，右鍵選單是我們自己定義的**：
   - 在 `CustomMdiArea.contextMenuEvent()` 方法中
   - 不是 Qt 的預設選單

2. **所有 MDI 子視窗共用同一套選單**：
   - `PopoutSubWindow` 沒有自定義選單
   - 由父容器 `CustomMdiArea` 統一管理

3. **選單內容**：
   - 視窗排列（層疊、平舖）
   - 視窗狀態（最大化、最小化、還原）
   - 關閉操作（關閉單一、關閉全部）

4. **可擴展性**：
   - 可以在 `CustomMdiArea` 中添加通用選項
   - 可以在 `PopoutSubWindow` 中覆寫以添加專屬選項

---

## 🎯 **下一步建議**

如果您想要：
1. **添加新的選單項目** → 修改 `CustomMdiArea.contextMenuEvent()`
2. **為特定模組添加專屬選項** → 在 `PopoutSubWindow` 中覆寫 `contextMenuEvent()`
3. **移除某些選項** → 在 `CustomMdiArea.contextMenuEvent()` 中註釋掉對應的 `addAction()`

需要我幫您實現哪一種嗎？
