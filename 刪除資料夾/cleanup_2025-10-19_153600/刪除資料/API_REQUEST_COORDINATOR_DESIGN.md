# API Request Coordinator 重構提案

## 背景
目前多數 GUI DataManager 在啟動分析流程前會於主執行緒執行同步的 API 健康檢查 (`requests.get`). 在網路延遲或 API 暫時無回應時，GUI 會出現「未回應」狀態。此外，每個模組都個別維護 API 請求、fallback 與監控邏輯，導致重複碼多且擴充困難。

## 問題摘要
- **UI 阻塞**：同步健康檢查與其他阻塞操作在主執行緒執行，造成 GUI 卡頓。
- **流程分散**：API 呼叫、健康檢查、fallback 及進度回報分散在不同 DataManager 中，各自實作相似邏輯。
- **測試負擔**：每個模組的 API 流程需獨立撰寫測試與 mock，管理成本高。
- **API-ONLY 政策**：面對後續 API 改版或節流策略時，缺乏統一控管點。

## 重構目標
1. **非阻塞健康檢查**：所有健康檢查均於背景執行緒進行，避免阻塞主執行緒。
2. **統一 API 請求協調器**：建立 `ApiRequestCoordinator`，集中處理 API 呼叫、健康檢查、fallback 與狀態信號。
3. **簡化 DataManager 責任**：各 DataManager 專注於參數驗證與資料後處理，API 交互流程由協調器處理。
4. **提升測試一致性**：提供共用 mock 與測試介面，降低各模組重複測試成本。
5. **保留現有 fallback 策略**：仍支援本地 JSON fallback 與 force refresh 等控制項。

## 擬議架構
```
GUI 模組
  └─ DataManager (遙測/雨/賽道/...)
       └─ ApiRequestCoordinator
            ├─ ApiHealthCheckWorker
            ├─ ApiAnalysisWorker (既有 QThread，整合健康檢查)
            └─ FallbackHandler (JSON / 使用者提示)
```

### ApiRequestCoordinator 核心職責
- 接收 DataManager 的請求參數與 callback。
- 控制健康檢查與分析 worker 的生命週期與 timeout。
- 統一進度、成功、失敗三種 signal 策略。
- 在 API 失敗時觸發回退策略，並提供細節原因。

### 健康檢查策略
- **步驟合併**：在 `ApiAnalysisWorker.run()` 中先呼叫健康檢查端點，成功後才進入主要分析 API。全程在背景執行緒運行。
- **超時設定**：健康檢查使用可調整 timeout（預設 2 秒），並與分析請求分離，防止單一延遲拖垮整體流程。

### DataManager 新責任邊界
- 驗證載入參數。
- 呼叫 `coordinator.start_request()`。
- 接收 coordinator signal 後進行資料轉換、快取與 GUI 更新。
- 在 `failure` signal 時啟動既有的本地 JSON fallback。

## 實施階段
1. **Phase 1：背景健康檢查**
   - 移除主執行緒的 `_is_api_available()` 呼叫。
   - 新增共用 `ApiHealthCheckWorker` 並導入核心模組（Telemetry、Rain、Track）。
   - 更新相關測試驗證新流程。

2. **Phase 2：協調器試點**
   - 實作 `ApiRequestCoordinator` 雛形。
   - 在遙測分析模組導入協調器，調整 DataManager 與測試。
   - 撰寫使用指南與整合測試。

3. **Phase 3：全面導入**
   - 逐步將其他模組 (Rain, Track, Pitstop, Tire, Lap Analysis 等) 切換至協調器架構。
   - 清理重複 API worker 與健康檢查邏輯。
   - 更新開發文件與 fallback 策略。

## 風險與緩解
| 風險 | 影響 | 緩解策略 |
| --- | --- | --- |
| 導入階段功能行為變動 | GUI 可能出現新錯誤訊息或 fallback 失敗 | 先在單一模組試行，並撰寫迴歸測試 |
| 協調器泛用性不足 | 新模組需求可能超出協調器設計 | 提前盤點模組差異，預留擴充欄位與 hook |
| 測試更新成本 | 單元測試需改寫 | 提供協調器專用 mock/fixture，撰寫最佳實務 |

## 待辦事項
- [ ] 設計 `ApiHealthCheckWorker` 與共用 signal 格式。
- [ ] 調整 Telemetry 模組 API 流程與測試。
- [ ] 撰寫協調器介面與使用手冊。
- [ ] 完成其他模組的逐步遷移。

## 參考
- 現有 DataManager：`telemetry_analysis_mdi.py`, `rain_analysis_mdi.py`, `track_analysis_mdi.py`, `pitstop_analysis_mdi.py`, `tire_analysis_mdi.py`, `lap_analysis/telemetry_data_loader_base.py` 等。
- API 端點：`/api/v2/analysis/execute`, `/api/v2/system/health`, `/health`（舊版）。
- 政策文件：`docs/CLI_REMOVAL_COMPLETE_REPORT.md`, `.github/copilot-instructions.md`（API-ONLY 模式）。
