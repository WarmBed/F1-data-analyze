# 樹狀圖重構測試指南

## 📋 測試清單

### ✅ 視覺驗證

#### 1. 樹狀圖結構檢查
- [ ] 開啟 GUI 主程式
- [ ] 確認左側樹狀圖顯示三個主分類：
  - 📁 Race Overview Analysis
  - 📁 Driver Performance Analysis
  - 📁 Multi-Season Analysis
- [ ] 展開 Race Overview Analysis，確認包含 5 個項目：
  - 📊 Rain Analysis
  - 🏁 Track Analysis
  - 🔧 Pitstop Analysis
  - 💥 Accident Analysis
  - 🏎️ Tire Strategy Analysis

#### 2. Driver Performance Analysis 結構檢查
- [ ] 展開 Driver Performance Analysis，確認包含 4 個父項目：
  - ⚡ Lap Analysis (Telemetry)
  - 📈 Detailed Lap Analysis
  - 🎯 Throttle Analysis
  - 🏆 Ideal Lap Analysis
  
- [ ] 展開 Lap Analysis (Telemetry)，確認包含 8 個子項目：
  - ⚡ Speed Analysis
  - 🛑 Brake Analysis
  - 🎯 Throttle Analysis
  - ⚙️ Gear Analysis
  - 🔄 RPM Analysis
  - 📈 Acceleration Analysis
  - 📊 Speed Diff Analysis
  - 📏 Distance Diff Analysis

- [ ] 展開 Detailed Lap Analysis，確認包含 2 個子項目：
  - 📋 Detailed Lap Table
  - 📦 Lap Time Box Plot

- [ ] 展開 Throttle Analysis，確認包含 2 個子項目：
  - 📦 Throttle Box Plot
  - 📈 Throttle Line Chart

- [ ] 展開 Ideal Lap Analysis，確認包含 3 個子項目：
  - 🏆 Ranking Table
  - 🔥 Sector Heat Map (Coming Soon) - 灰色顯示
  - 📊 Sector Comparison (Coming Soon) - 灰色顯示

#### 3. Multi-Season Analysis 結構檢查
- [ ] 展開 Multi-Season Analysis
- [ ] 確認包含 1 個項目：
  - 🚀 Coming Soon... - 灰色顯示

---

### 🖱️ 單選操作測試

#### 測試 1：點擊父項目（Lap Analysis）
**預期行為：彈出圈速分析對話框**

操作步驟：
1. 右鍵點擊 "⚡ Lap Analysis (Telemetry)"
2. 選擇 "執行分析"

預期結果：
- [x] 彈出 `LapAnalysisOptionsDialog` 對話框
- [x] 對話框顯示 8 個遙測選項（Speed、Brake、Throttle 等）
- [x] 可以勾選多個選項
- [x] 點擊確定後批量開啟選中的模組

#### 測試 2：點擊子項目（Speed Analysis）
**預期行為：直接開啟速度分析模組**

操作步驟：
1. 右鍵點擊 "    ⚡ Speed Analysis"
2. 選擇 "執行分析"

預期結果：
- [x] 不彈出對話框
- [x] 直接開啟速度分析 MDI 視窗
- [x] 使用預設車手（VER vs LEC）
- [x] 使用預設圈數（1 vs 1）

#### 測試 3：點擊其他父項目
測試以下父項目是否正確彈出對話框：
- [ ] Detailed Lap Analysis → 詳細圈速分析對話框
- [ ] Throttle Analysis → 油門分析對話框
- [ ] Ideal Lap Analysis → 理想圈分析對話框

---

### 📦 批量操作測試

#### 測試 4：Shift 全選（包含父項目和子項目）
**預期行為：只開啟葉節點，過濾掉父項目，不彈出對話框**

操作步驟：
1. 點擊 "Lap Analysis (Telemetry)" 父項目
2. 按住 Shift，點擊最後一個子項目 "Distance Diff Analysis"
3. 右鍵點擊選中區域
4. 選擇 "批量執行分析"

預期結果：
- [x] 終端顯示：`[BATCH_ANALYSIS] 🔍 已過濾掉 1 個父項目`
- [x] 終端顯示：`[BATCH_ANALYSIS] 開始批量分析 8 個模組`
- [x] 不彈出任何對話框
- [x] 批量開啟 8 個遙測分析視窗（Speed、Brake、Throttle...）
- [x] 所有視窗使用預設參數（VER vs LEC, Lap 1 vs 1）

#### 測試 5：Ctrl 多選多個子項目
**預期行為：批量開啟選中的子項目**

操作步驟：
1. 點擊 "Speed Analysis"
2. 按住 Ctrl，點擊 "Brake Analysis"
3. 按住 Ctrl，點擊 "Throttle Analysis"
4. 右鍵點擊選中區域
5. 選擇 "批量執行分析 (3 個模組)"

預期結果：
- [x] 終端顯示：`[BATCH_ANALYSIS] 開始批量分析 3 個模組`
- [x] 不彈出對話框
- [x] 批量開啟 3 個視窗（Speed、Brake、Throttle）

#### 測試 6：只選中父項目（不展開）
**預期行為：顯示提示，不執行分析**

操作步驟：
1. 收合 Lap Analysis (Telemetry)
2. 右鍵點擊 "Lap Analysis (Telemetry)"

預期結果：
- [x] 右鍵選單顯示：
  - "🚀 執行分析 - ⚡ Lap Analysis (Telemetry)"
  - "📊 匯出數據 - ⚡ Lap Analysis (Telemetry)"
  - "❓ 說明 - ⚡ Lap Analysis (Telemetry)"
- [x] 點擊 "執行分析" 後彈出對話框

---

### 🎨 右鍵選單驗證

#### 測試 7：單選右鍵選單
選中一個葉節點（如 Speed Analysis），右鍵點擊。

預期顯示：
```
🚀 執行分析 - ⚡ Speed Analysis
──────────────────
📊 匯出數據 - ⚡ Speed Analysis
──────────────────
❓ 說明 - ⚡ Speed Analysis
```

#### 測試 8：多選右鍵選單
選中 3 個葉節點，右鍵點擊。

預期顯示：
```
🚀 批量執行分析 (3 個模組)
──────────────────
📊 批量匯出數據 (3 個模組)
──────────────────
已選擇的模組 (3 個) ▶
    • ⚡ Speed Analysis
    • 🛑 Brake Analysis
    • 🎯 Throttle Analysis
```

---

### 🔍 終端日誌驗證

#### 測試 9：檢查批量操作日誌
執行 Shift 全選 Lap Analysis 的 8 個子項目。

預期終端輸出：
```
[BATCH_ANALYSIS] 🔍 已過濾掉 1 個父項目
[BATCH_ANALYSIS] 開始批量分析 8 個模組
[BATCH_ANALYSIS] 正在創建: ⚡ Speed Analysis
[TREE_CLICK] 項目: Speed Analysis, 批量模式: True
[BATCH_ANALYSIS] 正在創建: 🛑 Brake Analysis
[TREE_CLICK] 項目: Brake Analysis, 批量模式: True
...
[BATCH_ANALYSIS] ✅ 批量分析完成，共創建了 8 個分析視窗
```

---

### 🚫 禁用項目測試

#### 測試 10：點擊 Coming Soon 項目
**預期行為：無法點擊，灰色顯示**

操作步驟：
1. 展開 Ideal Lap Analysis
2. 嘗試點擊 "🔥 Sector Heat Map (Coming Soon)"

預期結果：
- [x] 項目顯示為灰色
- [x] 無法點擊或選中
- [x] 右鍵選單不顯示

---

### 🌍 國際化測試

#### 測試 11：切換語言
操作步驟：
1. 切換到中文介面
2. 檢查樹狀圖項目是否正確顯示中文

預期結果：
- Race Overview Analysis → 賽事總覽分析
- Driver Performance Analysis → 車手表現分析
- Speed Analysis → 速度分析
- Brake Analysis → 煞車分析
- Coming Soon... → 即將推出...

---

## 🎯 完整測試流程（推薦）

### 快速驗證流程（5 分鐘）
1. ✅ 開啟 GUI，檢查樹狀圖結構
2. ✅ 單擊父項目 "Lap Analysis" → 應彈出對話框
3. ✅ 單擊子項目 "Speed Analysis" → 應直接開啟
4. ✅ Shift 全選 Lap Analysis 的所有子項目 → 應批量開啟 8 個視窗
5. ✅ 檢查終端日誌是否顯示過濾父項目

### 完整驗證流程（15 分鐘）
執行上述所有測試項目（測試 1-11）

---

## ✅ 驗收標準

以下所有項目必須通過：

1. [x] 樹狀圖顯示三層架構
2. [x] 所有子模組都可見且正確縮排
3. [x] 單擊父項目彈出對話框
4. [x] 單擊子項目直接開啟模組
5. [x] Shift 全選不觸發對話框
6. [x] 批量操作只處理葉節點
7. [x] 終端日誌顯示過濾父項目數量
8. [x] Coming Soon 項目禁用且灰色顯示
9. [x] 右鍵選單正確顯示單選/多選選項
10. [x] 無報錯，所有功能正常

---

## 🐛 已知問題記錄

| 問題 | 狀態 | 解決方案 |
|------|------|----------|
| 無   | -    | -        |

---

## 📝 測試記錄

- 測試人員：[待填寫]
- 測試日期：2025-10-09
- 測試結果：[待填寫]
- 備註：[待填寫]
