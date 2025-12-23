# Live Timing - Laps in Traffic（距離門檻版）規格

## 0. 反幻覺編碼五原則（最高優先）
- 不懂就問
- 確認需求才實作
- 任何方法/欄位呼叫前先用 grep_search/read_file 驗證存在
- 優先複用 modules/gui 與 CLI_modules 既有工具
- print 輸出會被 logger 導出到 log，若需追查請查看 log

## 1. 目標
在 Live Timing Playback（PKL 快照）上計算：
- `laps_in_traffic`：車手「被前車困住」的圈數
- `time_in_traffic_ratio`：整場（或有效時間）「在 traffic 狀態」的時間比例

本版本採用「距離門檻（米）」判定 traffic，不使用「2 秒」門檻。

## 2. 資料來源（已驗證）
資料檔：`data/live_timing_cache/{year}/{year}_{race}_{session}.pkl`

以 `data/live_timing_cache/2025/2025_Abu_Dhabi_Race.pkl` 實測：
- `snapshots`: list，len 約 2 萬
  - snapshot keys：`current_lap`, `race_time`, `race_time_seconds`, `drivers`
  - drivers[driver_num] keys（至少包含）：`x`, `y`, `z`, `speed`, `position`, `lap`, `in_pit`, `status`
- `track_status`: list，每筆 `{timestamp, data}`，data keys：`Status`, `Message`
- `race_control_messages`: list，每筆 `{timestamp, data}`，data keys：`Messages`

## 3. 名詞定義
- **traffic（交通/跟車受阻）**：車手在賽道上行駛時，其「道路順序的前車」與其沿賽道的前方距離小於等於 `traffic_distance_threshold_m`。
- **道路順序前車**：使用 snapshot 中的 `position` 推導（同一時間點 position = p 的前車為 position = p-1）。
- **有效時間**：排除車手在 pit lane、缺值、或整圈被 SC/VSC 標記排除後的時間。

## 4. 輸入參數（需提供，可設預設）
- `traffic_distance_threshold_m`：距離門檻（米）
- `lap_traffic_ratio_threshold`：判定「該圈算 traffic 圈」所需的時間比例門檻（0-1）
- `exclude_track_status_codes`：要排除的賽道狀態碼集合（SC/VSC）

### 4.1 已確認預設值
- `traffic_distance_threshold_m = 50`
- `lap_traffic_ratio_threshold = 0.5`

備註：實作時應提供可調參數與預設值。

## 5. 距離計算方法（核心）
### 5.1 需求
我們需要「沿賽道前方距離」（非直線距離）。

### 5.2 可行且最小化的近似
注意：Live Timing 的 `x/y` 通常是「地圖座標單位」（不保證直接等於公尺）。

因此必須先做 **XY→公尺** 的比例校準：
- 取連續兩個快照
- `ds_xy = sqrt((x2-x1)^2 + (y2-y1)^2)`
- `ds_speed_m = (speed_kmh / 3.6) * dt_s`
- 將 `meters_per_xy_unit = median(ds_speed_m / ds_xy)` 作為換算比例（需濾除缺值/異常 dt/速度）
- 最終 `ds_m = ds_xy * meters_per_xy_unit`

接著使用每車的 XY 連續點做路徑積分，得到「單圈內累積距離」`s_lap_m`：
- 同一車手、同一圈：
  - 對 consecutive snapshots 計算 `ds_xy = sqrt((x2-x1)^2 + (y2-y1)^2)`
  - 換算 `ds_m = ds_xy * meters_per_xy_unit`
  - 累加得到 `s_lap_m`
- 換圈（driver_lap 變動）時重置 `s_lap_m = 0`

接著估計賽道單圈長度 `track_length_m`：
- 對多位車手的多圈 `s_lap_m` 最終值取中位數/平均（需排除 in_pit/缺值圈）

最後定義全域距離 `S_global_m = lap_index * track_length_m + s_lap_m`。

### 5.3 前車距離
對同一 snapshot：
- 找到 driver 的前車 ahead（position-1，並且 ahead 不在 pit）
- 計算 `gap_m = S_global_m(ahead) - S_global_m(driver)`
- 若 `gap_m < 0`，加上 `track_length_m` 做 wrap（跨終點線的情形）
- traffic 判定：`gap_m <= traffic_distance_threshold_m`

## 6. SC/VSC 整圈排除
使用 `track_status` 的狀態碼做時間對齊：
- 先把 `track_status` 轉成時間區間（下一筆 timestamp 前都視為同狀態）
- 對每一圈（以 driver 的 lap 切分出該圈的時間範圍）
  - 若該圈任一時間點落在 `exclude_track_status_codes`，則整圈排除（該圈不計入分母，也不計入 traffic 圈數）

備註：timestamp 格式可能是字串（例如 `00:59:52.792`），需先轉成秒並與 snapshot 的 `race_time_seconds` 對齊。

## 7. Pit lane / 缺值處理
- `in_pit == True` 的時間片段：不計入有效時間
- 若 driver 或 ahead 缺少 `x/y` 或 lap/position 缺值：該時間片段跳過
- 若 `dt`（相鄰快照時間差）異常（例如 <=0 或過大）：該片段跳過，避免影響比例

## 8. 輸出格式（建議 JSON schema）
建議輸出每位車手：
```json
{
  "year": 2025,
  "race": "Abu Dhabi",
  "session": "R",
  "traffic_distance_threshold_m": 50,
  "lap_traffic_ratio_threshold": 0.5,
  "drivers": {
    "1": {
      "driver_tla": "VER",
      "laps_in_traffic": 12,
      "time_in_traffic_ratio": 0.31,
      "per_lap": [
        {"lap": 1, "traffic_ratio": 0.10, "excluded": false},
        {"lap": 2, "traffic_ratio": 0.62, "excluded": false}
      ]
    }
  }
}
```

## 9. 下一步
- 決定預設 `traffic_distance_threshold_m` 與 `lap_traffic_ratio_threshold`
- 在 CLI 端先做離線計算與 JSON 輸出（GUI 僅透過 API/讀 JSON 顯示）
- 用至少一場賽事（例如 Abu Dhabi R）做 sanity check：
  - traffic ratio 分佈合理
  - SC/VSC 圈確實整圈排除
