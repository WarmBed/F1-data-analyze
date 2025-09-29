# 任務：API 伺服器啟動與整合測試

- **目標**：驗證 FastAPI 伺服器啟動流程並確保公開的分析端點運作正常。
- **負責人**：Codex 自動化工作階段
- **建立日期**：2025-09-29

## 工作範圍
1. 透過 `refactored_api.py` 啟動 FastAPI 伺服器。
2. 針對 API 關鍵分析功能執行整合測試（功能 1、2、13、26、28），確認回應結構與資料完整性。
3. 全量掃描 `json/` 目錄內的輸出，確認僅保留 2025 Japan R 相關檔案。
4. 比對 API 回傳內容與對應 JSON 檔案，確保資料完全一致（字典順序差異可忽略，但結構與欄位值需相符）。
5. 建立 JSON ↔ CLI 功能對照表，確認每個 JSON 可透過對應功能 ID 於 CLI 生成，並驗證 API 呼叫使用相同功能。

## 待辦清單
- [x] 以 VS Code 任務或命令列啟動 `refactored_api.py`（必要時改用替代連接埠）。
- [x] 確認根路徑 `/` 及文件 `/docs`、`/redoc` 可存取並記錄狀態碼。
- [x] 執行 `tests/test_api_endpoints_integration.py` 確認所有案例通過。
- [x] 掃描 `json/` 目錄，將非 Japan 2025 R 的檔案移至備援資料夾並產生清單紀錄。
- [x] 撰寫腳本或筆記，比對 API JSON 輸出與本地 JSON 檔案內容，標記差異（若存在）。
- [x] 整理 JSON 檔名與 CLI `-f` 功能 ID 對應表，並確認 API 測試使用相同功能 ID。
- [x] 紀錄測試輸出、比對結果與任何異常。

## 執行紀錄
- 2025-09-29 取得 PowerShell 啟動紀錄：`uvicorn refactored_api:app --host 127.0.0.1 --port 8005` 成功啟動，替代連接埠 8005 運作正常。
- 2025-09-29 以 `requests` 腳本驗證 `/`、`/docs`、`/redoc` 頁面皆回傳 HTTP 200。
- 2025-09-29 執行 `python -m pytest tests/test_api_endpoints_integration.py -v --tb=short`，5 項案例全數通過（記錄 Pydantic 及 FastAPI 既有棄用警告待後續重構）。
- 2025-09-29 以 Python 腳本列出 `json/` 目錄現況，共 11 份檔案，皆為 2025 Japan R 相關分析輸出。
- 2025-09-29 建立 API ↔ JSON 比對腳本，針對功能 1、2、13、26、28 成功驗證 API 回傳資料與對應 JSON 完全一致（處理 `NaN`→`null` 差異後比對為真）。
- 2025-09-29 更新 API 服務支援功能 3、4、5、8、12 並重新執行 CLI 映射；測試覆蓋擴充至 10 項案例，全數命中快取且資料與 JSON 同步。

## API 與 JSON 對照摘要
- ✅ 功能 1、2、3、4、5、8、12、13、26、28：API `data` 內容移除 `file_info`／`cache_info` 後與本地 JSON 完全一致。
- ✅ API 回應均含 `file_info.file_name` 指向 `json/` 目錄內相符檔案，便於後續追蹤。

## JSON ↔ CLI 功能對照表
| JSON 檔名 | CLI 功能 ID (`-f`) | 主要參數 | API 支援狀態 |
| --- | --- | --- | --- |
| `rain_intensity_analysis_2025_Japan_R.json` | 1 | `-y 2025 -r Japan -s R` | ✅ 已驗證 |
| `enhanced_rain_analysis_2025_Japan_R.json` | 1（增強輸出） | `-y 2025 -r Japan -s R --show-detailed` | ⚠️ 僅 CLI 快取 |
| `track_position_analysis_2025_Japan_R.json` | 2 | `-y 2025 -r Japan -s R` | ✅ 已驗證 |
| `comparison_telemetry_VER_LEC_2025_Japan_R_Lap99_Lap99.json` | 13 | `-y 2025 -r Japan -s R -d VER -d2 LEC` | ✅ 已驗證 |
| `tire_strategy_2025_Japan_R.json` | 26 | `-y 2025 -r Japan -s R -d VER`（可省略 driver） | ✅ 已驗證 |
| `detailed_laptime_analysis_2025_Japan_R_all_drivers.json` | 28 | `-y 2025 -r Japan -s R` | ✅ 已驗證 |
| `all_drivers_telemetry_analysis_2025_Japan_R.json` | 12 | `-y 2025 -r Japan -s R` | ✅ 已驗證 |
| `driver_fastest_pitstop_ranking_2025_Japanese_Grand_Prix.json` | 3 | `-y 2025 -r "Japanese Grand Prix" -s R` | ✅ 已驗證 |
| `team_pitstop_ranking_2025_Japanese_Grand_Prix.json` | 4 | `-y 2025 -r "Japanese Grand Prix" -s R` | ✅ 已驗證 |
| `driver_detailed_pitstop_records_2025_Japan_R.json` | 5 | `-y 2025 -r Japan -s R` | ✅ 已驗證 |
| `all_incidents_summary_2025_Japan.json` | 8 | `-y 2025 -r Japan -s R` | ✅ 已驗證 |

## 待後續追蹤事項
- FastAPI 服務現已支援 10 項核心功能，若需擴充更多 CLI 分析（例如事故統計、年度報表等），須持續擴大 `SimpleF1AnalysisService` 與路由的映射範圍。
- Pydantic `config`／`min_items`／`max_items` 及 FastAPI `regex` 參數皆出現棄用警告，需排期重構。
- `enhanced_rain_analysis` 作為增強輸出僅存於快取檔案，可評估是否需要 API 端加掛額外端點或於功能 1 響應中含括。

## 驗證標準
- FastAPI 伺服器成功啟動且可接受請求（根路徑與文件端點狀態碼皆為 200）。
- 針對 Japan 2025 R 場景，所有測試端點回傳 `success=True` 並提供有效資料。
- `json/` 目錄僅保留 Japan 2025 R 相關檔案，其餘檔案已歸檔。
- API 回傳內容與對應 JSON 檔案內容完全一致（欄位與值相符）。
- 每個 JSON 檔案皆能識別唯一 CLI 功能 ID，且 API 測試使用相同功能執行。
- 測試與比對過程中無未處理例外或 CLI 執行失敗。

## 參考命令
```powershell
# 啟動伺服器
python refactored_api.py

# 執行整合測試
python -m pytest tests/test_api_endpoints_integration.py -v --tb=short
```

## 備註
- 若測試中顯示 Pydantic/FastAPI 的廢棄警告，可記錄於備註，後續視情況重構。
- 若 CLI 行程耗時較長，建議確認快取目錄是否已有相應 JSON 以提升效率。
- JSON 比對建議優先使用 Python `json` 模組載入後比較字典（避免純文字排序影響）。
- JSON ↔ 功能 ID 對照可建立於表格或附錄，供後續 GUI/CLI 同步參考。
