# Brake Analysis 時間軸功能實施進度

## 📅 開始時間：2025-10-12

## ✅ 已完成步驟

### BrakeChartWidget 修改（`brake_analysis_chart_widget.py`）

- [x] **步驟 1**: 添加時間軸屬性到 `__init__`
  - ✅ `self.use_time_axis = False`
  - ✅ `self.driver1_time = []`
  - ✅ `self.driver2_time = []`

- [x] **步驟 2**: 修改 `set_brake_data()` 方法
  - ✅ 添加 `driver1_time` 和 `driver2_time` 參數
  - ✅ 儲存時間數據
  - ✅ 根據 `use_time_axis` 模式計算 X 軸範圍
  - ✅ 添加調試輸出

- [x] **步驟 3**: 添加 `set_time_axis_mode()` 方法
  - ✅ 切換時間軸模式
  - ✅ 重新計算 X 軸範圍
  - ✅ 重置視圖狀態
  - ✅ 強制重繪

- [x] **步驟 4**: 修改 `_draw_axes()` 方法
  - ✅ X 軸刻度格式化（時間: 浮點, 距離: 整數）
  - ✅ X 軸標題切換（"時間 (s)" / "距離 (m)"）

- [x] **步驟 5**: 修改 `_draw_brake_curves()` 方法
  - ✅ 根據時間軸模式選擇 X 軸數據源
  - ✅ 車手1使用 `driver1_time` 或 `distance_data`
  - ✅ 車手2使用 `driver2_time` 或 `distance_data`

---

## 🔲 待完成步驟

### BrakeChartWidget 修改（續）

- [ ] **步驟 6**: 修改 `_draw_tracking_line()` 方法
  - [ ] 根據模式選擇搜索數據源
  - [ ] 標籤顯示切換（"時間: XX.XX s" / "距離: XXXX m"）
  - [ ] 更新數據點搜索邏輯

- [ ] **步驟 7**: 修改 `_draw_linkage_line()` 方法
  - [ ] 根據模式選擇搜索數據源
  - [ ] 連動線標籤切換（"連動時間" / "連動距離"）

---

### BrakeAnalysisChartWidget 修改（包裝類）

- [ ] **步驟 8**: 添加 `set_time_axis_mode()` 代理方法
  - [ ] 找到包裝類定義
  - [ ] 添加代理方法轉發到 `self.chart_widget`

- [ ] **步驟 9**: 修改 `update_brake_data()` 方法
  - [ ] 提取時間數據 `driver1_time_seconds`, `driver2_time_seconds`
  - [ ] 傳遞給 `chart_widget.set_brake_data()`

---

### BrakeAnalysisModule 修改（MDI）

- [ ] **步驟 10**: 修改 `update_lap_parameters()` 方法
  - [ ] 添加 `use_time_axis: bool = False` 參數
  - [ ] 儲存 `self.use_time_axis`
  - [ ] 調用 `self.brake_chart_widget.set_time_axis_mode(use_time_axis)`

---

## 📊 預計完成時間

- **剩餘步驟**: 5 個
- **預計時間**: 15-20 分鐘
- **預計總時間**: 30-45 分鐘

---

## 🧪 測試清單

完成所有步驟後需要測試：

- [ ] 勾選 Use Time Axis → X 軸切換到時間 (s)
- [ ] 取消勾選 → X 軸切回距離 (m)
- [ ] X 軸範圍正確（時間: 0-95s, 距離: 0-5288m）
- [ ] 滑鼠追蹤線標籤顯示正確
- [ ] 固定垂直線標籤顯示正確
- [ ] 連動線標籤顯示正確
- [ ] 曲線數據對齊正確

---

## 📝 下一步行動

1. 完成步驟 6-7（追蹤線和連動線標籤）
2. 完成步驟 8-9（包裝類修改）
3. 完成步驟 10（MDI 修改）
4. 執行測試
5. 修復任何發現的問題
6. 提交 Brake Analysis 完成
7. 繼續下一個模組（Throttle Analysis）
