# 🔧 Box Plot MDI 視窗控制按鈕修正報告

## 🐛 問題描述

**用戶反饋**: Box Plot 視窗沒有像折線圖一樣的視窗控制按鈕（最小化、最大化、關閉）

**症狀**:
- ❌ 缺少視窗標題列的控制按鈕
- ❌ 無法最小化視窗
- ❌ 無法最大化視窗
- ❌ 關閉按鈕可能不完整

---

## 🔍 根本原因

### 錯誤實現（修正前）

```python
# ❌ 使用了標準的 QMdiSubWindow
sub_window = QMdiSubWindow()
sub_window.setWidget(boxplot_mdi.get_widget())
sub_window.setAttribute(Qt.WA_DeleteOnClose)
sub_window.setWindowTitle(window_title)
```

**問題**: `QMdiSubWindow` 是 Qt 的基本類別，缺少自訂的視窗控制功能。

---

### 正確實現（修正後）

```python
# ✅ 使用自訂的 PopoutSubWindow
sub_window = PopoutSubWindow(window_title, mdi_area, boxplot_mdi)
sub_window.setWidget(boxplot_mdi.get_widget())
```

**優勢**: `PopoutSubWindow` 是專案自訂類別，包含：
1. ✅ 完整的視窗控制按鈕（最小化、最大化、關閉）
2. ✅ 拖曳標題列移動視窗
3. ✅ 調整視窗大小
4. ✅ 彈出為獨立視窗功能
5. ✅ 自訂樣式和主題支援

---

## 📊 PopoutSubWindow vs QMdiSubWindow

| 特性 | QMdiSubWindow | PopoutSubWindow |
|------|---------------|-----------------|
| **最小化按鈕** | ❌ 有限支援 | ✅ 完整功能 |
| **最大化按鈕** | ❌ 有限支援 | ✅ 完整功能 |
| **關閉按鈕** | ⚠️ 基本功能 | ✅ 完整功能 |
| **拖曳移動** | ⚠️ 基本功能 | ✅ 增強功能 |
| **調整大小** | ⚠️ 基本功能 | ✅ 增強功能 |
| **彈出視窗** | ❌ 不支援 | ✅ 支援 |
| **自訂樣式** | ❌ 不支援 | ✅ 支援 |
| **resize 信號** | ❌ 無 | ✅ 有 |
| **主題整合** | ❌ 無 | ✅ 有 |

---

## 🔧 修正內容

### 文件: `f1t_gui_main.py`

#### 方法: `create_laptime_boxplot_window()` (約 Line 8613)

**修正前**:
```python
# 創建 MDI 子視窗
sub_window = QMdiSubWindow()
sub_window.setWidget(boxplot_mdi.get_widget())
sub_window.setAttribute(Qt.WA_DeleteOnClose)

# 設置視窗標題
window_title = f"📦 Lap Time Box Plot - {year} {race} {session}"
sub_window.setWindowTitle(window_title)

# 設置視窗大小
sub_window.resize(1400, 800)

# 獲取 MDI 區域
current_tab = self.tab_widget.currentWidget()
# ... 查找 mdi_area ...

# 添加子視窗到 MDI 區域
mdi_area.addSubWindow(sub_window)
sub_window.show()
```

**修正後**:
```python
# 獲取 MDI 區域（先取得，才能創建 PopoutSubWindow）
current_tab = self.tab_widget.currentWidget()
# ... 查找 mdi_area ...

# 設置視窗標題
window_title = f"📦 Lap Time Box Plot - {year} {race} {session}"

# 創建 PopoutSubWindow（帶完整視窗控制按鈕）
sub_window = PopoutSubWindow(window_title, mdi_area, boxplot_mdi)
sub_window.setWidget(boxplot_mdi.get_widget())

# 設置視窗大小
sub_window.resize(1400, 800)

# 更新參數並載入數據
boxplot_mdi.update_lap_parameters(year, race, session)

# 視窗會自動顯示（PopoutSubWindow 建構函式會處理）
```

---

## 🔑 關鍵改進

### 1. 調整執行順序

**原因**: `PopoutSubWindow` 的建構函式需要 `mdi_area` 參數

**修正前**:
```
更新參數 → 創建視窗 → 取得 MDI 區域 → 添加視窗
```

**修正後**:
```
取得 MDI 區域 → 創建 PopoutSubWindow → 更新參數
```

---

### 2. PopoutSubWindow 建構函式

```python
PopoutSubWindow(
    title: str,           # 視窗標題
    mdi_area: QMdiArea,   # MDI 區域（必須先取得）
    analysis_module       # 分析模組（可選）
)
```

**自動處理**:
- ✅ 自動添加到 `mdi_area`
- ✅ 自動顯示視窗
- ✅ 設置視窗控制按鈕
- ✅ 應用自訂樣式

---

### 3. 移除冗餘代碼

**移除項目**:
```python
sub_window.setAttribute(Qt.WA_DeleteOnClose)  # PopoutSubWindow 已內建
sub_window.setWindowTitle(window_title)       # 建構函式已設置
mdi_area.addSubWindow(sub_window)             # 建構函式已處理
sub_window.show()                              # 建構函式已處理
```

---

## 🎨 PopoutSubWindow 特性

### 視窗控制按鈕

```
┌─ 📦 Lap Time Box Plot - 2025 Belgium R ──────── □ ▢ ✕ ─┐
│                                                          │
│  [過濾控制面板]                                          │
│  ☑ 過濾進站圈  ☑ 過濾異常值  IQR: [1.5]  🔄  💾         │
│                                                          │
│  [箱型圖表區域]                                          │
│                                                          │
└──────────────────────────────────────────────────────────┘
 ↑                                              ↑  ↑  ↑
 拖曳移動                                    最小 最大 關閉
```

### 控制按鈕功能

| 按鈕 | 符號 | 功能 | 快捷鍵 |
|------|------|------|--------|
| **最小化** | `□` | 最小化視窗到任務列 | - |
| **最大化** | `▢` | 最大化填滿 MDI 區域 | - |
| **關閉** | `✕` | 關閉視窗 | Alt+F4 |

---

## 🧪 驗證測試

### 測試步驟

1. **啟動 GUI**
   ```powershell
   python f1t_gui_main.py
   ```

2. **開啟 Box Plot**
   - 選擇 2025 Belgium R
   - 點擊 "Detailed Lap Analysis"
   - 選擇 "Box Plot"

3. **測試控制按鈕**
   - ✅ 點擊最小化按鈕 → 視窗縮小
   - ✅ 點擊最大化按鈕 → 視窗填滿
   - ✅ 拖曳標題列 → 視窗移動
   - ✅ 拖曳邊框 → 調整大小
   - ✅ 點擊關閉按鈕 → 視窗關閉

---

## 📋 檢查清單

- [x] 使用 `PopoutSubWindow` 而非 `QMdiSubWindow`
- [x] 調整執行順序（先取得 `mdi_area`）
- [x] 移除冗餘的 `addSubWindow()` 和 `show()` 調用
- [x] 移除 `setAttribute(Qt.WA_DeleteOnClose)`（已內建）
- [x] 移除 `setWindowTitle()`（建構函式已處理）
- [x] 保留 `resize()` 設定視窗大小
- [x] 驗證無編譯錯誤

---

## 🔄 與其他模組的一致性

### 現有模組比較

**Rain Analysis** (正確實現):
```python
analysis_window = PopoutSubWindow(window_title, mdi_area, analysis_module)
```

**Tire Analysis** (正確實現):
```python
analysis_window = PopoutSubWindow(window_title, mdi_area, analysis_module)
```

**Box Plot Analysis** (修正後):
```python
sub_window = PopoutSubWindow(window_title, mdi_area, boxplot_mdi)
```

✅ **現在所有模組都使用相同的 `PopoutSubWindow` 架構**

---

## 📊 影響範圍

### 修改文件

- ✅ `f1t_gui_main.py` (1 個方法，~40 行)

### 未修改文件

- ⚪ `lap_box_plot_analysis_mdi.py` (無需修改)
- ⚪ `lap_box_plot_chart_widget.py` (無需修改)

---

## 🎯 預期結果

### 修正後的視窗外觀

```
┌─ 📦 Lap Time Box Plot - 2025 Belgium R ──────── □ ▢ ✕ ─┐
│ ☰                                                        │ ← 拖曳區域
├──────────────────────────────────────────────────────────┤
│  🔧 過濾控制                                             │
│  ☑ 過濾進站圈  ☑ 過濾異常值  IQR閾值: [1.5]             │
│  車手數: 20 | 總圈數: 900+ | 平均時間: 105.3秒          │
│  [🔄 重新載入]  [💾 匯出圖表]                            │
├──────────────────────────────────────────────────────────┤
│                                                          │
│               [箱型圖表顯示區域]                         │
│                                                          │
│  🏠━━━━━━━━━━━━ 導航工具列 ━━━━━━━━━━━━🔍              │
│  [Home][Back][Forward][Pan][Zoom][Config][Save]          │
│                                                          │
│     ┌──┐  ┌──┐  ┌──┐  ┌──┐  ┌──┐                      │
│     │  │  │  │  │  │  │  │  │  │                      │
│ 105s├──┤  ├══┤  ├══┤  ├══┤  ├══┤  ...                 │
│     ├──┤  ├──┤  ├──┤  ├──┤  ├──┤                      │
│     └──┘  └──┘  └──┘  └──┘  └──┘                      │
│     VER   LEC   HAM   NOR   PIA   ...                   │
│                                                          │
└──────────────────────────────────────────────────────────┘
 ↑                                              ↑  ↑  ↑
 可拖曳調整大小                              最小 最大 關閉
```

---

## 🏆 成就解鎖

✅ **完整的 MDI 視窗控制**  
✅ **與其他模組一致的架構**  
✅ **使用者體驗改善**  
✅ **專業級視窗管理**  

---

## 📝 總結

**問題**: Box Plot 視窗缺少視窗控制按鈕  
**原因**: 使用了標準 `QMdiSubWindow` 而非自訂 `PopoutSubWindow`  
**解決**: 修改 `create_laptime_boxplot_window()` 使用 `PopoutSubWindow`  
**結果**: 完整的視窗控制功能（最小化、最大化、關閉、拖曳、調整大小）  

**狀態**: ✅ **已修正並驗證**

---

*修正報告生成時間: 2025-10-02*  
*修正者: F1T AI Programming Assistant*  
*版本: 1.0.1*
