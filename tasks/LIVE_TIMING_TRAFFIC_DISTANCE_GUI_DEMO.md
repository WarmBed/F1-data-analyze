# Live Timing Traffic Distance GUI Demo (F127)

## 目標

在 GUI 中新增一個 Live Timing 子視窗，用來讀取既有的 F127 輸出 JSON（本地檔案），並以表格方式顯示每位車手的 traffic 統計。

## 限制與原則

- 僅允許讀取既有本地 JSON 檔案（API-ONLY 模式，禁止 GUI 直接呼叫 CLI）。
- 先以範例檔案 `json/live_timing_traffic_distance_2025_Abu_Dhabi_R.json` 進行 DEMO。
- 所有使用者可見字串必須使用 `tr()`。

## 交付內容

- 新增 Live Timing 模組：Traffic Distance
  - 顯示資訊（label）：年份/賽事/賽段、參數（50m / 0.5）、derived（track length、xy scale）、來源檔名
  - 顯示表格：每位車手 driver_tla、team、laps_analyzed、laps_in_traffic、time_in_traffic_ratio
- 掛載到 Live Timing 選單（與其他 Live Timing 模組一致）

## 測試計畫（三階段）

1. Import 測試
   - `python -c "from modules.gui.live_timing.live_timing_modules.traffic_distance import TrafficDistanceMDI"`
2. ModuleFactory 驗證
   - `python -c "from modules.gui.live_timing.core.module_factory import LiveTimingModuleFactory; print(LiveTimingModuleFactory.get_module_key('Traffic Distance'))"`
3. GUI 手動測試
   - 啟動 GUI，從 Live Timing 選單開啟 Traffic Distance
   - 確認能載入 Abu Dhabi 2025 R 的 JSON 並顯示表格內容
