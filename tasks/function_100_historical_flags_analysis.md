# 任務：功能 100 - 歷年旗幟統計分析

## 📋 任務概述

創建新的 CLI 功能 (Function 100)，用於分析特定賽道在 2020-2025 年期間的旗幟統計數據。

## 🎯 目標

1. **歷年賽道旗幟統計**
   - 掃描 2020-2025 年的賽事數據
   - 統計每年的 Yellow Flag、Double Yellow Flag、Red Flag、Safety Car 數量
   - 如果該年尚未完賽則自動跳過

2. **彎道級別旗幟分析**
   - 識別每個彎道在各年份的旗幟事件
   - 統計每個彎道的 Yellow Flag、Double Yellow Flag、Red Flag 數量
   - 識別最危險的彎道區域

3. **自動更新機制**
   - 類似功能 97 (Championship Standings) 的自動更新邏輯
   - 檢測賽季是否完賽，避免處理不存在的數據

## 📊 數據結構設計

### JSON 輸出格式

```json
{
  "metadata": {
    "circuit_name": "Suzuka",
    "country": "Japan",
    "years_analyzed": [2020, 2021, 2022, 2023, 2024],
    "total_years": 5,
    "corners_count": 18,
    "generated_at": "2025-11-09T10:30:00"
  },
  "yearly_summary": {
    "2020": {
      "yellow_flags": 5,
      "double_yellow_flags": 2,
      "red_flags": 1,
      "safety_cars": 1,
      "total_incidents": 9,
      "session_type": "R"
    },
    "2021": { ... }
  },
  "corner_analysis": {
    "T1": {
      "corner_number": 1,
      "corner_name": "Turn 1",
      "total_flags": 3,
      "yearly_breakdown": {
        "2020": {"yellow": 1, "double_yellow": 0, "red": 0},
        "2021": {"yellow": 0, "double_yellow": 1, "red": 0},
        ...
      }
    },
    "T13": { ... }
  },
  "trends": {
    "most_dangerous_corner": "T13",
    "highest_incident_year": 2023,
    "total_flags_all_years": 45,
    "average_flags_per_year": 9.0,
    "safety_car_deployments": 4
  }
}
```

## 🔧 實現計劃

### 階段 1: 核心分析模組 ✅

**檔案**: `CLI_modules/cli/analyzer/historical_flags_analysis.py`

**主要功能**:
- `analyze_historical_flags(race: str, start_year: int, end_year: int)` - 主分析函數
- `extract_flag_events_from_session(session)` - 從 race_control_messages 提取旗幟事件
- `map_event_to_corner(event, corners_data)` - 將事件映射到彎道
- `aggregate_yearly_statistics(events_by_year)` - 彙總年度統計
- `generate_json_output(data, race)` - 生成 JSON 輸出

**數據來源**:
- FastF1: `session.race_control_messages` DataFrame
- FastF1: `session.circuit_info.corners` 彎道資訊
- 關鍵字識別: "YELLOW", "DOUBLE YELLOW", "RED FLAG", "SAFETY CAR"

### 階段 2: Function Mapper 整合 ✅

**檔案**: `CLI_modules/cli/core/function_mapper.py`

**修改項目**:
1. 在 `function_mapping` 字典中添加:
   ```python
   100: self._execute_historical_flags_analysis,  # 歷年旗幟統計分析
   ```

2. 實現 `_execute_historical_flags_analysis()` 方法:
   - 接受 `race` 參數（必需）
   - 接受 `start_year`, `end_year` 參數（可選，默認 2020-2025）
   - 調用核心分析模組
   - 返回標準化結果

3. 更新 `show_help()` 中的幫助文檔

### 階段 3: CLI 測試 ✅

**測試命令**:
```powershell
# 基本測試 - 鈴鹿賽道
python f1_analysis_modular_main.py -f 100 -r Japan

# 指定年份範圍
python f1_analysis_modular_main.py -f 100 -r Japan -y 2020

# 其他賽道測試
python f1_analysis_modular_main.py -f 100 -r Monaco
python f1_analysis_modular_main.py -f 100 -r Singapore
python f1_analysis_modular_main.py -f 100 -r Baku
```

**預期結果**:
- ✅ JSON 檔案生成在 `json/` 目錄
- ✅ 檔案命名: `historical_flags_CIRCUIT_2020-2025_TIMESTAMP.json`
- ✅ 包含完整的年度統計和彎道分析
- ✅ 自動跳過未完賽的年份
- ✅ 終端顯示統計摘要

## ✅ 驗證清單

### 功能驗證
- [ ] 能夠成功載入 2020-2025 年的賽事數據
- [ ] 正確識別 Yellow Flag、Double Yellow Flag、Red Flag、Safety Car
- [ ] 正確映射事件到彎道位置
- [ ] 自動跳過未完賽的年份
- [ ] JSON 結構符合設計規範
- [ ] 檔案命名正確且包含時間戳

### 數據準確性
- [ ] 與現有功能 6 (accident_statistics_summary) 的數據一致
- [ ] 彎道映射準確（基於 sector 或 message 中的位置資訊）
- [ ] 年度統計加總正確
- [ ] 趨勢分析邏輯正確

### 錯誤處理
- [ ] 賽道不存在時顯示清晰錯誤訊息
- [ ] 年份超出範圍時正確處理
- [ ] FastF1 API 失敗時優雅降級
- [ ] 缺少彎道資訊時使用 sector 估計

### 性能
- [ ] 多年數據載入時間合理（< 5 分鐘）
- [ ] 使用 FastF1 緩存避免重複下載
- [ ] 進度顯示清晰（顯示當前處理的年份）

## 📝 開發注意事項

### 遵循開發原則
1. **禁用模擬數據政策**: 只使用真實的 FastF1/OpenF1 數據
2. **PowerShell 命令標準**: 所有測試命令使用 PowerShell 語法
3. **不需要節省 token**: 完整詳盡的實現和註解
4. **參考現有實現**: 
   - 功能 6: 旗幟事件識別邏輯
   - 功能 97: 自動更新和年份掃描機制
   - `generate_yellow_flag_statistics.py`: 彎道映射邏輯

### 關鍵技術決策
1. **彎道識別方法**:
   - 優先: 從 message 文本中提取彎道號碼 (regex)
   - 次要: 基於 Sector 推斷彎道範圍
   - 備用: 標記為 "unknown corner"

2. **年份篩選邏輯**:
   ```python
   try:
       session = fastf1.get_session(year, race, 'R')
       session.load()
   except Exception:
       # 該年份賽事不存在或未完賽，跳過
       continue
   ```

3. **JSON 檔案命名**:
   - 格式: `historical_flags_{circuit}_{start_year}-{end_year}_{timestamp}.json`
   - 範例: `historical_flags_Japan_2020-2025_20251109_103000.json`

## 🔄 進度追蹤

- [x] 任務規劃完成
- [ ] 核心分析模組實現
- [ ] Function Mapper 整合
- [ ] 基本功能測試
- [ ] 多賽道測試
- [ ] 錯誤處理完善
- [ ] 文檔更新
- [ ] 最終驗證

## 📚 相關功能參考

- **功能 6** (`accident_statistics_summary`): 旗幟事件識別
- **功能 8** (`all_incidents_summary`): 詳細事件列表
- **功能 97** (`championship_standings_analysis`): 多年數據掃描
- **現有腳本** (`generate_yellow_flag_statistics.py`): 彎道映射邏輯

## 🎯 成功標準

1. ✅ CLI 命令執行成功，無錯誤
2. ✅ JSON 輸出包含所有必需欄位
3. ✅ 數據準確性與功能 6 一致
4. ✅ 能處理至少 5 個不同賽道
5. ✅ 自動跳過未完賽年份
6. ✅ 終端輸出清晰易讀
7. ✅ 執行時間 < 5 分鐘（單賽道 6 年數據）

---

**創建時間**: 2025-11-09  
**預計完成**: 2025-11-09  
**功能 ID**: 100  
**優先級**: High
