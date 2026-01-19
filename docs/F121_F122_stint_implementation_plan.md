# F121 & F122 Stint Selection 功能實作計畫

## 1. 目標 (Objective)
將 F120 (Corner Analysis) 已實作的 **Stint Selection (分段分析)** 功能擴展至 **F121 (Straight Line Analysis)** 與 **F122 (Brake Analysis)**。
這將允許使用者針對特定的 Stint（例如：Soft 胎 Long Run、Quali Sim）分析直線極速表現與煞車性能，提供更細緻的賽車工程洞察。

## 2. 適用範圍 (Scope)
-   **F121**: `CLI_modules/cli/analyzer/fp2_straight_line_all_laps_analysis.py`
-   **F122**: `CLI_modules/cli/analyzer/brake_all_laps_analysis.py`
-   **JSON 輸出**: 兩個模組的輸出 JSON 都將遵循 F120 確立的新標準（新增 `stints` 欄位）。

## 3. 架構設計 (Architecture)

### 3.1 共用 Stint 偵測邏輯
為符合「通用模組優先」原則，建議將 `_detect_stints` 邏輯標準化。雖然目前各分析模組獨立，但在實作時將確保邏輯與 F120 完全一致：
1.  **Stint 切分點**: `PitIn`, `PitOut`, `TyreLife` 重置 (<= 2)。
2.  **Stint 分類**:
    -   `long_run`: 連續圈數 >= 5
    -   `quali_sim`: 連續圈數 <= 3 (且在 FP2 後半段或典型排位模擬特徵)
    -   `unknown`: 其他

### 3.2 F121 (Straight Line) 實作細節
**現狀**: `_analyze_unified_mode` 統一分析所有圈數。
**修改計畫**:
1.  **新增方法**: 複製/實作 `_detect_stints` 與 `_build_stint_data`。
2.  **修改分析流**:
    -   在 `_analyze_unified_mode` 中，為每位車手調用 `_detect_stints`。
    -   針對每個 Detected Stint，調用 `_analyze_driver_straight_speed(driver, main_straight, stint_laps)`。
    -   注意：需修改 `_analyze_driver_straight_speed` 或其調用方式以接受特定的 `driver_laps` 子集（目前它內部自行抓取該車手所有圈）。
3.  **JSON 結構**:
    ```json
    "drivers": [
      {
        "driver": "VER",
        "stints": [
          {
            "stint_id": 1,
            "type": "long_run",
            "straight_stats": { ... }, // 該 Stint 的直線統計
            "acceleration_stats": { ... } // 該 Stint 的加速統計
          }
        ],
        "speed_stats": { ... } // [KEEP] 向後兼容的總體數據
      }
    ]
    ```

### 3.3 F122 (Brake) 實作細節
**現狀**: `_analyze_unified_mode` 遍歷所有有效圈並統計。
**修改計畫**:
1.  **新增方法**: 複製/實作 `_detect_stints` 與 `_build_stint_data`。
2.  **修改分析流**:
    -   在 `_analyze_unified_mode` 中，為每位車手調用 `_detect_stints`。
    -   針對每個 Stint，遍歷其 `lap_range` 內的圈數。
    -   對這些圈數調用 `_analyze_brake_performance_in_zone` 收集數據。
    -   計算該 Stint 的統計指標（中位數、CV 等）。
3.  **JSON 結構**:
    ```json
    "drivers": [
      {
        "driver": "VER",
        "stints": [
          {
            "stint_id": 1,
            "type": "long_run",
            "brake_stats": { ... }, // 該 Stint 的煞車統計
            "entry_speed_stats": { ... }
          }
        ],
        "brake_decel_stats": { ... } // [KEEP] 向後兼容
      }
    ]
    ```

## 4. 執行步驟 (Execution Steps)

### 第一階段：程式碼修改
1.  **F121 修改**: 更新 `fp2_straight_line_all_laps_analysis.py`。
    -   導入 Stint 偵測邏輯。
    -   重構 `_analyze_driver_straight_speed` 以支援傳入自定義 `laps` DataFrame。
    -   整合至主分析流程。
2.  **F122 修改**: 更新 `brake_all_laps_analysis.py`。
    -   導入 Stint 偵測邏輯。
    -   新增 Stint 統計計算邏輯。

### 第二階段：驗證
1.  **測試腳本**: 擴充 `test_f120_stints.py` 或新建 `test_f121_f122_stints.py`。
2.  **檢查點**:
    -   確認 JSON 包含 `stints_available: true`。
    -   確認 `stints` 陣列存在且數據非空。
    -   確認舊有欄位結構未變（向後兼容）。

## 5. 風險評估 (Risks)
-   **JSON 大小增加**: 每個 Stint 都包含詳細數據可能導致 JSON 檔案變大，需監控對 GUI 載入效能的影響。
-   **數據稀疏性**: 若 Stint 圈數過少（例如 < 3 圈），統計數據（如 CV、標準差）可能無意義或誤導。需在 GUI 端或 JSON 生成時處理此類邊界情況（例如標記 "insufficient_data"）。

## 6. GUI 整合建議
-   F120, F121, F122 三者在 GUI 端應共用同一套 Stint Selector UI 組件。
-   當使用者在 F120 選擇了 "Stint 2"，切換到 F121/F122 分頁時，理想情況下應保持選擇狀態（連動分析）。
