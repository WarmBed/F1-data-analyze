# 開發任務：Track Map 與 Lap Analysis 連動同步標記

## 背景
- 目前圈速分析模組（Lap Analysis）已支援距離為基準的垂直 X 軸同步與固定線模式。
- Track Map 模組能渲染賽道路徑，但尚未視覺化顯示與 Lap Analysis 互動的實際位置。
- 目標是讓使用者在 Lap Analysis 滑鼠移動或固定距離時，於 Track Map 上同步顯示對應的綠色動態標記與紅色固定標記，以提升遙測對應體驗。

## 任務範圍
1. **資料對齊與索引建立**
   - 確認 `track_map_widget` 使用的 `position_data` 每筆均含 `distance_m` 欄位。
   - 建立距離→座標索引與最近點搜尋機制，支援快速定位特定距離對應的 `(x, y)`。
   - 處理資料缺漏（例如距離不連續或長度不同）時的容錯策略。

2. **Track Map 連動支援**
   - 讓 `TrackMapWidget` 註冊到 `linkage_manager`，接收 `send_x_linkage` 與 `send_click_linkage` 事件。
   - 實作綠色動態標記（滑鼠/連動距離）與紅色固定標記（固定距離）的繪製與樣式設定。
   - 遵循 API-ONLY 政策，僅使用既有資料或 API 回傳內容，不觸發 CLI。

3. **連動狀態管理與 UI 控制**
   - 新增屬性與方法控制 Track Map 游標顯示，確保與主連動開關、個別開關一致。
   - 視需求於 Track Analysis 模組 UI 增加選項（如 checkbox）來切換游標顯示。
   - 確保關閉連動或清除固定線時，同步清除 Track Map 上的標記。

4. **Lap Analysis 發送端檢查**
   - 檢視現有 Lap Analysis 模組是否已透過 linkage manager 廣播距離／固定線事件。
   - 若僅限於圖表內傳遞，需調整為對全域 linkage 廣播，或明確暴露距離資料供 Track Map 訂閱。
   - 確保訊號傳遞不造成循環更新或效能問題。

5. **測試與驗證**
   - 撰寫或更新單元／整合測試，覆蓋：距離索引計算、游標繪製狀態切換、連動訊號收發。
   - 手動驗證流程：同時開啟至少一個 Lap Analysis 圖表與 Track Map，確認滑鼠移動與固定距離標記同步。
   - 執行 `python -m pytest tests/ -v --tb=short` 確認既有測試維持綠燈。

## 里程碑
- M1：完成資料索引與 Track Map → linkage 註冊骨架。
- M2：Track Map 綠／紅標記繪製及 UI 控制完成。
- M3：Lap Analysis 發送端確認與必要調整。
- M4：測試與文件更新。

## 成功標準
- Lap Analysis 圖表移動滑鼠時，Track Map 能即時顯示綠色動態標記且對應距離無誤。
- 在 Lap Analysis 設置固定垂直線後，Track Map 顯示紅色固定標記並保持位置，直到手動清除。
- 連動關閉或清除時，Track Map 不再顯示標記，界面保持一致。
- 所有自動化測試與手動驗證通過。

## 風險與緩解
- **距離資料缺失或精度不足**：先檢查 JSON 結構，必要時在資料層新增插值或容錯邏輯。
- **效能問題**：大量位置點可能影響即時繪圖；需評估更新策略（例如快取最近索引）。
- **訊號循環**：確保 Track Map 僅接收連動而不回傳，以避免重複觸發。

## 檢核清單
- [x] Track Map 建立距離查找與座標映射機制。
- [x] Track Map 成功註冊 linkage 並能顯示綠色連動標記。
- [x] 固定距離模式在 Track Map 顯示紅色標記並可清除。
- [x] 連動狀態切換與 UI 操作一致。
- [x] 單元／整合測試與手動驗證完成，結果記錄。

## 測試紀錄
- 2025-10-05：`pytest tests/test_track_map_linkage.py -v --tb=short`（PASS）
