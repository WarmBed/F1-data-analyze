# F1T Batch Data Generator GUI

批次數據生成器的圖形化介面，用於快速生成所有分析功能的 JSON 數據檔案。

## 🚀 快速啟動

```powershell
# 方式 1: 使用啟動器
python launch_batch_generator_gui.py

# 方式 2: 直接執行
python tools/batch_generator_gui.py
```

## 📋 功能特性

### ✨ 核心功能
- ✅ **視覺化選擇**：賽季、賽事、分析功能一目了然
- ✅ **自動載入賽程**：從 FastF1 API 自動獲取當年賽事列表
- ✅ **智能分類**：功能按類別分組顯示（賽事概況、車手性能等）
- ✅ **批次預覽**：Dry Run 模式查看待執行任務
- ✅ **即時進度**：實時顯示任務執行狀態和進度條
- ✅ **無超時限制**：針對大數據量功能（F55-F58, F120-F122）自動禁用超時

### 📊 支援的功能分類

#### 📊 Race Overview (6 個功能)
- F1 - Rain Analysis (降雨分析)
- F2 - Track Analysis (賽道分析)
- F3 - Driver Fastest Pitstop (車手最快進站)
- F4 - Team Pitstop Ranking (車隊進站排行)
- F5 - Driver Detailed Pitstop (車手進站詳細)
- F8 - Accident Analysis (事故分析)

#### 🏎️ Driver Performance (8 個功能)
- F25 - Driver Race Position (車手位置)
- F26 - Tire Strategy (輪胎策略)
- F28 - Detailed Lap Analysis (詳細圈速)
- F34 - Brake Performance (煞車性能)
- F47 - Corner Analysis (彎道分析)
- F48 - Straight Line Speed (直線速度)
- F53 - Ideal Lap Analysis (理想圈分析)
- F54 - Throttle Analysis (油門分析)

#### ⛽ Fuel & Tire Analysis (4 個功能) ⚠️ 大數據量
- F55 - Fuel Corrected Laptime (燃油校正圈速)
- F56 - Tire Degradation (輪胎衰退)
- F57 - Combined Laptime Prediction (綜合圈速預測)
- F58 - Pit Stop Strategy (進站策略預測)

#### 🔮 Prediction (2 個功能) ⚠️ ML 處理時間長
- F74 - FP3→Q Prediction (排位賽預測)
- F80 - Q→R Prediction (正賽預測)

#### 📈 Data Collection (2 個功能)
- F81 - Overtake Data Collection (超車數據收集)
- F100 - Historical Track Map (歷年旗幟統計)

#### 🆕 FP2 All Laps Analysis (3 個功能) ⚠️ 大數據量
- F120 - FP2 Corner All Laps (FP2 彎道全圈)
- F121 - FP2 Straight Line All Laps (FP2 直線全圈)
- F122 - Brake All Laps (煞車全圈)

**總計：25 種分析功能**

## 🎯 使用流程

### 1. 選擇賽季
- 從下拉選單選擇年份（2024/2025/2026）
- 點擊「📥 Load Season Schedule」自動載入該年度所有賽事

### 2. 選擇賽事
- 勾選要分析的賽事（支援多選）
- 使用「✓ Select All」快速全選
- 使用「✗ Clear All」清除選擇

### 3. 選擇功能
- 按分類勾選要執行的分析功能
- 使用「⭐ Preset: Essential」快速選擇基礎功能
- 使用「✓ Select All」選擇所有功能

### 4. 設定執行選項
- **Dry Run**：勾選後只預覽任務列表，不實際執行
- **Skip Existing JSON**：自動跳過已存在的 JSON 檔案（建議勾選）
- **Parallel Jobs**：設定並行任務數量（預設 1，建議保持 1）

### 5. 查看任務統計
- 顯示總任務數和預估執行時間
- 每個任務平均 1 分鐘

### 6. 開始執行
- 點擊「▶️ Start Generation」開始批次生成
- 查看即時日誌輸出和進度條
- 必要時可點擊「⏹️ Stop」停止執行

## ⚙️ 進階設定

### 無超時限制功能
以下功能因數據量大，自動禁用超時限制（允許執行超過 10 分鐘）：
- F55-F58（燃油/輪胎分析）
- F74, F80（預測功能）
- F120-F122（FP2 全圈數分析）

其他功能預設超時為 10 分鐘。

### 日誌管理
- **Clear**：清空當前日誌
- **Save Log**：將日誌儲存為 TXT 檔案
  - 格式：`batch_generator_log_YYYYMMDD_HHMMSS.txt`

## 📁 輸出位置

所有生成的 JSON 檔案會儲存在專案根目錄的 `json/` 資料夾中。

檔案命名格式：
```
{function_name}_{year}_{race}_{session}_{timestamp}.json
```

範例：
```
enhanced_rain_analysis_2025_Japan_R_20251214_153045.json
brake_performance_2025_Monaco_Q_20251214_160230.json
```

## 🐛 常見問題

### Q1: 為什麼有些任務顯示 [SKIP]？
A: 該任務對應的 JSON 檔案已存在，系統自動跳過以節省時間。如需重新生成，請手動刪除對應的 JSON 檔案。

### Q2: 為什麼有些任務顯示 [FAIL]？
A: 可能原因：
- Session 不存在（例如 Sprint 週末沒有 FP2/FP3）
- 數據下載失敗
- 網路連線問題
- FastF1 API 限制

### Q3: 可以同時執行多個任務嗎？
A: 目前版本建議 Parallel Jobs 設為 1，避免 FastF1 API 限制或資源衝突。

### Q4: Dry Run 模式有什麼用？
A: Dry Run 模式只會生成任務列表並顯示，不會實際執行 CLI 命令。適合用於：
- 檢查任務數量
- 預估執行時間
- 確認賽事和功能選擇正確

## 🔧 技術細節

### 系統需求
- Python 3.8+
- PyQt5
- FastF1
- 所有 F1T 專案依賴項

### 架構設計
- **主視窗**：`BatchGeneratorMainWindow`
- **CLI 執行器**：`CLIExecutorWorker` (QThread)
- **配置管理**：`FUNCTION_CATEGORIES`, `FUNCTION_INFO`

### CLI 命令格式
```bash
python f1_analysis_modular_main.py -f {function_id} -y {year} -r {race} -s {session}
```

## 📝 版本歷史

### v1.0.0 (2025-12-14)
- ✅ 初版發布
- ✅ 支援 25 種分析功能
- ✅ 自動載入 FastF1 賽程
- ✅ 無超時限制支援
- ✅ 即時日誌和進度追蹤

## 🤝 貢獻

如有問題或建議，請聯繫 F1T Team。

---

**F1 Telemetry Station Pro (F1T)** - Batch Data Generator GUI v1.0
