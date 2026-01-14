# Ctrl+Z 撤銷系統實施計劃 (Undo System Implementation Plan)

**日期:** 2026-01-14
**目標:** 實現 `Ctrl+Z` 撤銷功能，支援恢復視窗、位置/大小、Tab 等操作。

## 1. 架構設計 (Architecture)

### 核心組件 (Core Components)

1.  **`WindowStateManager` (視窗狀態管理器)**
    *   負責管理視窗狀態的歷史堆疊 (History Stack)。
    *   提供 `push_state()` (記錄), `undo()` (撤銷), `redo()` (重做) 方法。
    *   管理 `WindowState` 快照。

2.  **`WindowState` (狀態快照)**
    *   Dataclass，用於儲存單一時間點的視窗狀態。
    *   包含：類型 (Close/Move/Resize), 標題, 幾何位置, 參數 (Params), Tab 索引等。

3.  **集成點 (Integration Points)**
    *   `f1t_gui_main.py`: 初始化 Manager，綁定 `Ctrl+Z` / `Ctrl+Y` 快捷鍵。
    *   `popout_subwindow.py`: 在視窗變更 (移動/調整/關閉) 時觸發狀態記錄。
    *   `analysis_window_creator.py`: 提供 `create_analysis_window_with_params` 方法，用於根據快照重建視窗。

### 狀態類型 (State Types)

| 類型 | 代碼 | 描述 | 恢復行為 |
| :--- | :--- | :--- | :--- |
| **視窗關閉** | `WINDOW_CLOSE` | 視窗被關閉時 | 使用保存的參數和類型**重建**視窗 |
| **視窗移動** | `WINDOW_MOVE` | 拖動結束後 | 將視窗**移動**回舊位置 |
| **視窗調整** | `WINDOW_RESIZE` | 調整大小結束後 | 將視窗**恢復**到舊尺寸 |
| **Tab 關閉** | `TAB_CLOSE` | Tab 關閉前 | **重建** Tab 及其內部的視窗 |

---

## 2. 實施步驟 (Implementation Steps)

### 第一階段：核心模組 (已完成)

*   [x] **建立 `windows/managers/window_state_manager.py`**
    *   定義 `WindowStateManager` 類別。
    *   定義 `WindowState` 和 `StateType`。
    *   實現 `_restore_closed_window` 等恢復邏輯。

### 第二階段：主程式集成 (已完成)

*   [x] **修改 `windows/managers/analysis_window_creator.py`**
    *   新增 `create_analysis_window_with_params` 方法，支援從歷史記錄重建視窗。
*   [x] **修改 `f1t_gui_main.py`**
    *   在初始化時 (`init_ui` 或 `__init__`) 實例化 `WindowStateManager`。
    *   定義 `_init_window_state_manager()`。
    *   註冊 `Ctrl+Z` (Undo) 和 `Ctrl+Y` (Redo) 全局快捷鍵。

### 第三階段：事件捕獲 (進行中)

*   [ ] **修改 `windows/widgets/popout_subwindow.py`**
    *   **關閉事件**: 覆寫 `closeEvent`，在視窗真正關閉前，捕獲當前狀態並 push 到 Manager。
    *   **移動/調整事件**: 在 `mouseReleaseEvent` 中，如果檢測到位置或大小發生變化，push `WINDOW_MOVE` 或 `WINDOW_RESIZE` 狀態。

*   [ ] **修改 `windows/widgets/draggable_title_bar.py`** (如需要)
    *   確保標題欄拖動也能正確觸發狀態記錄。

### 第四階段：Tab 支援 (待辦)

*   [ ] **修改 Tab 關閉邏輯 (`f1t_gui_main.py` 或 Tab Manager)**
    *   在關閉 Tab 前，遍歷該 Tab 下所有視窗，生成 `TAB_CLOSE` 複合狀態。

---

## 3. 驗證計劃 (Verification Plan)

|測試項目 | 預期結果 |
| :--- | :--- |
| **單一視窗關閉** | 開啟視窗 A -> 關閉 -> 按 `Ctrl+Z` -> 視窗 A 重新出現，參數與位置正確。 |
| **視窗位置移動** | 移動視窗 A 到右下角 -> 按 `Ctrl+Z` -> 視窗 A 跳回原位。 |
| **連續操作撤銷** | 移動 -> 調整大小 -> 關閉 -> 連按 3 次 `Ctrl+Z` -> 依序恢復。 |
| **重做 (Redo)** | 撤銷後按 `Ctrl+Y` -> 重新執行該操作 (如再次關閉視窗)。 |
| **歷史限制** | 執行 > 10 次操作 -> 只能撤銷最後 10 步。 |

---

## 4. 風險與注意事項

1.  **視窗重建複雜度**
    *   部分複雜模組 (如即時數據模組) 重建時可能需要重新連接信號或初始化數據，需確保 `create_analysis_window_with_params` 能處理。
    
2.  **物件生命週期**
    *   `PyQt` 的 `deleteLater()` 可能導致在撤銷時嘗試訪問已刪除的物件。必須確保撤銷堆疊只存**數據 (Data)**，不存 **Widget 引用**。

3.  **記憶體管理**
    *   雖然限制 10 步，但若參數過大 (如大型數據集)，仍需注意。目前僅快照參數 (`parameters`)，應無大礙。
