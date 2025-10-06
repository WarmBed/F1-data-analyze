# Telemetry Analysis API 化任務追蹤

**日期**: 2025-10-01  
**模組**: Telemetry Analysis (Driver Ranking)  
**CLI 功能**: Function 12 - All Drivers Telemetry  
**狀態**: 🚀 準備開始

---

## 📋 任務目標

將 Telemetry Analysis 模組從本地 JSON/CLI 模式升級為 **API 優先** 模式，同時保留本地後備機制。

---

## ✅ 已完成的準備工作

### 1. 模組基礎架構
- [x] `TelemetryAnalysisApiWorker` 已實現
- [x] `TelemetryDataManager` 已實現 API 優先邏輯
- [x] QPainter 資源管理問題已修正
- [x] 獨立測試腳本驗證通過

### 2. API 端點
- [x] `/api/v2/analysis/execute` 端點存在
- [x] Function 12 已在 `FUNCTION_SPECS` 中定義
  - **名稱**: All Drivers Telemetry
  - **必要參數**: year, race, session
  - **可選參數**: driver1
  - **緩存模式**: `all_drivers_telemetry`, `telemetry_analysis`

### 3. 數據格式
- [x] API 回應格式已標準化
  ```json
  {
    "success": true,
    "message": "分析完成",
    "data": {
      "all_drivers_telemetry": {
        "VER": {...},
        "HAM": {...}
      }
    },
    "source": "api",
    "execution_time": "2.5s"
  }
  ```

---

## 🔄 測試流程

### 階段 1: API 端點測試
**目的**: 確認 API 能正常返回 Function 12 數據

**測試腳本**: `tests/api/test_telemetry_api.py`

**測試步驟**:
1. 啟動 API 伺服器
   ```powershell
   python refactored_api.py
   ```

2. 執行 API 測試
   ```powershell
   python tests\api\test_telemetry_api.py
   ```

**預期結果**:
- [x] HTTP 200 狀態碼
- [x] `success: true`
- [x] 包含 `all_drivers_telemetry` 數據
- [x] 車手數量 >= 10
- [x] 每位車手包含 `driver_info`, `lap_time_analysis`, `sector_analysis`

---

### 階段 2: GUI 整合測試
**目的**: 確認 GUI 能正確使用 API 數據

**測試腳本**: `tests/api/test_telemetry_api.py` (GUI 整合部分)

**測試步驟**:
1. 確保 API 伺服器運行中
2. 執行整合測試
   ```powershell
   python tests\api\test_telemetry_api.py
   ```

**預期結果**:
- [x] `TelemetryDataManager` 成功載入數據
- [x] `telemetry_loaded` 信號被觸發
- [x] 數據格式符合 GUI 期望
- [x] 車手概覽表格正常填充

---

### 階段 3: 主 GUI 測試
**目的**: 在實際使用環境中測試完整流程

**測試步驟**:
1. 啟動 API 伺服器
2. 啟動主 GUI
   ```powershell
   python f1t_gui_main.py
   ```
3. 從功能樹點擊 "Driver Ranking"
4. 確認數據正常載入並顯示

**測試檢查項目**:
- [ ] 視窗正常開啟
- [ ] 顯示 "正在透過 API 載入遙測分析資料..."
- [ ] 進度條更新
- [ ] 數據成功載入（所有車手顯示在表格中）
- [ ] 統計卡片正確更新（最快車手、平均圈速）
- [ ] 表格排序功能正常
- [ ] 無 QPainter 或其他錯誤
- [ ] 多次開關視窗穩定

---

### 階段 4: 錯誤處理測試
**目的**: 確認各種錯誤情況都能正確處理

**測試場景**:

1. **API 伺服器未啟動**
   - [ ] 顯示錯誤訊息
   - [ ] 根據 `_allow_local_fallback` 設定決定是否回退到本地 JSON/CLI
   
2. **API 超時**
   - [ ] 75 秒後觸發超時
   - [ ] 顯示超時錯誤
   - [ ] 可選：回退到本地模式

3. **API 返回錯誤**
   - [ ] 處理 `success: false` 回應
   - [ ] 顯示 API 錯誤訊息
   
4. **數據格式錯誤**
   - [ ] 驗證失敗時顯示錯誤
   - [ ] 不會崩潰

---

## 🔧 當前配置

### API 配置
```python
# TelemetryDataManager.__init__
self._api_base_url = self._determine_api_base_url()  # "https://api.f1telemetrystationpro.org"
self._api_timeout = 75.0
```

### 本地後備策略
```python
# 預設：停用本地後備
self._allow_local_fallback, self._fallback_policy_reason = 
    self._resolve_local_fallback_policy()
# → (False, "預設策略 (API 優先，不允許本地回退)")
```

**啟用本地後備**:
```python
# 方法 1: 環境變數
os.environ["F1T_ALLOW_TELEMETRY_JSON_FALLBACK"] = "1"

# 方法 2: 程式碼
data_manager.set_local_fallback_allowed(True, reason="開發測試")
```

---

## 📝 待辦事項

### 高優先級
- [ ] **執行階段 1 測試** - API 端點測試
- [ ] **執行階段 2 測試** - GUI 整合測試
- [ ] **執行階段 3 測試** - 主 GUI 測試
- [ ] **執行階段 4 測試** - 錯誤處理測試

### 中優先級
- [ ] 添加 API 請求日誌
- [ ] 實現 API 請求重試機制（例如：網路暫時中斷）
- [ ] 優化 API 超時設定（根據實際性能調整）
- [ ] 添加 API 回應緩存（避免重複請求）

### 低優先級
- [ ] 實現 API 負載平衡（如果有多個 API 伺服器）
- [ ] 添加 API 性能監控
- [ ] 實現 API 版本協商

---

## 🐛 已知問題

### 1. 本地後備策略
**問題**: 預設停用本地 JSON 後備，API 失敗時無法回退

**影響**: 如果 API 伺服器未啟動或失敗，用戶無法使用功能

**解決方案**:
- 開發環境：啟用本地後備
- 生產環境：確保 API 高可用性

### 2. 環境變數讀取
**問題**: `F1T_ALLOW_TELEMETRY_JSON_FALLBACK` 環境變數需要在啟動前設定

**解決方案**: 
- 在主 GUI 啟動時統一設定
- 或在配置檔案中管理

---

## 📊 測試結果記錄

### 測試執行記錄
| 日期 | 測試階段 | 結果 | 備註 |
|------|---------|------|------|
| 2025-10-01 | 準備 | ✅ | 測試腳本已創建 |
| | 階段 1 | ⏳ | 待執行 |
| | 階段 2 | ⏳ | 待執行 |
| | 階段 3 | ⏳ | 待執行 |
| | 階段 4 | ⏳ | 待執行 |

---

## 🎯 成功標準

完成以下所有項目即視為 API 化成功：

1. ✅ API 端點正常運作
2. ✅ GUI 能透過 API 載入數據
3. ✅ 數據格式正確，所有欄位完整
4. ✅ 在主 GUI 中正常使用
5. ✅ 錯誤處理完善
6. ✅ 性能可接受（載入時間 < 10 秒）
7. ✅ 無崩潰或資源洩漏

---

## 📖 參考資料

### 相關檔案
- 模組實現: `modules/gui/telemetry_analysis_mdi.py`
- API 路由: `api/routers/analysis.py`
- 功能規格: `api/models/function_specs.py`
- 測試腳本: `tests/api/test_telemetry_api.py`

### 相關文檔
- API 化總結: `QPAINTER_FIX_SUMMARY.md`
- 架構說明: `MODULE_ARCHITECTURE_CLARIFICATION.md`
- QPainter 修正: `DETAILED_LAP_CRASH_FIX_REPORT.md`

---

**任務負責人**: AI Assistant  
**預計完成時間**: 2025-10-01  
**當前狀態**: 🚀 準備就緒，等待執行測試
