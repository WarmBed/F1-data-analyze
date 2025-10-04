# 開發任務：Function 48 - 全車手最高速度分析

## 背景
- 目標是在 CLI 層新增 `function_id=48`，取得指定賽事/會話的所有車手最高速度資訊。
- 功能須模組化並可由 FastAPI 服務 (`/api/v2/analysis/execute`) 調用，與既有遙測分析架構一致。
- 需參考 Function 13 (雙車手比較) 現有流程：資料抓取、JSON 輸出、API 響應格式與 GUI 相容性。

## 範圍與需求
1. **CLI 實作**
   - 在 `CLI_modules/cli/core/function_mapper.py` 補齊 `_execute_all_drivers_straight_line_speed`。
   - 實作新分析服務/工具類別（若現有模組可復用則共用）以計算每位車手的最高速度與相關統計。
   - 產出結構化 JSON，至少包含：車手代碼、最高速度（km/h）、發生圈數、發生點距離/時間等資訊。
   - 儲存輸出到 `json/` 目錄以利 GUI 後備讀取。

2. **API 整合**
   - 確認 `refactored_api.py` / `api` 模組的功能映射涵蓋 function 48。
   - 新增 Pydantic schema（若需要），確保 `/api/v2/analysis/execute` 能返回新資料結構。

3. **GUI 影響檢查**
   - 確認現有 GUI 模組是否需新建 MDI 或重用既有速度分析面板。
   - 若需 GUI 支援，制定下一步 (本任務先聚焦 CLI + API)。

4. **測試與驗證**
   - 編寫單元測試 / 整合測試以驗證 CLI 方法輸出。
   - 使用測試資料或緩存快取執行，確保 API 回傳格式與 CLI 一致。
   - 更新 `pytest` 相關測試檔案並確保 `python -m pytest tests/ -v --tb=short` 通過。

## 里程碑
- M1：完成資料蒐集與演算法設計。
- M2：完成 CLI 模組及 JSON 輸出。
- M3：完成 API 整合與序列化。
- M4：完成測試與文件更新。

## 成功標準
- 透過 CLI 指令：
  ```powershell
  python f1_analysis_modular_main.py -f 48 -y <YEAR> -r <RACE> -s <SESSION>
  ```
  能取得成功訊息並於 `json/` 生成對應檔案。
- 透過 API：
  ```powershell
  Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/v2/analysis/execute" -Body @{ function_id = 48; year = <YEAR>; race = '<RACE>'; session = '<SESSION>' }
  ```
  回傳 JSON 中帶有 `data.driver_speeds` 或等同結構。
- 新增或更新的測試全部綠燈。

## 風險與注意事項
- FastF1/OpenF1 取得速度資料時可能受限於緩存或 API 可用性，需確保有後備策略。
- API-ONLY 政策下，GUI 不可直接觸發 CLI；必須確保 API 路徑穩定。
- JSON 結構需兼容現有前端需求，避免破壞既有分析模組。

## 檢核清單
- [ ] function 48 CLI 實作完成並通過手動測試。
- [ ] API 端點可回傳正確資料。
- [ ] JSON 檔案命名遵循 `comparison_telemetry_*` 或新格式並記錄於文件。
- [ ] 測試覆蓋新增功能。
- [ ] 任務完成後更新此文件狀態並記錄測試結果。
