# MDI 視窗標題欄按鈕功能說明

## 📋 概述

F1T 遙測分析模組的 MDI 視窗左上方有三個控制按鈕：**S**、**L**、**D**，這些按鈕提供精細的同步和連動控制功能。

---

## 🔘 按鈕功能詳解

### 1. **S 按鈕** - 接收主程式同步 (Sync)

**位置**：標題欄左側第一個按鈕  
**預設狀態**：啟用 ✅  
**圖標切換**：`S` (啟用) ↔ `X` (停用)

#### 功能說明
控制該視窗是否接收來自主程式的參數同步更新。

- **啟用 (S)**：視窗會接收主程式傳送的賽事參數（年份、賽事、會話）
  - 當主程式選擇新的賽事時，該視窗會自動更新
  - 適合需要跟隨主程式切換分析目標的情況
  
- **停用 (X)**：視窗進入獨立運作模式
  - 不接收主程式的參數更新
  - 可保持當前分析結果，不被主程式影響
  - 適合需要對比不同賽事資料的情況

#### 使用情境範例
```
情境：您正在分析 2025 Japan R 的遙測資料
操作：將 S 按鈕切換為 X（停用）
結果：即使主程式切換到其他賽事，此視窗仍保持 Japan R 的資料
用途：同時對比多個賽事的分析結果
```

#### 實現位置
- 檔案：[windows/widgets/draggable_title_bar.py](c:\Users\mike2\OneDrive\Code\F1-data-analyze\windows\widgets\draggable_title_bar.py#L64-L71)
- 方法：`toggle_x_sync()` (第 340 行)

---

### 2. **L 按鈕** - 個別連動 (Linkage)

**位置**：標題欄左側第二個按鈕  
**預設狀態**：啟用 ✅  
**圖標切換**：`L` (啟用) ↔ `X` (停用)

#### 功能說明
控制該視窗是否參與圈速分析的連動功能。

- **啟用 (L)**：視窗參與連動系統
  - 當主連動開關啟用時，與其他視窗聯動
  - 點擊圖表中的某一圈，所有啟用連動的視窗會同步顯示該圈
  - 適合需要跨視窗對比同一圈數據的情況
  
- **停用 (X)**：視窗退出連動系統
  - 不響應其他視窗的連動請求
  - 可獨立選擇要分析的圈數
  - 適合需要固定顯示特定圈數據的情況

#### 連動系統架構
```
主連動開關（GUI 選單）
    ↓
個別視窗 L 按鈕
    ↓
視窗間圈速數據同步
```

#### 使用情境範例
```
情境：同時打開速度分析、RPM 分析、油門分析三個視窗
操作 1：所有視窗的 L 按鈕保持啟用
結果 1：在速度分析點擊第 10 圈 → RPM 和油門也自動切換到第 10 圈

操作 2：將 RPM 分析的 L 按鈕切換為 X（停用）
結果 2：RPM 視窗保持當前圈數，不受其他視窗影響
用途：對比特定圈的 RPM 與其他圈的速度/油門
```

#### 實現位置
- 檔案：[windows/widgets/draggable_title_bar.py](c:\Users\mike2\OneDrive\Code\F1-data-analyze\windows\widgets\draggable_title_bar.py#L74-L81)
- 方法：`toggle_individual_linkage()` (第 355 行)
- 參考：[modules/gui/lap_analysis/linkage/linkage_ui.py](c:\Users\mike2\OneDrive\Code\F1-data-analyze\modules\gui\lap_analysis\linkage\linkage_ui.py)

---

### 3. **D 按鈕** - 車手與圈數同步 (Driver Lap Sync)

**位置**：標題欄左側第三個按鈕  
**預設狀態**：啟用 ✅ (僅遙測模組顯示)  
**圖標切換**：`D` (啟用) ↔ `X` (停用)  
**顯示條件**：僅在遙測分析模組顯示，其他模組隱藏

#### 功能說明
控制遙測視窗是否與主視窗同步車手選擇和圈數選擇。

- **啟用 (D)**：與主視窗參數保持同步
  - 自動使用主視窗選擇的車手 1、車手 2
  - 自動使用主視窗選擇的圈數 1、圈數 2
  - 主視窗變更參數時，遙測視窗自動更新資料
  - 適合快速跟隨主視窗切換分析目標
  
- **停用 (X)**：使用全域參數池（獨立模式）
  - 使用遙測模組自己的設定對話框設定參數
  - 可選擇與主視窗不同的車手和圈數
  - 設定對話框的控制項變為可編輯狀態
  - 適合進行獨立的遙測分析

#### 與設定對話框的互動
```
D 按鈕啟用 (D) → Settings 對話框控制項鎖定（灰色）
                → 顯示主視窗參數
                → 不可編輯

D 按鈕停用 (X) → Settings 對話框控制項解鎖（可編輯）
                → 載入全域參數池
                → 可自由編輯車手和圈數
```

#### 使用情境範例
```
情境 1：跟隨主視窗模式
主視窗：VER vs LEC, Lap 10 vs Lap 15
D 按鈕：啟用 (D)
遙測視窗：自動顯示 VER vs LEC, Lap 10 vs Lap 15 的遙測對比

情境 2：獨立分析模式
主視窗：VER vs LEC, Lap 10 vs Lap 15
D 按鈕：停用 (X)
遙測視窗：可在 Settings 設定為 HAM vs SAI, Lap 5 vs Lap 8
用途：對比不同車手組合的遙測資料
```

#### 資料重新載入機制
當 D 按鈕狀態變更時，系統會自動重新載入資料：

1. **啟用 → 停用 (D → X)**
   - 調用 `_reload_data_with_shared_params()`
   - 載入全域參數池的資料
   - 更新 Settings 對話框 UI（如果已打開）

2. **停用 → 啟用 (X → D)**
   - 調用 `_reload_data_with_main_window_params()`
   - 讀取主視窗當前參數
   - 重新載入對應的遙測資料

#### 實現位置
- 檔案：[windows/widgets/draggable_title_bar.py](c:\Users\mike2\OneDrive\Code\F1-data-analyze\windows\widgets\draggable_title_bar.py#L84-L91)
- 方法：`toggle_driver_lap_sync()` (第 360 行)
- 重載邏輯：`_reload_data_with_main_window_params()` (第 414 行)

---

## 🎨 視覺化狀態指示

### 按鈕顏色系統
所有三個按鈕使用統一的顏色系統來指示狀態：

| 狀態 | 圖標 | 顏色 | 說明 |
|------|------|------|------|
| **啟用** | `S` / `L` / `D` | 🟢 綠色 | 功能正常運作 |
| **停用** | `X` | 🔴 紅色 / 灰色 | 功能已關閉 |

### 樣式強制更新
為確保顏色正確顯示，每次狀態切換時都會執行：
```python
# 強制重新應用樣式確保顏色更新
self.sync_btn.style().unpolish(self.sync_btn)
self.sync_btn.style().polish(self.sync_btn)
self.sync_btn.update()
```

---

## 🔄 按鈕互動邏輯

### 按鈕狀態組合範例

#### 組合 1：完全同步模式
```
S = ✅ 啟用  → 接收主程式賽事更新
L = ✅ 啟用  → 參與圈速連動
D = ✅ 啟用  → 同步車手與圈數（僅遙測模組）
```
**適用場景**：快速跟隨主程式進行多視窗分析

---

#### 組合 2：獨立分析模式
```
S = ❌ 停用  → 固定當前賽事
L = ❌ 停用  → 固定當前圈數
D = ❌ 停用  → 使用自訂車手與圈數
```
**適用場景**：深入分析特定賽事、特定圈、特定車手組合

---

#### 組合 3：部分連動模式
```
S = ✅ 啟用  → 跟隨主程式切換賽事
L = ❌ 停用  → 不參與圈速連動
D = ❌ 停用  → 使用自訂車手
```
**適用場景**：分析同一賽事的不同車手或圈數組合

---

## 🛠️ 開發者參考

### 按鈕初始化
```python
# S 按鈕 - 接收同步
self.sync_btn = QPushButton("S")
self.sync_btn.setCheckable(True)
self.sync_btn.setChecked(True)  # 預設啟用
self.sync_btn.clicked.connect(self.toggle_x_sync)

# L 按鈕 - 個別連動
self.linkage_btn = QPushButton("L")
self.linkage_btn.setCheckable(True)
self.linkage_btn.setChecked(True)  # 預設啟用
self.linkage_btn.clicked.connect(self.toggle_individual_linkage)

# D 按鈕 - 車手與圈數同步
self.driver_lap_sync_btn = QPushButton("D")
self.driver_lap_sync_btn.setCheckable(True)
self.driver_lap_sync_btn.setChecked(True)  # 預設啟用
self.driver_lap_sync_btn.setVisible(False)  # 預設隱藏
self.driver_lap_sync_btn.clicked.connect(self.toggle_driver_lap_sync)
```

### 按鈕顯示控制（D 按鈕）
D 按鈕只在遙測模組中顯示：
```python
# 在遙測模組初始化時啟用 D 按鈕
if hasattr(sub_window, 'title_bar_widget'):
    title_bar = sub_window.title_bar_widget
    if hasattr(title_bar, 'driver_lap_sync_btn'):
        title_bar.driver_lap_sync_btn.setVisible(True)
```

### 狀態同步機制
```python
# S 按鈕 → 更新視窗的 sync_enabled 屬性
self.parent_window.sync_enabled = is_enabled

# L 按鈕 → 調用視窗的 set_linkage_enabled 方法
self.parent_window.set_linkage_enabled(is_enabled)

# D 按鈕 → 更新分析模組的 sync_driver_lap_enabled 屬性
self.parent_window.analysis_module.sync_driver_lap_enabled = is_enabled
```

---

## 📚 相關檔案

### 核心實現
- [windows/widgets/draggable_title_bar.py](c:\Users\mike2\OneDrive\Code\F1-data-analyze\windows\widgets\draggable_title_bar.py) - 標題欄主實現
- [modules/gui/lap_analysis/linkage/linkage_ui.py](c:\Users\mike2\OneDrive\Code\F1-data-analyze\modules\gui\lap_analysis\linkage\linkage_ui.py) - 連動 UI 組件
- [windows/managers/lap_linkage_toggler.py](c:\Users\mike2\OneDrive\Code\F1-data-analyze\windows\managers\lap_linkage_toggler.py) - 主連動開關

### 遙測模組
- [modules/gui/telemetry_analysis_mdi.py](c:\Users\mike2\OneDrive\Code\F1-data-analyze\modules\gui\telemetry_analysis_mdi.py) - 遙測分析 MDI 主模組

---

## 🎯 最佳實踐建議

### 1. **多視窗對比分析**
```
建議配置：
- 開啟 3 個速度分析視窗
- 視窗 1: S=✅, L=✅, D=✅ (主視窗同步)
- 視窗 2: S=❌, L=✅, D=❌ (固定不同賽事，參與連動)
- 視窗 3: S=❌, L=❌, D=❌ (完全獨立)
```

### 2. **快速切換分析目標**
```
建議配置：
- 所有視窗: S=✅, L=✅, D=✅
- 在主視窗切換賽事/車手/圈數
- 所有視窗自動更新
```

### 3. **深入分析特定場景**
```
建議配置：
- 主視窗: S=✅ (跟隨賽事更新)
- 分析視窗: S=❌, L=❌, D=❌ (固定分析目標)
- 用途：主視窗瀏覽，分析視窗深入特定場景
```

---

## ❓ 常見問題

### Q1: 為什麼 S 按鈕切換為 X 後，視窗標題仍顯示「Speed Analysis」或「Brake Analysis」？
**A**: 您看到的「Speed Analysis」、「Brake Analysis」等文字是**分頁標籤 (Tab)**，不是視窗標題。

- **T3b 標籤**：位於視窗頂部，標識整個分頁區域
- **視窗標題**：位於 MDI 子視窗的標題欄中
- S 按鈕控制的是視窗是否接收主程式的參數同步，不會改變 Tab 標籤名稱

如果您想重新命名 Tab 標籤：
1. 在 Tab 標籤上按右鍵
2. 選擇「重新命名分頁」
3. 輸入新名稱（例如："速度分析 (獨立)"）

### Q2: 為什麼有些視窗看不到 D 按鈕？
**A**: D 按鈕僅在遙測分析模組中顯示，其他模組（如速度分析、RPM 分析）不需要此功能。

### Q2: S 按鈕和 D 按鈕有什麼區別？
**A**: 
- **S 按鈕**：控制是否接收主程式的**賽事參數**（年份、賽事、會話）
- **D 按鈕**：控制是否同步主視窗的**車手和圈數選擇**（僅遙測模組）

### Q4: L 按鈕停用後，為什麼還是會自動切換圈數？
**A**: 可能是主連動開關也啟用了。檢查 GUI 選單中的「圈速分析連動」總開關是否已關閉。

### Q5: 按鈕點擊後沒有反應怎麼辦？
**A**: 
1. 檢查終端日誌是否有錯誤訊息
2. 確認 `logger.debug` 是否輸出對應的狀態變更訊息
3. 檢查視窗是否正確實現對應的方法（`sync_enabled`、`set_linkage_enabled` 等）

### Q6: 如何完全禁用所有同步功能？
**A**: 將所有三個按鈕切換為 X 狀態：
```
S = X (停用接收同步)
L = X (停用個別連動)
D = X (停用車手圈數同步)
```

### Q7: 按鈕支援多國語言嗎？
**A**: ✅ **是的！** 自 v1.1.0 版本起，所有 S、L、D 按鈕的 tooltip 已完整支援多國語言：
- 🇨🇳 中文 (繁體)
- 🇬🇧 英文
- 🇯🇵 日文

切換語言後，tooltip 會自動更新為對應語言。

---

## 📝 更新日誌

| 日期 | 版本 | 變更內容 |
|------|------|----------|
| 2025-12-20 | 1.1.0 | ✅ 修復：完整多國語言化所有 S、L、D 按鈕的 tooltip<br>✅ 說明：澄清「同步」標籤實際上是 Tab 標籤，不會隨 S 按鈕變化 |
| 2025-12-20 | 1.0.0 | 初始版本 - 完整功能說明文檔 |

---

## 📧 技術支援

如有任何問題或建議，請參考：
- 專案 README: [README.md](c:\Users\mike2\OneDrive\Code\F1-data-analyze\README.md)
- 開發指導: [.github/copilot-instructions.md](c:\Users\mike2\OneDrive\Code\F1-data-analyze\.github\copilot-instructions.md)
- 即時遙測指南: [docs/LIVE_TIMING_MODULE_GUIDE.md](c:\Users\mike2\OneDrive\Code\F1-data-analyze\docs\LIVE_TIMING_MODULE_GUIDE.md)
