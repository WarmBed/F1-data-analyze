# 任務：Track Analysis 模組切換至 API 資料來源

- **目標**：將 Track Analysis GUI 模組的資料載入流程改為透過 FastAPI `/api/v2/analysis/execute`（function_id=2）取得最新賽道路徑資料，並僅在需求時才允許回退使用本地 JSON/CLI 產物。
- **負責人**：GitHub Copilot 自動化工作階段
- **建立日期**：2025-10-08

## 工作重點
1. 實作 API 優先的 `TrackAnalysisWorkerThread`，整合環境/配置取得 API 基底 URL 與逾時計時。
2. 於 GUI 模組建立後備策略開關；預設停用本地 JSON，必要時才允許 CLI 重新產出。
3. 重新整理 Track JSON 解析邏輯，統一輸出 `session_info`、`position_analysis`、`track_bounds` 等欄位以供地圖與資訊面板使用。
4. 擴充 `F1AnalysisCacheService`，讓缺乏 metadata 的舊 Track JSON 仍能被正確識別與標註參數。

## 待辦清單
- [x] 新增 API 優先的 Track Analysis worker，捕捉成功/錯誤狀態與回傳 metadata。
- [x] 將 GUI 模組更新為可設定本地後備策略，並支援重新載入時強制刷新。
- [x] 重構 JSON/回應解析流程，補齊 `track_bounds`、`session_info.track_name`、`position_analysis` 等欄位並相容 CLI JSON。
- [x] 更新快取服務 `cache_service.py`，支援以檔名推斷 Track JSON 的年/賽事/賽段並補寫 metadata。
- [ ] 實測 GUI 與 API 整合流程（啟動 FastAPI 後於 GUI 手動載入 Track Analysis）。
- [ ] 調整 Track 模組 UI，重新啟用資訊面板與圖表（若需要）。

## 測試計畫
- `python -m compileall modules/gui/track_analysis/track_analysis_module.py api/services/cache_service.py`
- `python -c "from api.services.simple_analysis_service import SimpleF1AnalysisService; import asyncio; async def main(): svc=SimpleF1AnalysisService(); res=await svc.execute_analysis(function_id=2, year=2025, race='Japan', session='R'); print(bool(res.get('success')), len(res.get('data',{}).get('data',{}).get('position_records',[]))) ; asyncio.run(main())"`（驗證 API 回傳結構可用）
- （待補）啟動 API 後執行 `python f1_analysis_modular_main.py -f 2 -y 2025 -r Japan -s R` 驗證 CLI 產出可被快取服務辨識。
- （待補）GUI 手動驗證：在 API 正常回應與故障時測試後備流程。

## 備註
- 本地後備策略透過 `F1T_ALLOW_TRACK_JSON_FALLBACK` 或 GUI 呼叫 `set_local_fallback_allowed()` 控制；預設停用。
- API 基底網址優先讀取 `F1_API_BASE_URL`，次選 `config/api_config.json` 的 `api_base_url`，最後以 `https://localhost:8000` 作為預設。
- 新增 metadata 標記 `metadata-inferred-from-track-filename` 以記錄快取服務的參數推斷來源。
- 2025-10-02：`TrackAnalysisDataManager` 已改為 API 優先流程，新增 `TrackAnalysisApiWorker` 與回退策略設定，待後續實測與 UI 校正。
