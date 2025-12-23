# Batch CLI Executor 使用指南

## 📋 功能說明

`batch_cli_executor.py` 是一個通用的批量 CLI 執行器，可以批量執行任意 F1 分析功能。

### ✨ 主要特性

- ✅ 支援任意功能 ID 組合
- ✅ 支援年份範圍和列表
- ✅ 支援多種會話類型（R/Q/FP1/FP2/FP3）
- ✅ 自動跳過已存在的檔案
- ✅ 進度追蹤（支援 tqdm）
- ✅ 錯誤處理和統計報告
- ✅ 詳細輸出模式

---

## 🚀 使用範例

### 範例 1：批量收集賽道特徵數據（功能 48, 54, 34, 47, 1）

```powershell
# 收集 2018-2024 年所有 FP3 會話的賽道特徵
python batch_cli_executor.py --functions 48,54,34,47,1 --years 2018-2024 --sessions FP3
```

**說明**：
- F48：全車手直線速度
- F54：車手油門比例
- F34：煞車性能分析
- F47：全車手彎道分析
- F1：降雨強度分析

---

### 範例 2：批量收集 FP→Q 預測數據（功能 70）

```powershell
# 收集 2018-2024 年所有賽事的 FP→Q 數據
python batch_cli_executor.py --functions 70 --years 2018-2024

# 只收集 2023-2024 年的數據
python batch_cli_executor.py --functions 70 --years 2023,2024
```

**說明**：
- F70：FP→Q 數據收集器（用於 XGBoost 訓練）

---

### 範例 3：批量訓練 XGBoost 模型（功能 72）

```powershell
# 使用 2018-2023 年數據訓練基準模型
python batch_cli_executor.py --functions 72 --years 2018-2023
```

**說明**：
- F72：XGBoost 訓練器

---

### 範例 4：多功能批量執行（所有會話）

```powershell
# 收集 2024 年所有賽事的完整數據（R/Q/FP3）
python batch_cli_executor.py --functions 1,34,47,48,54 --years 2024 --sessions R,Q,FP3 --verbose
```

**參數說明**：
- `--functions 1,34,47,48,54`：執行 5 個功能
- `--years 2024`：只處理 2024 年
- `--sessions R,Q,FP3`：處理正賽、排位賽和 FP3
- `--verbose`：顯示詳細輸出

---

### 範例 5：強制重新執行（不跳過已存在檔案）

```powershell
# 重新收集所有數據（即使檔案已存在）
python batch_cli_executor.py --functions 48 --years 2024 --sessions R --no-skip --verbose
```

---

## 📖 命令列參數詳解

### 必要參數

| 參數 | 簡寫 | 說明 | 範例 |
|------|------|------|------|
| `--functions` | `-f` | 功能 ID 列表（逗號分隔） | `48,54,34,47,1` |
| `--years` | `-y` | 年份範圍或列表 | `2018-2024` 或 `2023,2024` |

### 可選參數

| 參數 | 簡寫 | 預設值 | 說明 |
|------|------|--------|------|
| `--sessions` | `-s` | `R,Q,FP3` | 會話類型列表 |
| `--no-skip` | - | False | 不跳過已存在檔案 |
| `--verbose` | `-v` | False | 顯示詳細輸出 |

---

## 🎯 常用功能 ID 速查表

| 功能 ID | 名稱 | 輸出檔案模式 | 用途 |
|---------|------|--------------|------|
| **F1** | 降雨強度分析 | `enhanced_rain_analysis_*.json` | 天氣數據 |
| **F34** | 煞車性能分析 | `brake_performance_*.json` | 煞車數據 |
| **F47** | 全車手彎道分析 | `all_drivers_cornering_analysis_*.json` | 彎道性能 |
| **F48** | 全車手直線速度 | `all_drivers_straight_line_speed_*.json` | 直線速度 |
| **F54** | 車手油門比例 | `throttle_ratio_*.json` | 油門數據 |
| **F70** | FP→Q 數據收集 | `fp_q_data_*.json` | 預測訓練數據 |
| **F72** | XGBoost 訓練 | `xgboost_fp_q_baseline_*.pkl` | 機器學習模型 |

---

## 📊 執行流程

```
1. 解析命令列參數
   ↓
2. 建立任務列表（功能 × 年份 × 賽事 × 會話）
   ↓
3. 檢查已存在的檔案（如果啟用 --skip）
   ↓
4. 依序執行每個 CLI 任務
   ↓
5. 統計成功/失敗/跳過數量
   ↓
6. 輸出執行報告
```

---

## 🔍 輸出範例

### 正常模式（簡潔）

```
================================================================================
  F1 分析 CLI 批量執行器
================================================================================

執行計畫：
  - 功能列表：F48, F54, F34, F47, F1
  - 年份範圍：2018-2024
  - 會話類型：FP3
  - 總任務數：745
  - 跳過已存在：是

總進度 |########################################| 745/745 [100.0%] ETA: 0s

================================================================================
  執行完成
================================================================================

統計資訊：
  - [OK]   成功：623 個任務
  - [FAIL] 失敗：12 個任務
  - [SKIP] 跳過：110 個任務（已存在）
  - [TOTAL] 總計：745 個任務

執行時間：3847.2 秒 (64.1 分鐘)
```

### 詳細模式（--verbose）

```
[F48] 2024 Japan                FP3
  [OK] 成功 (all_drivers_straight_line_speed_2024_Japan_FP3.json)

[F54] 2024 Japan                FP3
  [SKIP] 已存在：throttle_ratio_2024_japan_FP3.json

[F34] 2024 Japan                FP3
  [FAIL] 執行失敗 (返回碼: 1)
```

---

## ⚠️ 注意事項

1. **執行時間**：批量執行可能需要數小時，建議在背景執行
2. **FastF1 緩存**：首次執行會下載數據，後續執行會更快
3. **錯誤處理**：失敗的任務會顯示錯誤訊息，但不會中斷整體執行
4. **檔案檢查**：預設會跳過已存在的檔案，使用 `--no-skip` 強制重新執行
5. **超時保護**：每個任務有 10 分鐘超時限制

---

## 🛠️ 進階使用

### 使用 PowerShell 背景執行

```powershell
# 背景執行並記錄日誌
Start-Process python -ArgumentList "batch_cli_executor.py", "--functions", "48,54,34,47,1", "--years", "2018-2024", "--sessions", "FP3" -RedirectStandardOutput "batch_log.txt" -NoNewWindow

# 監控進度
Get-Content batch_log.txt -Wait -Tail 20
```

### 組合多個批次

```powershell
# 先收集 FP→Q 數據
python batch_cli_executor.py --functions 70 --years 2018-2024

# 再訓練 XGBoost 模型
python batch_cli_executor.py --functions 72 --years 2018-2023

# 最後收集賽道特徵
python batch_cli_executor.py --functions 48,54,34,47,1 --years 2018-2024 --sessions FP3
```

---

## 📝 開發原則遵循

本腳本遵循 **反幻覺編碼五原則**：

1. ✅ **禁止幻覺編碼**：所有功能 ID 和檔名模式均經過驗證
2. ✅ **模組資料夾優先**：參考 `batch_f47_2025_to_mexico.py` 的實現
3. ✅ **通用模組優先**：使用統一的錯誤處理和進度追蹤架構
4. ✅ **多國語言化**：所有輸出字串可本地化（當前為繁體中文）
5. ✅ **日誌輸出**：所有 print 輸出會被導出到日誌

---

## 🐛 常見問題

### Q1：為什麼有些任務失敗？

**A**：可能原因：
- FastF1 數據不完整（某些賽季的某些會話）
- 網路連線問題
- 賽事名稱不匹配（如 "Australian" vs "Australia"）

### Q2：如何只重新執行失敗的任務？

**A**：使用 `--no-skip` 參數，並縮小年份/會話範圍：
```powershell
python batch_cli_executor.py --functions 48 --years 2024 --sessions R --no-skip
```

### Q3：可以同時執行多個批次嗎？

**A**：不建議。CLI 使用共享的 FastF1 緩存，同時執行可能導致衝突。

---

## 📚 相關文件

- `batch_generate_track_features.py`：賽道特徵專用批量腳本（已被此腳本取代）
- `scripts/batch_f47_2025_to_mexico.py`：F47 專用批量腳本（參考實現）
- `CLI_modules/cli/core/function_mapper.py`：所有可用功能 ID

---

**作者**：F1T Analysis Team  
**版本**：1.0.0  
**日期**：2025-10-31
