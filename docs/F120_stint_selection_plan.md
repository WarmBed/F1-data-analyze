# F120 Stint Selection 功能實作計畫

## 1. 目標 (Objective)
提升 `CLI-f120` (FP2 Corner All Laps Analysis) 的輸出粒度，使其能夠提供更詳細、更具情境的 FP2 數據。核心目標是讓 GUI 使用者能夠針對特定的 **Stint**（例如：使用 Soft 胎的 Long Run、Quali Sim）進行彎道表現分析，而不僅僅是查看整場練習賽的平均數據。

## 2. 架構設計 (Architecture)

### 2.1 數據流 (Data Flow)
1.  **CLI (資料生產者)**: 分析 FP2 數據，自動識別 Stint，計算每個 Stint 的統計數據，並生成結構化的 JSON 報告。
2.  **JSON (資料介面)**: 擴充現有的 JSON 格式，新增 `stints` 陣列，包含詳細的分組數據，同時保持 `corners` 欄位以支援舊版 GUI。
3.  **GUI (資料消費者)**: 讀取 JSON，若偵測到 `stints_available: true`，則顯示 Stint 選擇器供使用者篩選數據。

### 2.2 JSON 結構變更
```json
{
  "stints_available": true,  // [NEW] 標記此檔案包含 Stint 數據
  "mode_a_unified": {
    "drivers": [
      {
        "driver": "VER",
        "stints": [          // [NEW] Stint 列表
          {
            "stint_id": 1,
            "compound": "SOFT",
            "lap_range": [5, 12],
            "lap_count": 8,
            "type": "long_run",  // "long_run" | "quali_sim" | "unknown"
            "corners": {         // 該 Stint 的彎道統計
              "low_speed_corner_13": { "median_speed": 95.0, ... }
            },
            "laps_detail": [     // 該 Stint 的每圈詳情
               { "lap_number": 5, "lap_time": 80.123, "tyre_life": 3 }
            ]
          }
        ],
        "corners": { ... }   // [KEEP] 為了向後兼容保留的匯總數據
      }
    ]
  }
}
```

## 3. 實作細節 (Implementation Details)

### 3.1 CLI 端 (`CLI_modules/cli/analyzer/fp2_corner_all_laps_analysis.py`)
-   **狀態**: ✅ 已完成 (Verified)
-   **新增功能**:
    -   `_detect_stints(driver_laps)`: 基於進站事件 (`PitIn`/`PitOut`) 和輪胎更換 (`TyreLife` 重置) 自動切分 Stint。
    -   `_build_stint_data(...)`: 建構包含 `compound`, `type` (Long Run >= 5 laps), `laps_detail` 的物件。
    -   `_analyze_unified_mode`: 在分析迴圈中調用偵測邏輯，並為每個 Stint 獨立計算彎道統計數據。

### 3.2 GUI 端 (預計修改檔案)
-   **目標**: 實作 Stint 選擇與過濾功能。
-   **涉及模組**: `modules/gui/analysis_modules/corners_analysis_module.py` (假設名稱) 或對應的 GUI 顯示組件。
-   **待辦事項**:
    1.  檢查 JSON 頂層 `stints_available` 旗標。
    2.  若可用，啟用 "Filter by Stint" 下拉選單或側邊欄。
    3.  選單內容應顯示：`Stint X (SOFT) - 8 laps [Long Run]`。
    4.  選擇特定 Stint 時，更新圖表與數據表顯示該 `stint` 物件內的 `corners` 數據。
    5.  選擇 "All Stints" 時，顯示原本的頂層 `corners` 匯總數據。

## 4. 驗證計畫 (Verification Plan)
1.  **CLI 輸出驗證**: 使用 `test_f120_stints.py` 確認生成的 JSON 欄位正確且向後兼容。 (✅ 已完成)
2.  **批次生成驗證**: 執行 Batch Generator 確保大批量處理時能正確寫入新格式。 (⚠️ 進行中：需確保緩存更新)
3.  **GUI 整合測試**: 啟動 GUI，載入新生成的 JSON，確認 Stint 選擇器正常運作且數據切換正確。

## 5. 注意事項
-   **向後兼容性**: 必須保留 `drivers[].corners` 的扁平化統計數據，以防舊版檢視器崩潰。
-   **效能考量**: Stint 分組會增加 JSON 大小，但邏輯運算量增加不明顯，主要影響是在 JSON 序列化與 I/O。
-   **例外處理**: 若 Stint 檢測失敗或資料缺失，應優雅降級顯示 "Unknown Stint" 或僅顯示總體數據。
