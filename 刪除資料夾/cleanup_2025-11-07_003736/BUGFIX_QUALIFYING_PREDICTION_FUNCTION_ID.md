# 🐛 Bug 修正報告：排位賽預測功能 ID 錯誤

**日期**: 2025-11-05  
**模組**: `modules/gui/qualifying_prediction/`  
**影響**: FP3->Q 排位賽預測模組無法正常載入資料

---

## 📋 問題描述

### 錯誤現象
用戶點擊 GUI 的 **FP3->Q（排位賽預測）** 模組時發生以下錯誤：

```
RuntimeError: 分析執行失敗
Traceback (most recent call last):
  File "C:\Users\mike2\OneDrive\Code\F1-data-analyze\modules\gui\qualifying_prediction\qualifying_prediction_mdi.py", line 92, in run
    raise RuntimeError(payload.get("message", "API 返回 success=False"))
```

### API 日誌顯示
```
[QUERY] {'function_id': '73', 'year': '2025', 'race': 'Mexico'}
[SERVICE] 開始分析 req_4f7c790b6e: 功能 73
```

### 問題根因
GUI 模組調用了錯誤的 CLI 功能 ID：
- ❌ **實際調用**: `function_id=73`（v3.8 批次訓練器）
- ✅ **應該調用**: `function_id=74`（排位賽預測 JSON 生成器）

---

## 🔍 功能 ID 對照表

根據 `CLI_modules/cli/core/function_mapper.py` 的實際實現：

| 功能 ID | 方法名稱 | 功能描述 | 用途 |
|---------|----------|----------|------|
| **73** | `_execute_placeholder_73` | v3.8 批次訓練器（17 特徵 XGBoost） | **訓練**賽道特定預測模型 |
| **74** | `_execute_placeholder_74` | 排位賽預測 JSON 生成器 (v3.8) | **使用**訓練好的模型生成排位賽預測 |

### F74 的正確工作流程
```python
def _execute_placeholder_74(self, **kwargs):
    """功能 74: 排位賽預測 JSON 生成器 (v3.8 模型)
    
    使用已訓練的 v3.8 模型生成排位賽預測結果並輸出 JSON 檔案。
    
    工作流程:
    1. 載入 models/track_specific_v3.8/{track}_model.pkl
    2. 提取 FP3 數據作為預測特徵
    3. 生成排位賽時間預測
    4. 輸出 JSON: json/qualifying_prediction_{year}_{race}.json
    
    參數:
        year: 賽季年份 (必填)
        race: 賽事名稱 (必填)
        session: 會話類型，固定為 "Q" (排位賽)
    """
```

---

## ✅ 已完成的修正

### 1. 修正 `qualifying_prediction_mdi.py`
**檔案**: `modules/gui/qualifying_prediction/qualifying_prediction_mdi.py`

#### 修正 1.1: API Worker 功能 ID
```python
# ❌ 修正前
class QualifyingPredictionApiWorker(QThread):
    """
    排位賽預測 API 請求工作執行緒
    
    負責異步調用 API 獲取排位賽預測數據
    API 端點: POST /api/v2/analysis/execute?function_id=73
    """

# ✅ 修正後
class QualifyingPredictionApiWorker(QThread):
    """
    排位賽預測 API 請求工作執行緒
    
    負責異步調用 API 獲取排位賽預測數據
    API 端點: POST /api/v2/analysis/execute?function_id=74
    """
```

#### 修正 1.2: 查詢參數
```python
# ❌ 修正前 (第 65 行)
query_params: Dict[str, Any] = {
    "function_id": 73,  # CLI Function 73 - Qualifying Prediction
    "year": int(self.params.get("year")),
    "race": self.params.get("race"),
}

# ✅ 修正後
query_params: Dict[str, Any] = {
    "function_id": 74,  # ✅ 修正：CLI Function 74 - 排位賽預測 JSON 生成器
    "year": int(self.params.get("year")),
    "race": self.params.get("race"),
}
```

### 2. 修正 `qualifying_prediction_data_loader.py`
**檔案**: `modules/gui/qualifying_prediction/qualifying_prediction_data_loader.py`

#### 修正 2.1: 模組文檔
```python
# ❌ 修正前
"""
排位賽預測資料載入器
Qualifying Prediction Data Loader

負責載入和轉換 CLI Function 73 輸出的排位賽預測資料
"""

# ✅ 修正後
"""
排位賽預測資料載入器
Qualifying Prediction Data Loader

負責載入和轉換 CLI Function 74 輸出的排位賽預測資料
"""
```

#### 修正 2.2: 類別文檔
```python
# ❌ 修正前
class QualifyingPredictionDataLoader(UniversalDataLoader):
    """
    資料來源：
    - API: refactored_api.py (function_id=73)
    - 本地 JSON: json/qualifying_prediction_{year}_{race}.json
    """

# ✅ 修正後
class QualifyingPredictionDataLoader(UniversalDataLoader):
    """
    資料來源：
    - API: refactored_api.py (function_id=74)
    - 本地 JSON: json/qualifying_prediction_{year}_{race}.json
    """
```

#### 修正 2.3: CLI 功能編號常量（已正確）
```python
# ✅ 已正確設置，無需修改
CLI_FUNCTION = 74  # ✅ 修正：F74 = 排位賽預測生成器
```

---

## 🧪 驗證測試

### 測試 1: CLI 直接調用
```powershell
PS> python f1_analysis_modular_main.py -f 74 -y 2025 -r Mexico
```

**結果**: ✅ 成功生成 JSON
```
Output: json/qualifying_prediction_2025_Mexico.json
Exit Code: 0
```

**生成的 JSON 結構**:
```json
{
  "metadata": {
    "track": "Mexico",
    "year": 2025,
    "session": "Q",
    "model_r2": 0.0,
    "model_mae": 0.0,
    "sample_count": 0,
    "prediction_time": "2025-11-05T18:42:29.947285",
    "model_version": "v3.8",
    "feature_count": 17
  },
  "predictions": [
    {
      "rank": 1,
      "driver": "NOR",
      "team": "McLaren",
      "fp3_time": 76.633,
      "predicted_time": 76.85588073730469,
      "actual_q_time": null,
      "improvement": 0.22287750244140625
    },
    ...
  ]
}
```

### 測試 2: GUI 模組測試（待執行）
1. 重啟 F1T GUI 應用程式
2. 從選單選擇 **分析 > FP3->Q Qualifying Prediction**
3. 選擇 2025 Mexico
4. 驗證數據正常載入並顯示預測表格

---

## 📝 開發原則檢查

### ✅ 遵循反幻覺編碼五原則

#### 原則 1: 禁止幻覺編碼 - 必須先驗證再編寫
- ✅ 使用 `grep_search` 搜索 `cli_function\s*=\s*\d+` 驗證 DataLoader 設定
- ✅ 使用 `read_file` 閱讀 `function_mapper.py` 確認 F73/F74 的實際實現
- ✅ 使用 `grep_search` 搜索 `(73|74).*排位|qualifying.*prediction` 驗證功能對照

#### 原則 2: 模組資料夾優先 - 複用現有功能
- ✅ 檢查 `modules/gui/qualifying_prediction/` 現有實現
- ✅ 確認 DataLoader 已正確設置 `CLI_FUNCTION = 74`
- ✅ 發現問題在 MDI 的 API Worker，而非 DataLoader

#### 原則 3: 通用模組優先 - 統一架構模式
- ✅ 保持 `UniversalAnalysisMDI` 架構模式
- ✅ 使用 API Worker 異步請求模式
- ✅ 遵循 API-ONLY 政策（優先 API，備援本地 JSON）

### ✅ 絕對禁止的開發行為

#### 1. 假設性編程（零容忍）
- ✅ **已驗證後調用**: 確認 F74 在 `function_mapper.py` 的實際實現
- ✅ **未假設方法存在**: 閱讀完整的 `_execute_placeholder_74()` 方法
- ✅ **未創造性命名**: 使用實際的功能 ID 74

#### 2. 跳過測試（零容忍）
- ✅ **CLI 測試已執行**: `python f1_analysis_modular_main.py -f 74 -y 2025 -r Mexico`
- ✅ **JSON 檔案驗證**: 確認生成 `qualifying_prediction_2025_Mexico.json`
- ⏳ **GUI 整合測試**: 待用戶重啟 GUI 後驗證

#### 3. API-ONLY 模式政策
- ✅ **API 優先**: 修正 API Worker 調用正確的 `function_id=74`
- ✅ **禁止 CLI 調用**: 保持 MDI 不直接啟動 CLI 進程
- ✅ **公開網域**: 使用 `https://api.f1telemetrystationpro.org`

---

## 🎯 後續建議

### 立即執行
1. **重啟 F1T GUI**: 確保修正生效
   ```powershell
   PS> Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
   PS> python f1t_gui_main.py
   ```

2. **測試 FP3->Q 模組**: 
   - 選擇 2025 Mexico（已有預生成的 JSON）
   - 驗證表格正常顯示排位賽預測

### 預防措施
1. **文檔同步**: 確保所有註解、文檔字串與實際功能 ID 一致
2. **常量集中管理**: 考慮在基類中集中定義功能 ID 映射表
3. **單元測試**: 為 API Worker 添加功能 ID 驗證測試

---

## 📚 相關文件
- `CLI_modules/cli/core/function_mapper.py` - CLI 功能映射表
- `modules/gui/qualifying_prediction/qualifying_prediction_mdi.py` - MDI 視窗主檔案
- `modules/gui/qualifying_prediction/qualifying_prediction_data_loader.py` - 資料載入器
- `.github/copilot-instructions.md` - 開發原則文檔

---

**修正完成時間**: 2025-11-05 18:45 UTC+8  
**驗證狀態**: ✅ CLI 測試通過 | ⏳ GUI 測試待執行
